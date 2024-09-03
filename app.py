from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

sensors_data = {"temperature":22,"pH":6.5}

@app.route('/sensors', methods=['POST'])
def update_sensors():
    data = request.get_json()
    sensors_data.update(data)
    return jsonify({"message": "Sensor data updated", "data": data}), 200

@app.route('/sensors', methods=['GET'])
def get_sensors():
    return jsonify(sensors_data)

@app.route('/actuators', methods=['POST'])
def control_actuator():
    command = request.get_json()
    # Here you would add code to send command to the actuators
    return jsonify({"message": "Actuator command received", "command": command}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')