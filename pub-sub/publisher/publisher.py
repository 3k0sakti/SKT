import paho.mqtt.client as mqtt
import time
import json
import random
import os
from datetime import datetime

# Konfigurasi broker dari environment variable
BROKER_HOST = os.environ.get("MQTT_BROKER", "10.34.100.103")
BROKER_PORT = int(os.environ.get("MQTT_PORT", 1883))
TOPIC       = os.environ.get("MQTT_TOPIC", "sensor/suhu")
INTERVAL    = float(os.environ.get("PUBLISH_INTERVAL", 2))

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[Publisher] Terhubung ke broker {BROKER_HOST}:{BROKER_PORT}")
    else:
        print(f"[Publisher] Gagal terhubung, kode: {reason_code}")

def on_publish(client, userdata, mid, reason_code, properties):
    print(f"[Publisher] Pesan terkirim (mid={mid})")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="publisher-demo")
client.on_connect = on_connect
client.on_publish  = on_publish

print(f"[Publisher] Menghubungi broker di {BROKER_HOST}:{BROKER_PORT} ...")
client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
client.loop_start()

try:
    while True:
        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "suhu_c":    round(random.uniform(20.0, 40.0), 2),
            "kelembaban": round(random.uniform(40.0, 90.0), 2),
        }
        result = client.publish(TOPIC, json.dumps(payload), qos=1)
        print(f"[Publisher] → topik '{TOPIC}' | data: {payload}")
        time.sleep(INTERVAL)
except KeyboardInterrupt:
    print("\n[Publisher] Dihentikan.")
finally:
    client.loop_stop()
    client.disconnect()
