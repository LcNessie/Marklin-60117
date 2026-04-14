import unittest
import socket
import subprocess
from unittest.mock import patch, MagicMock

# We need to import the module we are testing
import constants
import network_utils

class TestNetworkStatus(unittest.TestCase):
    """
    Test suite for the network_utils.NetworkStatus class.
    These tests mock psutil and subprocess to test the logic of the
    `get_interface_info` method in isolation.
    """

    @patch('network_utils.psutil', None)
    def test_get_info_no_psutil(self):
        """Tests that the function returns NO_PSUTIL status if psutil is not installed."""
        network_status = network_utils.NetworkStatus()
        result = network_status.get_interface_info('wlan0')
        expected = (constants.STATUS_NA, constants.STATUS_NO_PSUTIL, constants.STATUS_NA)
        self.assertEqual(result, expected)

    @patch('network_utils.subprocess.check_output')
    @patch('network_utils.psutil')
    def test_get_info_for_wireless_iface_success(self, mock_psutil, mock_check_output):
        """Tests getting info for a healthy, connected wireless interface."""
        # --- Arrange: Configure our mocks to return fake data ---
        # Mock psutil to return address info
        mock_addr = MagicMock()
        mock_addr.family = socket.AF_INET
        mock_addr.address = '192.168.1.101'
        mock_psutil.net_if_addrs.return_value = {'wlan0': [mock_addr]}

        # Mock psutil to return interface status
        mock_stat = MagicMock()
        mock_stat.isup = True
        mock_psutil.net_if_stats.return_value = {'wlan0': mock_stat}

        # Mock subprocess to return an SSID
        mock_check_output.return_value = "MyHomeWiFi\n"

        # --- Act ---
        network_status = network_utils.NetworkStatus()
        result = network_status.get_interface_info('wlan0')

        # --- Assert ---
        expected = ('192.168.1.101', constants.STATUS_UP, 'MyHomeWiFi')
        self.assertEqual(result, expected)
        mock_check_output.assert_called_once_with(['iwgetid', '-r', 'wlan0'], text=True)

    @patch('network_utils.subprocess.check_output')
    @patch('network_utils.psutil')
    def test_get_info_for_wired_iface_success(self, mock_psutil, mock_check_output):
        """Tests getting info for a healthy wired interface."""
        # --- Arrange ---
        mock_addr = MagicMock()
        mock_addr.family = socket.AF_INET
        mock_addr.address = '192.168.1.102'
        mock_psutil.net_if_addrs.return_value = {'eth0': [mock_addr]}

        mock_stat = MagicMock()
        mock_stat.isup = True
        mock_psutil.net_if_stats.return_value = {'eth0': mock_stat}

        # --- Act ---
        network_status = network_utils.NetworkStatus()
        result = network_status.get_interface_info('eth0')

        # --- Assert ---
        expected = ('192.168.1.102', constants.STATUS_UP, constants.STATUS_NA)
        self.assertEqual(result, expected)
        # The check for SSID should not be called for a wired interface
        mock_check_output.assert_not_called()

    @patch('network_utils.psutil')
    def test_get_info_for_nonexistent_iface(self, mock_psutil):
        """Tests getting info for an interface that does not exist."""
        # --- Arrange ---
        # psutil returns a dict of existing interfaces. 'wlan1' is not in it.
        mock_psutil.net_if_addrs.return_value = {'eth0': [], 'wlan0': []}

        # --- Act ---
        network_status = network_utils.NetworkStatus()
        result = network_status.get_interface_info('wlan1')

        # --- Assert ---
        expected = (constants.STATUS_NA, constants.STATUS_DOWN, constants.STATUS_NA)
        self.assertEqual(result, expected)

    @patch('network_utils.psutil')
    def test_get_info_when_psutil_fails(self, mock_psutil):
        """Tests that the function handles an unexpected exception from psutil."""
        # --- Arrange ---
        # Simulate psutil raising an error
        mock_psutil.net_if_addrs.side_effect = Exception("psutil failed")

        # --- Act ---
        network_status = network_utils.NetworkStatus()
        result = network_status.get_interface_info('wlan0')

        # --- Assert ---
        expected = (constants.STATUS_NA, constants.STATUS_UNKNOWN, constants.STATUS_NA)
        self.assertEqual(result, expected)

    @patch('network_utils.subprocess.check_output')
    @patch('network_utils.psutil')
    def test_get_info_when_ssid_fails(self, mock_psutil, mock_check_output):
        """Tests that the function handles a failure to get the SSID."""
        # --- Arrange ---
        mock_addr = MagicMock()
        mock_addr.family = socket.AF_INET
        mock_addr.address = '192.168.1.101'
        mock_psutil.net_if_addrs.return_value = {'wlan0': [mock_addr]}

        mock_stat = MagicMock()
        mock_stat.isup = True
        mock_psutil.net_if_stats.return_value = {'wlan0': mock_stat}

        # Simulate the iwgetid command failing
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "cmd")

        # --- Act ---
        network_status = network_utils.NetworkStatus()
        result = network_status.get_interface_info('wlan0')

        # --- Assert ---
        # The SSID should fall back to N/A, but the other info should be correct.
        expected = ('192.168.1.101', constants.STATUS_UP, constants.STATUS_NA)
        self.assertEqual(result, expected)

# This allows running the tests directly from the command line
if __name__ == '__main__':
    unittest.main()