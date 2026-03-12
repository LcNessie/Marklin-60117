try:
    import pigpio
except ImportError:
    pigpio = None

# --- LED Colors ---
# Using 0-255 scale for pigpio PWM
COLOR_GREEN_GO = (0, 255, 0)
COLOR_RED_STOP = (255, 0, 0)
COLOR_YELLOW_NO_LINK = (150, 150, 0) # Dimmer yellow
COLOR_WHITE_STARTING = (255, 255, 255)
COLOR_OFF = (0, 0, 0)

class StatusLED:
    """
    Manages a single RGB status LED using the pigpio library.
    This class encapsulates the state (pi connection, pin numbers) and provides
    a simple interface to set the color and clean up resources.
    """
    def __init__(self, red_pin, green_pin, blue_pin):
        """
        Initializes pigpio and sets up GPIO pins for the LED.
        Raises ImportError if pigpio is not installed, or ConnectionError if
        the pigpiod daemon is not accessible.
        """
        if not pigpio:
            raise ImportError("The 'pigpio' library is not installed.")

        self.red_pin = red_pin
        self.green_pin = green_pin
        self.blue_pin = blue_pin

        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise ConnectionError("Could not connect to the pigpiod daemon.")

        self.pi.set_mode(self.red_pin, pigpio.OUTPUT)
        self.pi.set_mode(self.green_pin, pigpio.OUTPUT)
        self.pi.set_mode(self.blue_pin, pigpio.OUTPUT)

    def set_color(self, color):
        """Sets the RGB LED color using pigpio PWM."""
        if not self.pi or not self.pi.connected:
            return
        r, g, b = color
        self.pi.set_PWM_dutycycle(self.red_pin, r)
        self.pi.set_PWM_dutycycle(self.green_pin, g)
        self.pi.set_PWM_dutycycle(self.blue_pin, b)

    def cleanup(self):
        """Turns off the LED and releases pigpio resources."""
        if self.pi and self.pi.connected:
            self.set_color(COLOR_OFF)
            self.pi.stop()
            self.pi = None # Prevent further use after cleanup