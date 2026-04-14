# Märklin UDP Bridge

**Control your Märklin layout from a PC or Smart Home without the expense of a Central Station!**

The Märklin 60117 WLAN box (or 60113 with a WiFi/LAN adapter) is a fantastic, budget-friendly alternative to investing in a full CS2 or CS3 Central Station. However, out of the box, the 60117 creates its own isolated Wi-Fi network. This makes it difficult to integrate with your existing home network, standard PC control software, or custom smart home systems.

The primary intention of this project is to bridge that fixed 60117 access point directly to your native home network. Running on a Raspberry Pi, this robust Python-based application seamlessly translates and manages traffic between your control software (like Rocrail, iTrain), an MQTT broker, and the Märklin tracks.

---

### 🚂 Where to find the code and docs?

The main source code, documentation, and configuration for this project are located in the `pi/opt/marklin-bridge/` directory.

👉 [**Click here to go to the Main README**](pi/opt/marklin-bridge/README.md) for comprehensive details, installation instructions, and usage guides.