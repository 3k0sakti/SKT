"""
Subscriber — Parallel Processing Mode
=======================================
Skenario:
  Setiap event sensor yang masuk langsung di-dispatch ke ThreadPoolExecutor.
  Empat worker menjalankan tugas yang BERBEDA secara BERSAMAAN (task parallelism):

    Worker A — hitung & update statistik suhu (running min/max/avg)
    Worker B — hitung & update statistik kelembaban
    Worker C — deteksi anomali + klasifikasi kategori suhu
    Worker D — simulasi I/O logging (catat event ke in-memory log)

  Semua worker disubmit bersamaan per event, hasilnya dikumpulkan setelah
  keempat worker selesai menggunakan as_completed().

  Setiap NUM_REPORT event, ringkasan statistik kumulatif ditampilkan.

  Cocok untuk: CPU-bound / I/O-bound task parallelism, distributed ML
  preprocessing, pipeline komputasi multi-tahap.
"""

import paho.mqtt.client as mqtt
import json
import os
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from datetime import datetime

# ── Konfigurasi ───────────────────────────────────────────────────────
BROKER_HOST  = os.environ.get("MQTT_BROKER", "10.34.100.103")
BROKER_PORT  = int(os.environ.get("MQTT_PORT", 1883))
TOPIC        = os.environ.get("MQTT_TOPIC", "sensor/suhu")
NUM_WORKERS  = int(os.environ.get("NUM_WORKERS", 4))    # ukuran thread pool
NUM_REPORT   = int(os.environ.get("NUM_REPORT",  5))    # interval cetak ringkasan
SUHU_ANOMALI = float(os.environ.get("SUHU_ANOMALI", 35.0))
LEMBAB_ANOMALI = float(os.environ.get("LEMBAB_ANOMALI", 82.0))
CLIENT_ID    = f"sub-parallel-{socket.gethostname()}"

# ── Shared state (dilindungi Lock) ────────────────────────────────────
_lock = Lock()

_stats = {
    "suhu":   {"n": 0, "total": 0.0, "min": float("inf"), "max": float("-inf")},
    "lembab": {"n": 0, "total": 0.0, "min": float("inf"), "max": float("-inf")},
}
_class_count = {"panas": 0, "normal": 0, "dingin": 0}
_anomali_count = 0
_log: list = []          # in-memory event log

# ── Event counter ─────────────────────────────────────────────────────
_event_counter = 0
_counter_lock  = Lock()

# ── Thread pool (dibuat sekali, digunakan untuk semua event) ──────────
_executor = ThreadPoolExecutor(max_workers=NUM_WORKERS)


# ════════════════════════════════════════════════════════════════════════
#  WORKER A — Statistik Suhu
# ════════════════════════════════════════════════════════════════════════
def worker_suhu(payload: dict, eid: int) -> str:
    """Update statistik suhu secara thread-safe."""
    suhu = payload["suhu_c"]
    with _lock:
        s = _stats["suhu"]
        s["n"]     += 1
        s["total"] += suhu
        if suhu < s["min"]: s["min"] = suhu
        if suhu > s["max"]: s["max"] = suhu
    return f"A:suhu={suhu:.2f}C"


# ════════════════════════════════════════════════════════════════════════
#  WORKER B — Statistik Kelembaban
# ════════════════════════════════════════════════════════════════════════
def worker_kelembaban(payload: dict, eid: int) -> str:
    """Update statistik kelembaban secara thread-safe."""
    lembab = payload["kelembaban"]
    with _lock:
        s = _stats["lembab"]
        s["n"]     += 1
        s["total"] += lembab
        if lembab < s["min"]: s["min"] = lembab
        if lembab > s["max"]: s["max"] = lembab
    return f"B:lembab={lembab:.2f}%"


# ════════════════════════════════════════════════════════════════════════
#  WORKER C — Deteksi Anomali & Klasifikasi
# ════════════════════════════════════════════════════════════════════════
def worker_anomali(payload: dict, eid: int) -> str:
    """Klasifikasi suhu dan deteksi kondisi anomali."""
    global _anomali_count
    suhu   = payload["suhu_c"]
    lembab = payload["kelembaban"]

    # Klasifikasi berdasarkan suhu
    if suhu > 32:
        kategori = "panas"
    elif suhu >= 26:
        kategori = "normal"
    else:
        kategori = "dingin"

    # Deteksi anomali (suhu ATAU kelembaban melampaui threshold)
    is_anomali = (suhu >= SUHU_ANOMALI) or (lembab >= LEMBAB_ANOMALI)

    with _lock:
        _class_count[kategori] += 1
        if is_anomali:
            _anomali_count += 1

    flag = "ANOMALI" if is_anomali else "ok"
    return f"C:kategori={kategori}/{flag}"


# ════════════════════════════════════════════════════════════════════════
#  WORKER D — I/O Logger (simulasi)
# ════════════════════════════════════════════════════════════════════════
def worker_logger(payload: dict, eid: int) -> str:
    """Catat event ke in-memory log (simulasi I/O disk/network)."""
    ts    = payload.get("timestamp", datetime.utcnow().isoformat() + "Z")
    entry = {
        "eid":        eid,
        "timestamp":  ts,
        "suhu_c":     payload["suhu_c"],
        "kelembaban": payload["kelembaban"],
    }
    # Simulasi latency I/O ringan (misal: kirim ke remote log service)
    time.sleep(0.002)
    with _lock:
        _log.append(entry)
    return f"D:log#{len(_log)}"


# ── Daftar semua worker tasks ─────────────────────────────────────────
_TASKS = [worker_suhu, worker_kelembaban, worker_anomali, worker_logger]


# ════════════════════════════════════════════════════════════════════════
#  RINGKASAN STATISTIK KUMULATIF
# ════════════════════════════════════════════════════════════════════════
def print_summary(eid: int) -> None:
    with _lock:
        s_suhu   = _stats["suhu"]
        s_lembab = _stats["lembab"]
        avg_suhu  = round(s_suhu["total"]  / s_suhu["n"],   2) if s_suhu["n"]   else 0
        avg_lembab = round(s_lembab["total"] / s_lembab["n"], 2) if s_lembab["n"] else 0
        anomali = _anomali_count
        classes = dict(_class_count)
        total_log = len(_log)

    print(f"\n  ┌── Ringkasan kumulatif setelah {eid} event ─────────────────────")
    print(f"  │  Suhu    : min={s_suhu['min']:.2f}C  "
          f"max={s_suhu['max']:.2f}C  avg={avg_suhu:.2f}C")
    print(f"  │  Lembab  : min={s_lembab['min']:.2f}%  "
          f"max={s_lembab['max']:.2f}%  avg={avg_lembab:.2f}%")
    print(f"  │  Klasif  : panas={classes['panas']}  "
          f"normal={classes['normal']}  dingin={classes['dingin']}")
    print(f"  │  Anomali : {anomali} event  |  Log entries : {total_log}")
    print(f"  └────────────────────────────────────────────────────────────\n")


# ════════════════════════════════════════════════════════════════════════
#  MQTT CALLBACKS
# ════════════════════════════════════════════════════════════════════════
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[Parallel Subscriber] Terhubung ke {BROKER_HOST}:{BROKER_PORT}")
        print(f"  Topik         : {TOPIC}")
        print(f"  Thread pool   : {NUM_WORKERS} worker threads")
        print(f"  Tugas paralel : {len(_TASKS)} "
              f"(A=suhu, B=kelembaban, C=anomali, D=logger)")
        print(f"  Laporan setiap: {NUM_REPORT} event\n")
        client.subscribe(TOPIC, qos=1)
    else:
        print(f"[Parallel Subscriber] Gagal terhubung, kode: {reason_code}")


def on_message(client, userdata, msg):
    global _event_counter

    try:
        payload = json.loads(msg.payload.decode())
    except (json.JSONDecodeError, KeyError) as exc:
        print(f"[Parallel Subscriber] Pesan tidak valid: {exc}")
        return

    with _counter_lock:
        _event_counter += 1
        eid = _event_counter

    print(f"[Parallel #{eid:>4}] ← suhu={payload['suhu_c']:.2f}C  "
          f"lembab={payload['kelembaban']:.2f}%  "
          f"→ dispatch {len(_TASKS)} workers")

    # Submit semua task secara paralel ke thread pool
    future_to_name = {
        _executor.submit(fn, payload, eid): fn.__name__
        for fn in _TASKS
    }

    # Kumpulkan hasil semua worker
    results = []
    for future in as_completed(future_to_name):
        try:
            results.append(future.result())
        except Exception as exc:
            results.append(f"ERR({future_to_name[future]}:{exc})")

    print(f"             hasil: {' | '.join(results)}")

    # Cetak ringkasan setiap NUM_REPORT event
    if eid % NUM_REPORT == 0:
        print_summary(eid)


# ════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
client.on_connect = on_connect
client.on_message = on_message

print(f"[Parallel Subscriber] Menghubungi {BROKER_HOST}:{BROKER_PORT} ...")
client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[Parallel Subscriber] Dihentikan.")
    _executor.shutdown(wait=False)
finally:
    client.disconnect()
