# This file contains hardcoded constants for the application.
# These are fundamental to the protocol and are not intended for user configuration.

# --- Märklin Protocol Constants ---
FRAME_MIN_LENGTH = 13         # A full CAN-over-UDP frame is 13 bytes
SYSTEM_CMD_CAN_ID = b'\x00\x00\x00\x00' # CAN-ID for a system command (Go, Stop, etc.)
GO_STOP_SUBCMD_INDEX = 5      # The sub-command for Go/Stop is the 1st data byte
GO_STOP_SUBCMD = 0x00
GO_STOP_STATUS_INDEX = 8      # The actual status (0 or 1) is the 4th data byte
SYSTEM_GO = 0x01
SYSTEM_STOP = 0x00

# --- Connectivity Constants ---
CONNECTION_TIMEOUT_S = 10  # Seconds before assuming connection is lost
QUERY_INTERVAL_S = 5       # Seconds between sending a query when link is down
MQTT_KEEPALIVE_S = 60      # Seconds for MQTT keepalive
# This is a CAN "ping" packet from a generic client (UID 0x00)
QUERY_PACKET = b'\x00\x30\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

# --- Network & Timing Constants ---
UDP_BUFFER_SIZE = 1024
MAIN_LOOP_DELAY_S = 0.02
IFACE_CHECK_INTERVAL_S = 5
SOCKET_TIMEOUT_S = 1.0
PROBE_PORT = 80

# --- Status Strings ---
STATUS_UP = "UP"
STATUS_DOWN = "DOWN"
STATUS_UNKNOWN = "UNKNOWN"
STATUS_NA = "N/A"
STATUS_NO_PSUTIL = "NO_PSUTIL"
STATUS_HOST_NOT_FOUND = "HOST NOT FOUND"

# --- Application Info ---
APP_VERSION = "1.0.0"