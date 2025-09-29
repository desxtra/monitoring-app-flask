# Flask Smart Lamp Server with SQLite Database
from flask import Flask, request, jsonify, render_template_string
import time
import threading
import sqlite3
from datetime import datetime

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

# Database setup
def init_db():
    """Initialize the database and create tables"""
    conn = sqlite3.connect('smart_lamp.db')
    cursor = conn.cursor()
    
    # Create events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lamp_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            pir_detected BOOLEAN,
            lamp_state BOOLEAN,
            auto_mode BOOLEAN,
            source TEXT
        )
    ''')
    
    # Create status history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            pir_detected BOOLEAN,
            lamp_state BOOLEAN,
            auto_mode BOOLEAN,
            connected BOOLEAN
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

# Database helper functions
def log_event(event_type, pir_detected=None, lamp_state=None, auto_mode=None, source=None):
    """Log an event to the database"""
    try:
        conn = sqlite3.connect('smart_lamp.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO lamp_events (event_type, pir_detected, lamp_state, auto_mode, source)
            VALUES (?, ?, ?, ?, ?)
        ''', (event_type, pir_detected, lamp_state, auto_mode, source))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error logging event: {e}")
        return False

def save_status_snapshot(pir_detected, lamp_state, auto_mode, connected):
    """Save current status to history"""
    try:
        conn = sqlite3.connect('smart_lamp.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO status_history (pir_detected, lamp_state, auto_mode, connected)
            VALUES (?, ?, ?, ?)
        ''', (pir_detected, lamp_state, auto_mode, connected))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving status: {e}")
        return False

def get_recent_events(limit=50):
    """Get recent events from database"""
    try:
        conn = sqlite3.connect('smart_lamp.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, event_type, pir_detected, lamp_state, auto_mode, source
            FROM lamp_events 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        events = cursor.fetchall()
        conn.close()
        
        return [{
            'timestamp': event[0],
            'event_type': event[1],
            'pir_detected': bool(event[2]),
            'lamp_state': bool(event[3]),
            'auto_mode': bool(event[4]),
            'source': event[5]
        } for event in events]
    except Exception as e:
        print(f"Error getting events: {e}")
        return []

def get_status_history(hours=24):
    """Get status history for the last specified hours"""
    try:
        conn = sqlite3.connect('smart_lamp.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, pir_detected, lamp_state, auto_mode, connected
            FROM status_history 
            WHERE timestamp > datetime('now', ?)
            ORDER BY timestamp ASC
        ''', (f'-{hours} hours',))
        
        history = cursor.fetchall()
        conn.close()
        
        return [{
            'timestamp': record[0],
            'pir_detected': bool(record[1]),
            'lamp_state': bool(record[2]),
            'auto_mode': bool(record[3]),
            'connected': bool(record[4])
        } for record in history]
    except Exception as e:
        print(f"Error getting history: {e}")
        return []

def get_statistics():
    """Get statistics from database"""
    try:
        conn = sqlite3.connect('smart_lamp.db')
        cursor = conn.cursor()
        
        # Get total lamp on time in last 24 hours
        cursor.execute('''
            SELECT COUNT(*) FROM status_history 
            WHERE lamp_state = 1 AND timestamp > datetime('now', '-24 hours')
        ''')
        lamp_on_count = cursor.fetchone()[0]
        
        # Get PIR detection count in last 24 hours
        cursor.execute('''
            SELECT COUNT(*) FROM lamp_events 
            WHERE event_type = 'pir_detected' AND timestamp > datetime('now', '-24 hours')
        ''')
        pir_detection_count = cursor.fetchone()[0]
        
        # Get auto mode usage count
        cursor.execute('''
            SELECT COUNT(*) FROM status_history 
            WHERE auto_mode = 1 AND timestamp > datetime('now', '-24 hours')
        ''')
        auto_mode_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'lamp_on_samples': lamp_on_count,
            'pir_detections': pir_detection_count,
            'auto_mode_samples': auto_mode_count,
            'estimated_lamp_on_hours': round(lamp_on_count * 5 / 3600, 2)  # Assuming 5-second intervals
        }
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return {}

# Initialize database
init_db()

# HTML Dashboard Template with Statistics
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
            max-width: 1000px;
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
            margin-bottom: 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .status-card, .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #007bff;
        }
        .stat-card {
            border-left: 4px solid #28a745;
        }
        .status-card h3, .stat-card h3 {
            margin: 0 0 10px 0;
            color: #333;
            font-size: 16px;
        }
        .status-value {
            font-size: 24px;
            font-weight: bold;
            margin: 10px 0;
        }
        .stat-value {
            font-size: 20px;
            font-weight: bold;
            margin: 5px 0;
            color: #495057;
        }
        .status-on { color: #28a745; }
        .status-off { color: #dc3545; }
        .status-connected { color: #28a745; }
        .status-disconnected { color: #dc3545; }
        
        .controls {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
            margin-bottom: 30px;
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
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            max-height: 300px;
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
        .log-entry {
            margin-bottom: 5px;
            padding: 2px 0;
        }
        .log-time {
            color: #6c757d;
        }
        .log-event {
            font-weight: bold;
        }
        .log-source {
            color: #6c757d;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Smart Lamp Dashboard</h1>
        
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
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Lamp ON Today</h3>
                <div id="lampOnStats" class="stat-value">-</div>
                <small>Estimated hours</small>
            </div>
            <div class="stat-card">
                <h3>PIR Detections</h3>
                <div id="pirStats" class="stat-value">-</div>
                <small>Last 24 hours</small>
            </div>
            <div class="stat-card">
                <h3>Auto Mode Usage</h3>
                <div id="autoStats" class="stat-value">-</div>
                <small>Samples today</small>
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
            <h3>Activity Log (Last 50 Events)</h3>
            <div id="logContent">
                <div class="log-entry">Loading events...</div>
            </div>
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
                    addLog('Error: Failed to fetch status', 'system');
                });
        }
        
        function updateStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('lampOnStats').textContent = 
                        data.estimated_lamp_on_hours + ' hrs';
                    document.getElementById('pirStats').textContent = 
                        data.pir_detections;
                    document.getElementById('autoStats').textContent = 
                        data.auto_mode_samples;
                })
                .catch(error => {
                    console.error('Error fetching stats:', error);
                });
        }
        
        function loadEvents() {
            fetch('/api/events')
                .then(response => response.json())
                .then(events => {
                    const logContent = document.getElementById('logContent');
                    logContent.innerHTML = '';
                    
                    events.forEach(event => {
                        const logEntry = document.createElement('div');
                        logEntry.className = 'log-entry';
                        
                        const time = new Date(event.timestamp).toLocaleTimeString();
                        const eventType = formatEventType(event.event_type);
                        const source = event.source || 'system';
                        
                        logEntry.innerHTML = `
                            <span class="log-time">[${time}]</span>
                            <span class="log-event">${eventType}</span>
                            <span class="log-source">(${source})</span>
                        `;
                        
                        logContent.appendChild(logEntry);
                    });
                })
                .catch(error => {
                    console.error('Error loading events:', error);
                    document.getElementById('logContent').innerHTML = 
                        '<div class="log-entry">Error loading events</div>';
                });
        }
        
        function formatEventType(eventType) {
            const eventMap = {
                'pir_detected': 'Motion Detected',
                'pir_cleared': 'Motion Cleared',
                'lamp_on': 'Lamp Turned ON',
                'lamp_off': 'Lamp Turned OFF',
                'lamp_manual_on': 'Lamp Manually ON',
                'lamp_manual_off': 'Lamp Manually OFF',
                'auto_mode_toggle': 'Auto Mode Toggled',
                'device_connected': 'Device Connected',
                'device_disconnected': 'Device Disconnected'
            };
            return eventMap[eventType] || eventType;
        }
        
        function toggleAuto() {
            fetch('/api/toggle_auto', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    addLog(`Auto mode ${data.auto_mode ? 'enabled' : 'disabled'}`, 'dashboard');
                    // Reload events to show the change
                    setTimeout(loadEvents, 500);
                })
                .catch(error => {
                    console.error('Error toggling auto mode:', error);
                    addLog('Error: Failed to toggle auto mode', 'system');
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
                addLog(`Lamp manually turned ${state ? 'ON' : 'OFF'}`, 'dashboard');
                // Reload events to show the change
                setTimeout(loadEvents, 500);
            })
            .catch(error => {
                console.error('Error controlling lamp:', error);
                addLog('Error: Failed to control lamp', 'system');
            });
        }
        
        function addLog(message, source = 'system') {
            const timestamp = new Date().toLocaleTimeString();
            logMessages.unshift(`[${timestamp}] ${message} (${source})`);
            if (logMessages.length > 50) {
                logMessages.pop();
            }
            // We're now using the database events, so this is just for real-time updates
        }
        
        // Initialize dashboard
        updateStatus();
        updateStats();
        loadEvents();
        
        // Update status every 2 seconds
        setInterval(updateStatus, 2000);
        
        // Update stats every 30 seconds
        setInterval(updateStats, 30000);
        
        // Reload events every 10 seconds
        setInterval(loadEvents, 10000);
        
        // Add initial log message
        addLog('Dashboard initialized with database support');
    </script>
</body>
</html>
'''

def check_device_connection():
    """Check if device is connected based on last seen timestamp"""
    global device_status
    current_time = time.time()
    if device_status['last_seen'] > 0:
        was_connected = device_status['connected']
        device_status['connected'] = (current_time - device_status['last_seen']) < 10
        
        # Log connection state changes
        if was_connected != device_status['connected']:
            event_type = 'device_connected' if device_status['connected'] else 'device_disconnected'
            log_event(event_type, source='system')
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
            old_state = device_status.copy()
            device_status.update({
                'pir_detected': data.get('pir_detected', False),
                'lamp_state': data.get('lamp_state', False),
                'auto_mode': data.get('auto_mode', False),
                'last_seen': time.time()
            })
            
            # Log status changes
            save_status_snapshot(
                device_status['pir_detected'],
                device_status['lamp_state'],
                device_status['auto_mode'],
                device_status['connected']
            )
            
            # Log PIR detection events
            if old_state['pir_detected'] != device_status['pir_detected']:
                event_type = 'pir_detected' if device_status['pir_detected'] else 'pir_cleared'
                log_event(event_type, 
                         pir_detected=device_status['pir_detected'],
                         lamp_state=device_status['lamp_state'],
                         auto_mode=device_status['auto_mode'],
                         source='device')
            
            # Log lamp state changes from device
            if old_state['lamp_state'] != device_status['lamp_state']:
                event_type = 'lamp_on' if device_status['lamp_state'] else 'lamp_off'
                log_event(event_type,
                         pir_detected=device_status['pir_detected'],
                         lamp_state=device_status['lamp_state'],
                         auto_mode=device_status['auto_mode'],
                         source='device')
        
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
    
    # Log auto mode change
    log_event('auto_mode_toggle',
             pir_detected=device_status['pir_detected'],
             lamp_state=device_status['lamp_state'],
             auto_mode=new_auto,
             source='dashboard')
    
    return jsonify({'auto_mode': new_auto})

@app.route('/api/toggle_lamp', methods=['POST'])
def api_toggle_lamp():
    """Manual lamp control"""
    data = request.get_json()
    if data and 'state' in data:
        lamp_state = bool(data['state'])
        pending_commands['manual_toggle'] = lamp_state
        
        # Log manual lamp control
        event_type = 'lamp_manual_on' if lamp_state else 'lamp_manual_off'
        log_event(event_type,
                 pir_detected=device_status['pir_detected'],
                 lamp_state=lamp_state,
                 auto_mode=device_status['auto_mode'],
                 source='dashboard')
        
        return jsonify({'lamp_state': lamp_state})
    
    return jsonify({'error': 'Invalid request'}), 400

# New API routes for database access
@app.route('/api/events')
def api_events():
    """Get recent events from database"""
    limit = request.args.get('limit', 50, type=int)
    events = get_recent_events(limit)
    return jsonify(events)

@app.route('/api/history')
def api_history():
    """Get status history from database"""
    hours = request.args.get('hours', 24, type=int)
    history = get_status_history(hours)
    return jsonify(history)

@app.route('/api/stats')
def api_stats():
    """Get statistics from database"""
    stats = get_statistics()
    return jsonify(stats)

# Web Routes
@app.route('/')
def dashboard():
    """Serve the dashboard"""
    return render_template_string(DASHBOARD_HTML)

def periodic_cleanup():
    """Periodic cleanup and connection check"""
    while True:
        check_device_connection()
        
        # Save status snapshot every 5 seconds
        save_status_snapshot(
            device_status['pir_detected'],
            device_status['lamp_state'],
            device_status['auto_mode'],
            device_status['connected']
        )
        
        time.sleep(5)

if __name__ == '__main__':
    # Start background cleanup thread
    cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
    cleanup_thread.start()
    
    print("Starting Smart Lamp Server with Database...")
    print("Dashboard available at: http://localhost:5000")
    print("Database file: smart_lamp.db")
    print("Make sure to update the SERVER_IP in ESP32 code to this computer's IP address")
    
    app.run(host='0.0.0.0', port=5000, debug=False)