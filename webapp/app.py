"""
Farm Health Monitoring Dashboard - Flask Backend
PROTOTYPE VERSION - Static data for demonstration
"""
from flask import Flask, jsonify, send_file, render_template, Response
from datetime import datetime
import cv2
import time

app = Flask(__name__)

# ============================================
# CAMERA SETUP
# ============================================
camera = None

def get_camera():
    global camera
    if camera is None:
        print("📷 Attempting to open camera...")
        camera = cv2.VideoCapture(0)
        time.sleep(1) # Allow camera to warm up
        if not camera.isOpened():
            print("❌ Failed to open camera!")
            camera = None
        else:
            print("✅ Camera connected successfully")
    return camera

def generate_frames():
    global camera
    if camera is None:
        camera = get_camera()
    
    while True:
        if camera is None:
            print("⚠️ Camera is None, attempting to reconnect...")
            camera = get_camera()
            if camera is None:
                time.sleep(1)
                continue

        success, frame = camera.read()
        if not success:
            print("❌ Failed to read frame. Reconnecting...")
            camera.release()
            camera = None
            continue
            
        try:
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.03) # Limit to ~30 FPS
        except Exception as e:
            print(f"Error encoding frame: {e}")
            continue
                
# ============================================
# SENSOR & STATUS HANDLING
# ============================================

def get_sensor_data():
    # In a real scenario, this would read from serial or database
    # For now, we return None to simulate "Not Connected"
    return None

def get_system_status():
    return {
        "esp32": "offline", # Forced offline as requested
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
    data = get_sensor_data()
    if data:
        return jsonify(data)
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
    """Return static weed detection prediction (mock since no ML model yet)"""
    return jsonify({
        "status": "clean", 
        "confidence": 0.0
    })

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

