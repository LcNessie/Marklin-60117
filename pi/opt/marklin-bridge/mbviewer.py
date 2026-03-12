#!/usr/bin/env python3
import argparse
import json
import locale
import time
import paho.mqtt.client as mqtt

try:
    import curses
except ImportError:
    import sys
    if sys.platform == 'win32':
        sys.exit("Error: 'curses' module not found. Please install it via pip: pip install windows-curses")
    else:
        raise

# --- Default Configuration ---
DEFAULT_BROKER_IP = "127.0.0.1"
DEFAULT_BROKER_PORT = 1883
DEFAULT_STATUS_TOPIC = "marklin/status"

class CursesUI:
    """Manages the curses-based terminal user interface for the status monitor."""

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
            self.stdscr.addstr(0, 0, f"Märklin Bridge Status Monitor", self.COLOR_PAIR_DEFAULT)
            next_line = 2
            
            # Helper to safely get data
            def get_val(key, default='N/A'):
                return status_data.get(key, default) if status_data else default

            # Helper to extract interface info
            def get_iface_info(iface_name):
                ifaces = get_val('interface_status', {})
                info = ifaces.get(iface_name, {})
                if isinstance(info, dict):
                    return info.get('status', 'UNKNOWN'), info.get('ip', 'N/A'), info.get('ssid')
                return info or 'UNKNOWN', 'N/A', None

            # --- [ CORE ] ---
            self.stdscr.addstr(next_line, 0, "-- Bridge --", self.COLOR_PAIR_DEFAULT)
            next_line += 1
            self.stdscr.addstr(next_line, 2, "Version:", self.COLOR_PAIR_DEFAULT)
            self.stdscr.addstr(next_line, 24, f"{get_val('version')}", self.COLOR_PAIR_DEFAULT)
            next_line += 1
            next_line += 2

            # --- [ LEG 1 ] Märklin Interface (WiFi) ---
            self.stdscr.addstr(next_line, 0, "-- Märklin Side --", self.COLOR_PAIR_DEFAULT)
            next_line += 1

            if not status_data:
                self.stdscr.addstr(next_line, 0, "Waiting for first status message...", self.COLOR_PAIR_YELLOW)
            else: # UP
                marklin_iface = get_val('marklin_interface', 'wlan0')
                status, ip, ssid = get_iface_info(marklin_iface)
                
                if status == "UP": icon, color = "🟢", self.COLOR_PAIR_DEFAULT
                else: icon, color = "🔴", self.COLOR_PAIR_RED
                
                if ssid:
                    self.stdscr.addstr(next_line, 2, f"Interface ({marklin_iface}):", self.COLOR_PAIR_DEFAULT)
                    self.stdscr.addstr(next_line, 24, f"{icon} {status} ({ssid})", color)
                else:
                    self.stdscr.addstr(next_line, 2, f"Interface ({marklin_iface}):", self.COLOR_PAIR_DEFAULT)
                    self.stdscr.addstr(next_line, 24, f"{icon} {status}", color)
                next_line += 1

                self.stdscr.addstr(next_line, 2, "Marklin Bridge IP:", self.COLOR_PAIR_DEFAULT)
                self.stdscr.addstr(next_line, 24, ip, self.COLOR_PAIR_DEFAULT)
                next_line += 1

                # Target IP (60117)
                target_ip = get_val('marklin_ip', 'N/A')
                self.stdscr.addstr(next_line, 2, "Marklin Wifi Box IP:", self.COLOR_PAIR_DEFAULT)
                self.stdscr.addstr(next_line, 24, target_ip, self.COLOR_PAIR_DEFAULT)
                next_line += 1

                # UDP Link
                link_status = get_val('link_status', 'UNKNOWN')
                if link_status == "DOWN": link_icon, link_color = "🔴", self.COLOR_PAIR_RED
                else: link_icon, link_color = "🟢", self.COLOR_PAIR_DEFAULT
                self.stdscr.addstr(next_line, 2, "UDP Link:", self.COLOR_PAIR_DEFAULT)
                self.stdscr.addstr(next_line, 24, f"{link_icon} {link_status}", link_color)
                next_line += 1

                # Track Power
                track_power = get_val('track_power', 'UNKNOWN')
                if track_power == "GO": power_icon, power_color = "🟢", self.COLOR_PAIR_GREEN
                elif track_power == "STOP": power_icon, power_color = "🔴", self.COLOR_PAIR_RED
                else: power_icon, power_color = "😵", self.COLOR_PAIR_YELLOW
                self.stdscr.addstr(next_line, 2, "Track Power:", self.COLOR_PAIR_DEFAULT)
                self.stdscr.addstr(next_line, 24, f"{power_icon} {track_power}", power_color)
                next_line += 1

                self.stdscr.addstr(next_line, 2, "UDP from Marklin:", self.COLOR_PAIR_DEFAULT)
                self.stdscr.addstr(next_line, 24, f"{get_val('packets_from_marklin', 0)}", self.COLOR_PAIR_DEFAULT)
                next_line += 1
                self.stdscr.addstr(next_line, 2, "UDP to Marklin:", self.COLOR_PAIR_DEFAULT)
                self.stdscr.addstr(next_line, 24, f"{get_val('packets_to_marklin', 0)}", self.COLOR_PAIR_DEFAULT)
                next_line += 1

            next_line += 2

            # --- [ LEG 2 ] Downlink (LAN/MQTT) ---
            self.stdscr.addstr(next_line, 0, "-- Network Side --", self.COLOR_PAIR_DEFAULT)
            next_line += 1

            if status_data:
                home_iface = get_val('home_interface', 'eth0')
                status, ip, ssid = get_iface_info(home_iface)

                if status == "UP": icon, color = "🟢", self.COLOR_PAIR_DEFAULT
                else: icon, color = "🔴", self.COLOR_PAIR_RED

                if ssid:
                    self.stdscr.addstr(next_line, 2, f"Interface ({home_iface}):", self.COLOR_PAIR_DEFAULT)
                    self.stdscr.addstr(next_line, 24, f"{icon} {status} ({ssid})", color)
                else:
                    self.stdscr.addstr(next_line, 2, f"Interface ({home_iface}):", self.COLOR_PAIR_DEFAULT)
                    self.stdscr.addstr(next_line, 24, f"{icon} {status}", color)
                next_line += 1

                self.stdscr.addstr(next_line, 2, "Bridge Home IP:", self.COLOR_PAIR_DEFAULT)
                self.stdscr.addstr(next_line, 24, ip, self.COLOR_PAIR_DEFAULT)
                next_line += 1

                self.stdscr.addstr(next_line, 2, "MQTT Broker IP:", self.COLOR_PAIR_DEFAULT)
                self.stdscr.addstr(next_line, 24, f"{get_val('mqtt_broker_ip')}", self.COLOR_PAIR_DEFAULT)
                next_line += 1

                mqtt_status = get_val('mqtt_status', 'UNKNOWN')
                if mqtt_status == "CONNECTED": mqtt_icon, mqtt_color = "🟢", self.COLOR_PAIR_GREEN
                else: mqtt_icon, mqtt_color = "🔴", self.COLOR_PAIR_RED
                self.stdscr.addstr(next_line, 2, "Bridge MQTT Status:", self.COLOR_PAIR_DEFAULT)
                self.stdscr.addstr(next_line, 24, f"{mqtt_icon} {mqtt_status}", mqtt_color)
                next_line += 1

                self.stdscr.addstr(next_line, 2, "MQTT from Broker:", self.COLOR_PAIR_DEFAULT)
                self.stdscr.addstr(next_line, 24, f"{get_val('packets_from_mqtt', 0)}", self.COLOR_PAIR_DEFAULT)
                next_line += 1
                self.stdscr.addstr(next_line, 2, "MQTT to Broker:", self.COLOR_PAIR_DEFAULT)
                self.stdscr.addstr(next_line, 24, f"{get_val('packets_to_mqtt', 0)}", self.COLOR_PAIR_DEFAULT)
                next_line += 2

            # Viewer MQTT Connection
            if connection_status == "CONNECTED": conn_icon, conn_color = "🟢", self.COLOR_PAIR_GREEN
            elif connection_status == "DISCONNECTED": conn_icon, conn_color = "🔴", self.COLOR_PAIR_RED
            else: conn_icon, conn_color = "🟡", self.COLOR_PAIR_YELLOW
            self.stdscr.addstr(next_line, 2, "Viewer MQTT:", self.COLOR_PAIR_DEFAULT)
            self.stdscr.addstr(next_line, 24, f"{conn_icon} {connection_status}", conn_color)
            next_line += 1

            # --- Bridge Activity (Legacy Grouping Removed, merged into Core/Legs) ---
            
            self.stdscr.addstr(next_line + 1, 0, "Press 'q' or Ctrl+C to exit.", self.COLOR_PAIR_DEFAULT)
            self.stdscr.refresh()
        except self.curses.error:
            pass # Ignore screen resize errors

def on_connect(client, userdata, flags, reason_code, properties):
    """Callback for when connection to MQTT broker is established (Paho v2)."""
    if reason_code == 0:
        userdata['connection_status'] = "CONNECTED"
        client.subscribe(userdata['topic'])
    else:
        userdata['connection_status'] = f"FAILED ({reason_code})"

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
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

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata=userdata)
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
    parser = argparse.ArgumentParser(description="A real-time status monitor for the Märklin UDP Bridge.")
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