import unittest
from unittest.mock import patch, MagicMock

# Import the module to be tested
import led

class TestStatusLED(unittest.TestCase):
    """
    Test suite for the led.StatusLED class.

    This suite demonstrates how to test code that depends on a hardware-specific
    library (`pigpio`), which won't be available on a standard development machine.
    We use `unittest.mock.patch` to replace the `pigpio` module with a mock
    object, allowing us to test the logic of our `led.py` functions in isolation
    without needing actual GPIO hardware.
    """

    # The `@patch` decorator intercepts any attempt by the `led` module to import
    # or access `pigpio` and replaces it with a `MagicMock` object. This mock
    # is then passed as an argument (`mock_pigpio`) to our test method.
    @patch('led.pigpio')
    def test_init_success(self, mock_pigpio):
        """
        Tests the successful initialization of the StatusLED class.
        This is the "happy path" where the pigpio library is present and the
        hardware daemon (`pigpiod`) is running.
        """
        # --- Arrange: Configure the mock pigpio library to behave as if it's working. ---

        # 1. The `StatusLED` constructor calls `pigpio.pi()`. We need to control
        #    what this call returns. We'll create a mock instance of the `pi` object.
        mock_pi_instance = MagicMock()

        # 2. The code checks `self.pi.connected`. We'll set this to True to simulate a
        #    successful connection to the `pigpiod` daemon.
        mock_pi_instance.connected = True

        # 3. We configure our top-level `mock_pigpio` so that when `pi()` is called
        #    on it, it returns our pre-configured `mock_pi_instance`.
        mock_pigpio.pi.return_value = mock_pi_instance

        # --- Act: Instantiate the class we are testing. ---
        status_led = led.StatusLED(16, 20, 21)

        # --- Assert: Check that our function interacted with the mock library correctly. ---

        # Was `pigpio.pi()` called exactly once to get the connection?
        mock_pigpio.pi.assert_called_once()

        # Were the GPIO pins set to OUTPUT mode? We use `assert_any_call` because
        # the order in which the pins are set doesn't matter.
        mock_pi_instance.set_mode.assert_any_call(16, mock_pigpio.OUTPUT)
        mock_pi_instance.set_mode.assert_any_call(20, mock_pigpio.OUTPUT)
        mock_pi_instance.set_mode.assert_any_call(21, mock_pigpio.OUTPUT)

        # Did the constructor correctly assign the pi instance?
        self.assertEqual(
            status_led.pi,
            mock_pi_instance,
            msg="The constructor should assign the created pigpio instance to self.pi."
        )

    # Here, we patch `led.pigpio` and replace it with `None`. This directly
    # simulates the `ImportError` case where the `pigpio` module is not installed.
    @patch('led.pigpio', None)
    def test_init_no_pigpio_library(self):
        """Tests that the constructor raises ImportError if pigpio is not installed."""
        # --- Arrange ---
        # The `@patch('led.pigpio', None)` decorator handles the entire setup.
        # It ensures that within this test, the `pigpio` variable inside the
        # `led` module is `None`.

        # --- Act & Assert ---
        # We use `assertRaises` as a context manager. The code inside the `with`
        # block is expected to raise an `ImportError`. If it does, the test passes.
        # If it raises a different error or no error, the test fails.
        with self.assertRaises(ImportError) as cm:
            led.StatusLED(16, 20, 21)

        # We can also inspect the exception object (`cm.exception`) to ensure
        # it contains the correct error message.
        self.assertEqual(
            str(cm.exception),
            "The 'pigpio' library is not installed.",
            msg="The error message should clearly state that pigpio is missing."
        )

    @patch('led.pigpio')
    def test_init_daemon_not_connected(self, mock_pigpio):
        """Tests that the constructor raises ConnectionError if the daemon is not running."""
        # --- Arrange: Configure the mock to simulate a disconnected daemon. ---
        mock_pi_instance = MagicMock()
        # This is the key part: we set `.connected` to False.
        mock_pi_instance.connected = False
        mock_pigpio.pi.return_value = mock_pi_instance

        # --- Act & Assert: Check that a ConnectionError is raised. ---
        with self.assertRaises(ConnectionError) as cm:
            led.StatusLED(16, 20, 21)
        self.assertEqual(
            str(cm.exception),
            "Could not connect to the pigpiod daemon.",
            msg="A specific ConnectionError should be raised if the daemon is not found."
        )

    @patch('led.pigpio')
    def test_set_color_success(self, mock_pigpio):
        """Tests setting the LED color with a valid, connected instance."""
        # --- Arrange ---
        # We mock pigpio to allow the StatusLED to initialize successfully.
        mock_pi_instance = MagicMock()
        mock_pi_instance.connected = True
        mock_pigpio.pi.return_value = mock_pi_instance

        status_led = led.StatusLED(16, 20, 21)
        red, green, blue = 16, 20, 21
        color = (10, 20, 30)

        # --- Act ---
        status_led.set_color(color)

        # --- Assert: Verify that the PWM duty cycle was set for each color pin. ---
        # `assert_any_call` is used because the order of these calls is not important.
        mock_pi_instance.set_PWM_dutycycle.assert_any_call(red, 10)
        mock_pi_instance.set_PWM_dutycycle.assert_any_call(green, 20)
        mock_pi_instance.set_PWM_dutycycle.assert_any_call(blue, 30)

        # We also assert that exactly 3 calls were made, no more, no less.
        self.assertEqual(
            mock_pi_instance.set_PWM_dutycycle.call_count,
            3,
            msg="Should call set_PWM_dutycycle exactly once for each of the R, G, and B pins."
        )

    @patch('led.pigpio')
    def test_set_color_pi_not_connected(self, mock_pigpio):
        """
        Tests that set_color does nothing if the pi instance is not connected.
        This tests the function's safety guard.
        """
        # --- Arrange ---
        mock_pi_instance = MagicMock()
        mock_pi_instance.connected = True # Connect for successful init
        mock_pigpio.pi.return_value = mock_pi_instance

        status_led = led.StatusLED(16, 20, 21)

        # Now, simulate a disconnection and reset the mock for the next check
        status_led.pi.connected = False
        status_led.pi.reset_mock()

        # --- Act ---
        status_led.set_color((10, 20, 30))

        # --- Assert ---
        # The function should have returned early without attempting any hardware calls.
        status_led.pi.set_PWM_dutycycle.assert_not_called()

    @patch('led.pigpio')
    def test_set_color_pi_is_none(self, mock_pigpio):
        """
        Tests that set_color handles a None pi object gracefully. This could
        happen if the object was manually modified after cleanup.
        """
        # --- Arrange ---
        mock_pi_instance = MagicMock()
        mock_pi_instance.connected = True
        mock_pigpio.pi.return_value = mock_pi_instance

        status_led = led.StatusLED(16, 20, 21)
        status_led.pi = None # Manually set pi to None

        # --- Act & Assert ---
        # The `set_color` method has a guard `if not self.pi:`. We are testing
        # that this guard works correctly, preventing an AttributeError.
        try:
            status_led.set_color((10, 20, 30))
            # If we reach this line, it means no exception was raised, which is the correct behavior.
        except Exception as e:
            self.fail(f"set_color() raised an unexpected exception when pi is None: {e}")

    @patch('led.pigpio')
    def test_cleanup_success(self, mock_pigpio):
        """Tests that cleanup turns off the LED, stops the pi instance, and clears the reference."""
        # --- Arrange ---
        mock_pi_instance = MagicMock()
        mock_pi_instance.connected = True
        mock_pigpio.pi.return_value = mock_pi_instance

        status_led = led.StatusLED(16, 20, 21)
        red, green, blue = 16, 20, 21

        # --- Act ---
        status_led.cleanup()

        # --- Assert ---
        # 1. Check that it tried to set the color to OFF (0, 0, 0) to turn off the LED.
        mock_pi_instance.set_PWM_dutycycle.assert_any_call(red, 0)
        mock_pi_instance.set_PWM_dutycycle.assert_any_call(green, 0)
        mock_pi_instance.set_PWM_dutycycle.assert_any_call(blue, 0)

        # 2. Check that it stopped the connection to release pigpio resources.
        mock_pi_instance.stop.assert_called_once_with()

        # 3. Check that the internal pi reference is cleared to prevent reuse.
        self.assertIsNone(status_led.pi, "The internal pi reference should be set to None after cleanup.")

# This allows running the tests directly from the command line
if __name__ == '__main__':
    unittest.main()