import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

THRESHOLDS = {
    'temperature': {'max': 30, 'min': 18},
    'co2': {'max': 1000, 'min': None},
    'light': {'max': None, 'min': 300},
    'humidity': {'max': 70, 'min': 30}
}

influx = InfluxDBClient(host=INFLUX_HOST, database=INFLUX_DB)

def check_anomaly(metric_type, value, room, sensor_id):
    threshold = THRESHOLDS.get(metric_type, {})

    if threshold.get('max') and value > threshold['max']:
        print_alert(metric_type, value, room, sensor_id, 'HIGH', '↑')
        log_alert(f"HIGH {metric_type.upper()}: {value} in {room}", metric_type, value, room, sensor_id, 'HIGH')
        return True

    if threshold.get('min') and value < threshold['min']:
        print_alert(metric_type, value, room, sensor_id, 'LOW', '↓')
        log_alert(f"LOW {metric_type.upper()}: {value} in {room}", metric_type, value, room, sensor_id, 'LOW')
        return True

    return False

def print_alert(metric_type, value, room, sensor_id, severity, symbol):
    print(f"[ALERT] {symbol} {severity:<4} | {metric_type.upper():<11} | Room: {room:<8} | Sensor: {sensor_id:<12} | Value: {value:>7.1f}")

def log_alert(message, metric_type, value, room, sensor_id, severity):
    json_body = [{
        "measurement": "alerts",
        "tags": {
            "sensor_id": sensor_id,
            "room": room,
            "type": metric_type,
            "severity": severity
        },
        "fields": {
            "message": message,
            "value": float(value)
        }
    }]
    influx.write_points(json_body)

def on_connect(client, userdata, flags, rc):
    print("="*80)
    print("ANOMALY DETECTOR - Connected to MQTT Broker")
    print("="*80)
    client.subscribe("sensors/#")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        metric_type = msg.topic.split('/')[1]
        check_anomaly(metric_type, payload['value'], payload['room'], payload['sensor_id'])
    except Exception as e:
        print(f"[ERROR] {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, 1883, 60)
print("Anomaly Detector started...")
client.loop_forever()
