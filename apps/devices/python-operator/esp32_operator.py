import json
import sys
import paho.mqtt.client as mqtt # type: ignore
from kubernetes import client, config, watch # type: ignore







# --- MQTT Callback Functions ---

def on_connect(client, userdata, flags, rc):

    if rc == 0:
        print("SUCCESS: Connected to Mosquitto Broker successfully!", flush=True)

        # 1. Route specific topic traffic to our new birth function
        client.message_callback_add("esp32/birth", on_birth_message)

        # 2. Subscribe to the birth topic (using QoS 1 to match command delivery expectations)
        client.subscribe("esp32/birth", qos=1)
        print("Subscribed to tracking topic: esp32/birth", flush=True)

    else:
        error_codes = {
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorized"
        }
        err_msg = error_codes.get(rc, f"Unknown error code {rc}")
        print(f"ERROR: Failed to connect to Mosquitto. Reason: {err_msg}", file=sys.stderr, flush=True)

def on_publish(client, userdata, mid):
    """
    This fires when a message has traveled across the wire and the broker
    has acknowledged receipt (crucial for QoS 1).
    """
    print(f"Packet Delivery Confirmed by Broker (Message ID: {mid})", flush=True)

def on_birth_message(client, userdata, msg):
    """
    Fires whenever an ESP32 boots up and publishes its hardware specifications 
    to the 'esp32/birth' channel.
    """
    try:
        # Decode the raw byte array from the broker
        payload_str = msg.payload.decode('utf-8')
        birth_data = json.loads(payload_str)

        # Extract the fields from the incoming JSON
        ip_address = birth_data.get("IP", "Unknown IP")
        version = birth_data.get("firmware", "Unknown Version")
        mac_addr = birth_data.get("MacAddress", "Unknown MAC")

        print(f"\n[DEVICE BIRTH DETECTED]", flush=True)
        print(f" -> MAC Address:      {mac_addr}", flush=True)
        print(f" -> IP Address:       {ip_address}", flush=True)
        print(f" -> Current Firmware: {version}\n", flush=True)

    except json.JSONDecodeError:
        print(f"WARNING: Received birth payload on topic {msg.topic}, but it was not valid JSON: {msg.payload}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"ERROR: Failed to process birth message: {e}", file=sys.stderr, flush=True)

# -------------------------------









# --- MQTT Initialization ---
print("Initializing ESP32 GitOps Operator (Jun10 1230)...", flush=True)

# Connect to local cluster core
# Connect to local Mosquitto broker
# Bind logging callbacks
config.load_incluster_config()
custom_api = client.CustomObjectsApi()

mqtt_client = mqtt.Client(client_id="esp32-python-operator")

mqtt_client.on_connect = on_connect
mqtt_client.on_publish = on_publish
mqtt_client.on_message = on_birth_message

try:
    # 'iot' broker service
    broker_address = "mosquitto-service.iot.svc.cluster.local" 
    print(f"Attempting background connection to: {broker_address}...", flush=True)

    mqtt_client.connect(broker_address, 1883, 60)
except Exception as e:
    print(f"CRITICAL: Could not resolve or reach broker address. Details: {e}", file=sys.stderr, flush=True)
    sys.exit(1)

# start the background network thread to handle callbacks and reconnects automatically
mqtt_client.loop_start()

# -------------------------------









# Point to your MinIO instance running inside storage namespace
MINIO_BASE_URL = "http://minio-service.storage.svc.cluster.local:9000/firmware-binaries"

print("Watching for ESP32 target firmware adjustments in GitOps...", flush=True)
w = watch.Watch()

# Watch your custom devices folder for changes synced by ArgoCD inside 'esp32' namespace
for event in w.stream(custom_api.list_namespaced_custom_object, group="iot.homelab", version="v1alpha1", namespace="esp32", plural="esp32devices"):
    device = event['object']
    device_name = device['metadata']['name']

    spec = device.get('spec', {})
    status = device.get('status', {})

    target_version = spec.get('targetFirmwareVersion')
    current_version = status.get('currentFirmwareVersion')

    # If Git target version doesn't match what the silicon is running, trigger the OTA update!
    if target_version and target_version != current_version:
        print(f"Mismatch detected on {device_name}! Target: {target_version}, Running: {current_version}", flush=True)

        # Construct the target binary path pointing to your adjacent MinIO repository
        ota_payload = {
            "command": "TRIGGER_OTA",
            "version": target_version,
            "url": f"{MINIO_BASE_URL}/{device_name}/firmware_{target_version}.bin"
        }

        # Blast the instructions down to the specific physical chip channel over MQTT
        command_topic = f"esp32/commands/{device_name}"
        mqtt_client.publish(command_topic, json.dumps(ota_payload), qos=1)
        print(f"Dispatched OTA command to topic: {command_topic}", flush=True)