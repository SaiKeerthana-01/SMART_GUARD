from flask import Flask, jsonify, request
from influxdb import InfluxDBClient
import os

app = Flask(__name__)

INFLUX_HOST = os.environ.get("INFLUX_HOST", "localhost")
INFLUX_DB = os.environ.get("INFLUX_DB", "sensor_data")
INFLUX_PORT = int(os.environ.get("INFLUX_PORT", 8086))

try:
    influx = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, database=INFLUX_DB)
except Exception as e:
    print(f"Error connecting to InfluxDB: {e}")

registered_sensors = []

@app.route("/api/register_sensor", methods=["POST"])
def register_sensor():
    sensor = request.json
    registered_sensors.append(sensor)
    return jsonify({"status": "registered", "sensor": sensor}), 201

@app.route("/api/blocks")
def get_blocks():
    query = 'SHOW TAG VALUES FROM "sensor_data" WITH KEY = "room"'
    rooms = [v['value'] for v in influx.query(query).get_points()]
    blocks = sorted(set([room.split("1")[0].replace("_","") for room in rooms]))
    return jsonify(blocks)

@app.route("/api/rooms")
def get_rooms():
    block = request.args.get('block')
    query = 'SHOW TAG VALUES FROM "sensor_data" WITH KEY = "room"'
    rooms = sorted([v['value'] for v in influx.query(query).get_points()])
    if block:
        rooms = [room for room in rooms if room.startswith(block)]
    return jsonify(rooms)

@app.route("/api/sensors")
def get_sensors():
    room = request.args.get('room')
    query = f'SELECT DISTINCT("sensor_id") FROM "sensor_data" WHERE "room" = \'{room}\''
    sensors = [r['distinct'] for r in influx.query(query).get_points()]
    return jsonify(sensors)

@app.route("/api/latest")
def get_latest():
    room = request.args.get('room')
    query = (
        f'SELECT LAST("value") AS value, "sensor_id", "type", time '
        f'FROM "sensor_data" WHERE "room" = \'{room}\' GROUP BY "type"'
    )
    readings = [r for r in influx.query(query).get_points()]
    return jsonify(readings)

@app.route("/api/history")
def get_history():
    room = request.args.get('room')
    metric = request.args.get('metric')
    limit = int(request.args.get("limit", 1000))
    start_time = request.args.get("start_time", None)
    end_time = request.args.get("end_time", None)

    # Ensure that time params end with 'Z' denoting UTC
    if start_time and not start_time.endswith('Z'):
        start_time += 'Z'
    if end_time and not end_time.endswith('Z'):
        end_time += 'Z'

    where = f'WHERE "room" = \'{room}\' AND "type" = \'{metric}\' '
    if start_time and end_time:
        where += f'AND time >= \'{start_time}\' AND time <= \'{end_time}\' '
    query = (
        f'SELECT "value", time FROM "sensor_data" {where}ORDER BY time ASC LIMIT {limit}'
    )
    print(f"[DEBUG] /api/history query: {query}")
    data = [d for d in influx.query(query).get_points()]
    if data:
        print(f"[DEBUG] Fetched {len(data)} points, last time: {data[-1]['time']}")
    return jsonify(data)

@app.route("/api/alerts")
def get_alerts():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 15))
    offset = (page - 1) * per_page
    query = f'SELECT * FROM "alerts" ORDER BY time DESC LIMIT {per_page} OFFSET {offset}'
    alerts = [a for a in influx.query(query).get_points()]
    return jsonify(alerts)

@app.route("/api/thresholds")
def get_thresholds():
    return jsonify({
        'temperature': {'min': 18, 'max': 30},
        'humidity': {'min': 30, 'max': 70},
        'light': {'min': 300, 'max': 1500},
        'co2': {'min': 350, 'max': 1000}
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
