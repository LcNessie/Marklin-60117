import socket
import time
import signal
import argparse
import logging
import os
import json
from logging.handlers import RotatingFileHandler

# Local module imports
import config
import constants
import led
import mqtt_handler
import network_utils

try:
    import psutil
except ImportError:
    psutil = None # Allow running without psutil for network info

try:
    import coloredlogs
except ImportError:
    coloredlogs = None

class MarklinBridgeApp:
    """Encapsulates the entire Märklin Bridge application."""

    def __init__(self):
        # Resources
        self.status_led = None
        self.mqtt_client = None
        self.sock = None
        self.network_status_checker = network_utils.NetworkStatus()

        self.running = False
        # State
        self.link_status = constants.STATUS_DOWN
        self.track_power = constants.STATUS_UNKNOWN
        self.packets_from_marklin = 0
        self.packets_to_marklin = 0
        self.packets_from_mqtt = 0
        self.packets_to_mqtt = 0
        self.last_source = constants.STATUS_NA
        self.last_controller_addr = None # Stores (ip, port) of the last seen controller
        self.mqtt_status = constants.STATUS_NA # Set by mqtt_handler
        self.interface_status = {}

        # Timers
        self.last_marklin_packet_time = 0
        self.last_query_time = 0
        self.last_iface_check_time = 0
        self.last_status_publish_time = 0.0

    class ColoredFormatter(logging.Formatter):
        """Custom formatter to add colors to console logs."""
        grey = "\x1b[38;20m"
        green = "\x1b[32;20m"
        yellow = "\x1b[33;20m"
        red = "\x1b[31;20m"
        bold_red = "\x1b[31;1m"
        reset = "\x1b[0m"
        format_str = "%(asctime)s - %(levelname)s - %(message)s"

        FORMATS = {
            logging.DEBUG: grey + format_str + reset,
            logging.INFO: green + format_str + reset,
            logging.WARNING: yellow + format_str + reset,
            logging.ERROR: red + format_str + reset,
            logging.CRITICAL: bold_red + format_str + reset
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            if log_fmt is None:
                log_fmt = self.format_str
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    def _setup_logging(self):
        log_fmt = '%(asctime)s - %(levelname)s - %(message)s'
        logger = logging.getLogger() # Get the root logger
        logger.setLevel(logging.DEBUG) # Set to DEBUG for detailed troubleshooting

        if config.LOG_FILE:
            max_bytes = config.LOG_FILE_MAX_SIZE_MB * 1024 * 1024
            handler = RotatingFileHandler(config.LOG_FILE, maxBytes=max_bytes, backupCount=config.LOG_FILE_BACKUP_COUNT)
            handler.setFormatter(logging.Formatter(log_fmt))
            logger.addHandler(handler)
        else: # Default to stderr for journald
            if coloredlogs:
                # Use the level already set on the root logger
                coloredlogs.install(level=logger.level, fmt=log_fmt)
            else:
                handler = logging.StreamHandler()
                handler.setFormatter(self.ColoredFormatter())
                logger.addHandler(handler)

        logging.info(f"Starting Märklin UDP Bridge. Logging to {'journald/stderr' if not config.LOG_FILE else config.LOG_FILE}.")

    def _setup_gpio(self):
        """
        Initializes the status LED using the factory function in the led module.
        The factory handles all backend selection and error handling.
        """
        self.status_led = led.create_led_instance(config.config)

    def _setup_network(self):
        # Bind to '0.0.0.0' and the dedicated listening port (15730) to receive
        # packets on all interfaces. This is crucial for capturing UDP broadcasts
        # from the Märklin box after client registration.
        logging.info(f"Binding UDP socket to 0.0.0.0:%s", config.LISTEN_PORT)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Enable receiving broadcast packets. This is crucial for seeing the
        # "Go" and "Stop" commands which are sent as broadcasts by the Märklin box.
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind(("0.0.0.0", config.LISTEN_PORT))
        self.sock.setblocking(False)

    def _setup_mqtt(self):
        import paho.mqtt.client as mqtt
        logging.info(f"MQTT Gateway mode enabled. Connecting to {config.MQTT_BROKER_IP}:{config.MQTT_BROKER_PORT}")

        # Pass a reference to this app instance to the MQTT callbacks
        userdata = {'app': self}
        self.mqtt_status = 'CONNECTING'

        try:
            self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"marklin_bridge_{os.getpid()}", userdata=userdata)
            self.mqtt_client.on_message = mqtt_handler.on_mqtt_message
            self.mqtt_client.on_connect = mqtt_handler.on_mqtt_connect
            self.mqtt_client.on_disconnect = mqtt_handler.on_mqtt_disconnect
            if config.MQTT_USERNAME:
                self.mqtt_client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
            self.mqtt_client.connect(config.MQTT_BROKER_IP, config.MQTT_BROKER_PORT, constants.MQTT_KEEPALIVE_S)
            self.mqtt_client.subscribe(config.MQTT_TOPIC_TO_MARKLIN)
            self.mqtt_client.loop_start() # Start non-blocking background thread
        except Exception as e:
            message = f"FATAL: Could not connect to MQTT broker: {e}"
            logging.critical(message)
            raise ConnectionRefusedError(message) from e

    def _check_psutil(self):
        if not psutil:
            message = "Warning: 'psutil' library not found. Network interface info will be unavailable."
            logging.warning(message)

    def set_led_color(self, color):
        """Safely sets the LED color if the LED is initialized."""
        if self.status_led:
            self.status_led.set_color(color)

    def _check_interface_status(self):
        """Periodically checks the status of configured network interfaces."""
        if time.time() - self.last_iface_check_time > constants.IFACE_CHECK_INTERVAL_S:
            self.interface_status = {}
            interfaces_to_check = {config.MARKLIN_INTERFACE, config.HOME_INTERFACE}
            for iface in interfaces_to_check:
                if iface and iface != constants.STATUS_NA:
                    ip, status, ssid = self.network_status_checker.get_interface_info(iface)
                    self.interface_status[iface] = {
                        "status": status,
                        "ip": ip,
                        "ssid": ssid
                    }
            self.last_iface_check_time = time.time()

    def _publish_status(self):
        """Publishes the current application status to MQTT."""
        if not config.MQTT_ENABLED or not self.mqtt_client:
            return

        payload = {
            "version": constants.APP_VERSION,
            "link_status": self.link_status,
            "track_power": self.track_power,
            "interface_status": self.interface_status,
            "packets_from_marklin": self.packets_from_marklin,
            "packets_to_marklin": self.packets_to_marklin,
            "packets_from_mqtt": self.packets_from_mqtt,
            "packets_to_mqtt": self.packets_to_mqtt,
            "marklin_ip": config.MARKLIN_IP,
            "mqtt_broker_ip": config.MQTT_BROKER_IP,
            "mqtt_status": self.mqtt_status,
            "marklin_interface": config.MARKLIN_INTERFACE,
            "home_interface": config.HOME_INTERFACE
        }

        try:
            self.mqtt_client.publish(
                config.MQTT_STATUS_TOPIC,
                json.dumps(payload, indent=4),
                retain=True
            )
        except Exception as e:
            logging.warning("Could not publish status to MQTT: %s", e)

    def _check_connection_health(self):
        time_since_last_packet = time.time() - self.last_marklin_packet_time

        if time_since_last_packet > constants.CONNECTION_TIMEOUT_S:
            if self.link_status != constants.STATUS_DOWN:
                self.link_status = constants.STATUS_DOWN
                self.track_power = constants.STATUS_UNKNOWN
                self.set_led_color(led.COLOR_YELLOW_NO_LINK)
                logging.warning("Link to Märklin interface lost (timeout).")
                self._publish_status()

        # If the link is down or idle, send a query packet to elicit a response.
        should_probe = (self.link_status == constants.STATUS_DOWN) or (time_since_last_packet > constants.QUERY_INTERVAL_S)
        if should_probe and (time.time() - self.last_query_time > constants.QUERY_INTERVAL_S):
            logging.debug("Sending query packet to %s", config.MARKLIN_IP)
            self.sock.sendto(constants.QUERY_PACKET, (config.MARKLIN_IP, config.PORT))
            self.last_query_time = time.time()

    def _handle_marklin_packet(self, data):
        # Log every packet from the Märklin box at DEBUG level for diagnostics
        logging.debug(f"RX from {config.MARKLIN_IP}: {data.hex()}")

        if self.link_status != constants.STATUS_UP:
            self.link_status = constants.STATUS_UP
            logging.info("Link to Märklin interface established.")
            self._publish_status()

        self.last_marklin_packet_time = time.time()
        self.packets_from_marklin += 1

        if config.MQTT_ENABLED:
            self.mqtt_client.publish(config.MQTT_TOPIC_FROM_MARKLIN, data)
            self.packets_to_mqtt += 1
        else:
            # In UDP Bridge mode, forward to the last known controller address.
            if self.last_controller_addr:
                self.sock.sendto(data, self.last_controller_addr)
            else:
                logging.warning("Received Märklin packet in bridge mode, but no controller address is known yet. Packet not forwarded.")
 
        # Check for system commands (CAN ID 0x00) that affect track power
        if len(data) >= constants.FRAME_MIN_LENGTH and data[0:4] == constants.SYSTEM_CMD_CAN_ID:
            subcommand = data[constants.GO_STOP_SUBCMD_INDEX]
            new_power_state = None  # Use None to indicate no relevant state change found

            # Case 1: Normal Go/Stop command (subcommand 0x00)
            if subcommand == constants.GO_STOP_SUBCMD:
                status = data[constants.GO_STOP_STATUS_INDEX]
                if status == constants.SYSTEM_GO:
                    new_power_state = "GO"
                elif status == constants.SYSTEM_STOP:
                    new_power_state = "STOP"

            # Case 2: System Halt command (subcommand 0x01), also means STOP
            elif subcommand == constants.SYSTEM_HALT_SUBCMD:
                new_power_state = "STOP"

            # Log the parsed system command details for debugging
            status_val = data[constants.GO_STOP_STATUS_INDEX] if subcommand == constants.GO_STOP_SUBCMD and len(data) > constants.GO_STOP_STATUS_INDEX else 'N/A'
            logging.debug(f"-> Parsed as System Command: sub={hex(subcommand)}, status={hex(status_val) if status_val != 'N/A' else 'N/A'}, state={new_power_state}")

            # If a valid power state was detected and it's a change, update the system state
            if new_power_state and self.track_power != new_power_state:
                self.track_power = new_power_state
                logging.info(f"Track power state changed to: {self.track_power}")
                if self.track_power == "GO":
                    self.set_led_color(led.COLOR_GREEN_GO)
                else:  # STOP
                    self.set_led_color(led.COLOR_RED_STOP)
                self._publish_status()

    def _process_packets(self):
        try:
            data, addr = self.sock.recvfrom(constants.UDP_BUFFER_SIZE)
            source_ip = addr[0]
            self.last_source = source_ip

            # If the packet is from the Märklin box, handle it internally.
            # This logic is the same for both Bridge and MQTT Gateway modes.
            if source_ip == config.MARKLIN_IP:
                self._handle_marklin_packet(data)

            # If the packet is from any other source (a controller),
            # forward it to the Märklin box, but ONLY in UDP Bridge mode.
            elif not config.MQTT_ENABLED:
                # This is a packet from a controller.
                # Store its address so we can send replies back to it.
                self.last_controller_addr = addr
                self.sock.sendto(data, (config.MARKLIN_IP, config.PORT))
                self.packets_to_marklin += 1

        except BlockingIOError:
            pass # Normal, no data received
        except Exception as e:
            logging.error(f"An unexpected error occurred in packet processing: {e}", exc_info=True)
            self.last_source = f"ERROR: {e}"
            time.sleep(1) # Prevent spamming logs on repeated errors

    def _main_loop(self):
        """The main processing loop."""
        self.running = True
        while self.running:
            now = time.time()

            # Core logic
            self._check_interface_status()
            self._check_connection_health()
            self._process_packets()

            # Publish status periodically
            if config.MQTT_ENABLED and (now - self.last_status_publish_time > config.MQTT_STATUS_INTERVAL_S):
                self._publish_status()
                self.last_status_publish_time = now

            time.sleep(constants.MAIN_LOOP_DELAY_S)

    def _signal_handler(self, signum, frame):
        """Handles system signals for graceful shutdown."""
        logging.info(f"Received signal {signum}. Initiating graceful shutdown...")
        self.running = False

    def cleanup(self):
        if self.mqtt_client:
            logging.info("Disconnecting from MQTT broker.")
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        if self.status_led:
            self.status_led.cleanup()
        if self.sock:
            self.sock.close()

    def run(self):
        """Sets up resources and starts the main application loop."""
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        self._setup_logging()
        logging.info("--- Marklin Bridge v%s ---", constants.APP_VERSION)
        try:
            self._check_psutil()
            self._setup_gpio()

            # Indicate startup with a white LED
            self.set_led_color(led.COLOR_WHITE_STARTING)
            time.sleep(1)

            self._setup_network()

            if config.MQTT_ENABLED:
                self._setup_mqtt()

            self.set_led_color(led.COLOR_YELLOW_NO_LINK)
            # Send the initial registration/query packet to the send port (15731)
            self.sock.sendto(constants.QUERY_PACKET, (config.MARKLIN_IP, config.PORT))
            self.last_marklin_packet_time = time.time()
            self.last_query_time = time.time()

            self._main_loop()
        except Exception as e:
            logging.critical("A critical error occurred: %s", e, exc_info=True)
        finally:
            self.cleanup()


def main():
    """Parses arguments and runs the application."""
    parser = argparse.ArgumentParser(
        description="A UDP bridge for Märklin CAN-over-UDP traffic with status LED.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {constants.APP_VERSION}'
    )
    args = parser.parse_args()

    app = MarklinBridgeApp()
    app.run()

if __name__ == "__main__":
    main()