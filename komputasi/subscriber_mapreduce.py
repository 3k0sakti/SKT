"""
Subscriber — MapReduce Mode
============================
Skenario:
  Publisher mengirim data sensor (suhu & kelembaban) setiap 2 detik.
  Subscriber ini mengumpulkan BATCH_SIZE pesan terlebih dahulu, lalu
  menjalankan pipeline MapReduce sederhana:

    MAP     → setiap record dipetakan ke (key, value)
               key   = kategori suhu: "panas" | "normal" | "dingin"
               value = {"suhu_c": ..., "kelembaban": ...}

    SHUFFLE → pasangan dikelompokkan berdasarkan key

    REDUCE  → setiap grup direduksi menjadi statistik agregat
               (count, min, max, avg suhu, avg kelembaban)

  Cocok untuk: analisis historis periodik, ETL, laporan berkala.
"""

import paho.mqtt.client as mqtt
import json
import os
import socket
from collections import defaultdict

# ── Konfigurasi ───────────────────────────────────────────────────────
BROKER_HOST = os.environ.get("MQTT_BROKER", "10.34.100.103")
BROKER_PORT = int(os.environ.get("MQTT_PORT", 1883))
TOPIC       = os.environ.get("MQTT_TOPIC", "sensor/suhu")
BATCH_SIZE  = int(os.environ.get("BATCH_SIZE", 10))   # ukuran batch sebelum diproses
CLIENT_ID   = f"sub-mapreduce-{socket.gethostname()}"

# Buffer batch global
_batch: list[dict] = []
_batch_num: int = 0


# ════════════════════════════════════════════════════════════════════════
#  MAP
# ════════════════════════════════════════════════════════════════════════
def map_fn(record: dict) -> tuple[str, dict]:
    """
    Petakan satu record sensor ke pasangan (key, value).

    key   → kategori berdasarkan suhu
    value → data relevan untuk tahap reduce
    """
    suhu = record["suhu_c"]
    if suhu > 32:
        key = "panas"
    elif suhu >= 26:
        key = "normal"
    else:
        key = "dingin"
    return (key, {"suhu_c": suhu, "kelembaban": record["kelembaban"]})


# ════════════════════════════════════════════════════════════════════════
#  SHUFFLE / GROUP
# ════════════════════════════════════════════════════════════════════════
def shuffle_group(mapped_pairs: list[tuple]) -> dict[str, list]:
    """
    Kelompokkan daftar (key, value) menjadi {key: [value, ...]}
    — fase shuffle sebelum reduce.
    """
    grouped: dict[str, list] = defaultdict(list)
    for key, val in mapped_pairs:
        grouped[key].append(val)
    return grouped


# ════════════════════════════════════════════════════════════════════════
#  REDUCE
# ════════════════════════════════════════════════════════════════════════
def reduce_fn(values: list[dict]) -> dict:
    """
    Reduksi sekelompok value menjadi satu statistik agregat.
    """
    n          = len(values)
    suhu_list  = [v["suhu_c"]     for v in values]
    lembab_list = [v["kelembaban"] for v in values]
    return {
        "count":      n,
        "suhu_min":   round(min(suhu_list), 2),
        "suhu_max":   round(max(suhu_list), 2),
        "suhu_avg":   round(sum(suhu_list) / n, 2),
        "lembab_avg": round(sum(lembab_list) / n, 2),
    }


# ════════════════════════════════════════════════════════════════════════
#  PIPELINE RUNNER
# ════════════════════════════════════════════════════════════════════════
def run_mapreduce(batch: list[dict]) -> None:
    global _batch_num
    _batch_num += 1

    print(f"\n{'═' * 60}")
    print(f"[MapReduce] Batch #{_batch_num}  ({len(batch)} record)")
    print(f"{'─' * 60}")

    # Fase MAP
    mapped = [map_fn(r) for r in batch]
    keys_found = [k for k, _ in mapped]
    print(f"[Map]     {len(mapped)} record → pasangan (key, value)")
    print(f"          distribusi key: {dict((k, keys_found.count(k)) for k in set(keys_found))}")

    # Fase SHUFFLE/GROUP
    grouped = shuffle_group(mapped)
    print(f"[Shuffle] {len(grouped)} grup terbentuk: {sorted(grouped.keys())}")

    # Fase REDUCE
    print(f"[Reduce]  Hasil per grup:")
    print(f"  {'Kategori':>8}  {'Count':>5}  {'Suhu Min':>9}  "
          f"{'Suhu Max':>9}  {'Suhu Avg':>9}  {'Lembab Avg':>11}")
    print(f"  {'─'*8}  {'─'*5}  {'─'*9}  {'─'*9}  {'─'*9}  {'─'*11}")
    for key in ("dingin", "normal", "panas"):
        if key in grouped:
            r = reduce_fn(grouped[key])
            print(f"  {key:>8}  {r['count']:>5}  "
                  f"{r['suhu_min']:>8.2f}C  {r['suhu_max']:>8.2f}C  "
                  f"{r['suhu_avg']:>8.2f}C  {r['lembab_avg']:>10.2f}%")
    print(f"{'═' * 60}\n")


# ════════════════════════════════════════════════════════════════════════
#  MQTT CALLBACKS
# ════════════════════════════════════════════════════════════════════════
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[MapReduce Subscriber] Terhubung ke {BROKER_HOST}:{BROKER_PORT}")
        print(f"  Topik      : {TOPIC}")
        print(f"  Batch size : {BATCH_SIZE} pesan sebelum MapReduce dijalankan\n")
        client.subscribe(TOPIC, qos=1)
    else:
        print(f"[MapReduce Subscriber] Gagal terhubung, kode: {reason_code}")


def on_message(client, userdata, msg):
    global _batch
    try:
        payload = json.loads(msg.payload.decode())
        _batch.append(payload)
        print(f"[Buffer {len(_batch):>2}/{BATCH_SIZE}] "
              f"suhu={payload['suhu_c']:>5.2f}C  "
              f"lembab={payload['kelembaban']:>5.2f}%  "
              f"ts={payload.get('timestamp', '')}")

        # Jalankan MapReduce saat batch penuh
        if len(_batch) >= BATCH_SIZE:
            run_mapreduce(_batch)
            _batch = []
    except (json.JSONDecodeError, KeyError) as exc:
        print(f"[MapReduce Subscriber] Pesan tidak valid: {exc}")


# ════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
client.on_connect = on_connect
client.on_message = on_message

print(f"[MapReduce Subscriber] Menghubungi {BROKER_HOST}:{BROKER_PORT} ...")
client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[MapReduce Subscriber] Dihentikan.")
finally:
    client.disconnect()
