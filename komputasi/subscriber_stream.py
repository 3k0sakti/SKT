"""
Subscriber — Stream Processing Mode
=====================================
Skenario:
  Setiap event sensor LANGSUNG diproses begitu tiba (zero buffering
  sebelum komputasi). Dua mekanisme windowing diterapkan:

  1. SLIDING WINDOW (terakhir SLIDE_SIZE event)
       Stats suhu/kelembaban dihitung ulang setelah setiap event baru.
       Menunjukkan kondisi terkini secara kontinu.

  2. TUMBLING WINDOW (non-overlapping, setiap WINDOW_SIZE event)
       Setelah WINDOW_SIZE event terkumpul, jendela "diputar" dan
       laporan agregat dicetak — jendela tidak saling tumpang-tindih.

  3. REAL-TIME ALERTING
       Setiap event diperiksa terhadap threshold suhu dan kelembaban.
       Alert langsung dicetak tanpa menunggu jendela penuh.

  4. TREND DETECTION
       Perubahan suhu terhadap event sebelumnya ditampilkan sebagai
       tren naik / turun per milidetik.

  Cocok untuk: monitoring IoT, fraud detection, live analytics.
"""

import paho.mqtt.client as mqtt
import json
import os
import socket
from collections import deque
from datetime import datetime

# ── Konfigurasi ───────────────────────────────────────────────────────
BROKER_HOST  = os.environ.get("MQTT_BROKER", "10.34.100.103")
BROKER_PORT  = int(os.environ.get("MQTT_PORT", 1883))
TOPIC        = os.environ.get("MQTT_TOPIC", "sensor/suhu")
WINDOW_SIZE  = int(os.environ.get("WINDOW_SIZE", 5))   # tumbling window (event)
SLIDE_SIZE   = int(os.environ.get("SLIDE_SIZE",  5))   # sliding window  (event)
SUHU_ALERT   = float(os.environ.get("SUHU_ALERT",  35.0))   # °C
LEMBAB_ALERT = float(os.environ.get("LEMBAB_ALERT", 80.0))  # %
CLIENT_ID    = f"sub-stream-{socket.gethostname()}"

# ── State stream ───────────────────────────────────────────────────────
_event_count:    int   = 0
_tumbling_buf:   list  = []
_sliding_suhu          = deque(maxlen=SLIDE_SIZE)
_sliding_lembab        = deque(maxlen=SLIDE_SIZE)
_prev_suhu:      float = None  # untuk deteksi tren


def _stats(values) -> dict:
    """Hitung min / max / avg dari sebuah koleksi angka."""
    vals = list(values)
    n    = len(vals)
    return {
        "n":   n,
        "min": round(min(vals), 2),
        "max": round(max(vals), 2),
        "avg": round(sum(vals) / n, 2),
    }


# ════════════════════════════════════════════════════════════════════════
#  STREAM PROCESSOR — dipanggil per event
# ════════════════════════════════════════════════════════════════════════
def process_event(payload: dict) -> None:
    global _event_count, _tumbling_buf, _prev_suhu

    _event_count += 1
    suhu    = payload["suhu_c"]
    lembab  = payload["kelembaban"]
    ts      = payload.get("timestamp", datetime.utcnow().isoformat() + "Z")

    # ── 1. Masukkan ke jendela ────────────────────────────────────────
    _sliding_suhu.append(suhu)
    _sliding_lembab.append(lembab)
    _tumbling_buf.append(payload)

    # ── 2. Deteksi tren suhu ──────────────────────────────────────────
    trend_str = ""
    if _prev_suhu is not None:
        delta = suhu - _prev_suhu
        symbol = "▲" if delta > 0 else ("▼" if delta < 0 else "=")
        trend_str = f"  {symbol}{abs(delta):.2f}C"
    _prev_suhu = suhu

    # ── 3. Log per-event ──────────────────────────────────────────────
    print(f"[Stream #{_event_count:>4}]  "
          f"suhu={suhu:>6.2f}C  lembab={lembab:>6.2f}%  "
          f"ts={ts}{trend_str}")

    # ── 4. Real-time alert (langsung, tanpa menunggu window) ─────────
    alerts = []
    if suhu >= SUHU_ALERT:
        alerts.append(f"SUHU TINGGI ({suhu}C >= {SUHU_ALERT}C)")
    if lembab >= LEMBAB_ALERT:
        alerts.append(f"KELEMBABAN TINGGI ({lembab}% >= {LEMBAB_ALERT}%)")
    if alerts:
        print(f"           *** ALERT: {' | '.join(alerts)} ***")

    # ── 5. Sliding window stats (setelah setiap event, bila cukup data)
    if len(_sliding_suhu) >= SLIDE_SIZE:
        s_suhu   = _stats(_sliding_suhu)
        s_lembab = _stats(_sliding_lembab)
        print(f"           [sliding-{SLIDE_SIZE}] "
              f"suhu  avg={s_suhu['avg']}C "
              f"[{s_suhu['min']}..{s_suhu['max']}]  |  "
              f"lembab avg={s_lembab['avg']}% "
              f"[{s_lembab['min']}..{s_lembab['max']}]")

    # ── 6. Tumbling window (flush setiap WINDOW_SIZE event) ──────────
    if len(_tumbling_buf) >= WINDOW_SIZE:
        _flush_tumbling_window()


def _flush_tumbling_window() -> None:
    """Aggregate & reset jendela tumbling."""
    global _tumbling_buf

    buf       = _tumbling_buf
    suhu_vals  = [r["suhu_c"]     for r in buf]
    lembab_vals = [r["kelembaban"] for r in buf]
    ts_start  = buf[0].get("timestamp", "?")
    ts_end    = buf[-1].get("timestamp", "?")

    s_suhu   = _stats(suhu_vals)
    s_lembab = _stats(lembab_vals)

    print(f"\n  ┌── Tumbling Window flush ({WINDOW_SIZE} event) "
          f"────────────────────────")
    print(f"  │  Rentang waktu : {ts_start}  →  {ts_end}")
    print(f"  │  Suhu   : min={s_suhu['min']}C  max={s_suhu['max']}C  "
          f"avg={s_suhu['avg']}C")
    print(f"  │  Lembab : min={s_lembab['min']}%  max={s_lembab['max']}%  "
          f"avg={s_lembab['avg']}%")
    hot_count = sum(1 for v in suhu_vals if v > 32)
    print(f"  │  Kategori panas (>32C) : {hot_count}/{WINDOW_SIZE} event")
    print(f"  └───────────────────────────────────────────────────────────\n")

    _tumbling_buf = []   # reset jendela


# ════════════════════════════════════════════════════════════════════════
#  MQTT CALLBACKS
# ════════════════════════════════════════════════════════════════════════
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[Stream Subscriber] Terhubung ke {BROKER_HOST}:{BROKER_PORT}")
        print(f"  Topik            : {TOPIC}")
        print(f"  Tumbling window  : setiap {WINDOW_SIZE} event")
        print(f"  Sliding window   : {SLIDE_SIZE} event terakhir")
        print(f"  Alert suhu       : >= {SUHU_ALERT}C")
        print(f"  Alert kelembaban : >= {LEMBAB_ALERT}%\n")
        client.subscribe(TOPIC, qos=1)
    else:
        print(f"[Stream Subscriber] Gagal terhubung, kode: {reason_code}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        process_event(payload)
    except (json.JSONDecodeError, KeyError) as exc:
        print(f"[Stream Subscriber] Pesan tidak valid: {exc}")


# ════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
client.on_connect = on_connect
client.on_message = on_message

print(f"[Stream Subscriber] Menghubungi {BROKER_HOST}:{BROKER_PORT} ...")
client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[Stream Subscriber] Dihentikan.")
finally:
    client.disconnect()
