# Demo Pub/Sub Berbasis MQTT

Proyek ini mendemonstrasikan pola **Publish/Subscribe** menggunakan protokol MQTT
dengan tiga kontainer Docker:

| Kontainer | Peran |
|---|---|
| `mqtt-broker` | Eclipse Mosquitto 2 – perantara pesan |
| `mqtt-publisher` | Mengirim data sensor (suhu & kelembaban) setiap 2 detik |
| `mqtt-subscriber-1` | Berlangganan topik `sensor/suhu` |
| `mqtt-subscriber-2` | Berlangganan wildcard `sensor/#` |

## Arsitektur

```
┌─────────────────┐        MQTT         ┌──────────────────────┐
│   Publisher     │  ──── sensor/suhu ──▶│      Broker          │
│ (Python/paho)   │                      │  (Mosquitto :1883)   │
└─────────────────┘                      └──────┬──────┬────────┘
                                                │      │
                                      sensor/suhu  sensor/#
                                                │      │
                                         ┌──────▼─┐ ┌──▼──────────┐
                                         │  Sub-1  │ │   Sub-2     │
                                         └─────────┘ └─────────────┘
```

## Prasyarat

- Docker Engine ≥ 24
- Docker Compose v2

## Menjalankan Demo

```bash
# Masuk ke direktori proyek
cd pub-sub

# Bangun image dan jalankan semua kontainer
docker compose up --build
```

Tekan **Ctrl+C** untuk menghentikan semua kontainer.

## Melihat Log Masing-masing Kontainer

```bash
# Log publisher
docker compose logs -f publisher

# Log subscriber-1
docker compose logs -f subscriber1

# Log subscriber-2
docker compose logs -f subscriber2

# Log broker
docker compose logs -f broker
```

## Uji Manual dengan CLI Mosquitto

```bash
# Subscribe dari terminal lain
docker exec -it mqtt-broker mosquitto_sub -h localhost -t "sensor/#" -v

# Publish pesan manual
docker exec -it mqtt-broker mosquitto_pub -h localhost -t "sensor/suhu" -m '{"test": true}'
```

## Variabel Environment

| Variabel | Default | Keterangan |
|---|---|---|
| `MQTT_BROKER` | `broker` | Hostname broker MQTT |
| `MQTT_PORT` | `1883` | Port broker |
| `MQTT_TOPIC` | `sensor/suhu` | Topik yang digunakan |
| `PUBLISH_INTERVAL` | `2` | Interval publish (detik) |

## Port yang Dibuka

| Port | Protokol |
|---|---|
| `1883` | MQTT (TCP) |
| `9001` | MQTT over WebSocket |
