# Installation and Setup Guide

<< [Home](../README.md) | **Installation Guide** | [Troubleshooting](TROUBLESHOOTING.md) | [Status Monitor](MBVIEWER.md) | [Robustness](ROBUSTNESS.md) | [Updating](UPDATING.md) | [Changelog](CHANGELOG.md) | [Code of Conduct](CODE_OF_CONDUCT.md)

---

## Table of Contents

- [Installation Steps](#installation-steps)
- [Configuration Details](#configuration-details)
- [Running as a Systemd Service](#running-as-a-systemd-service)

---

This guide provides detailed instructions for installing the Märklin UDP Bridge, configuring it, and setting it up to run as a `systemd` service on a Raspberry Pi.

## Installation Steps

1. **Create Directory and User:**

    ```bash
    sudo mkdir -p /opt/marklin-bridge
    sudo useradd -r -s /bin/false marklin-bridge
    ```

2. **Copy Application Files:**
    Copy all Python files (`*.py`), `requirements.txt`, `config.ini.template`, and `marklin-bridge.service` from the project's `pi/opt/marklin-bridge` directory to `/opt/marklin-bridge/` on your Raspberry Pi.

3. **Create and Edit Configuration:**
    Create your personal configuration file by copying the template, then edit it to match your network and GPIO setup.

    ```bash
    sudo cp /opt/marklin-bridge/config.ini.template /opt/marklin-bridge/config.ini
    sudo -u marklin-bridge nano /opt/marklin-bridge/config.ini
    ```

    Be sure to configure your network IPs and choose your operating modes (you can enable UDP Bridge, MQTT Gateway, or both simultaneously).

4. **Set Permissions:**
    Give the `marklin-bridge` user ownership of the entire application directory.

    ```bash
    sudo chown -R marklin-bridge:marklin-bridge /opt/marklin-bridge
    ```

5. **Create Python Virtual Environment:**
    Using a virtual environment is a best practice that isolates the project's dependencies from the system's global Python packages.

    ```bash
    # Run as the 'marklin-bridge' user to ensure correct permissions
    sudo -u marklin-bridge /usr/bin/python3 -m venv /opt/marklin-bridge/venv
    ```

6. **Install Python Dependencies:**
    Install the required Python libraries into the new virtual environment.

    ```bash
    # Use the pip from the virtual environment. No sudo is needed.
    sudo -u marklin-bridge /opt/marklin-bridge/venv/bin/pip3 install -r /opt/marklin-bridge/requirements.txt
    ```
    
7. **Verify GPIO Access (Optional):**
    This application uses the `libgpiod` library for LED control, which is included in modern Raspberry Pi OS. The `pip install` command in the previous step will have installed the necessary Python bindings. No further action is typically required.

## Configuration Details

The `config.ini` file allows you to customize the bridge's behavior.

- **[Network]**: Configure IP addresses for your controller and the Märklin interface.
- **[GPIO]**: Enable/disable the status LED and specify the GPIO pins.
- **Note on Constants**: Fundamental protocol constants (e.g., CAN frame details) are defined in `constants.py` and are not intended for user configuration.
- **[MQTT]**: Enable MQTT Gateway mode and configure broker details and topics.
- **[Logging]**: (Service Mode Only)
  - **Default (Recommended):** By default, `LogFile` is empty, and all logs are sent to the `systemd` journal. You can view them with `journalctl -u marklin-bridge.service`. This is the best option for most users.
  - **Alternative (File Logging):** If you prefer a dedicated log file, you can set the `LogFile` path. This is useful if you are not using `systemd` or want a separate, self-managed log.
  - `LogFile`: Path to a dedicated log file (e.g., `/opt/marklin-bridge/marklin_bridge.log`).
  - `LogFileMaxSizeMB`: The maximum size in megabytes before the log file is rotated.
  - `LogFileBackupCount`: The number of old log files to keep.

Example `[Logging]` section for a dedicated log file:

```ini
[Logging]
LogFile = /opt/marklin-bridge/marklin_bridge.log
```

## Running as a Systemd Service

To have the bridge start automatically on boot, you can use the provided `systemd` service file.

1. **Copy the service file:**

    Copy the service file from the application directory to the systemd directory.

    ```bash
    sudo cp /opt/marklin-bridge/marklin-bridge.service /etc/systemd/system/
    ```

2. **Enable and start the service:**

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable marklin-bridge.service
    sudo systemctl start marklin-bridge.service
    ```

3. **Check the status:**

    You can check if the service is running correctly with:

    ```bash
    sudo systemctl status marklin-bridge.service
    ```

    To view the logs from the service, use `journalctl`:

    ```bash
    journalctl -u marklin-bridge.service -f
    ```
