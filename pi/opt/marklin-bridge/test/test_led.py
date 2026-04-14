import unittest
from unittest.mock import patch, MagicMock
import configparser

# Import the module to be tested
import led

@patch('led.gpiod')
class TestLibgpiodLED(unittest.TestCase):
    """
    Test suite for the led.LibgpiodLED class.
    We mock the `gpiod` library to test the logic in isolation.
    """

    def setUp(self):
        """Set up a mock gpiod chip and lines for each test."""
        self.mock_chip = MagicMock()
        self.mock_lines = MagicMock()
        self.mock_chip.get_lines.return_value = self.mock_lines

    def test_init_success(self, mock_gpiod):
        """Tests successful initialization of LibgpiodLED."""
        mock_gpiod.Chip.return_value = self.mock_chip
        led_instance = led.LibgpiodLED(16, 20, 21)

        mock_gpiod.Chip.assert_called_once_with('gpiochip0')
        self.mock_chip.get_lines.assert_called_once_with((16, 20, 21))
        self.mock_lines.request.assert_called_once()
        # Check it turns off the LED on initialization
        self.mock_lines.set_values.assert_called_once_with([0, 0, 0])

    def test_init_no_gpiod_library(self, mock_gpiod):
        """Tests constructor raises ImportError if gpiod is not installed."""
        with patch('led.gpiod', None):
            with self.assertRaises(ImportError) as cm:
                led.LibgpiodLED(16, 20, 21)
            self.assertEqual(str(cm.exception),
                             "The 'gpiod' library is not installed.")

    def test_set_color_common_cathode(self, mock_gpiod):
        """Tests setting color for a common-cathode LED (non-inverted)."""
        mock_gpiod.Chip.return_value = self.mock_chip
        led_instance = led.LibgpiodLED(16, 20, 21, common_anode=False)
        self.mock_lines.reset_mock()  # Reset mock from the init call

        # Test RED
        led_instance.set_color((255, 0, 0))
        self.mock_lines.set_values.assert_called_with([1, 0, 0])

        # Test GREEN (any value > 0 should be ON)
        led_instance.set_color((0, 100, 0))
        self.mock_lines.set_values.assert_called_with([0, 1, 0])

        # Test WHITE
        led_instance.set_color((255, 255, 255))
        self.mock_lines.set_values.assert_called_with([1, 1, 1])

        # Test OFF
        led_instance.set_color((0, 0, 0))
        self.mock_lines.set_values.assert_called_with([0, 0, 0])

    def test_set_color_common_anode(self, mock_gpiod):
        """Tests setting color for a common-anode LED (inverted logic)."""
        mock_gpiod.Chip.return_value = self.mock_chip
        led_instance = led.LibgpiodLED(16, 20, 21, common_anode=True)
        self.mock_lines.reset_mock()  # Reset mock from the init call

        # Test RED (inverted: R=0, G=1, B=1)
        led_instance.set_color((255, 0, 0))
        self.mock_lines.set_values.assert_called_with([0, 1, 1])

        # Test WHITE (inverted: all 0)
        led_instance.set_color((255, 255, 255))
        self.mock_lines.set_values.assert_called_with([0, 0, 0])

        # Test OFF (inverted: all 1)
        led_instance.set_color((0, 0, 0))
        self.mock_lines.set_values.assert_called_with([1, 1, 1])

    def test_cleanup(self, mock_gpiod):
        """Tests that cleanup turns off the LED and releases the lines."""
        mock_gpiod.Chip.return_value = self.mock_chip
        led_instance = led.LibgpiodLED(16, 20, 21)
        self.mock_lines.reset_mock()  # Reset mock from the init call

        led_instance.cleanup()
        # Check it turns off the LED
        self.mock_lines.set_values.assert_called_with([0, 0, 0])
        # Check it releases the lines
        self.mock_lines.release.assert_called_once()


class TestNullLED(unittest.TestCase):
    """Tests for the NullLED fallback implementation."""

    def test_null_led_methods_do_not_fail(self):
        """Ensures NullLED methods can be called without errors."""
        # The NullLED should be instantiable and its methods should do nothing.
        # This test passes if no exceptions are raised.
        null_led = led.NullLED()
        self.assertIsInstance(null_led, led.AbstractLED)
        null_led.set_color((255, 0, 0))
        null_led.cleanup()


class TestFactory(unittest.TestCase):
    """Tests for the create_led_instance factory function."""

    def get_mock_config(self, enabled=True, common_anode=False):
        """Helper to create a mock configparser object for tests."""
        config = configparser.ConfigParser()
        config['GPIO'] = {
            'Enabled': str(enabled),
            'RedPin': '16',
            'GreenPin': '20',
            'BluePin': '21',
            'CommonAnode': str(common_anode)
        }
        return config

    def test_factory_returns_null_when_disabled_in_config(self):
        """The factory should return a NullLED if GPIO is disabled."""
        config = self.get_mock_config(enabled=False)
        instance = led.create_led_instance(config)
        self.assertIsInstance(instance, led.NullLED)

    @patch('led.LibgpiodLED')
    def test_factory_returns_libgpiod_when_enabled(self, mock_LibgpiodLED):
        """The factory should create a LibgpiodLED instance when enabled."""
        config = self.get_mock_config(enabled=True)
        instance = led.create_led_instance(config)

        # The factory should return the instance created by the mock
        self.assertEqual(instance, mock_LibgpiodLED.return_value)
        # Check that it was called with the correct parameters from config
        mock_LibgpiodLED.assert_called_once_with(16, 20, 21, common_anode=False)

    @patch('led.LibgpiodLED')
    def test_factory_passes_common_anode_config(self, mock_LibgpiodLED):
        """The factory should correctly pass the CommonAnode setting."""
        config = self.get_mock_config(enabled=True, common_anode=True)
        led.create_led_instance(config)
        mock_LibgpiodLED.assert_called_once_with(16, 20, 21, common_anode=True)

    @patch('led.logger')
    @patch('led.LibgpiodLED', side_effect=ImportError("gpiod not found"))
    def test_factory_falls_back_to_null_on_import_error(self, mock_LibgpiodLED, mock_logger):
        """If LibgpiodLED fails with ImportError, factory should return NullLED."""
        config = self.get_mock_config(enabled=True)
        instance = led.create_led_instance(config)
        self.assertIsInstance(instance, led.NullLED)
        # Verify that the error was logged, which also suppresses console output
        mock_logger.error.assert_called_once_with(
            "Could not initialize LibgpiodLED (gpiod not found), falling back to NullLED."
        )

    @patch('led.logger')
    @patch('led.LibgpiodLED', side_effect=FileNotFoundError("chip not found"))
    def test_factory_falls_back_to_null_on_file_not_found_error(self, mock_LibgpiodLED, mock_logger):
        """If LibgpiodLED fails with FileNotFoundError, factory should return NullLED."""
        config = self.get_mock_config(enabled=True)
        instance = led.create_led_instance(config)
        self.assertIsInstance(instance, led.NullLED)
        # Verify that the error was logged, which also suppresses console output
        mock_logger.error.assert_called_once_with(
            "Could not initialize LibgpiodLED (chip not found), falling back to NullLED."
        )


# This allows running the tests directly from the command line
if __name__ == '__main__':
    unittest.main()