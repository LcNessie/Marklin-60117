#!/usr/bin/env python3
import argparse
import curses
import json
import locale
import time
import paho.mqtt.client as mqtt

# --- Default Configuration ---
DEFAULT_BROKER_IP = "127.0.0.1"
DEFAULT_BROKER_PORT = 1883
DEFAULT_STATUS_TOPIC = "marklin/status"

class CursesUI:
    """Manages the curses-based terminal user interface for the diagnostic tool."""

    def __init__(self, stdscr):
        """Initializes the curses screen and color pairs."""
        self.curses = curses
        self.stdscr = stdscr
        self.curses.curs_set(0)
        self.stdscr.nodelay(True)

        self.COLOR_PAIR_DEFAULT = self.curses.A_NORMAL
        self.COLOR_PAIR_GREEN = self.curses.A_NORMAL
        self.COLOR_PAIR_RED = self.curses.A_NORMAL
        self.COLOR_PAIR_YELLOW = self.curses.A_NORMAL
        if self.curses.has_colors():
            self.curses.start_color()
            self.curses.use_default_colors()
            self.curses.init_pair(1, self.curses.COLOR_GREEN, -1)
            self.curses.init_pair(2, self.curses.COLOR_RED, -1)
            self.curses.init_pair(3, self.curses.COLOR_YELLOW, -1)
            self.COLOR_PAIR_GREEN = self.curses.color_pair(1)
            self.COLOR_PAIR_RED = self.curses.color_pair(2)
            self.COLOR_PAIR_YELLOW = self.curses.color_pair(3)

    def draw(self, status_data, connection_status):
        """Draws the entire UI based on the application's state."""
        try:
            self.stdscr.erase()
            self.stdscr.addstr(0, 0, f"Märklin Bridge Diagnostics Tool", self.COLOR_PAIR_DEFAULT)
            next_line = 2

            # --- Connection Status ---
            self.stdscr.addstr(next_line, 0, "-- MQTT Connection --", self.COLOR_PAIR_DEFAULT)
            next_line += 1
            if connection_status == "CONNECTED":
                conn_icon, conn_color = "🟢", self.COLOR_PAIR_GREEN
            elif connection_status == "DISCONNECTED":
                conn_icon, conn_color = "🔴", self.COLOR_PAIR_RED
            else:
                conn_icon, conn_color = "🟡", self.COLOR_PAIR_YELLOW
            self.stdscr.addstr(next_line, 2, "Broker Status:", self.COLOR_PAIR_DEFAULT)
            self.stdscr.addstr(next_line, 20, f"{conn_icon} {connection_status}", conn_color)
            next_line += 2

            if not status_data:
                self.stdscr.addstr(next_line, 0, "Waiting for first status message...", self.COLOR_PAIR_YELLOW)
                self.stdscr.refresh()
                return

            # --- System Status ---
            self.stdscr.addstr(next_line, 0, "-- Bridge Status --", self.COLOR_PAIR_DEFAULT)
            next_line += 1
            self.stdscr.addstr(next_line, 2, "Version:", self.COLOR_PAIR_DEFAULT)
            self.stdscr.addstr(next_line, 20, f"{status_data.get('version', 'N/A')}", self.COLOR_PAIR_DEFAULT)
            next_line += 1
            self.stdscr.addstr(next_line, 2, "UDP Link:", self.COLOR_PAIR_DEFAULT)
            link_status = status_data.get('link_status', 'UNKNOWN')
            if link_status == "DOWN":
                link_icon, link_color = "😵", self.COLOR_PAIR_YELLOW
            else: # UP
                link_icon, link_color = "🟢", self.COLOR_PAIR_DEFAULT
            self.stdscr.addstr(next_line, 20, f"{link_icon} {link_status}", link_color)
            next_line += 1
            self.stdscr.addstr(next_line, 2, "Track Power:", self.COLOR_PAIR_DEFAULT)
            track_power = status_data.get('track_power', 'UNKNOWN')
            if track_power == "GO": power_icon, power_color = "🟢", self.COLOR_PAIR_GREEN
            elif track_power == "STOP": power_icon, power_color = "🔴", self.COLOR_PAIR_RED
            else: power_icon, power_color = "🟡", self.COLOR_PAIR_YELLOW
            self.stdscr.addstr(next_line, 20, f"{power_icon} {track_power}", power_color)
            next_line += 2

            # --- Interface Status ---
            self.stdscr.addstr(next_line, 0, "-- Network Interfaces --", self.COLOR_PAIR_DEFAULT)
            next_line += 1
            ifaces = status_data.get('interface_status', {})
            if ifaces:
                for iface, status in ifaces.items():
                    if status == "UP": iface_icon, iface_color = "🟢", self.COLOR_PAIR_DEFAULT
                    else: iface_icon, iface_color = "🔴", self.COLOR_PAIR_RED
                    self.stdscr.addstr(next_line, 2, f"{iface}:", self.COLOR_PAIR_DEFAULT)
                    self.stdscr.addstr(next_line, 20, f"{iface_icon} {status}", iface_color)
                    next_line += 1
            else:
                self.stdscr.addstr(next_line, 2, "No interface data available.", self.COLOR_PAIR_YELLOW)
                next_line += 1
            next_line += 1

            # --- Bridge Activity ---
            self.stdscr.addstr(next_line, 0, "-- Bridge Activity --", self.COLOR_PAIR_DEFAULT)
            next_line += 1
            self.stdscr.addstr(next_line, 2, "From Box:", self.COLOR_PAIR_DEFAULT)
            self.stdscr.addstr(next_line, 20, f"{status_data.get('packets_from_marklin', 0)}", self.COLOR_PAIR_DEFAULT)
            next_line += 1
            self.stdscr.addstr(next_line, 2, "To Box:", self.COLOR_PAIR_DEFAULT)
            self.stdscr.addstr(next_line, 20, f"{status_data.get('packets_to_marklin', 0)}", self.COLOR_PAIR_DEFAULT)
            next_line += 1
            self.stdscr.addstr(next_line, 2, "Last Source:", self.COLOR_PAIR_DEFAULT)
            self.stdscr.addstr(next_line, 20, f"{status_data.get('last_source', 'N/A')}", self.COLOR_PAIR_DEFAULT)
            
            self.stdscr.addstr(next_line + 2, 0, "Press 'q' or Ctrl+C to exit.", self.COLOR_PAIR_DEFAULT)
            self.stdscr.refresh()
        except self.curses.error:
            pass # Ignore screen resize errors

def on_connect(client, userdata, flags, rc):
    """Callback for when connection to MQTT broker is established."""
    if rc == 0:
        userdata['connection_status'] = "CONNECTED"
        client.subscribe(userdata['topic'])
    else:
        userdata['connection_status'] = f"FAILED ({rc})"

def on_disconnect(client, userdata, rc):
    """Callback for when the client disconnects from the MQTT broker."""
    userdata['connection_status'] = "DISCONNECTED"

def on_message(client, userdata, msg):
    """Callback for when a status message is received."""
    try:
        userdata['status_data'] = json.loads(msg.payload)
    except json.JSONDecodeError:
        userdata['status_data'] = {"error": "Invalid JSON received"}

def main_loop(stdscr, args):
    """The main application loop."""
    ui = CursesUI(stdscr)
    
    # Userdata dict to share state with MQTT callbacks
    userdata = {
        'status_data': None,
        'connection_status': 'CONNECTING',
        'topic': args.topic
    }

    client = mqtt.Client(userdata=userdata)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    if args.username:
        client.username_pw_set(args.username, args.password)

    try:
        client.connect(args.broker, args.port, 60)
    except Exception as e:
        # Curses is already running, so print error and wait for exit
        stdscr.erase()
        stdscr.addstr(0, 0, f"FATAL: Could not connect to MQTT broker at {args.broker}:{args.port}")
        stdscr.addstr(1, 0, f"Error: {e}")
        stdscr.addstr(3, 0, "Press any key to exit.")
        stdscr.nodelay(False)
        stdscr.getch()
        return

    client.loop_start()

    while True:
        ui.draw(userdata['status_data'], userdata['connection_status'])
        
        # Check for user input to quit
        try:
            key = stdscr.getch()
            if key == ord('q'):
                break
        except curses.error:
            # No input
            pass
        except KeyboardInterrupt:
            break
            
        time.sleep(0.1)

    client.loop_stop()
    client.disconnect()

def main():
    """Parses arguments and starts the curses wrapper."""
    parser = argparse.ArgumentParser(description="A real-time diagnostic tool for the Märklin UDP Bridge.")
    parser.add_argument('--broker', default=DEFAULT_BROKER_IP, help=f"IP address of the MQTT broker (default: {DEFAULT_BROKER_IP})")
    parser.add_argument('--port', type=int, default=DEFAULT_BROKER_PORT, help=f"Port of the MQTT broker (default: {DEFAULT_BROKER_PORT})")
    parser.add_argument('--topic', default=DEFAULT_STATUS_TOPIC, help=f"MQTT status topic to subscribe to (default: {DEFAULT_STATUS_TOPIC})")
    parser.add_argument('--username', help="MQTT username (optional)")
    parser.add_argument('--password', help="MQTT password (optional)")
    args = parser.parse_args()

    locale.setlocale(locale.LC_ALL, '')
    try:
        curses.wrapper(main_loop, args)
    except KeyboardInterrupt:
        print("\nExiting.")
    except Exception as e:
        print(f"\nA critical error occurred: {e}")

if __name__ == "__main__":
    main()