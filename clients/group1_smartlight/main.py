import network
import time
import json
import gc
from machine import Pin, Timer
import urequests

# Import configuration
try:
    from config import *
except ImportError:
    print("Error: config.py not found. Please create it from common_config.py")
    raise

class IoTClient:
    def __init__(self):
        print("\n" + "="*40)
        print("IoT Client Starting")
        print("="*40)
        print(f"Group: {GROUP_ID}")
        print(f"Server: {SERVER_URL}")
        
        # Initialize hardware
        self.setup_pins()
        self.setup_sensors()
        
        # State variables
        self.led_state = False
        self.gesture_detected = False
        self.gesture_start_time = 0
        self.last_gesture_time = 0
        self.gesture_count = 0
        
        # Sensor data
        self.current_distance = 0
        self.current_temp = 0
        self.current_humidity = 0
        
        # Network
        self.wifi = None
        self.connected = False
        self.failed_attempts = 0
        
        # Setup
        self.connect_wifi()
        self.setup_timers()
        
    def setup_pins(self):
        """Initialize GPIO pins"""
        self.trigger = Pin(TRIGGER_PIN, Pin.OUT)
        self.echo = Pin(ECHO_PIN, Pin.IN)
        self.led = Pin(LED_PIN, Pin.OUT, Pin.PULL_DOWN)
        self.led.value(0)
        print("GPIO pins initialized")
        
    def setup_sensors(self):
        """Initialize sensors"""
        try:
            import dht
            self.dht_sensor = dht.DHT11(Pin(DHT_PIN))
            self.dht_available = True
            print("DHT11 sensor initialized")
        except:
            self.dht_available = False
            print("DHT11 not available")
            
    def connect_wifi(self):
        """Connect to WiFi network"""
        self.wifi = network.WLAN(network.STA_IF)
        self.wifi.active(True)
        
        if not self.wifi.isconnected():
            print(f"Connecting to WiFi: {WIFI_SSID}")
            self.wifi.connect(WIFI_SSID, WIFI_PASSWORD)
            
            timeout = 0
            while not self.wifi.isconnected() and timeout < 20:
                print(".", end="")
                time.sleep(1)
                timeout += 1
                
        if self.wifi.isconnected():
            ip = self.wifi.ifconfig()[0]
            print(f"\n✅ WiFi connected! IP: {ip}")
            self.connected = True
            self.failed_attempts = 0
        else:
            print("\n❌ Failed to connect to WiFi")
            self.connected = False
            self.failed_attempts += 1
            
    def setup_timers(self):
        """Setup periodic timers"""
        try:
            self.gesture_timer = Timer(0)
            self.sensor_timer = Timer(1)
            self.send_timer = Timer(2)
            
            self.gesture_timer.init(period=100, mode=Timer.PERIODIC, callback=self.check_gesture)
            self.sensor_timer.init(period=2000, mode=Timer.PERIODIC, callback=self.read_sensors)
            self.send_timer.init(period=SEND_INTERVAL, mode=Timer.PERIODIC, callback=self.send_data)
            
            print("Timers initialized successfully")
        except Exception as e:
            print(f"Timer setup error: {e}")
            
    def measure_distance(self):
        """Measure distance using HC-SR04"""
        try:
            self.trigger.value(0)
            time.sleep_us(2)
            self.trigger.value(1)
            time.sleep_us(10)
            self.trigger.value(0)
            
            timeout_us = 30000
            start_time = time.ticks_us()
            
            pulse_start = time.ticks_us()
            while self.echo.value() == 0:
                if time.ticks_diff(time.ticks_us(), start_time) > timeout_us:
                    return 0
                pulse_start = time.ticks_us()
                
            pulse_end = time.ticks_us()
            while self.echo.value() == 1:
                if time.ticks_diff(time.ticks_us(), start_time) > timeout_us:
                    return 0
                pulse_end = time.ticks_us()
                
            pulse_duration = time.ticks_diff(pulse_end, pulse_start)
            distance = pulse_duration * 0.034 / 2
            
            if 2 <= distance <= MAX_DISTANCE:
                return round(distance, 1)
            else:
                return 0
                
        except Exception as e:
            print(f"Distance measurement error: {e}")
            return 0
            
    def check_gesture(self, timer):
        """Check for gesture detection"""
        current_time = time.ticks_ms()
        self.current_distance = self.measure_distance()
        
        if 0 < self.current_distance <= GESTURE_THRESHOLD:
            if not self.gesture_detected:
                self.gesture_detected = True
                self.gesture_start_time = current_time
            elif time.ticks_diff(current_time, self.gesture_start_time) >= GESTURE_DURATION:
                if time.ticks_diff(current_time, self.last_gesture_time) >= GESTURE_COOLDOWN:
                    self.toggle_led()
                    self.last_gesture_time = current_time
                    self.gesture_count += 1
                    print(f"✨ Gesture #{self.gesture_count} confirmed!")
                    
                self.gesture_detected = False
        else:
            self.gesture_detected = False
            
    def toggle_led(self):
        """Toggle LED state"""
        self.led_state = not self.led_state
        self.led.value(1 if self.led_state else 0)
        
        status = "ON" if self.led_state else "OFF"
        print(f"💡 LED: {status} (Total gestures: {self.gesture_count})")
        
    def read_sensors(self, timer):
        """Read sensors"""
        if self.dht_available:
            try:
                self.dht_sensor.measure()
                self.current_temp = self.dht_sensor.temperature()
                self.current_humidity = self.dht_sensor.humidity()
            except Exception as e:
                print(f"DHT sensor error: {e}")
    
    def send_data(self, timer):
        """Send data to server"""
        if not self.connected:
            if self.failed_attempts < 3:
                print("⚠️ Not connected to WiFi, attempting reconnect...")
                self.connect_wifi()
            else:
                print("🔴 Too many failed attempts, waiting before retry...")
                time.sleep(RETRY_DELAY)
                self.failed_attempts = 0
            return
        
        try:
            # Prepare data payload
            data = {
                "group_id": GROUP_ID,
                "device_type": "smart_light",
                "distance": self.current_distance,
                "gesture_count": self.gesture_count,
                "light_status": "ON" if self.led_state else "OFF"
            }
            
            if self.dht_available:
                data["temperature"] = self.current_temp
                data["humidity"] = self.current_humidity
            
            # Send data to server
            headers = {'Content-Type': 'application/json'}
            response = urequests.post(SERVER_URL, json=data, headers=headers)
            response.close()
            
            print("📤 Data sent to server successfully")
            
        except Exception as e:
            print(f"❌ Error sending data: {e}")
            self.connected = False
    
    def run(self):
        """Main application loop"""
        print("\n🚀 IoT Client is running!")
        print("👋 Wave your hand near the sensor to control the lamp")
        print("📡 Data will be sent to server automatically")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Check WiFi connection periodically
                if not self.wifi.isconnected():
                    print("📶 WiFi disconnected. Attempting reconnection...")
                    self.connect_wifi()
                    
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down IoT Client...")
        except Exception as e:
            print(f"Unexpected error: {e}")
            print("Restarting in 10 seconds...")
            time.sleep(10)
            machine.reset()

# Start the client
if __name__ == "__main__":
    client = IoTClient()
    client.run()