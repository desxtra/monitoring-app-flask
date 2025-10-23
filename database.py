"""
Database operations for sensor data
Uses SQLite for simplicity
"""

import sqlite3
import json
from datetime import datetime

def get_db_connection():
    """Create connection to SQLite database"""
    conn = sqlite3.connect('sensor_data.db')
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    
    # Create sensor data table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT NOT NULL,
            timestamp REAL NOT NULL,
            sensor_data TEXT NOT NULL,  -- Store as JSON string
            received_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Database initialized")

def save_sensor_data(group_id, timestamp, sensor_data):
    """Save sensor data from ESP32 to database"""
    conn = get_db_connection()
    
    # Convert sensor_data dict to JSON string
    sensor_json = json.dumps(sensor_data)
    
    # Insert data
    conn.execute(
        'INSERT INTO sensor_data (group_id, timestamp, sensor_data) VALUES (?, ?, ?)',
        (group_id, timestamp, sensor_json)
    )
    
    conn.commit()
    conn.close()
    print(f"✓ Data saved for {group_id}")

def get_latest_data_all_groups():
    """Get latest data from all groups for dashboard"""
    conn = get_db_connection()
    
    # Get the most recent entry for each group
    query = '''
        SELECT sd1.* 
        FROM sensor_data sd1
        INNER JOIN (
            SELECT group_id, MAX(timestamp) as max_timestamp 
            FROM sensor_data 
            GROUP BY group_id
        ) sd2 ON sd1.group_id = sd2.group_id AND sd1.timestamp = sd2.max_timestamp
        ORDER BY sd1.group_id
    '''
    
    rows = conn.execute(query).fetchall()
    conn.close()
    
    # Convert to list of dictionaries
    result = []
    for row in rows:
        result.append({
            'group_id': row['group_id'],
            'timestamp': row['timestamp'],
            'sensor_data': json.loads(row['sensor_data']),
            'received_at': row['received_at']
        })
    
    return result

def get_group_history(group_id, limit=10):
    """Get recent history for a specific group"""
    conn = get_db_connection()
    
    rows = conn.execute(
        'SELECT * FROM sensor_data WHERE group_id = ? ORDER BY timestamp DESC LIMIT ?',
        (group_id, limit)
    ).fetchall()
    
    conn.close()
    
    result = []
    for row in rows:
        result.append({
            'group_id': row['group_id'],
            'timestamp': row['timestamp'],
            'sensor_data': json.loads(row['sensor_data']),
            'received_at': row['received_at']
        })
    
    return result