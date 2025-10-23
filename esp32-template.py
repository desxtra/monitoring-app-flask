"""
ESP32 Template for Class Project

What you need to change in this template:
1. GROUP_ID - Change to your group number (e.g., "group_1", "group_2", etc.)
2. WIFI_NAME and WIFI_PASSWORD - Your Wi-Fi connection details
3. SERVER_IP - The IP address where the dashboard server is running
4. PIN_NUMBERS - The GPIO pins where you connected your sensors
5. read_sensor_data() function - The code to read your specific sensors

Additional Notes:
- You can test your connection by checking if data appears in the dashboard
- Make sure your sensors are properly connected to the specified GPIO pins
- The code automatically handles Wi-Fi connection and reconnection
"""

# Import required libraries
import network      # For Wi-Fi functionality
import urequests   # For making HTTP requests
import time        # For delays and timestamps
from machine import Pin, ADC  # For controlling GPIO pins

# ==================== CONFIGURATION ====================
# !!! CHANGE THESE VALUES FOR YOUR GROUP !!!

# Your group identification
GROUP_ID = "group_1"        # 👈 Change this to your group number!

# Network settings
SERVER_IP = "10.15.22.38"   # The IP address of the dashboard server
SERVER_PORT = "9000"        # The port number (usually don't change this)
WIFI_NAME = "Hotspot-SMK"   # 👈 Your Wi-Fi network name
WIFI_PASSWORD = ""          # 👈 Your Wi-Fi password (leave empty if no password)

# Create the complete server URL (don't change this)
API_URL = f"http://{SERVER_IP}:{SERVER_PORT}/api/data"

# ==================== HARDWARE SETUP ====================
# Define which GPIO pins your sensors are connected to
SENSOR_PIN = 34    # 👈 Change this to match your sensor pin
STATUS_LED = 2     # Built-in LED on most ESP32 boards

# Example sensor setup (modify for your sensors)
sensor = ADC(Pin(SENSOR_PIN))    # For analog sensors (like temperature)
sensor.atten(ADC.ATTN_11DB)      # Full 0-3.3V range
led = Pin(STATUS_LED, Pin.OUT)   # Status LED to show when sending data

# ==================== NETWORK FUNCTIONS ====================

def connect_wifi(wifi_name, wifi_password, timeout=20):
    """
    Connect ESP32 to your Wi-Fi network
    
    Parameters:
    - wifi_name: Your Wi-Fi network name
    - wifi_password: Your Wi-Fi password (can be empty for open networks)
    - timeout: How long to wait for connection (in seconds)
    
    Returns:
    - wlan: Wi-Fi object if connected
    - None: If connection failed
    """
    # Initialize Wi-Fi in client mode
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # If already connected, return immediately
    if wlan.isconnected():
        print("✓ Already connected to Wi-Fi!")
        print("  IP address:", wlan.ifconfig()[0])
        return wlan

    # Try to connect
    print(f"Connecting to Wi-Fi: {wifi_name}")
    wlan.connect(wifi_name, wifi_password)

    # Wait for connection with timeout
    start_time = time.time()
    while not wlan.isconnected():
        if time.time() - start_time > timeout:
            print("✗ Wi-Fi connection failed (timeout)")
            return None
        time.sleep(1)  # Wait 1 second between checks

    print("✓ Connected to Wi-Fi successfully!")
    print("  IP address:", wlan.ifconfig()[0])
    return wlan

def ensure_wifi():
    """
    Makes sure we have a Wi-Fi connection, with retries
    Will try to connect 3 times before giving up
    """
    for attempt in range(3):
        wlan = connect_wifi(WIFI_NAME, WIFI_PASSWORD)
        if wlan and wlan.isconnected():
            return wlan
        
        # If connection failed, wait longer before each retry
        wait_time = 2 ** attempt  # 1, 2, 4 seconds between retries
        print(f"Retrying Wi-Fi in {wait_time} seconds... (attempt {attempt + 1}/3)")
        time.sleep(wait_time)
    
    print("✗ Could not connect to Wi-Fi after 3 attempts")
    return None

# ==================== SENSOR FUNCTIONS ====================

def read_sensor_data():
    """
    Read data from your sensors
    
    👋 YOU NEED TO MODIFY THIS FUNCTION! 
    This is just an example that reads an analog sensor.
    Replace it with code for your actual sensors.
    """
    # Example: Reading an analog sensor (like temperature)
    raw_value = sensor.read()
    
    # Convert raw ADC value (0-4095) to voltage (0-3.3V)
    voltage = (raw_value / 4095) * 3.3
    
    # Example conversion to temperature (this is just an example!)
    temperature = (voltage - 0.5) * 100
    
    # Return your sensor readings in a dictionary
    return {
        "temperature": temperature,
        "voltage": voltage,
        "raw_value": raw_value
    }

# ==================== SERVER COMMUNICATION ====================

def send_to_server(sensor_readings):
    """
    Send your sensor readings to the dashboard server
    
    Parameters:
    - sensor_readings: Dictionary containing your sensor data
    
    The function will:
    1. Add your group ID and timestamp
    2. Send data to the server
    3. Flash the LED to show success/failure
    """
    # Get current time for timestamp
    current_time = time.time()
    
    # Prepare the data to send
    data = {
        "group_id": GROUP_ID,
        "timestamp": current_time,  # Send as number, not string!
        "sensor_data": sensor_readings,
        "device_type": "esp32"
    }

    try:
        # Send data to server
        print(f"Sending data... Timestamp: {current_time}")
        response = urequests.post(
            API_URL,
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Check if server accepted our data
        if response.status_code == 200:
            print("✓ Data sent successfully!")
            led.value(1)  # Turn LED on for success
        else:
            print(f"✗ Server error: {response.status_code}")
            led.value(0)  # Turn LED off for failure
            
        # Always close the response to free memory
        response.close()
        
    except Exception as e:
        print(f"✗ Failed to send data: {str(e)}")
        led.value(0)  # Turn LED off for failure

# ==================== MAIN PROGRAM ====================

def main_loop():
    """
    Main program that runs forever:
    1. Makes sure we're connected to Wi-Fi
    2. Reads sensor data
    3. Sends data to the server
    4. Waits before next reading
    """
    print(f"\nStarting ESP32 program for {GROUP_ID}")
    print("----------------------------------------")
    
    # First, connect to Wi-Fi
    wlan = ensure_wifi()
    if not wlan:
        print("Starting in offline mode (will keep trying to connect)")
    
    # Keep track of last reading for change detection
    last_reading = None
    
    # Main loop - runs forever
    while True:
        try:
            # Step 1: Check Wi-Fi connection
            if not wlan or not wlan.isconnected():
                print("\nWi-Fi disconnected - trying to reconnect...")
                wlan = ensure_wifi()
            
            # Step 2: Read sensor data
            sensor_data = read_sensor_data()
            
            # Step 3: Print readings (only if they changed)
            if last_reading is None or has_significant_change(sensor_data, last_reading):
                print(f"\nNew readings at {time.time()}:")
                for key, value in sensor_data.items():
                    print(f"  {key}: {value}")
                last_reading = sensor_data.copy()
            
            # Step 4: Send to server (if online)
            if wlan and wlan.isconnected():
                send_to_server(sensor_data)
            else:
                print("Skipping server update (offline)")
            
            # Step 5: Wait before next reading
            time.sleep(5)  # Change this to adjust how often you send data
            
        except Exception as e:
            print(f"\n✗ Error in main loop: {str(e)}")
            led.value(0)  # Turn off LED to indicate error
            time.sleep(10)  # Wait longer when there's an error

def has_significant_change(new_data, old_data, threshold=0.5):
    """Helper function to detect significant sensor changes"""
    if not old_data:
        return True
    
    # Check each sensor value for significant changes
    for key in new_data:
        if key in old_data:
            if isinstance(new_data[key], (int, float)):
                if abs(new_data[key] - old_data[key]) > threshold:
                    return True
            elif new_data[key] != old_data[key]:
                return True
    return False

# ==================== PROGRAM START ====================

if __name__ == "__main__":
    try:
        # Start the main program
        main_loop()
        
    except KeyboardInterrupt:
        # Handle when user presses Ctrl+C
        print("\n\nProgram stopped by user")
        print("Cleaning up...")
        led.value(0)  # Turn off LED
        print("Goodbye!")
        
    except Exception as e:
        # Handle any other errors
        print("\n\n✗ Program crashed!")
        print(f"Error: {str(e)}")
        led.value(0)  # Turn off LED
        print("\nTrying to restart in 10 seconds...")
        time.sleep(10)
        machine.reset()  # Restart the ESP32