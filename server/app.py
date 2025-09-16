from flask import Flask, render_template, jsonify, request
import logging
from logging.handlers import RotatingFileHandler
import time
from datetime import datetime
from collections import deque
import threading
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize data storage
group_data = {group: deque(maxlen=1) for group in Config.GROUPS}
data_lock = threading.Lock()

# Setup logging
def setup_logging():
    """Configure logging for the application"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    try:
        # File handler with rotation
        file_handler = RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=1024 * 1024,  # 1MB
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        file_handler.setLevel(getattr(logging, Config.LOG_LEVEL))

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        console_handler.setLevel(getattr(logging, Config.LOG_LEVEL))

        # Get app logger
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    except Exception as e:
        print(f"Error setting up logging: {str(e)}")

# Initialize logging
setup_logging()

@app.route('/')
def dashboard():
    """Main dashboard showing all groups"""
    try:
        return render_template('dashboard.html', groups=Config.GROUPS)
    except Exception as e:
        app.logger.error(f"Error rendering dashboard: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/data', methods=['POST'])
def receive_data():
    """API endpoint for IoT devices to send data"""
    try:
        data = request.get_json()

        if not data:
            app.logger.warning("Received empty data")
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        # Validate required fields
        if 'group_id' not in data:
            app.logger.warning("Missing group_id in data")
            return jsonify({'status': 'error', 'message': 'Missing group_id'}), 400

        group_id = data['group_id']
        if group_id not in Config.GROUPS:
            app.logger.warning(f"Invalid group_id: {group_id}")
            return jsonify({'status': 'error', 'message': 'Invalid group_id'}), 400

        # Add timestamp and store data
        try:
            data['timestamp'] = datetime.now().isoformat()
        except Exception as e:
            app.logger.error(f"Error creating timestamp: {str(e)}")
            return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

        with data_lock:
            group_data[group_id].append(data)

        app.logger.info(f"Data received from {group_id}")
        return jsonify({'status': 'success', 'message': 'Data received'}), 200

    except Exception as e:
        app.logger.error(f"Error processing data: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/data/<group_id>', methods=['GET'])
def get_group_data(group_id):
    """API endpoint to get data for a specific group"""
    try:
        if group_id not in Config.GROUPS:
            return jsonify({'status': 'error', 'message': 'Invalid group_id'}), 404

        # Get latest data for the group
        with data_lock:
            if group_data[group_id]:
                latest_data = list(group_data[group_id])
            else:
                latest_data = []

        return jsonify({
            'status': 'success',
            'group_id': group_id,
            'group_name': Config.GROUPS[group_id],
            'data': latest_data
        }), 200

    except Exception as e:
        app.logger.error(f"Error retrieving data for {group_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/status')
def get_status():
    """API endpoint to check server status"""
    try:
        status = {
            'status': 'online',
            'timestamp': datetime.now().isoformat(),
            'groups': {}
        }

        with data_lock:
            for group_id in Config.GROUPS:
                status['groups'][group_id] = {
                    'name': Config.GROUPS[group_id],
                    'data_count': len(group_data[group_id]),
                    'last_update': group_data[group_id][-1]['timestamp'] if group_data[group_id] else None
                }

        return jsonify(status), 200

    except Exception as e:
        app.logger.error(f"Error generating status: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

def cleanup_old_data():
    """Background task to clean up old data"""
    while True:
        try:
            current_time = time.time()

            with data_lock:
                for group_id in Config.GROUPS:
                    # Convert deque to list for processing
                    data_list = list(group_data[group_id])

                    # Filter out old data
                    filtered_data = []
                    for item in data_list:
                        try:
                            item_time = datetime.fromisoformat(item['timestamp']).timestamp()
                            if current_time - item_time < Config.DATA_RETENTION:
                                filtered_data.append(item)
                        except Exception as e:
                            app.logger.error(f"Error parsing timestamp: {str(e)}")

                    # Replace with filtered data
                    group_data[group_id].clear()
                    for item in filtered_data:
                        group_data[group_id].append(item)

            app.logger.debug("Cleaned up old data")
            time.sleep(60)  # Run every minute

        except Exception as e:
            app.logger.error(f"Error in cleanup task: {str(e)}")
            time.sleep(60)

if __name__ == '__main__':
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_old_data, daemon=True)
    cleanup_thread.start()

    # Start Flask server
    try:
        app.logger.info(f"Starting IoT Monitoring Server on {Config.HOST}:{Config.PORT}")
        app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
    except Exception as e:
        app.logger.error(f"Error starting server: {str(e)}")
