import sys
import unittest
from unittest.mock import Mock, patch, ANY

# Mock the curses module at a high level to ensure tests can be discovered.
sys.modules['curses'] = Mock()

import mbviewer

class TestMqttCallbacks(unittest.TestCase):

    def test_on_connect(self):
        """Test the on_connect MQTT callback."""
        userdata = {'connection_status': '', 'topic': 'test/topic'}
        mock_client = Mock()
        
        # Paho v2 signature: client, userdata, flags, reason_code, properties
        mbviewer.on_connect(mock_client, userdata, None, 0, None)
        self.assertEqual(userdata['connection_status'], "CONNECTED")
        mock_client.subscribe.assert_called_with('test/topic')

        mock_client.reset_mock()
        
        mbviewer.on_connect(mock_client, userdata, None, 1, None)
        self.assertEqual(userdata['connection_status'], "FAILED (1)")
        mock_client.subscribe.assert_not_called()

    def test_on_disconnect(self):
        """Test the on_disconnect MQTT callback."""
        userdata = {'connection_status': 'CONNECTED'}
        # Paho v2 signature: client, userdata, disconnect_flags, reason_code, properties
        mbviewer.on_disconnect(None, userdata, None, 0, None)
        self.assertEqual(userdata['connection_status'], "DISCONNECTED")

    def test_on_message(self):
        """Test the on_message MQTT callback."""
        userdata = {'status_data': None}
        mock_msg = Mock()
        
        mock_msg.payload = b'{"version": "1.0"}'
        mbviewer.on_message(None, userdata, mock_msg)
        self.assertEqual(userdata['status_data'], {"version": "1.0"})

        mock_msg.payload = b'{"version": "1.0"'
        mbviewer.on_message(None, userdata, mock_msg)
        self.assertEqual(userdata['status_data'], {"error": "Invalid JSON received"})

class TestCursesUI(unittest.TestCase):

    def setUp(self):
        """Set up a patch for the curses module before each test."""
        self.patcher = patch('mbviewer.curses')
        self.mock_curses = self.patcher.start()
        self.addCleanup(self.patcher.stop)

        self.mock_stdscr = Mock()
        
        self.mock_curses.has_colors.return_value = True
        self.mock_curses.color_pair.side_effect = lambda x: f'color_{x}'
        self.mock_curses.A_NORMAL = 'A_NORMAL'
        self.mock_curses.error = type('curses_error', (Exception,), {})
        
        self.ui = mbviewer.CursesUI(self.mock_stdscr)

    def test_init_with_colors(self):
        """Test UI initialization when colors are supported."""
        self.mock_curses.start_color.assert_called_once()
        self.assertEqual(self.ui.COLOR_PAIR_GREEN, 'color_1')

    def test_init_without_colors(self):
        """Test UI initialization when colors are not supported."""
        self.mock_curses.has_colors.return_value = False
        ui_no_color = mbviewer.CursesUI(self.mock_stdscr)
        self.assertEqual(ui_no_color.COLOR_PAIR_GREEN, 'A_NORMAL')
        self.mock_curses.start_color.assert_called_once()

    def test_draw_waiting_for_message(self):
        """Test drawing when waiting for the first message."""
        self.ui.draw(None, "CONNECTING", None)
        # Use ANY for line number to accommodate layout changes
        self.mock_stdscr.addstr.assert_any_call(ANY, 0, "Waiting for first status message...", self.ui.COLOR_PAIR_YELLOW)

    def test_draw_with_status_data(self):
        """Test drawing with a full set of status data."""
        # Updated data format to include rich interface info (dict) and legacy info (string)
        status_data = {
            'version': '1.2.3', 'link_status': 'UP', 'track_power': 'GO',
            'interface_status': {
                'eth0': {'status': 'UP', 'ip': '192.168.1.50'}, 
                'wlan0': {'status': 'UP', 'ssid': 'TestWiFi', 'ip': '192.168.1.105'}
            },
            'packets_from_marklin': 123, 'packets_to_marklin': 456, 'last_source': '192.168.1.10',
            'packets_from_mqtt': 789, 'packets_to_mqtt': 101,
            'marklin_ip': '192.168.160.1',
            'mqtt_broker_ip': '192.168.1.1',
            'mqtt_status': 'CONNECTED',
            'marklin_interface': 'wlan0',
            'home_interface': 'eth0'
        }
        self.ui.draw(status_data, "CONNECTED", None)
        
        # Use ANY for line numbers as layout is complex. Verify headers and content.
        self.mock_stdscr.addstr.assert_any_call(ANY, 0, "-- Bridge --", self.ui.COLOR_PAIR_DEFAULT)
        self.mock_stdscr.addstr.assert_any_call(ANY, 0, "-- Märklin Side --", self.ui.COLOR_PAIR_DEFAULT)
        self.mock_stdscr.addstr.assert_any_call(ANY, 0, "-- Network Side --", self.ui.COLOR_PAIR_DEFAULT)

        # Core Data
        self.mock_stdscr.addstr.assert_any_call(ANY, 24, "1.2.3", self.ui.COLOR_PAIR_DEFAULT)
        
        # Leg 1 Data (Marklin/WiFi)
        self.mock_stdscr.addstr.assert_any_call(ANY, 2, "Interface (wlan0):", self.ui.COLOR_PAIR_DEFAULT)
        self.mock_stdscr.addstr.assert_any_call(ANY, 24, "🟢 UP (TestWiFi)", self.ui.COLOR_PAIR_DEFAULT)
        self.mock_stdscr.addstr.assert_any_call(ANY, 24, "192.168.1.105", self.ui.COLOR_PAIR_DEFAULT) # Marklin Bridge IP
        self.mock_stdscr.addstr.assert_any_call(ANY, 24, "192.168.160.1", self.ui.COLOR_PAIR_DEFAULT) # Marklin Wifi Box IP
        self.mock_stdscr.addstr.assert_any_call(ANY, 2, "UDP from Marklin:", self.ui.COLOR_PAIR_DEFAULT)
        self.mock_stdscr.addstr.assert_any_call(ANY, 2, "UDP to Marklin:", self.ui.COLOR_PAIR_DEFAULT)

        # Leg 2 Data (Downlink/Interfaces)
        self.mock_stdscr.addstr.assert_any_call(ANY, 2, "Interface (eth0):", self.ui.COLOR_PAIR_DEFAULT)
        self.mock_stdscr.addstr.assert_any_call(ANY, 24, "🟢 UP", self.ui.COLOR_PAIR_DEFAULT) # eth0
        self.mock_stdscr.addstr.assert_any_call(ANY, 24, "192.168.1.1", self.ui.COLOR_PAIR_DEFAULT) # MQTT Broker IP
        self.mock_stdscr.addstr.assert_any_call(ANY, 24, "🟢 CONNECTED", self.ui.COLOR_PAIR_GREEN) # Bridge MQTT Status
        self.mock_stdscr.addstr.assert_any_call(ANY, 2, "MQTT from Broker:", self.ui.COLOR_PAIR_DEFAULT)
        self.mock_stdscr.addstr.assert_any_call(ANY, 2, "MQTT to Broker:", self.ui.COLOR_PAIR_DEFAULT)

    def test_draw_box_down_scenario(self):
        """Test drawing when the UDP link is down (Scenario 2)."""
        status_data = {
            'link_status': 'DOWN', 'track_power': 'UNKNOWN',
            'interface_status': {}
        }
        self.ui.draw(status_data, "CONNECTED", None)

        # Verify icons for Box Down scenario
        self.mock_stdscr.addstr.assert_any_call(ANY, 24, "🔴 DOWN", self.ui.COLOR_PAIR_RED)
        self.mock_stdscr.addstr.assert_any_call(ANY, 24, "😵 UNKNOWN", self.ui.COLOR_PAIR_YELLOW)

    def test_draw_ignores_curses_error(self):
        """Test that draw method handles curses errors gracefully."""
        self.mock_stdscr.erase.side_effect = self.mock_curses.error
        try:
            self.ui.draw({}, "CONNECTED", None)
        except self.mock_curses.error:
            self.fail("Curses error was not handled gracefully (it was re-raised).")

if __name__ == '__main__':
    unittest.main()
