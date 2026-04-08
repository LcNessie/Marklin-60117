# Troubleshooting Guide

<< [Home](../README.md) | [Installation Guide](INSTALL.md) | **Troubleshooting** | [Status Monitor](MBVIEWER.md) | [Robustness](ROBUSTNESS.md) | [Updating](UPDATING.md) | [Changelog](CHANGELOG.md) | [Code of Conduct](CODE_OF_CONDUCT.md)

---

## Table of Contents

- [Check Service Status](#check-service-status)
- [Use the Status Monitor](#use-the-status-monitor)
- [View the Logs](#view-the-logs)
- [Test Manually](#test-manually)
- [Check Dependencies](#check-dependencies)

---

If the `marklin-bridge` service fails to start or is not behaving as expected, here are some steps to diagnose the problem.

## Check Service Status

This is the first command you should run. It provides a summary of the service's state.

```bash
sudo systemctl status marklin-bridge.service
```

- **Look for `Active: active (running)`:** This means the service is running. If you still have issues, check the logs.
- **Look for `Active: failed`:** This means the service tried to start but exited with an error. The status output may include some recent log lines that give a clue.

## Use the Status Monitor

The real-time status monitor (`mbviewer`) is your best tool for spotting issues quickly.

```bash
bin/mbviewer
```

The dashboard is divided into three sections to help you isolate the problem:

1. **Bridge:** Shows application health and total packet traffic.
2. **Märklin Side:** Diagnoses the connection to the tracks (WiFi/UDP).
    - **UDP Link:** If this is `🔴 DOWN`, the Pi cannot reach the Märklin 60117 box. Check if the box is powered on and connected to the WiFi.
    - **Track Power:** `😵 UNKNOWN` means the bridge is confused (usually because the UDP link is down).
3. **Network Side:** Diagnoses the connection to your LAN or MQTT Broker.

### UDP Link is DOWN on a Multi-Homed System (e.g., WiFi and Ethernet)

If your Raspberry Pi is connected to two networks, the operating system might try to send packets to the Märklin box through the wrong interface (e.g., sending out the Ethernet port instead of the WiFi). This will cause the UDP link to fail.

The most reliable solution is to ensure only the `wlan0` interface is connected to the Märklin network and that any other network connections (like `eth0`) are either disconnected or configured at the OS level with static routes to not interfere.

- **Bridge MQTT Status:** If `🔴 FAILED`, the service cannot connect to your broker.

### Track Power is `UNKNOWN` but UDP Link is `UP`

This is a common state after the bridge first starts. It means the bridge is receiving data from the Märklin box, but it has not yet seen a specific "System Go" or "System Stop" command packet.

The Märklin system typically only broadcasts these packets when the power state *changes*.

**Solution:** Use your controller (e.g., Mobile Station, Central Station, or control software) to press "Go" or "Stop". This will send the command, the bridge will see it, and the status will update to 🟢 `GO` or 🔴 `STOP`.

### Status Monitor shows "Waiting for first status message..."

If the `mbviewer` connects successfully to the broker (`Viewer MQTT: 🟢 CONNECTED`) but remains on this screen, it means the `marklin-bridge` service has not published any status information.

This is almost always because the service is not configured to use MQTT. By default, the bridge operates in a simpler "UDP Bridge" mode.

**Solution:**

1. Edit the configuration file: `sudo nano /opt/marklin-bridge/config.ini`
2. Find the `[MQTT]` section.
3. Set `Enabled = true`.
4. Ensure `BrokerIP` points to your MQTT server (use `127.0.0.1` if it's on the same Pi).
5. Restart the service: `sudo systemctl restart marklin-bridge.service`

The viewer should begin displaying data within a few seconds.

## View the Logs

To see the full output from the script, use `journalctl`.

```bash
# View the most recent logs and follow new entries
journalctl -u marklin-bridge.service -f

# View all logs from the current boot session
journalctl -u marklin-bridge.service -b
```

Look for Python tracebacks or error messages from the script itself (e.g., "Could not connect to MQTT broker", "GPIO setup failed").

## Test Manually

Sometimes it's easiest to run the script directly to see immediate errors. Run it as the `marklin-bridge` user to ensure the environment is the same as the service.
This will show any startup errors (like problems with `config.ini` or network sockets) directly in your terminal as log messages.

```bash
sudo -u marklin-bridge /opt/marklin-bridge/venv/bin/python3 /opt/marklin-bridge/marklin_bridge.py
```

This will show any startup errors (like problems with `config.ini` or network sockets) directly in your terminal.

## Check Dependencies

The service depends on the network. Ensure that you can `ping` the Märklin interface IP address from your `config.ini`. If using the status LED, ensure the `marklin-bridge` user has GPIO access. If the logs show errors related to `gpiod` or `/dev/gpiochip0`, there may be a permissions issue or the library may not be installed correctly.
