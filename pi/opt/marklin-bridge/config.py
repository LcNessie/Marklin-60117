import configparser
import os

# This module centralizes all configuration for the application.
# It establishes default values, then overrides them with any values
# found in the user-editable 'config.ini' file.
#
# It also defines non-user-configurable constants for the application.

# --- Configuration Loading ---
config = configparser.ConfigParser()

# Define default values
config['Network'] = {
    'UDPBridgeEnabled': 'true',
    'ControllerIP': '192.168.1.161',
    'MarklinIP': '192.168.160.1',
    'Port': '15731', # Destination port for sending commands to the Marklin box
    'ListenPort': '15730', # Local port to listen on for all messages from the Marklin box
    'MarklinInterface': 'wlan0',
    'HomeInterface': 'eth0'
}
config['GPIO'] = {
    'Enabled': 'true',
    'RedPin': '16',
    'GreenPin': '20',
    'BluePin': '21'
}
config['MQTT'] = {
    'Enabled': 'false',
    'BrokerIP': '127.0.0.1',
    'BrokerPort': '1883',
    'Username': '',
    'Password': '',
    'TopicFromMarklin': 'marklin/from_interface',
    'TopicToMarklin': 'marklin/to_interface',
    'StatusTopic': 'marklin/status',
    'StatusIntervalS': '5.0'
}
config['Logging'] = {
    'LogFile': '', # Default: empty, logs to journald/stderr
    'LogFileMaxSizeMB': '5',
    'LogFileBackupCount': '3'
}

# Find and read the external config file
try:
    script_dir = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(script_dir, 'config.ini')
    config.read(config_path)
except Exception:
    # If there's an error, we'll just use defaults.
    # The main script will handle logging this if needed.
    pass

# --- Exported Configuration Values ---

# [Network]
UDP_BRIDGE_ENABLED = config.getboolean('Network', 'UDPBridgeEnabled')
CONTROLLER_IP = config.get('Network', 'ControllerIP')
MARKLIN_IP = config.get('Network', 'MarklinIP')
PORT = config.getint('Network', 'Port')
LISTEN_PORT = config.getint('Network', 'ListenPort')
MARKLIN_INTERFACE = config.get('Network', 'MarklinInterface')
HOME_INTERFACE = config.get('Network', 'HomeInterface')

# [GPIO]
GPIO_ENABLED = config.getboolean('GPIO', 'Enabled')
LED_RED_PIN = config.getint('GPIO', 'RedPin')
LED_GREEN_PIN = config.getint('GPIO', 'GreenPin')
LED_BLUE_PIN = config.getint('GPIO', 'BluePin')

# [MQTT]
MQTT_ENABLED = config.getboolean('MQTT', 'Enabled')
MQTT_BROKER_IP = config.get('MQTT', 'BrokerIP')
MQTT_BROKER_PORT = config.getint('MQTT', 'BrokerPort')
MQTT_USERNAME = config.get('MQTT', 'Username', fallback=None)
MQTT_PASSWORD = config.get('MQTT', 'Password', fallback=None)
MQTT_TOPIC_FROM_MARKLIN = config.get('MQTT', 'TopicFromMarklin')
MQTT_TOPIC_TO_MARKLIN = config.get('MQTT', 'TopicToMarklin')
MQTT_STATUS_TOPIC = config.get('MQTT', 'StatusTopic')
MQTT_STATUS_INTERVAL_S = config.getfloat('MQTT', 'StatusIntervalS')

# [Logging]
LOG_FILE = config.get('Logging', 'LogFile', fallback='')
LOG_FILE_MAX_SIZE_MB = config.getint('Logging', 'LogFileMaxSizeMB', fallback=5)
LOG_FILE_BACKUP_COUNT = config.getint('Logging', 'LogFileBackupCount', fallback=3)