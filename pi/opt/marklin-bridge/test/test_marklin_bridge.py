import unittest
import socket
import json
import logging
import signal
from unittest.mock import patch, MagicMock, ANY

# Local module imports
from marklin_bridge import MarklinBridgeApp
import led

class TestMarklinBridgeApp(unittest.TestCase):
    """
    Test suite for the MarklinBridgeApp class.

    This suite tests the core application logic. All external dependencies like
    sockets, hardware libraries (led, network_utils), and time are mocked.
    This allows us to test the application's state machine and logic in a
    predictable and isolated environment, without needing any actual hardware
    or network connections.
    """

    def setUp(self):
        """
        This method is run before each test. It sets up a clean environment.
        We patch all the modules that the MarklinBridgeApp depends on.
        """
        # The `patch.object` is used here to mock methods on an instance after it's created.
        # We create a real app instance, then mock the methods that deal with external resources.
        self.app = MarklinBridgeApp()

        # Mock the resources that are created during the app's setup phase
        self.app.sock = MagicMock(spec=socket.socket)
        self.app.status_led = MagicMock(spec=led.AbstractLED)
        self.app.mqtt_client = MagicMock()

        # Mock time to control time-based logic (e.g., timeouts)
        self.time_patcher = patch('time.time')
        self.mock_time = self.time_patcher.start()
        self.mock_time.return_value = 1000.0

        # Mock config to control application behavior for tests
        self.config_patcher = patch('marklin_bridge.config')
        self.mock_config = self.config_patcher.start()

        # Mock constants to control application behavior for tests
        self.constants_patcher = patch('marklin_bridge.constants')
        self.mock_constants = self.constants_patcher.start()

        self._configure_default_mocks()
        
        # Clear any existing handlers on the root logger to prevent test pollution
        logging.getLogger().handlers = []

    def tearDown(self):
        """This method is run after each test to clean up the patches."""
        self.time_patcher.stop()
        self.config_patcher.stop()
        self.constants_patcher.stop()
        logging.getLogger().handlers = []

    def _configure_default_mocks(self):
        """Sets up default values for our mocked config."""
        # Configurable values
        self.mock_config.MQTT_ENABLED = False # Default to UDP Bridge mode
        self.mock_config.MARKLIN_IP = '192.168.160.1'
        self.mock_config.CONTROLLER_IP = '192.168.1.100'
        self.mock_config.PORT = 15731
        self.mock_config.MARKLIN_INTERFACE = 'wlan0'
        self.mock_config.HOME_INTERFACE = 'eth0'
        self.mock_config.MQTT_TOPIC_FROM_MARKLIN = 'marklin/from'

        self.mock_config.MQTT_STATUS_TOPIC = 'marklin/status'
        self.mock_config.MQTT_STATUS_INTERVAL_S = 1.0
        self.mock_config.MQTT_BROKER_IP = '127.0.0.1'

        # Hardcoded constants
        self.mock_constants.CONNECTION_TIMEOUT_S = 10
        self.mock_constants.QUERY_INTERVAL_S = 5
        self.mock_constants.QUERY_PACKET = b'ping'
        # CAN frame constants
        self.mock_constants.FRAME_MIN_LENGTH = 13
        self.mock_constants.SYSTEM_CMD_CAN_ID = b'\x00\x00\x00\x00'
        self.mock_constants.GO_STOP_SUBCMD_INDEX = 5
        self.mock_constants.GO_STOP_SUBCMD = 0x00
        self.mock_constants.SYSTEM_HALT_SUBCMD = 0x01
        self.mock_constants.GO_STOP_STATUS_INDEX = 8
        self.mock_constants.SYSTEM_GO = 0x01
        self.mock_constants.SYSTEM_STOP = 0x00
        self.mock_constants.MQTT_KEEPALIVE_S = 60
        self.mock_constants.UDP_BUFFER_SIZE = 1024
        self.mock_constants.MAIN_LOOP_DELAY_S = 0.02
        self.mock_constants.IFACE_CHECK_INTERVAL_S = 5
        self.mock_constants.STATUS_UP = "UP"
        self.mock_constants.STATUS_DOWN = "DOWN"
        self.mock_constants.STATUS_UNKNOWN = "UNKNOWN"
        self.mock_constants.APP_VERSION = "1.0.0"

    def test_initial_state(self):
        """Tests that the app initializes with the correct default state."""
        # The app is created in setUp, we just check its initial attributes
        self.assertEqual(self.app.link_status, self.mock_constants.STATUS_DOWN, "Initial link status should be DOWN")
        self.assertEqual(self.app.track_power, self.mock_constants.STATUS_UNKNOWN, "Initial track power should be UNKNOWN")
        self.assertEqual(self.app.packets_from_marklin, 0)
        self.assertEqual(self.app.packets_to_marklin, 0)
        self.assertEqual(self.app.packets_from_mqtt, 0)
        self.assertEqual(self.app.packets_to_mqtt, 0)

    @patch('marklin_bridge.MarklinBridgeApp.ColoredFormatter')
    @patch('marklin_bridge.coloredlogs', new_callable=MagicMock)
    def test_setup_logging_uses_coloredlogs_if_available(self, mock_coloredlogs, mock_formatter):
        """Tests that coloredlogs is used for console logging when available."""
        # --- Arrange ---
        self.mock_config.LOG_FILE = "" # Ensure console logging path

        # --- Act ---
        # Capture the startup log message
        with self.assertLogs(level='INFO') as cm:
            self.app._setup_logging()
        self.assertIn("Starting Märklin UDP Bridge", cm.output[0])

        # --- Assert ---
        # The root logger level is set to DEBUG in the method, which coloredlogs should inherit.
        mock_coloredlogs.install.assert_called_once_with(level=logging.DEBUG, fmt=ANY)
        # Assert that our custom formatter was not instantiated, proving we didn't enter the 'else' block.
        mock_formatter.assert_not_called()

    @patch('marklin_bridge.logging.StreamHandler')
    @patch('marklin_bridge.coloredlogs', None)
    def test_setup_logging_falls_back_to_custom_formatter(self, mock_stream_handler):
        """Tests that the custom formatter is used when coloredlogs is not available."""
        # --- Arrange ---
        self.mock_config.LOG_FILE = "" # Ensure console logging path

        # --- Act ---
        # Configure mock handler to have a valid level to prevent comparison errors
        mock_stream_handler.return_value.level = 0
        # Capture the startup log message
        with self.assertLogs(level='INFO') as cm:
            self.app._setup_logging()
        self.assertIn("Starting Märklin UDP Bridge", cm.output[0])

        # --- Assert ---
        mock_stream_handler.assert_called_once()
        # Check that the formatter set on the handler is the custom one
        handler_instance = mock_stream_handler.return_value
        handler_instance.setFormatter.assert_called_once()
        formatter_arg = handler_instance.setFormatter.call_args[0][0]
        self.assertIsInstance(formatter_arg, self.app.ColoredFormatter)

    @patch('marklin_bridge.RotatingFileHandler')
    @patch('marklin_bridge.coloredlogs', new_callable=MagicMock)
    def test_setup_logging_uses_file_handler(self, mock_coloredlogs, mock_file_handler):
        """Tests that RotatingFileHandler is used when a log file is configured."""
        # --- Arrange ---
        self.mock_config.LOG_FILE = "/var/log/test.log"
        self.mock_config.LOG_FILE_MAX_SIZE_MB = 5
        self.mock_config.LOG_FILE_BACKUP_COUNT = 3
        expected_max_bytes = 5 * 1024 * 1024

        # Configure mock handler to have a valid level
        mock_file_handler.return_value.level = 0

        # --- Act ---
        # Capture the startup log message
        with self.assertLogs(level='INFO') as cm:
            self.app._setup_logging()
        self.assertIn("Starting Märklin UDP Bridge", cm.output[0])

        # --- Assert ---
        mock_file_handler.assert_called_once_with(
            "/var/log/test.log", maxBytes=expected_max_bytes, backupCount=3
        )
        mock_coloredlogs.install.assert_not_called()

    def test_handle_marklin_go_packet(self):
        """
        Tests the logic for when a 'System GO' packet is received from the Märklin box.
        """
        # --- Arrange ---
        # Start with the link down to see the state transition
        self.app.link_status = self.mock_constants.STATUS_DOWN
        self.app.track_power = self.mock_constants.STATUS_UNKNOWN
        # This is a valid CAN frame for "System Go"
        go_packet = b'\x00\x00\x00\x00\x05\x00\x00\x00\x01\x00\x00\x00\x00'

        self.app._publish_status = MagicMock()

        # --- Act ---
        self.app._handle_marklin_packet(go_packet)

        # --- Assert ---
        # 1. State variables should be updated
        self.assertEqual(self.app.link_status, self.mock_constants.STATUS_UP)
        self.assertEqual(self.app.track_power, "GO")
        self.assertEqual(self.app.packets_from_marklin, 1)
        self.assertEqual(self.app.last_marklin_packet_time, 1000.0)

        # 2. The LED should be set to green
        self.app.status_led.set_color.assert_called_with(led.COLOR_GREEN_GO)

        # 3. In bridge mode, the packet should be forwarded to the controller
        self.app.sock.sendto.assert_called_once_with(go_packet, (self.mock_config.CONTROLLER_IP, self.mock_config.PORT))

        # 4. Should publish status (Link UP + Power GO = 2 calls)
        self.assertEqual(self.app._publish_status.call_count, 2)

    def test_handle_marklin_stop_packet(self):
        """
        Tests the logic for when a 'System STOP' packet is received from the Märklin box.
        """
        # --- Arrange ---
        # Start with the link up and power on to see the state transition
        self.app.link_status = self.mock_constants.STATUS_UP
        self.app.track_power = "GO"
        # This is a valid CAN frame for "System Stop"
        stop_packet = b'\x00\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00'

        self.app._publish_status = MagicMock()

        # --- Act ---
        self.app._handle_marklin_packet(stop_packet)

        # --- Assert ---
        # 1. State variables should be updated
        self.assertEqual(self.app.link_status, self.mock_constants.STATUS_UP) # Link should remain UP
        self.assertEqual(self.app.track_power, "STOP")
        self.assertEqual(self.app.packets_from_marklin, 1)
        self.assertEqual(self.app.last_marklin_packet_time, 1000.0)

        # 2. The LED should be set to red
        self.app.status_led.set_color.assert_called_with(led.COLOR_RED_STOP)

        # 3. In bridge mode, the packet should be forwarded to the controller
        self.app.sock.sendto.assert_called_once_with(stop_packet, (self.mock_config.CONTROLLER_IP, self.mock_config.PORT))

        # 4. Should publish status (Power change only = 1 call)
        self.app._publish_status.assert_called_once()

    def test_handle_marklin_halt_packet(self):
        """
        Tests the logic for when a 'System HALT' packet is received from the Märklin box.
        This is another form of 'Stop'.
        """
        # --- Arrange ---
        # Start with the link up and power on to see the state transition
        self.app.link_status = self.mock_constants.STATUS_UP
        self.app.track_power = "GO"
        # This is a valid CAN frame for "System Halt" (subcommand 0x01)
        halt_packet = b'\x00\x00\x00\x00\x04\x01\x00\x00\x00\x00\x00\x00\x00'

        self.app._publish_status = MagicMock()

        # --- Act ---
        self.app._handle_marklin_packet(halt_packet)

        # --- Assert ---
        # 1. State variables should be updated
        self.assertEqual(self.app.link_status, self.mock_constants.STATUS_UP) # Link should remain UP
        self.assertEqual(self.app.track_power, "STOP")
        self.assertEqual(self.app.packets_from_marklin, 1)
        self.assertEqual(self.app.last_marklin_packet_time, 1000.0)

        # 2. The LED should be set to red
        self.app.status_led.set_color.assert_called_with(led.COLOR_RED_STOP)

        # 3. In bridge mode, the packet should be forwarded to the controller
        self.app.sock.sendto.assert_called_once_with(halt_packet, (self.mock_config.CONTROLLER_IP, self.mock_config.PORT))

        # 4. Should publish status (Power change only = 1 call)
        self.app._publish_status.assert_called_once()

    def test_handle_marklin_packet_mqtt_mode(self):
        """
        Tests that in MQTT Gateway mode, a packet from the Märklin box is
        published to the MQTT broker.
        """
        # --- Arrange ---
        # Enable MQTT mode
        self.mock_config.MQTT_ENABLED = True
        self.app.link_status = self.mock_constants.STATUS_UP # Start with link up to isolate test
        packet_from_marklin = b'some status data'

        # --- Act ---
        self.app._handle_marklin_packet(packet_from_marklin)

        # --- Assert ---
        # 1. The MQTT client's publish method should be called with the correct topic and payload.
        self.app.mqtt_client.publish.assert_called_once_with(
            self.mock_config.MQTT_TOPIC_FROM_MARKLIN,
            packet_from_marklin
        )

        # 2. The UDP socket should NOT be used to forward the packet directly.
        self.app.sock.sendto.assert_not_called()

        # 3. The packet counters should be incremented.
        self.assertEqual(self.app.packets_from_marklin, 1)
        self.assertEqual(self.app.packets_to_mqtt, 1)

    def test_connection_health_timeout(self):
        """
        Tests that the link status changes to DOWN after a connection timeout.
        """
        # --- Arrange ---
        # Start with a healthy, "UP" link
        self.app.link_status = self.mock_constants.STATUS_UP
        self.app.last_marklin_packet_time = 1000.0
        self.app.last_query_time = 1000.0

        # Simulate time advancing just past the timeout threshold
        self.mock_time.return_value = 1000.0 + self.mock_constants.CONNECTION_TIMEOUT_S + 1

        self.app._publish_status = MagicMock()

        # --- Act & Assert ---
        # Use assertLogs to capture the expected warning and prevent it from
        # printing to the console during the test run.
        with self.assertLogs('root', level='WARNING') as cm:
            self.app._check_connection_health()
            # The test also asserts that the correct log message was generated.
            self.assertEqual(cm.output, ['WARNING:root:Link to Märklin interface lost (timeout).'])

        # Should publish status immediately on timeout
        self.app._publish_status.assert_called_once()

        # Assert state changes after the action
        # 1. State should be updated to reflect the lost link
        self.assertEqual(self.app.link_status, self.mock_constants.STATUS_DOWN)
        self.assertEqual(self.app.track_power, self.mock_constants.STATUS_UNKNOWN)

        # 2. The LED should be set to yellow
        self.app.status_led.set_color.assert_called_with(led.COLOR_YELLOW_NO_LINK)

        # 3. A query packet should be sent to try to re-establish the link
        self.app.sock.sendto.assert_called_once_with(
            self.mock_constants.QUERY_PACKET,
            (self.mock_config.MARKLIN_IP, self.mock_config.PORT)
        )
        self.assertEqual(self.app.last_query_time, self.mock_time.return_value)

    def test_process_packet_from_controller_bridge_mode(self):
        """
        Tests that in UDP Bridge mode, a packet from the controller is
        correctly forwarded to the Märklin box.
        """
        # --- Arrange ---
        self.mock_config.MQTT_ENABLED = False # Ensure bridge mode
        packet_from_controller = b'some command'
        controller_addr = (self.mock_config.CONTROLLER_IP, 12345)

        # Configure the mock socket to return this packet when recvfrom is called
        self.app.sock.recvfrom.return_value = (packet_from_controller, controller_addr)

        # --- Act ---
        self.app._process_packets()

        # --- Assert ---
        # 1. The packet should be sent to the Märklin IP
        self.app.sock.sendto.assert_called_once_with(
            packet_from_controller,
            (self.mock_config.MARKLIN_IP, self.mock_config.PORT)
        )

        # 2. The packet counter should be incremented
        self.assertEqual(self.app.packets_to_marklin, 1)
        self.assertEqual(self.app.last_source, self.mock_config.CONTROLLER_IP)

    def test_process_packet_from_marklin(self):
        """
        Tests that a packet from the Märklin box is correctly passed to the
        packet handler.
        """
        # --- Arrange ---
        packet_from_marklin = b'some status'
        marklin_addr = (self.mock_config.MARKLIN_IP, 12345)
        self.app.sock.recvfrom.return_value = (packet_from_marklin, marklin_addr)

        # We can mock the internal handler method to test the routing logic in isolation.
        self.app._handle_marklin_packet = MagicMock()

        # --- Act ---
        self.app._process_packets()

        # --- Assert ---
        # 1. The internal handler should have been called with the packet data.
        self.app._handle_marklin_packet.assert_called_once_with(packet_from_marklin)

        # 2. No packets should have been sent directly in this method.
        self.app.sock.sendto.assert_not_called()
        self.assertEqual(self.app.last_source, self.mock_config.MARKLIN_IP)

    def test_process_packet_blocking_io(self):
        """
        Tests that a BlockingIOError (no data) is handled gracefully.
        """
        # --- Arrange ---
        # Configure the mock socket to raise the error
        self.app.sock.recvfrom.side_effect = BlockingIOError

        # We'll also mock the handler to ensure it's not called
        self.app._handle_marklin_packet = MagicMock()

        # --- Act ---
        # We call the method and expect it to simply pass without raising an exception.
        try:
            self.app._process_packets()
        except BlockingIOError:
            self.fail("_process_packets() should not propagate BlockingIOError")

        # --- Assert ---
        # No other methods should have been called.
        self.app._handle_marklin_packet.assert_not_called()
        self.app.sock.sendto.assert_not_called()

    def test_cleanup(self):
        """Tests that the cleanup method correctly closes all resources."""
        # --- Arrange ---
        # The app and its mocked resources are already set up.

        # --- Act ---
        self.app.cleanup()

        # --- Assert ---
        # 1. The MQTT client should be stopped and disconnected.
        self.app.mqtt_client.loop_stop.assert_called_once()
        self.app.mqtt_client.disconnect.assert_called_once()

        # 2. The LED should be cleaned up.
        self.app.status_led.cleanup.assert_called_once()

        # 3. The socket should be closed.
        self.app.sock.close.assert_called_once()

    def test_publish_status_sends_correct_payload(self):
        """Tests that the status publishing method sends a correct JSON payload."""
        # --- Arrange ---
        self.mock_config.MQTT_ENABLED = True
        self.app.mqtt_client = MagicMock() # Ensure we have a fresh mock
        self.mock_config.MQTT_BROKER_IP = "10.0.0.1"

        # Set some state on the app to be reflected in the payload
        self.app.link_status = self.mock_constants.STATUS_UP
        self.app.track_power = "GO"
        self.app.packets_from_marklin = 123
        self.app.packets_to_marklin = 456
        self.app.packets_from_mqtt = 789
        self.app.packets_to_mqtt = 101
        self.app.last_source = '192.168.1.100'
        self.app.interface_status = { 'wlan0': self.mock_constants.STATUS_UP }
        self.app.mqtt_status = "CONNECTED"

        expected_payload = {
            "version": "1.0.0",
            "link_status": self.mock_constants.STATUS_UP,
            "track_power": "GO",
            "interface_status": { 'wlan0': self.mock_constants.STATUS_UP },
            "packets_from_marklin": 123,
            "packets_to_marklin": 456,
            "packets_from_mqtt": 789,
            "packets_to_mqtt": 101,
            "marklin_ip": "192.168.160.1",
            "mqtt_broker_ip": "10.0.0.1",
            "mqtt_status": "CONNECTED",
            "marklin_interface": "wlan0",
            "home_interface": "eth0"
        }

        # --- Act ---
        # Assume a new private method `_publish_status` exists in the app
        self.app._publish_status()

        # --- Assert ---
        # Check that publish was called with the correct topic and a JSON payload
        self.app.mqtt_client.publish.assert_called_once_with(
            self.mock_config.MQTT_STATUS_TOPIC,
            json.dumps(expected_payload, indent=4),
            retain=True
        )

    def test_signal_handler_sets_running_false(self):
        """Tests that the signal handler stops the main loop."""
        self.app.running = True
        # Use assertLogs to capture the INFO message about the shutdown signal
        with self.assertLogs(level='INFO') as cm:
            self.app._signal_handler(signal.SIGTERM, None)
            self.assertIn("Received signal", cm.output[0])
        self.assertFalse(self.app.running)

    def test_main_loop_calls_core_functions_and_publishes_status(self):
        """
        Tests the main loop structure: it should call processing functions
        and periodically publish status if enabled.
        """
        # --- Arrange ---
        self.mock_config.MQTT_ENABLED = True
        self.app.last_status_publish_time = 999.0
        self.mock_time.return_value = 1000.1 # Trigger status publish

        # Mock the core logic methods and the new status publisher
        self.app._check_interface_status = MagicMock()
        self.app._check_connection_health = MagicMock()
        self.app._process_packets = MagicMock()
        self.app._publish_status = MagicMock()

        # Break out of the loop after one iteration
        with patch('time.sleep', side_effect=KeyboardInterrupt):
            # --- Act ---
            with self.assertRaises(KeyboardInterrupt):
                self.app._main_loop()

        # --- Assert ---
        # Verify that all core logic functions were called once
        self.app._check_interface_status.assert_called_once()
        self.app._check_connection_health.assert_called_once()
        self.app._process_packets.assert_called_once()
        # Verify that the status was published
        self.app._publish_status.assert_called_once()
        # Verify the timestamp was updated
        self.assertEqual(self.app.last_status_publish_time, 1000.1)


# This allows running the tests directly from the command line
if __name__ == '__main__':
    unittest.main()