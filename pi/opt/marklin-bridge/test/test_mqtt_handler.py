import unittest
from unittest.mock import MagicMock, patch

# Local module imports
import mqtt_handler
import config

class TestMqttHandler(unittest.TestCase):
    """
    Test suite for the mqtt_handler module.

    These tests focus on the callback functions that are triggered by the
    paho-mqtt client. We simulate these callbacks and verify that they
    interact correctly with the main application instance (`app`).
    """

    def setUp(self):
        """Set up a mock application object for each test."""
        # The handlers receive the main app instance via the `userdata` dict.
        # We create a mock `app` that has all the attributes the handlers expect.
        self.mock_app = MagicMock()
        self.mock_app.sock = MagicMock()
        self.mock_app.is_interactive = False # Test the service-mode logging path
        # Initialize the counter as a real integer so `+=` works as expected.
        self.mock_app.packets_to_marklin = 0

        # We also need a mock for the MQTT message object.
        self.mock_msg = MagicMock()
        self.mock_msg.topic = 'marklin/to_interface'
        self.mock_msg.payload = b'test payload'

        # The handler uses config directly, so we patch it.
        self.config_patcher = patch('mqtt_handler.config')
        self.mock_config = self.config_patcher.start()
        self.mock_config.MARKLIN_IP = '192.168.160.1'
        self.mock_config.PORT = 15731

    def tearDown(self):
        """Clean up patches after each test."""
        self.config_patcher.stop()

    def test_on_mqtt_message_success(self):
        """Tests that a received MQTT message is correctly forwarded via UDP."""
        # --- Act ---
        mqtt_handler.on_mqtt_message(None, {'app': self.mock_app}, self.mock_msg)

        # --- Assert ---
        # 1. The socket's sendto method should be called with the payload.
        self.mock_app.sock.sendto.assert_called_once_with(
            b'test payload',
            ('192.168.160.1', 15731)
        )

        # 2. The application's packet counter and last source should be updated.
        self.assertEqual(self.mock_app.packets_to_marklin, 1)
        self.assertEqual(self.mock_app.last_source, 'MQTT:marklin/to_interface')

    def test_on_mqtt_message_socket_error(self):
        """Tests that an exception during socket.sendto is handled gracefully."""
        # --- Arrange ---
        # Simulate a network error when trying to send the UDP packet.
        self.mock_app.sock.sendto.side_effect = OSError("Network is down")

        # --- Act & Assert ---
        # Use assertLogs to verify that the error is logged correctly.
        with self.assertLogs('root', level='ERROR') as cm:
            mqtt_handler.on_mqtt_message(None, {'app': self.mock_app}, self.mock_msg)
            self.assertIn("Error forwarding MQTT message", cm.output[0])

        # The app's last_source should be updated to show the error.
        self.assertIn("ERROR: Network is down", self.mock_app.last_source)

        # The packet counter should NOT be incremented on failure.
        self.assertEqual(self.mock_app.packets_to_marklin, 0)

    def test_on_mqtt_connect_success(self):
        """Tests the callback for a successful MQTT connection."""
        # --- Act ---
        # A result code (rc) of 0 means success.
        mqtt_handler.on_mqtt_connect(None, {'app': self.mock_app}, None, 0)

        # --- Assert ---
        self.assertEqual(self.mock_app.mqtt_status, "CONNECTED")

    def test_on_mqtt_connect_failure(self):
        """Tests the callback for a failed MQTT connection."""
        # --- Act & Assert ---
        # A non-zero result code means failure (e.g., 5 = Not authorized).
        with self.assertLogs('root', level='ERROR') as cm:
            mqtt_handler.on_mqtt_connect(None, {'app': self.mock_app}, None, 5)
            self.assertIn("Failed to connect to MQTT broker", cm.output[0])

        # --- Assert ---
        self.assertEqual(self.mock_app.mqtt_status, "FAILED (5)")

    def test_on_mqtt_disconnect(self):
        """Tests the callback for a disconnection event."""
        # --- Act & Assert ---
        # A non-zero result code (rc) means an unexpected disconnect.
        with self.assertLogs('root', level='WARNING') as cm:
            mqtt_handler.on_mqtt_disconnect(None, {'app': self.mock_app}, 1)
            self.assertIn("Unexpectedly disconnected from MQTT broker", cm.output[0])

        # --- Assert ---
        self.assertEqual(self.mock_app.mqtt_status, "DISCONNECTED")