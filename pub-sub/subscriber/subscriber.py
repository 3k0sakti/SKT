import paho.mqtt.client as mqtt
import json
import os

# Konfigurasi broker dari environment variable
BROKER_HOST = os.environ.get("MQTT_BROKER", "10.34.100.103")
BROKER_PORT = int(os.environ.get("MQTT_PORT", 1883))
TOPIC       = os.environ.get("MQTT_TOPIC", "sensor/suhu")

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[Subscriber] Terhubung ke broker {BROKER_HOST}:{BROKER_PORT}")
        client.subscribe(TOPIC, qos=1)
        print(f"[Subscriber] Berlangganan topik: '{TOPIC}'")
    else:
        print(f"[Subscriber] Gagal terhubung, kode: {reason_code}")

def on_subscribe(client, userdata, mid, reason_code_list, properties):
    print(f"[Subscriber] Berlangganan berhasil (mid={mid})")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print("─" * 50)
        print(f"[Subscriber] ← Pesan diterima")
        print(f"  Topik      : {msg.topic}")
        print(f"  Waktu      : {payload.get('timestamp')}")
        print(f"  Suhu       : {payload.get('suhu_c')} °C")
        print(f"  Kelembaban : {payload.get('kelembaban')} %")
        print(f"  Data lengkap: {json.dumps(payload, indent=4)}")
    except json.JSONDecodeError:
        print("─" * 50)
        print(f"[Subscriber] ← topik '{msg.topic}' | payload mentah: {msg.payload}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="subscriber-demo")
client.on_connect   = on_connect
client.on_subscribe = on_subscribe
client.on_message   = on_message

print(f"[Subscriber] Menghubungi broker di {BROKER_HOST}:{BROKER_PORT} ...")
client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[Subscriber] Dihentikan.")
finally:
    client.disconnect()
