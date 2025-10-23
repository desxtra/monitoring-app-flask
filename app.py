"""
Main Flask Server for ESP32 Class Project
Simple API to receive data from all groups and serve dashboard
"""

from flask import Flask, request, jsonify, render_template
import database
import config
from datetime import datetime

# Create Flask app
app = Flask(__name__)

@app.route('/')
def index():
    """Redirect to dashboard"""
    return render_template('dashboard.html')

@app.route('/api/data', methods=['POST'])
def receive_esp32_data():
    """
    Receive data from ESP32 devices
    All groups send data to this same endpoint
    """
    try:
        # Get JSON data from ESP32
        data = request.get_json()
        
        # Validate required fields
        if not data or 'group_id' not in data or 'sensor_data' not in data:
            return jsonify({"error": "Missing required fields"}), 400
        
        group_id = data['group_id']
        timestamp = data.get('timestamp', datetime.now().timestamp())
        sensor_data = data['sensor_data']
        
        # Validate group ID
        if group_id not in config.VALID_GROUPS:
            return jsonify({"error": "Invalid group ID"}), 400
        
        # Save to database
        database.save_sensor_data(group_id, timestamp, sensor_data)
        
        # Return success response
        return jsonify({
            "status": "success",
            "message": f"Data received from {group_id}",
            "received_at": str(datetime.now())
        }), 200
        
    except Exception as e:
        print(f"Error processing data: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/dashboard')
def get_dashboard_data():
    """Provide data for the dashboard - used by AJAX"""
    try:
        latest_data = database.get_latest_data_all_groups()
        return jsonify({
            "status": "success",
            "data": latest_data,
            "last_updated": str(datetime.now())
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/group/<group_id>')
def get_group_data(group_id):
    """Get data for specific group"""
    try:
        history = database.get_group_history(group_id)
        return jsonify({
            "status": "success",
            "group_id": group_id,
            "data": history
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/dashboard')
def dashboard():
    """Serve the main dashboard page"""
    return render_template('dashboard.html')

# Initialize and run the application
if __name__ == '__main__':
    print("Starting ESP32 Class Server...")
    
    # Initialize database
    database.init_database()
    
    # Start Flask server
    print(f"✓ Server starting on http://{config.SERVER_HOST}:{config.SERVER_PORT}")
    app.run(
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        debug=config.DEBUG_MODE
    )