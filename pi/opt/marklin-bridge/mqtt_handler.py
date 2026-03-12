import logging
import config

def on_mqtt_message(client, userdata, msg):
    """Callback for when a message is received from the MQTT broker."""
    app = userdata['app']
    app.packets_from_mqtt += 1
    try:
        app.sock.sendto(msg.payload, (config.MARKLIN_IP, config.PORT))
        app.packets_to_marklin += 1
        app.last_source = f"MQTT:{msg.topic}"
    except Exception as e:
        logging.error(f"Error forwarding MQTT message as UDP to Märklin interface: {e}")
        app.last_source = f"ERROR: {e}"

def on_mqtt_connect(client, userdata, flags, reason_code, properties):
    """Callback for when connection to MQTT broker is established (Paho v2)."""
    app = userdata['app']
    if reason_code == 0:
        app.mqtt_status = "CONNECTED"
        logging.info("Successfully connected to MQTT broker.")
        app._publish_status()
    else:
        app.mqtt_status = f"FAILED ({reason_code})"
        logging.error(f"Failed to connect to MQTT broker, return code {reason_code}")

def on_mqtt_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    """Callback for when the client disconnects from the MQTT broker (Paho v2)."""
    app = userdata['app']
    app.mqtt_status = "DISCONNECTED"
    if reason_code != 0: # 0 means a clean disconnect from our side
        logging.warning("Unexpectedly disconnected from MQTT broker. Reconnecting...")