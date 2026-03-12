# Troubleshooting Guide

<< Home | Installation Guide | **Troubleshooting** | Status Monitor | Robustness | Updating | Changelog | Code of Conduct

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

*   **Look for `Active: active (running)`:** This means the service is running. If you still have issues, check the logs.
*   **Look for `Active: failed`:** This means the service tried to start but exited with an error. The status output may include some recent log lines that give a clue.

## Use the Status Monitor

The real-time status monitor (`mbviewer`) is your best tool for spotting issues quickly.

```bash
bin/mbviewer
```

The dashboard is divided into three sections to help you isolate the problem:

1.  **Bridge:** Shows application health and total packet traffic.
2.  **Märklin Side:** Diagnoses the connection to the tracks (WiFi/UDP).
    *   **UDP Link:** If this is `🔴 DOWN`, the Pi cannot reach the Märklin 60117 box. Check if the box is powered on and connected to the WiFi.
    *   **Track Power:** `😵 UNKNOWN` means the bridge is confused (usually because the UDP link is down).
3.  **Network Side:** Diagnoses the connection to your LAN or MQTT Broker.
    *   **Bridge MQTT Status:** If `🔴 FAILED`, the service cannot connect to your broker.

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

The service depends on the network and the `pigpio` daemon. Ensure `systemctl status pigpiod.service` shows it is `active (running)` and that you can `ping` the Märklin interface IP address from your `config.ini`.