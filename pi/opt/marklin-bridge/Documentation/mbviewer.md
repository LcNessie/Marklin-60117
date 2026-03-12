# Status Monitor Guide

<< [Home](../README.md) | [Installation Guide](INSTALL.md) | [Troubleshooting](TROUBLESHOOTING.md) | **Status Monitor** | [Robustness](ROBUSTNESS.md) | [Updating](UPDATING.md) | [Changelog](CHANGELOG.md) | [Code of Conduct](CODE_OF_CONDUCT.md)

---

The **Märklin UDP Bridge Status Monitor** (`mbviewer.py`) is a real-time, terminal-based dashboard. It connects to the MQTT broker to visualize the telemetry data published by the main bridge application. This allows you to monitor the health of the UDP link to the tracks, the MQTT connection, and traffic statistics without needing to SSH into the Pi and tail logs.

## Prerequisites

The viewer runs on any machine that has Python 3 and network access to your MQTT broker. It does not need to run on the Raspberry Pi itself, although it often does.

### Dependencies

*   **Python 3**
*   **paho-mqtt**
*   **windows-curses** (Windows only)

To install dependencies:

```bash
pip install paho-mqtt
# On Windows only:
pip install windows-curses
```

## Usage

To launch the viewer, run the script from the terminal:

```bash
# Linux / macOS
./mbviewer.py

# Windows
python mbviewer.py
```

### Command Line Arguments

By default, the viewer tries to connect to an MQTT broker on `127.0.0.1` (localhost). You can configure the connection using command-line arguments:

| Argument | Default | Description |
| :--- | :--- | :--- |
| `--broker` | `127.0.0.1` | The IP address or hostname of the MQTT broker. |
| `--port` | `1883` | The port of the MQTT broker. |
| `--topic` | `marklin/status` | The MQTT topic where the bridge publishes its status. |
| `--username` | *None* | Username for MQTT authentication. |
| `--password` | *None* | Password for MQTT authentication. |

> **Note:** The viewer does not read `config.ini`. If you have customized the MQTT broker or topic in the bridge configuration, you must provide those same details here using arguments.

**Example:** Connecting to a remote broker:

```bash
python mbviewer.py --broker 192.168.1.10 --username myuser --password mypass
```

## Interface Guide

The dashboard is divided into three main sections:

### 1. Bridge
Displays general application information.
*   **Version:** The version of the `marklin-bridge` service running.

### 2. Märklin Side
Monitors the connection between the Raspberry Pi and the Märklin 60117/60113 Box (CS3).

*   **Interface:** The network interface on the Pi used for this connection (e.g., `wlan0`). Shows connection status and SSID.
*   **Marklin Bridge IP:** The IP address of the Pi on this interface.
*   **Marklin Wifi Box IP:** The target IP of the Märklin hardware.
*   **UDP Link:**
    *   🟢 `UP`: The bridge is successfully exchanging packets with the Märklin box.
    *   🔴 `DOWN`: No packets received recently. The link is broken.
*   **Track Power:**
    *   🟢 `GO`: Track power is ON.
    *   🔴 `STOP`: Track power is OFF (Emergency Stop).
    *   😵 `UNKNOWN`: State cannot be determined (usually because the link is down).
*   **UDP Counters:** Total packets sent and received over UDP.

### 3. Network Side
Monitors the connection between the Raspberry Pi and your home network/MQTT broker.

*   **Interface:** The network interface used (e.g., `eth0`).
*   **Bridge Home IP:** The IP address of the Pi on your home LAN.
*   **MQTT Broker IP:** The configured broker address.
*   **Bridge MQTT Status:**
    *   🟢 `CONNECTED`: The bridge service is successfully talking to the broker.
    *   🔴 `FAILED`: The bridge service cannot connect.
*   **MQTT Counters:** Total packets sent and received over MQTT.

### Viewer MQTT
At the bottom, the **Viewer MQTT** status indicates if *this viewer application* is successfully connected to the broker.