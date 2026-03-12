# Making the System Robust (Optional but Recommended)

[<< Home](../README.md) | [Installation Guide](INSTALL.md) | [Troubleshooting](TROUBLESHOOTING.md) | **Robustness** | [Updating](UPDATING.md) | [Changelog](CHANGELOG.md) | [Code of Conduct](CODE_OF_CONDUCT.md)

---

## Table of Contents
- [How to Enable Read-Only Mode](#how-to-enable-read-only-mode)
- [How to Make Changes (e.g., Update the Script)](#how-to-make-changes-eg-update-the-script)

---

For a truly "headless" appliance that needs to be resilient against sudden power loss (e.g., being unplugged), it is highly recommended to make the root filesystem read-only. This prevents SD card corruption, which is a common issue when power is cut during a write operation.

The `raspi-config` tool on Raspberry Pi OS provides an easy way to set this up using an overlay filesystem. When enabled, all file writes are sent to a temporary layer in RAM and are discarded on reboot.

## How to Enable Read-Only Mode

1. Ensure your system is fully configured, and the `marklin-bridge` script is installed and working.

2. Open the configuration tool:

    ```bash
    sudo raspi-config
    ```

3. Navigate to `Performance Options` -> `Overlay File System`.

4. Select **Yes** to enable the overlay filesystem.

5. Select **Yes** again when asked if you want the boot partition to be write-protected.

6. Reboot the Pi when prompted.

After rebooting, the system will be in read-only mode. The `marklin-bridge` service will continue to function correctly, with its logs being written to the in-memory journal.

> **Important Note on Logging in Read-Only Mode:**
> When the read-only overlay is active, all file write operations are redirected to a temporary in-memory filesystem. This affects all logging:
>
> 1.  **File Logs (`LogFile` setting):** Any log file you configure will be written to memory and **will be lost upon reboot.**
> 2.  **Systemd Journal:** By default, `systemd-journald` also writes its logs to an in-memory location on a read-only system. These logs **are also lost upon reboot.**
>
> For this appliance, non-persistent logging is usually acceptable, as you typically only need the logs from the current boot session for troubleshooting (`journalctl -u marklin-bridge.service`). If you require persistent logs across reboots, you would need to configure `systemd-journald` to store logs on a separate, writable partition, which is an advanced setup.

## How to Make Changes (e.g., Update the Script)

Since the filesystem is read-only, you must temporarily disable this protection to make permanent changes.

1. Run `sudo raspi-config` again.
2. Navigate back to `Performance Options` -> `Overlay File System`.
3. Select **No** to disable the overlay filesystem and reboot.
4. After the Pi reboots, the filesystem will be writable. You can now make your changes (e.g., `git pull`, edit configuration).
5. Once you are finished, repeat the steps in "How to Enable Read-Only Mode" to protect your system again.