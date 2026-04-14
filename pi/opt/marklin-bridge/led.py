import abc
import logging

# Attempt to import optional libraries, but don't fail if they're not installed.
# The factory function will determine which implementation to use.
try:
    import gpiod
except ImportError:
    gpiod = None

logger = logging.getLogger(__name__)

# --- LED Colors ---
# Using simple on/off (0 or 255) as PWM is not used.
COLOR_GREEN_GO = (0, 255, 0)
COLOR_RED_STOP = (255, 0, 0)
COLOR_YELLOW_NO_LINK = (255, 255, 0) # Simple on/off yellow
COLOR_WHITE_STARTING = (255, 255, 255)
COLOR_OFF = (0, 0, 0)

class AbstractLED(abc.ABC):
    """Abstract base class for an RGB LED controller."""
    @abc.abstractmethod
    def set_color(self, color):
        """Sets the color of the LED. Color is an (R, G, B) tuple."""
        pass

    @abc.abstractmethod
    def cleanup(self):
        """Cleans up resources used by the LED controller."""
        pass

class LibgpiodLED(AbstractLED):
    """An RGB LED controller using libgpiod for simple on/off control."""
    def __init__(self, red_pin, green_pin, blue_pin, common_anode=False):
        if not gpiod:
            raise ImportError("The 'gpiod' library is not installed.")

        self.pins = (red_pin, green_pin, blue_pin)
        self.common_anode = common_anode
        self.chip = gpiod.Chip('gpiochip0')
        self.lines = self.chip.get_lines(self.pins)
        self.lines.request(consumer='marklin-bridge', type=gpiod.LINE_REQ_DIR_OUT)
        self.set_color(COLOR_OFF)  # Start with LED off
        logger.info("LibgpiodLED initialized (simple on/off).")

    def set_color(self, color):
        """Sets the color of the LED by turning pins on or off."""
        r, g, b = color

        # Convert 0-255 values to simple 0 or 1. Any value > 0 is considered ON.
        r_val = 1 if r > 0 else 0
        g_val = 1 if g > 0 else 0
        b_val = 1 if b > 0 else 0

        if self.common_anode:
            # Invert logic for common anode (0=on, 1=off)
            r_val, g_val, b_val = 1 - r_val, 1 - g_val, 1 - b_val

        self.lines.set_values([r_val, g_val, b_val])

    def cleanup(self):
        logger.info("Cleaning up LibgpiodLED resources.")
        self.set_color(COLOR_OFF)
        self.lines.release()

class NullLED(AbstractLED):
    """A no-op LED controller for when GPIO is disabled or unavailable."""
    def __init__(self, *args, **kwargs):
        logger.info("NullLED initialized. GPIO operations will be ignored.")

    def set_color(self, color):
        pass

    def cleanup(self):
        pass

def create_led_instance(config):
    """
    Factory function to create the LED instance.
    It attempts to use `libgpiod` for GPIO control. If the library is not
    available, if GPIO is disabled in the config, or if an error occurs,
    it returns a `NullLED` instance that does nothing.
    """
    if not config.getboolean('GPIO', 'Enabled', fallback=False):
        logger.info("GPIO is disabled in config.ini. Using NullLED.")
        return NullLED()

    try:
        red_pin = config.getint('GPIO', 'RedPin')
        green_pin = config.getint('GPIO', 'GreenPin')
        blue_pin = config.getint('GPIO', 'BluePin')
        common_anode = config.getboolean('GPIO', 'CommonAnode', fallback=False)
    except Exception as e:
        logger.error(f"Failed to read GPIO pin configuration: {e}. Using NullLED.")
        return NullLED()

    # Try to initialize libgpiod
    try:
        return LibgpiodLED(red_pin, green_pin, blue_pin, common_anode=common_anode)
    except (ImportError, FileNotFoundError) as e: # FileNotFoundError if /dev/gpiochip0 is missing
        logger.error(f"Could not initialize LibgpiodLED ({e}), falling back to NullLED.")
        return NullLED()
    except Exception as e:
        logger.error(f"LibgpiodLED failed unexpectedly: {e}. Falling back to NullLED.")
        return NullLED()