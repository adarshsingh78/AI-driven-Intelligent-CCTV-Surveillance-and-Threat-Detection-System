from flask import Flask, render_template, Response, jsonify
import cv2
from ultralytics import YOLO
import numpy as np
import threading
import time

app = Flask(__name__)

model = YOLO("yolov8n.pt")

THREAT_CLASSES = ['person']

frame_lock = threading.Lock()
alert_lock = threading.Lock()

output_frame = None
alerts = []

video_source = 0
cap = cv2.VideoCapture(video_source)

def detect_threats():
    global output_frame, alerts, cap
    while True:
        if not cap.isOpened():
            print("Error: Camera not accessible. Retrying...")
            time.sleep(2)
            cap = cv2.VideoCapture(video_source)
            continue
        success, frame = cap.read()
        if not success:
            print("Error: Failed to read frame. Retrying...")
            time.sleep(2)
            cap = cv2.VideoCapture(video_source)
            continue
        results = model(frame, verbose=False)
        current_alerts = []
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                class_name = result.names[cls_id]
                if class_name in THREAT_CLASSES:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    confidence = float(box.conf[0])
                    label = f"{class_name.upper()} ({confidence:.2f})"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    alert_message = f"Threat Detected: {class_name.upper()}"
                    if alert_message not in [a['message'] for a in alerts]:
                         current_alerts.append({'message': alert_message, 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')})
        with alert_lock:
            if current_alerts:
                alerts.extend(current_alerts)
                alerts = alerts[-5:]
        with frame_lock:
            output_frame = frame.copy()

def generate_frames():
    global output_frame
    while True:
        with frame_lock:
            if output_frame is None:
                continue
            (flag, encodedImage) = cv2.imencode(".jpg", output_frame)
            if not flag:
                continue
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
              bytearray(encodedImage) + b'\r\n')
        time.sleep(0.03)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_alerts')
def get_alerts():
    with alert_lock:
        return jsonify(alerts)

if __name__ == '__main__':
    detection_thread = threading.Thread(target=detect_threats)
    detection_thread.daemon = True
    detection_thread.start()
    app.run(debug=True, threaded=True, use_reloader=False)
