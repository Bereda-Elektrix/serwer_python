import random
import paho.mqtt.client as mqtt
import time

# Konfiguracja MQTT
mqtt_server = "localhost"
mqtt_port = 1883  # Ustaw ten port na taki sam jak w aplikacji Flask
topic = "test/puls"

def on_connect(client, userdata, flags, rc):
    print("Połączono z MQTT")
    client.subscribe(topic)

client = mqtt.Client()
client.on_connect = on_connect
client.connect(mqtt_server, mqtt_port, 60)
client.loop_start()

# Główna pętla programu
while True:
    pulse_data = random.randint(60, 100)
    client.publish(topic, pulse_data)
    print(f"Wysłano puls: {pulse_data}")
    time.sleep(5)