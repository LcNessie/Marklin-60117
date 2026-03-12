# Märklin UDP Bridge

A Python-based application for Märklin CAN-over-UDP traffic, designed to run on a Raspberry Pi. It provides a visual status of the track power (Go/Stop) and network link via an RGB LED and can operate in two modes: UDP Bridge or MQTT Gateway.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Usage](#usage)
- [License](#license)
- [Installation and Setup Guide](Documentation/INSTALL.md)
- [Troubleshooting Guide](Documentation/TROUBLESHOOTING.md)
- [Status Monitor Guide](Documentation/mbviewer.md)
- [Updating the Application](Documentation/UPDATING.md)
- [Changelog](Documentation/CHANGELOG.md)
- [Code of Conduct](Documentation/CODE_OF_CONDUCT.md)
- [Making the System Robust (Read-Only Filesystem)](Documentation/ROBUSTNESS.md)

## Features

* **Two Operating Modes:**
  * **UDP Bridge:** Directly relays UDP packets between a control computer and the Märklin network interface.
  * **MQTT Gateway:** A more robust mode that translates the UDP traffic from the Märklin interface into MQTT messages, publishing them to a broker. It also subscribes to a topic to receive commands and send them via UDP to the Märklin interface. This decouples your control software from the bridge.
* **Visual Status LED:** Uses an RGB LED to show the current system state:
  * **Green:** Track power is ON (Go).
  * **Red:** Track power is OFF (Stop).
  * **Yellow:** No packets received from the Märklin interface within a timeout period (link down).
* **MQTT Status Reporting:** Periodically publishes the bridge's status (link, power, packet counts) to a configurable MQTT topic, allowing for remote monitoring and diagnostics.
* **Active Link Probing:** When the link to the Märklin interface goes down, the script actively sends "ping" packets to re-establish the connection and status as quickly as possible.
* **Optional GPIO:** The status LED functionality can be completely disabled in the configuration, allowing the script to run on hardware without GPIO access.
* **Headless Operation:** Designed to run as a `systemd` service for reliable, headless operation.
* **Robust GPIO Control:** Uses the `pigpio` daemon for stable and performant control of the GPIO pins.

## Requirements

### Hardware

* Raspberry Pi (any model with GPIO pins).
* A common-anode or common-cathode RGB LED.
* Appropriate current-limiting resistors for the LED.
* Märklin network interface (e.g., 60117) and a control PC on the same network.

### Software

* Python 3
* A Debian-based OS like Raspberry Pi OS.
* The `pigpiod` daemon must be installed and running if you enable the GPIO status LED feature in the configuration.
* The Python libraries listed in `requirements.txt`, which support the application's optional features (LED status, MQTT mode, etc.).

## Getting Started

* **[Installation and Setup Guide](Documentation/INSTALL.md)**
* **[Troubleshooting Guide](Documentation/TROUBLESHOOTING.md)**
* **[Making the System Robust (Read-Only Filesystem)](Documentation/ROBUSTNESS.md)**

## Usage

The script is designed to be run as a service. To run it in the foreground for testing, navigate to its directory and execute it. All output will be logged to the console.

```bash
python3 marklin_bridge.py
```

## Status Monitor

This project includes a separate, real-time status monitor that provides a terminal-based dashboard for monitoring the bridge's status. It displays the connection status to the MQTT broker, the UDP link status to the Märklin box, track power, and network interface details.

To run the status monitor, you can use the wrapper scripts located in the `bin` directory.

### Windows

```bash
bin\mbviewer.cmd
```

### Linux / macOS

First, make the script executable:

```bash
chmod +x bin/mbviewer
```

Then, run the script:

```bash
bin/mbviewer
```

Press `q` or `Ctrl+C` to exit. For more details, see the [Status Monitor Documentation](Documentation/mbviewer.md).
