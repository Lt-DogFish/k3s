import json
import paho.mqtt.client as mqtt
from kubernetes import client, config, watch

# Connect to your local cluster core
config.load_incluster_config()
custom_api = client.CustomObjectsApi()

# Connect to your local Mosquitto broker
mqtt_client = mqtt.Client()
mqtt_client.connect("mosquitto-service.iot.svc.cluster.local", 1883, 60)
mqtt_client.loop_start()

MINIO_BASE_URL = "http://minio-service.storage.svc.cluster.local:9000/firmware-binaries"

print("Watching for ESP32 target firmware adjustments in GitOps...")
w = watch.Watch()

# Watch your custom devices folder for changes synced by ArgoCD
for event in w.stream(custom_api.list_namespaced_custom_object, group="iot.homelab", version="v1alpha1", namespace="iot", plural="esp32devices"):
    device = event['object']
    device_name = device['metadata']['name']
    
    spec = device.get('spec', {})
    status = device.get('status', {})
    
    target_version = spec.get('targetFirmwareVersion')
    current_version = status.get('currentFirmwareVersion')
    
    # If Git target version doesn't match what the silicon is running, trigger the OTA update!
    if target_version and target_version != current_version:
        print(f"Mismatch detected on {device_name}! Target: {target_version}, Running: {current_version}")
        
        # Construct the target binary path pointing to your adjacent MinIO repository
        ota_payload = {
            "command": "TRIGGER_OTA",
            "version": target_version,
            "url": f"{MINIO_BASE_URL}/{device_name}/firmware_{target_version}.bin"
        }
        
        # Blast the instructions down to the specific physical chip channel over MQTT
        command_topic = f"esp32/commands/{device_name}"
        mqtt_client.publish(command_topic, json.dumps(ota_payload), qos=1)
        print(f"Dispatched OTA command to topic: {command_topic}")