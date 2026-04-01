from flask import Flask, jsonify
import threading
import time
import random
import math

app = Flask(__name__)

iot_memory = {
    "is_recording": False,
    "sensor_data": []
}

def sensor_loop():
    t = 0
    while True:
        if iot_memory["is_recording"]:
            # szum od -5 do 5
            base_z = random.uniform(-5, 5)
            cycle = t % 4
            
            if cycle < 2:
                # math.sin - od 0 do 100 i z powrotem
                rep_amplitude = math.sin(math.pi * (cycle / 2)) * 100
                z = base_z + rep_amplitude
            else:
                z = base_z 
                
            data_point = {
                "accelerometer": [
                    round(random.uniform(-10, 10), 2), 
                    round(random.uniform(-10, 10), 2), 
                    round(z, 2)                        
                ],
                "timestamp": round(time.time(), 2)
            }
            iot_memory["sensor_data"].append(data_point)
            t += 0.2
        else:
            t = 0
            
        time.sleep(0.2)

@app.route('/iot/start', methods=['POST'])
def start_recording():
    iot_memory["sensor_data"] = []
    iot_memory["is_recording"] = True
    return jsonify({"status": "recording_started"})

@app.route('/iot/stop', methods=['POST'])
def stop_recording():
    iot_memory["is_recording"] = False
    return jsonify({
        "device_id": "RaspberryPi_BenchPress",
        "workout_data": iot_memory["sensor_data"]
    })

if __name__ == "__main__":
    threading.Thread(target=sensor_loop, daemon=True).start()
    print("symulator IoT nasłuchuje na porcie 5000")
    app.run(port=5000, debug=False)
