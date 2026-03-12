# Troubleshooting Guide

[<< Home](../README.md) | [Installation Guide](INSTALL.md) | **Troubleshooting** | [Robustness](ROBUSTNESS.md) | [Updating](UPDATING.md) | [Changelog](CHANGELOG.md) | [Code of Conduct](CODE_OF_CONDUCT.md)

---

## Table of Contents
- [Check Service Status](#check-service-status)
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