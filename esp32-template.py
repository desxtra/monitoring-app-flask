"""
ESP32 Template for Class Project
Each group only needs to change the GROUP_ID and sensor reading logic
"""

import urequests
import json
import time
from machine import Pin, ADC

# ==================== CONFIGURATION ====================
# !! EACH GROUP CHANGES ONLY THESE VALUES !!
GROUP_ID = "group_1"  # Change to group_1, group_2, etc.
SERVER_IP = "192.168.1.100"  # Your server IP
SERVER_PORT = "9000"  # Your server port
# =======================================================

# API endpoint
API_URL = f"http://{SERVER_IP}:{SERVER_PORT}/api/data"

# Example sensor setup (adjust based on your sensors)
# For analog sensors:
adc = ADC(Pin(34))
adc.atten(ADC.ATTN_11DB)  # For 0-3.3V range

def read_sensor_data():
    """
    Read data from your sensors
    Each group customizes this function based on their sensors
    """
    # Example: Read analog sensor (0-4095)
    raw_value = adc.read()
    
    # Convert to voltage (0-3.3V) - adjust conversion for your sensor
    voltage = (raw_value / 4095) * 3.3
    
    # Example: Convert to temperature (fake conversion - replace with your sensor's formula)
    temperature = (voltage * 30) + 20  # This is example only!
    
    return {
        "temperature": temperature,
        "raw_value": raw_value,
        "voltage": voltage
    }

def send_to_server(sensor_readings):
    """
    Send sensor data to the central server
    """
    # Prepare data in standard format
    data = {
        "group_id": GROUP_ID,
        "timestamp": str(time.time()),  # Current time
        "sensor_data": sensor_readings,
        "device_type": "esp32"
    }
    
    try:
        # Send POST request to server
        response = urequests.post(
            API_URL,
            json=data,  # Convert to JSON
            headers={'Content-Type': 'application/json'}
        )
        
        # Check if request was successful
        if response.status_code == 200:
            print("✓ Data sent successfully")
        else:
            print(f"✗ Server error: {response.status_code}")
        
        # Always close response to free memory
        response.close()
        
    except Exception as e:
        print(f"✗ Failed to send data: {e}")

def main_loop():
    """
    Main program loop - runs forever
    """
    print(f"Starting ESP32 data sender for {GROUP_ID}")
    
    while True:
        try:
            # 1. Read sensors
            sensor_data = read_sensor_data()
            print(f"Sensor readings: {sensor_data}")
            
            # 2. Send to server
            send_to_server(sensor_data)
            
            # 3. Wait before next reading (e.g., 5 seconds)
            time.sleep(5)
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(10)  # Wait longer if error

# Start the program
if __name__ == "__main__":
    main_loop()