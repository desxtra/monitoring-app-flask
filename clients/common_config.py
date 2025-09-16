# Common configuration for all ESP32 clients
# Copy this file to each group folder and rename to config.py

# ===== MUST EDIT THESE VALUES =====
GROUP_ID = "group1"  # Change to group2, group3, etc.

# Server IP address (get from your teacher)
SERVER_IP = "192.168.1.100"  # Change to your server's IP address
SERVER_URL = f"http://{SERVER_IP}:5000/api/data"

# WiFi Configuration
WIFI_SSID = "Hotspot-SMK"  # Change to your WiFi name
WIFI_PASSWORD = ""  # Change to your WiFi password

# ===== HARDWARE CONFIGURATION =====
# Edit these based on your project's hardware

# Example for Smart Light:
TRIGGER_PIN = 13
ECHO_PIN = 12
LED_PIN = 27
DHT_PIN = 14

# Example for Smart Trash:
# SERVO_PIN = 26
# ULTRASONIC_TRIG_PIN = 13
# ULTRASONIC_ECHO_PIN = 12

# ===== SENSOR CONFIGURATION =====
# Adjust these values based on your project needs
MAX_DISTANCE = 50
GESTURE_THRESHOLD = 10
GESTURE_DURATION = 500
GESTURE_COOLDOWN = 2000

# ===== NETWORK CONFIGURATION =====
RETRY_DELAY = 10  # seconds between connection retries
SEND_INTERVAL = 5000  # milliseconds between data sends