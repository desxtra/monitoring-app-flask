# Common configuration for all ESP32 clients

# ===== MUST EDIT THESE VALUES =====
GROUP_ID = "group1"

# Server IP address
SERVER_IP = "192.168.1.100"
SERVER_URL = f"http://{SERVER_IP}:6000/api/data"

# WiFi Configuration
WIFI_SSID = "Hotspot-SMK"
WIFI_PASSWORD = ""

# ===== HARDWARE CONFIGURATION =====
TRIGGER_PIN = 13
ECHO_PIN = 12
LED_PIN = 27
DHT_PIN = 14

# ===== NETWORK CONFIGURATION =====
RETRY_DELAY = 10  # seconds between connection retries
SEND_INTERVAL = 5000  # milliseconds between data sends