# constants.py

# Application Version
APP_VERSION = "1.0.0" # Placeholder, should be updated with actual version

# Network Configuration
PORT = 15731  # Default UDP port for Märklin CAN-over-UDP
UDP_BUFFER_SIZE = 1024 # Max UDP packet size

# Connection Health
CONNECTION_TIMEOUT_S = 10 # Seconds without a packet before link is considered DOWN
QUERY_INTERVAL_S = 5    # Seconds between sending query packets when link is DOWN or no recent activity
MAIN_LOOP_DELAY_S = 0.02 # Delay in main loop to prevent 100% CPU usage

# Network Interface Checking
IFACE_CHECK_INTERVAL_S = 5 # Seconds between checking network interface status

# MQTT Configuration
MQTT_KEEPALIVE_S = 60 # MQTT keepalive interval in seconds

# Status Strings
STATUS_UP = "UP"
STATUS_DOWN = "DOWN"
STATUS_UNKNOWN = "UNKNOWN"
STATUS_NA = "N/A" # Not Applicable
STATUS_NO_PSUTIL = "PSUTIL_MISSING" # Status when psutil is not installed

# Märklin CAN Protocol Constants (based on known protocol details)
# These are byte sequences or integer values derived from the Märklin CAN protocol.

# CAN ID for System Commands (e.g., Go/Stop, Halt)
SYSTEM_CMD_CAN_ID = b'\x00\x00\x00\x00'

# Minimum length of a valid CAN frame (header + data)
FRAME_MIN_LENGTH = 13 # 4 bytes CAN ID + 1 byte DLC + 8 bytes data

# Index of the subcommand byte within the data payload for system commands
GO_STOP_SUBCMD_INDEX = 5 # For CAN ID 0x00000000, data[5] is the subcommand

# Subcommand for normal Go/Stop messages (data[5] = 0x00)
GO_STOP_SUBCMD = 0x00

# Subcommand for System Halt messages (data[5] = 0x01)
SYSTEM_HALT_SUBCMD = 0x01

# Index of the status byte within the data payload for Go/Stop messages (subcommand 0x00)
GO_STOP_STATUS_INDEX = 8 # For CAN ID 0x00000000, subcommand 0x00, data[8] is the status

# Status values for Go/Stop messages
SYSTEM_GO = 0x01  # Data[8] = 0x01 means "Go"
SYSTEM_STOP = 0x00 # Data[8] = 0x00 means "Stop"

# Query Packet: A valid CAN "System Ping" frame (CAN-ID 0x00030000, DLC 0).
QUERY_PACKET = b'\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'