# Diagnostics Tool (`mbviewer.py`)

The `mbviewer.py` script is a real-time, terminal-based dashboard for monitoring the status of the Märklin Bridge application. It provides a quick and easy way to verify that all components of the system are working correctly.

## Running the Tool

To run the tool, simply execute it with Python from the `pi/opt/marklin-bridge` directory:

```bash
python3 mbviewer.py
```

The dashboard will appear in your terminal. Press `q` or `Ctrl+C` to exit.

## Understanding the Dashboard

The dashboard is split into several sections, each providing specific information about the bridge's status.

### MQTT Connection

This section shows the status of the diagnostic tool's own connection to the MQTT broker.

- **Broker Status:**
  - `🟢 CONNECTED`: The tool is successfully connected to the MQTT broker and is receiving status updates.
  - `🔴 DISCONNECTED`: The tool has lost its connection to the broker.
  - `🟡 CONNECTING` / `FAILED`: The tool is attempting to connect or has failed to connect. Check that the broker IP and port are configured correctly in `config.py` and that the broker is running.

### Bridge Status

This section displays the core status of the main bridge application, as reported in the MQTT status messages.

-   **Version:** The version of the running Märklin Bridge application.
-   **UDP Link:** The status of the direct UDP connection between the bridge and the Märklin network interface box (e.g., 60117).
    -   `🟢 UP`: The bridge is receiving UDP packets from the Märklin box.
    -   `😵 DOWN`: The bridge has not received any UDP packets from the Märklin box within the expected timeout. This indicates a potential problem with the physical connection or the Märklin box itself.
-   **Track Power:** The last known status of the track power.
    -   `🟢 GO`: Track power is on.
    -   `🔴 STOP`: Track power is off.
    -   `🟡 UNKNOWN`: The bridge has not yet received a message indicating the track power status.

### Network Interfaces

This section shows the status of the network interfaces on the machine running the bridge (e.g., the Raspberry Pi).

-   For each interface (e.g., `eth0`, `wlan0`):
    -   `🟢 UP`: The interface is active and has an IP address.
    -   `🔴 DOWN`: The interface is down or not configured.

### Bridge Activity

This section provides a live look at the packet counters.

-   **From Box:** A counter of UDP packets received by the bridge *from* the Märklin network interface.
-   **To Box:** A counter of UDP packets sent *to* the Märklin network interface from the bridge.
-   **Last Source:** The IP address and port of the last device that sent a command to the bridge.
