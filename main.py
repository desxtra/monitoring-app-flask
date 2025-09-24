# ESP32 Smart Lamp Client - MicroPython
import network
import socket
import time
import json
from machine import Pin
import urequests

# Hardware Configuration
PIR_PIN = 34        # PIR sensor pin
RELAY_PIN = 35       # Relay pin for lamp control

# Network Configuration
WIFI_SSID = "Roar Relaxing"
WIFI_PASSWORD = "bebyschalke07"
SERVER_IP = "192.168.1.6"
SERVER_PORT = 5000

# Initialize hardware
pir = Pin(PIR_PIN, Pin.IN)
relay = Pin(RELAY_PIN, Pin.IN)

# Global variables
lamp_state = False
auto_mode = False
last_pir_state = False
last_update = 0

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
    relay.value(1 if state else 0)  # Active high relay
    print(f"Lamp {'ON' if state else 'OFF'}")

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
        response = urequests.post(url, 
                                json=data, 
                                headers={'Content-Type': 'application/json'})
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
    global auto_mode, lamp_state
    
    if 'auto_mode' in commands:
        auto_mode = commands['auto_mode']
        print(f"Auto mode: {'ON' if auto_mode else 'OFF'}")
    
    if 'manual_toggle' in commands:
        control_lamp(commands['manual_toggle'])
        print(f"Manual toggle: {'ON' if commands['manual_toggle'] else 'OFF'}")

def auto_control():
    """Automatic PIR-based lamp control"""
    global last_pir_state
    
    if auto_mode:
        current_pir = bool(pir.value())
        
        # PIR state changed
        if current_pir != last_pir_state:
            last_pir_state = current_pir
            
            if current_pir:  # Motion detected
                if not lamp_state:
                    control_lamp(True)
                    print("Motion detected - Lamp ON")
            else:  # No motion
                if lamp_state:
                    control_lamp(False)
                    print("No motion - Lamp OFF")

def main():
    """Main program loop"""
    global last_update
    
    print("Starting Smart Lamp Client...")
    
    # Connect to WiFi
    connect_wifi()
    
    # Initialize lamp state
    control_lamp(False)
    
    print("Smart Lamp Client ready!")
    
    while True:
        try:
            current_time = time.time()
            
            # Auto control based on PIR
            auto_control()
            
            # Send status every 2 seconds
            if current_time - last_update >= 2:
                send_status()
                
                # Get and process commands
                commands = get_commands()
                if commands:
                    process_commands(commands)
                
                last_update = current_time
            
            time.sleep(0.1)  # Small delay to prevent excessive CPU usage
            
        except KeyboardInterrupt:
            print("\nShutting down...")
            control_lamp(False)
            break
        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()