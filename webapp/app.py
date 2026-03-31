"""
Farm Health Monitoring Dashboard - Flask Backend
PROTOTYPE VERSION - Static data for demonstration
"""
from flask import Flask, jsonify, send_file, render_template, Response
from datetime import datetime
import cv2
import time
import urllib.request
import json
import threading

# Try importing YOLO, ignore if running without it for some reason (handled in try block below)
try:
    from ultralytics import YOLO
    import numpy as np
    yolo_model = YOLO('best.pt')
    print("✅ YOLO model loaded successfully from best.pt")
except Exception as e:
    print(f"⚠️ Failed to load YOLO model: {e}")
    yolo_model = None

app = Flask(__name__)

# ============================================
# ESP32 CONFIGURATION
# ============================================
# Replace this with the actual IP address of your ESP32-CAM shown in Arduino Serial Monitor
ESP32_IP = "10.127.196.76" 
STREAM_URL = f"http://{ESP32_IP}/stream"
MOISTURE_API_URL = f"http://{ESP32_IP}/api/moisture"

# Global state
camera = None
latest_prediction = {
    "status": "clean", 
    "confidence": 0.0,
    "last_update": None
}
latest_moisture = None
sensor_status = "disconnected"

def get_camera():
    global camera
    if camera is None:
        print(f"📷 Attempting to connect to ESP32 stream at {STREAM_URL}...")
        # For remote stream, cv2.VideoCapture takes the URL
        camera = cv2.VideoCapture(STREAM_URL)
        time.sleep(1) # Allow connection to establish
        if not camera.isOpened():
            print("❌ Failed to open ESP32 stream! Check IP address and power.")
            camera = None
        else:
            print("✅ Connected to ESP32 stream")
    return camera

def process_frame(frame):
    """Run YOLO inference and draw boxes on the frame."""
    global latest_prediction
    
    if yolo_model is None:
        return frame
        
    try:
        # Run inference
        results = yolo_model(frame, verbose=False)
        
        # Analyze results
        found_weed = False
        max_conf = 0.0
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # Class 0 assuming weed (adjust if your model has multiple classes)
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                
                if conf > max_conf:
                    max_conf = conf
                
                if conf > 0.5: # Confidence threshold
                    found_weed = True
                    # Draw bounding box
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2) # Red box
                    
                    # Label
                    label = f"Weed {conf:.2f}"
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    
        # Update global state for API
        latest_prediction["status"] = "weed" if found_weed else "clean"
        latest_prediction["confidence"] = max_conf
        latest_prediction["last_update"] = time.time()
        
    except Exception as e:
        print(f"Error processing frame: {e}")
        
    return frame

def generate_frames():
    global camera
    if camera is None:
        camera = get_camera()
    
    while True:
        if camera is None:
            print("⚠️ Camera is None, attempting to reconnect...")
            camera = get_camera()
            if camera is None:
                time.sleep(2)
                continue

        success, frame = camera.read()
        if not success:
            print("❌ Failed to read frame from ESP32. Reconnecting...")
            camera.release()
            camera = None
            time.sleep(2)
            continue
            
        try:
            # Process frame with ML Model
            annotated_frame = process_frame(frame)
        
            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            if not ret:
                continue
                
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.03) # Yield to prevent overwhelming CPU
        except Exception as e:
            print(f"Error encoding frame: {e}")
            continue

# ============================================
# SENSOR & STATUS HANDLING
# ============================================

def sensor_polling_loop():
    """Background thread to fetch moisture data periodically"""
    global latest_moisture, sensor_status
    while True:
        try:
            req = urllib.request.Request(MOISTURE_API_URL, method="GET")
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    latest_moisture = data.get("moisture_percent")
                    sensor_status = "connected"
                else:
                    sensor_status = "disconnected"
        except Exception as e:
            sensor_status = "disconnected"
        
        time.sleep(2) # Poll every 2 seconds

# Start background sensor polling thread
polling_thread = threading.Thread(target=sensor_polling_loop, daemon=True)
polling_thread.start()

def get_system_status():
    return {
        "esp32": "online" if sensor_status == "connected" or (camera is not None and camera.isOpened()) else "offline",
        "lastUpdate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fps": 30.0,
        "uptime": 3600
    }

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/sensors')
def get_sensors():
    """Return sensor readings or null if not connected"""
    if sensor_status == "connected":
        return jsonify({
            "status": "connected",
            "temperature": None, # ESP32 currently only sending moisture
            "humidity": None,
            "moisture": latest_moisture,
            "message": "Connected to ESP32-CAM"
        })
    else:
        return jsonify({
            "status": "disconnected",
            "temperature": None,
            "humidity": None,
            "moisture": None,
            "message": "Sensors not connected"
        })

@app.route('/api/frame')
def get_frame():
    """Legacy endpoint - keeping for compatibility but logic moved to /video_feed"""
    return jsonify({
        "image": None,
        "format": "stream",
        "timestamp": datetime.now().isoformat(),
        "message": "Use /video_feed for live stream"
    })

@app.route('/api/prediction')
def get_prediction():
    """Return latest YOLO weed detection prediction"""
    return jsonify(latest_prediction)

@app.route('/api/heatmap')
def get_heatmap():
    """Return empty heatmap since no data"""
    return jsonify({
        "grid": [["clean"] * 5 for _ in range(5)]
    })

@app.route('/api/history')
def get_history():
    """Return empty history"""
    return jsonify([])

@app.route('/api/status')
def get_status():
    """Return system status"""
    return jsonify(get_system_status())

@app.route('/api/alerts')
def get_alerts():
    """Return alerts based on connection status"""
    return jsonify([
        {"type": "warning", "message": "Sensors Disconnected", "icon": "alert-triangle"},
         {"type": "info", "message": "Live Camera Feed Active", "icon": "video"}
    ])

if __name__ == '__main__':
    print("🌱 Farm Health Monitor")
    print("📷 Connecting to local camera...")
    print("🌐 Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)

