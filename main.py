# SIMPLIFIED RELAY CONTROL - ESP32 MicroPython
import network
import time
import json
from machine import Pin
import urequests

# Hardware Configuration
PIR_PIN = 13        
RELAY_PIN = 2

# Network Configuration
WIFI_SSID = "Khusus iot"
WIFI_PASSWORD = "123456789"
SERVER_IP = "192.168.1.117"
SERVER_PORT = 5000

# Auto-off timeout configuration (seconds)
NO_PRESENCE_TIMEOUT = 10  # Turn off lamp after some times

# Initialize hardware
pir = Pin(PIR_PIN, Pin.IN)
relay = Pin(RELAY_PIN, Pin.OUT, value=1)  # Start HIGH (relay OFF)

# Global variables
lamp_state = True  # Start with lamp OFF
auto_mode = False   # Start with auto mode OFF
last_pir_state = False
last_update = 0
last_presence_time = 0  # Track when presence was last detected

def connect_wifi():
    """Connect to WiFi network"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print('Connecting to WiFi...')
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        while not wlan.isconnected():
            time.sleep(1)
            print('.', end='')
    
    print('\nWiFi connected!')
    print('IP address:', wlan.ifconfig()[0])
    return wlan.ifconfig()[0]

def control_lamp(state):
    """Control the relay/lamp"""
    global lamp_state
    lamp_state = state
    
    if state:  # Lamp ON
        relay.value(1)  # Relay OFF
        print("Lamp OFF")
    else:      # Lamp OFF
        relay.value(0)  # Relay ON
        print("Lamp ON")

def send_status():
    """Send status to server"""
    try:
        data = {
            'pir_detected': bool(pir.value()),
            'lamp_state': lamp_state,
            'auto_mode': auto_mode,
            'timestamp': time.time()
        }
        
        url = f"http://{SERVER_IP}:{SERVER_PORT}/api/status"
        response = urequests.post(url, json=data, headers={'Content-Type': 'application/json'})
        response.close()
        
    except Exception as e:
        print(f"Error sending status: {e}")

def get_commands():
    """Get commands from server"""
    try:
        url = f"http://{SERVER_IP}:{SERVER_PORT}/api/commands"
        response = urequests.get(url)
        
        if response.status_code == 200:
            commands = response.json()
            response.close()
            return commands
        
        response.close()
        return {}
        
    except Exception as e:
        print(f"Error getting commands: {e}")
        return {}

def process_commands(commands):
    """Process commands from server"""
    global auto_mode
    
    if 'auto_mode' in commands:
        auto_mode = commands['auto_mode']
        print(f"Auto mode: {'ON' if auto_mode else 'OFF'}")
    
    if 'manual_toggle' in commands:
        control_lamp(commands['manual_toggle'])
        print(f"Manual toggle: {'ON' if commands['manual_toggle'] else 'OFF'}")

def auto_control():
    """Automatic PIR-based lamp control"""
    global last_pir_state, last_presence_time
    
    if auto_mode:
        current_pir = bool(pir.value())
        current_time = time.time()
        
        # If motion is detected, update presence time and turn lamp on
        if current_pir:
            last_presence_time = current_time
            if not lamp_state:
                control_lamp(True)  # Turn lamp ON
                print("Motion detected - Lamp ON")
        
        # Check if timeout has elapsed since last presence
        elif lamp_state and (current_time - last_presence_time >= NO_PRESENCE_TIMEOUT):
            control_lamp(False)  # Turn lamp OFF
            print(f"No presence for {NO_PRESENCE_TIMEOUT} seconds - Lamp OFF")
        
        last_pir_state = current_pir

def main():
    """Main program loop"""
    global last_update, last_presence_time
    
    print("Starting Smart Lamp Client")
    
    # Connect to WiFi
    connect_wifi()
    
    # Initialize lamp to OFF state
    control_lamp(False)
    
    # Initialize presence time
    last_presence_time = time.time()
    
    print("Smart Lamp Client ready!")
    print(f"Initial state - Lamp: {'ON' if lamp_state else 'OFF'}, Auto mode: {'ON' if auto_mode else 'OFF'}")
    
    while True:
        try:
            current_time = time.time()
            
            # Auto control based on PIR
            auto_control()
            
            # Send status every 1 second
            if current_time - last_update >= 1:
                send_status()
                
                # Get and process commands
                commands = get_commands()
                if commands:
                    process_commands(commands)
                
                last_update = current_time
            
            time.sleep(0.1)
            
        except KeyboardInterrupt:
            print("\nShutting down...")
            control_lamp(False)
            break
        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()