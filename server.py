from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import paho.mqtt.client as mqtt
from threading import Thread, Lock

# Global variables to store the data
temperature = None
status_info = None
data_lock = Lock()

# MQTT configuration
mqtt_server = "172.25.25.20"
mqtt_user = "CityNet"
mqtt_password = "123456"
mqtt_port = 1883
mqtt_topic = "esp32/GREE16/status"

# MQTT callback functions
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker")
    client.subscribe(mqtt_topic)

def on_message(client, userdata, message):
    global temperature, status_info
    msg = message.payload.decode()
    with data_lock:
        if msg.startswith("POWER"):
            status_info = msg
        else:
            temperature = msg

# MQTT client setup
def start_mqtt_client():
    client = mqtt.Client()
    client.username_pw_set(mqtt_user, mqtt_password)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_server, mqtt_port, 60)
    client.loop_forever()

# Start MQTT client in a separate thread
mqtt_thread = Thread(target=start_mqtt_client)
mqtt_thread.daemon = True
mqtt_thread.start()

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/poll':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            with data_lock:
                data = {
                    'temperature': temperature,
                    'statusInfo': status_info
                }
            self.wfile.write(json.dumps(data).encode())
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            with open('index.html', 'r') as file:
                self.wfile.write(file.read().encode())

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__":
    run()
