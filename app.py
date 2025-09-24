# Flask Smart Lamp Server
from flask import Flask, request, jsonify, render_template_string
import time
import threading

app = Flask(__name__)

# Global state variables
device_status = {
    'pir_detected': False,
    'lamp_state': False,
    'auto_mode': False,
    'last_seen': 0,
    'connected': False
}

# Command queue for ESP32
pending_commands = {}

# HTML Dashboard Template
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Smart Lamp Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #007bff;
        }
        .status-card h3 {
            margin: 0 0 10px 0;
            color: #333;
        }
        .status-value {
            font-size: 24px;
            font-weight: bold;
            margin: 10px 0;
        }
        .status-on { color: #28a745; }
        .status-off { color: #dc3545; }
        .status-connected { color: #28a745; }
        .status-disconnected { color: #dc3545; }
        
        .controls {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .control-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .control-card h3 {
            margin: 0 0 15px 0;
            color: #333;
        }
        button {
            padding: 12px 24px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
            transition: background-color 0.3s;
        }
        .btn-primary {
            background-color: #007bff;
            color: white;
        }
        .btn-primary:hover {
            background-color: #0056b3;
        }
        .btn-success {
            background-color: #28a745;
            color: white;
        }
        .btn-success:hover {
            background-color: #1e7e34;
        }
        .btn-danger {
            background-color: #dc3545;
            color: white;
        }
        .btn-danger:hover {
            background-color: #c82333;
        }
        .log {
            margin-top: 30px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            max-height: 200px;
            overflow-y: auto;
        }
        .log h3 {
            margin: 0 0 10px 0;
            color: #333;
        }
        #logContent {
            font-family: monospace;
            font-size: 14px;
            line-height: 1.4;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏠 Smart Lamp Dashboard</h1>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>PIR Sensor</h3>
                <div id="pirStatus" class="status-value">-</div>
            </div>
            <div class="status-card">
                <h3>Lamp Status</h3>
                <div id="lampStatus" class="status-value">-</div>
            </div>
            <div class="status-card">
                <h3>Auto Mode</h3>
                <div id="autoStatus" class="status-value">-</div>
            </div>
            <div class="status-card">
                <h3>Device Status</h3>
                <div id="deviceStatus" class="status-value">-</div>
            </div>
        </div>
        
        <div class="controls">
            <div class="control-card">
                <h3>Auto Mode Control</h3>
                <button id="autoBtn" class="btn-primary" onclick="toggleAuto()">
                    Toggle Auto Mode
                </button>
                <p><small>Enable/disable automatic PIR detection</small></p>
            </div>
            <div class="control-card">
                <h3>Manual Lamp Control</h3>
                <button class="btn-success" onclick="toggleLamp(true)">Turn ON</button>
                <button class="btn-danger" onclick="toggleLamp(false)">Turn OFF</button>
                <p><small>Manual override for lamp control</small></p>
            </div>
        </div>
        
        <div class="log">
            <h3>Activity Log</h3>
            <div id="logContent"></div>
        </div>
    </div>

    <script>
        let logMessages = [];
        
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    // Update PIR status
                    const pirElement = document.getElementById('pirStatus');
                    pirElement.textContent = data.pir_detected ? 'DETECTED' : 'NO MOTION';
                    pirElement.className = 'status-value ' + (data.pir_detected ? 'status-on' : 'status-off');
                    
                    // Update lamp status
                    const lampElement = document.getElementById('lampStatus');
                    lampElement.textContent = data.lamp_state ? 'ON' : 'OFF';
                    lampElement.className = 'status-value ' + (data.lamp_state ? 'status-on' : 'status-off');
                    
                    // Update auto mode status
                    const autoElement = document.getElementById('autoStatus');
                    autoElement.textContent = data.auto_mode ? 'ENABLED' : 'DISABLED';
                    autoElement.className = 'status-value ' + (data.auto_mode ? 'status-on' : 'status-off');
                    
                    // Update device status
                    const deviceElement = document.getElementById('deviceStatus');
                    deviceElement.textContent = data.connected ? 'CONNECTED' : 'DISCONNECTED';
                    deviceElement.className = 'status-value ' + (data.connected ? 'status-connected' : 'status-disconnected');
                    
                    // Update auto button text
                    document.getElementById('autoBtn').textContent = 
                        data.auto_mode ? 'Disable Auto Mode' : 'Enable Auto Mode';
                })
                .catch(error => {
                    console.error('Error fetching status:', error);
                    addLog('Error: Failed to fetch status');
                });
        }
        
        function toggleAuto() {
            fetch('/api/toggle_auto', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    addLog(`Auto mode ${data.auto_mode ? 'enabled' : 'disabled'}`);
                })
                .catch(error => {
                    console.error('Error toggling auto mode:', error);
                    addLog('Error: Failed to toggle auto mode');
                });
        }
        
        function toggleLamp(state) {
            fetch('/api/toggle_lamp', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({state: state})
            })
            .then(response => response.json())
            .then(data => {
                addLog(`Lamp manually turned ${state ? 'ON' : 'OFF'}`);
            })
            .catch(error => {
                console.error('Error controlling lamp:', error);
                addLog('Error: Failed to control lamp');
            });
        }
        
        function addLog(message) {
            const timestamp = new Date().toLocaleTimeString();
            logMessages.unshift(`[${timestamp}] ${message}`);
            if (logMessages.length > 50) {
                logMessages.pop();
            }
            document.getElementById('logContent').innerHTML = logMessages.join('<br>');
        }
        
        // Update status every 2 seconds
        setInterval(updateStatus, 2000);
        updateStatus(); // Initial update
        
        // Add initial log message
        addLog('Dashboard initialized');
    </script>
</body>
</html>
'''

def check_device_connection():
    """Check if device is connected based on last seen timestamp"""
    current_time = time.time()
    if device_status['last_seen'] > 0:
        device_status['connected'] = (current_time - device_status['last_seen']) < 10
    else:
        device_status['connected'] = False

# API Routes
@app.route('/api/status', methods=['GET', 'POST'])
def api_status():
    """Handle status updates from ESP32 and provide current status"""
    global device_status
    
    if request.method == 'POST':
        # Update status from ESP32
        data = request.get_json()
        if data:
            device_status.update({
                'pir_detected': data.get('pir_detected', False),
                'lamp_state': data.get('lamp_state', False),
                'auto_mode': data.get('auto_mode', False),
                'last_seen': time.time()
            })
        return jsonify({'status': 'ok'})
    
    else:
        # Return current status for dashboard
        check_device_connection()
        return jsonify(device_status)

@app.route('/api/commands', methods=['GET'])
def api_commands():
    """Provide pending commands to ESP32"""
    global pending_commands
    
    commands = pending_commands.copy()
    pending_commands.clear()  # Clear after sending
    
    return jsonify(commands)

@app.route('/api/toggle_auto', methods=['POST'])
def api_toggle_auto():
    """Toggle auto mode"""
    current_auto = device_status.get('auto_mode', False)
    new_auto = not current_auto
    
    pending_commands['auto_mode'] = new_auto
    
    return jsonify({'auto_mode': new_auto})

@app.route('/api/toggle_lamp', methods=['POST'])
def api_toggle_lamp():
    """Manual lamp control"""
    data = request.get_json()
    if data and 'state' in data:
        lamp_state = bool(data['state'])
        pending_commands['manual_toggle'] = lamp_state
        return jsonify({'lamp_state': lamp_state})
    
    return jsonify({'error': 'Invalid request'}), 400

# Web Routes
@app.route('/')
def dashboard():
    """Serve the dashboard"""
    return render_template_string(DASHBOARD_HTML)

def periodic_cleanup():
    """Periodic cleanup and connection check"""
    while True:
        check_device_connection()
        time.sleep(5)

if __name__ == '__main__':
    # Start background cleanup thread
    cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
    cleanup_thread.start()
    
    print("Starting Smart Lamp Server...")
    print("Dashboard available at: http://localhost:5000")
    print("Make sure to update the SERVER_IP in ESP32 code to this computer's IP address")
    
    app.run(host='0.0.0.0', port=5000, debug=False)