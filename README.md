# IoT Monitoring System Setup Guide

## For Server Administrator

1. Ensure Python 3.7+ is installed on the server machine
2. Copy the `server` folder to the server machine
3. Open a terminal, navigate to the server folder, and run:

```bash
    pip install -r requirements.txt
    python app.py
```

4. The server will run at http://0.0.0.0:5000
5. Note the server's IP address (use `ipconfig` on Windows or `ifconfig` on Linux/Mac)

## For Each Client

1. Obtain the server's IP address from the administrator
2. Copy the example client folder (e.g., `group1_smartlight`) and rename it according to your group
3. Edit the `config.py` file in your group folder:
- Change `GROUP_ID` to your group's ID (group1, group2, etc.)
- Change `SERVER_IP` to the server's IP address
- Adjust pin and sensor configurations according to your hardware
4. Upload the `main.py` and `config.py` files to the ESP32 using Thonny IDE
5. Ensure the ESP32 is connected to the same WiFi network as the server

## Accessing the Dashboard

Open a web browser and visit: http://[SERVER_IP]:5000
Example: http://192.168.1.100:5000
