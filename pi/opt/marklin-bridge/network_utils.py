import socket
import subprocess
try:
    import constants
    import psutil
except ImportError:
    psutil = None

class NetworkStatus:
    """
    A utility class to determine network interface status by probing a target IP.
    Encapsulates the logic for finding the active interface and its status.
    """
    def __init__(self):
        """Initializes the NetworkStatus utility."""
        self.psutil_available = psutil is not None

    def _get_iface_status(self, iface_name):
        """Gets the UP/DOWN status for a given interface name."""
        if not iface_name or iface_name == constants.STATUS_NA:
            return constants.STATUS_UNKNOWN
        try:
            stats = psutil.net_if_stats()
            if iface_name in stats:
                return constants.STATUS_UP if stats[iface_name].isup else constants.STATUS_DOWN
        except Exception:
            pass # Keep status as UNKNOWN
        return constants.STATUS_UNKNOWN

    def _get_ssid(self, iface_name):
        """Gets the SSID for a given wireless interface name."""
        if not iface_name or not iface_name.startswith('wl'):
            return constants.STATUS_NA
        try:
            # Use iwgetid to get the SSID. This is Linux-specific.
            output = subprocess.check_output(['iwgetid', '-r', iface_name], text=True)
            return output.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Command fails if not a wireless interface or not connected
            return constants.STATUS_NA

    def get_interface_info(self, iface_name):
        """
        Gets the details for a specific network interface.
        Returns: (ip_address, link_status, ssid)
        """
        if not self.psutil_available:
            return (constants.STATUS_NA, constants.STATUS_NO_PSUTIL, constants.STATUS_NA)

        try:
            all_ifaces = psutil.net_if_addrs()
            if iface_name not in all_ifaces:
                return (constants.STATUS_NA, constants.STATUS_DOWN, constants.STATUS_NA)

            # Find the IPv4 address
            ip_address = constants.STATUS_NA
            for addr in all_ifaces[iface_name]:
                if addr.family == socket.AF_INET:
                    ip_address = addr.address
                    break

            status = self._get_iface_status(iface_name)
            ssid = self._get_ssid(iface_name)

            return (ip_address, status, ssid)
        except Exception:
            return (constants.STATUS_NA, constants.STATUS_UNKNOWN, constants.STATUS_NA)