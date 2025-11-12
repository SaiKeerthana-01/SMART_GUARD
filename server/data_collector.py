import ssl
print("SSL module imported successfully")

import socket
# Force IPv4 sockets to avoid address family errors
original_socket = socket.socket
def ipv4_socket(family=socket.AF_INET, *args, **kwargs):
    return original_socket(socket.AF_INET, *args, **kwargs)
socket.socket = ipv4_socket

import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient
import json

MQTT_BROKER = "10.0.0.254"
INFLUX_HOST = "localhost"
INFLUX_DB = "sensor_data"

influx = InfluxDBClient(host=INFLUX_HOST, database=INFLUX_DB)

def on_connect(client, userdata, flags, rc):
    print("="*80)
    print("DATA COLLECTOR - Connected to MQTT Broker")
    print("="*80)
    client.subscribe("sensors/#")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        metric_type = msg.topic.split('/')[1]
        timestamp_str = payload['timestamp']
        json_body = [{
            "measurement": "sensor_data",
            "tags": {
                "sensor_id": payload['sensor_id'],
                "room": payload['room'],
                "type": metric_type
            },
            "fields": {
                "value": float(payload['value'])
            }
            # Removed the "time" field to let InfluxDB auto-assign
        }]
        influx.write_points(json_body, time_precision='s')

        # Pretty print timestamp inline with other details
        print(f"[STORED] {timestamp_str} | Room: {payload['room']:<8} | Sensor: {payload['sensor_id']:<12} | {metric_type.upper():<11} | Value: {float(payload['value']):>7.1f}")
    except Exception as e:
        print(f"[ERROR] {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message 
client.connect(MQTT_BROKER, 1883, 60)
client.loop_forever()