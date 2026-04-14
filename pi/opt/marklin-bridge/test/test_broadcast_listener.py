import unittest
from unittest.mock import patch, MagicMock, call

# Import the module to be tested
import broadcast_listener

class TestBroadcastListener(unittest.TestCase):
    """Test suite for the broadcast_listener diagnostic script."""

    @patch('builtins.print')
    @patch('broadcast_listener.socket')
    def test_socket_setup_and_cleanup(self, mock_socket_module, mock_print):
        """Tests that the socket is created, configured, bound, and closed correctly."""
        mock_socket_instance = MagicMock()
        mock_socket_module.socket.return_value = mock_socket_instance

        # Simulate the loop running once then raising an exception to exit
        mock_socket_instance.recvfrom.side_effect = KeyboardInterrupt

        # Call the main function of the script
        broadcast_listener.listen_loop()

        # 1. Check socket creation
        mock_socket_module.socket.assert_called_once_with(
            mock_socket_module.AF_INET, mock_socket_module.SOCK_DGRAM
        )

        # 2. Check socket options
        expected_calls = [
            call(mock_socket_module.SOL_SOCKET, mock_socket_module.SO_BROADCAST, 1),
            call(mock_socket_module.SOL_SOCKET, mock_socket_module.SO_REUSEADDR, 1)
        ]
        mock_socket_instance.setsockopt.assert_has_calls(expected_calls, any_order=True)

        # 3. Check bind call
        mock_socket_instance.bind.assert_called_once_with(('0.0.0.0', 15730))

        # 4. Check that close was called on exit
        mock_socket_instance.close.assert_called_once()

    @patch('builtins.print')
    @patch('broadcast_listener.socket')
    def test_packet_reception_and_print(self, mock_socket_module, mock_print):
        """Tests that received packets are printed correctly to the console."""
        mock_socket_instance = MagicMock()
        mock_socket_module.socket.return_value = mock_socket_instance

        # Simulate receiving one packet, then an interrupt to exit the loop
        test_payload = b'\x00\x01\x02'
        test_addr = ('192.168.1.1', 12345)
        mock_socket_instance.recvfrom.side_effect = [
            (test_payload, test_addr),
            KeyboardInterrupt
        ]

        # Call the main function
        broadcast_listener.listen_loop()

        # Check that print was called with the formatted output
        mock_print.assert_any_call(f"Received packet from {test_addr}: {test_payload.hex()}")

    @patch('builtins.print')
    @patch('broadcast_listener.socket')
    def test_general_exception_handling(self, mock_socket_module, mock_print):
        """Tests that a general exception is caught and the socket is closed."""
        mock_socket_instance = MagicMock()
        mock_socket_module.socket.return_value = mock_socket_instance

        # Simulate an error during recvfrom
        test_error = OSError("Test error")
        mock_socket_instance.recvfrom.side_effect = test_error

        # Call the main function
        broadcast_listener.listen_loop()

        # Check that the error was printed
        mock_print.assert_any_call(f"An error occurred: {test_error}")

        # Crucially, check that cleanup still happened
        mock_socket_instance.close.assert_called_once()