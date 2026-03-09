# Penjelasan Cara Kerja Tiga Mekanisme Komputasi di Sisi Subscriber

Sistem pub-sub ini menggunakan MQTT sebagai transport layer. Publisher mengirim data sensor
(suhu & kelembaban) setiap 2 detik ke broker. Tiga subscriber masing-masing menerapkan
mekanisme komputasi yang berbeda terhadap data yang sama.

---

## Gambaran Umum Arsitektur

```
                        ┌─────────────────────────────────────────────────────┐
                        │                  MQTT Broker                        │
                        │              (Eclipse Mosquitto)                    │
                        └──────────────────────┬──────────────────────────────┘
                                               │ topik: sensor/suhu
                     ┌─────────────────────────┼──────────────────────────────┐
                     │                         │                              │
                     ▼                         ▼                              ▼
          ┌──────────────────┐   ┌──────────────────────┐   ┌─────────────────────────┐
          │  MapReduce       │   │  Stream Processing   │   │  Parallel Processing    │
          │  subscriber      │   │  subscriber          │   │  subscriber             │
          └──────────────────┘   └──────────────────────┘   └─────────────────────────┘
          Batch 10 pesan         Per event langsung          4 worker thread paralel
          (~20 detik sekali)     (real-time)                 (per event)
```

---

## 1. MapReduce — `subscriber_mapreduce.py`

### Konsep

MapReduce adalah paradigma komputasi yang memecah masalah menjadi tiga fase:
**Map** (transformasi), **Shuffle** (pengelompokan), dan **Reduce** (agregasi).
Data dikumpulkan terlebih dahulu dalam batch, baru diproses sekaligus.

### Alur Kerja

```
Publisher (MQTT)
      │  1 pesan / 2 detik
      ▼
on_message()
      │
      ▼
_batch (list) ──── akumulasi ────► [msg1, msg2, ..., msg10]
                                          │
                                    batch penuh (10 msg)
                                          │  ~20 detik setelah mulai
                                          ▼
                                    run_mapreduce()
                                    ┌──────────────────┐
                                    │  Fase MAP        │
                                    │  Fase SHUFFLE    │
                                    │  Fase REDUCE     │
                                    └──────────────────┘
                                          │
                                    _batch = []  (reset, siklus ulang)
```

### Fase MAP

Setiap record ditransformasi secara independen menjadi pasangan `(key, value)`.

```python
def map_fn(record: dict) -> tuple[str, dict]:
    suhu = record["suhu_c"]
    if suhu > 32:    key = "panas"
    elif suhu >= 26: key = "normal"
    else:            key = "dingin"
    return (key, {"suhu_c": suhu, "kelembaban": record["kelembaban"]})
```

Contoh hasil:

```
{suhu_c: 34.2, kelembaban: 72.1}  →  ("panas",  {suhu_c: 34.2, kelembaban: 72.1})
{suhu_c: 27.5, kelembaban: 65.0}  →  ("normal", {suhu_c: 27.5, kelembaban: 65.0})
{suhu_c: 24.0, kelembaban: 55.0}  →  ("dingin", {suhu_c: 24.0, kelembaban: 55.0})
```

### Fase SHUFFLE / GROUP

Semua pasangan `(key, value)` dikelompokkan berdasarkan key — menjembatani Map ke Reduce.

```python
def shuffle_group(mapped_pairs):
    grouped = defaultdict(list)
    for key, val in mapped_pairs:
        grouped[key].append(val)
    return grouped
```

Contoh hasil:

```
{
  "panas":  [{suhu_c: 34.2, ...}, {suhu_c: 36.1, ...}],
  "normal": [{suhu_c: 27.5, ...}, {suhu_c: 29.0, ...}, ...],
  "dingin": [{suhu_c: 24.0, ...}]
}
```

### Fase REDUCE

Setiap grup direduksi menjadi satu nilai agregat (statistik).

```python
def reduce_fn(values: list[dict]) -> dict:
    n = len(values)
    suhu_list   = [v["suhu_c"]     for v in values]
    lembab_list = [v["kelembaban"] for v in values]
    return {
        "count":      n,
        "suhu_min":   round(min(suhu_list), 2),
        "suhu_max":   round(max(suhu_list), 2),
        "suhu_avg":   round(sum(suhu_list) / n, 2),
        "lembab_avg": round(sum(lembab_list) / n, 2),
    }
```

Contoh output:

```
 Kategori  Count   Suhu Min   Suhu Max   Suhu Avg  Lembab Avg
 ────────  ─────  ─────────  ─────────  ─────────  ──────────
   dingin      1     24.00C     24.00C     24.00C      55.00%
   normal      7     26.10C     31.80C     28.43C      63.10%
    panas      2     34.20C     36.10C     35.15C      71.30%
```

### Timing Eksekusi

```
t=0s   msg ke-1  masuk  → _batch=[1]
t=2s   msg ke-2  masuk  → _batch=[1,2]
t=4s   msg ke-3  masuk  → _batch=[1,2,3]
...
t=18s  msg ke-10 masuk  → _batch PENUH
                           → MAP → SHUFFLE → REDUCE dijalankan
                           → _batch=[]  (reset)
t=20s  msg ke-11 masuk  → siklus baru
```

MapReduce berjalan setiap **±20 detik** (10 pesan × 2 detik/pesan).

---

## 2. Stream Processing — `subscriber_stream.py`

### Konsep

Stream processing memproses setiap event **segera saat tiba** tanpa menunggu
data terkumpul. Agregasi dilakukan melalui mekanisme *windowing* — jendela
waktu/event yang bergerak atau berganti secara periodik.

### Alur Kerja

```
Publisher (MQTT)
      │  1 pesan / 2 detik
      ▼
on_message()
      │
      ▼
process_event()  ← LANGSUNG diproses, tanpa buffer menunggu
      │
      ├─► Trend Detection   → bandingkan suhu dengan event sebelumnya
      ├─► Real-time Alert   → cek threshold suhu / kelembaban
      ├─► Sliding Window    → statistik 5 event terakhir (diperbarui tiap event)
      └─► Tumbling Window   → flush & reset setiap 5 event
```

### Step 1 — Trend Detection

```python
if _prev_suhu is not None:
    delta  = suhu - _prev_suhu
    symbol = "▲" if delta > 0 else ("▼" if delta < 0 else "=")
_prev_suhu = suhu
```

Hanya menyimpan **1 nilai sebelumnya** — tidak butuh buffer besar.

Contoh output:

```
[Stream #   5]  suhu=28.30C  lembab=65.20%  ts=...  ▲1.20C
[Stream #   6]  suhu=26.80C  lembab=70.10%  ts=...  ▼1.50C
[Stream #   7]  suhu=26.80C  lembab=68.50%  ts=...  =0.00C
```

### Step 2 — Real-time Alert

```python
if suhu   >= SUHU_ALERT:    # default 35.0°C
    alerts.append(f"SUHU TINGGI ({suhu}C >= {SUHU_ALERT}C)")
if lembab >= LEMBAB_ALERT:  # default 80.0%
    alerts.append(f"KELEMBABAN TINGGI ({lembab}% >= {LEMBAB_ALERT}%)")
```

Alert diperiksa **setiap event** — tidak menunggu window penuh, latency mendekati nol.

### Step 3 — Sliding Window

```python
_sliding_suhu   = deque(maxlen=SLIDE_SIZE)   # SLIDE_SIZE = 5
_sliding_lembab = deque(maxlen=SLIDE_SIZE)

_sliding_suhu.append(suhu)    # otomatis hapus event terlama saat penuh
```

`deque(maxlen=5)` secara otomatis membuang elemen terlama saat elemen baru masuk.

Visualisasi pergerakan jendela:

```
Event #1:  [27.1]
Event #2:  [27.1, 28.3]
Event #3:  [27.1, 28.3, 26.8]
Event #4:  [27.1, 28.3, 26.8, 34.5]
Event #5:  [27.1, 28.3, 26.8, 34.5, 29.0]  ← stats dihitung (n=5)
Event #6:  [28.3, 26.8, 34.5, 29.0, 31.2]  ← 27.1 dibuang, stats diperbarui
Event #7:  [26.8, 34.5, 29.0, 31.2, 25.5]  ← 28.3 dibuang
```

### Step 4 — Tumbling Window

```python
_tumbling_buf.append(payload)
if len(_tumbling_buf) >= WINDOW_SIZE:   # WINDOW_SIZE = 5
    _flush_tumbling_window()
    _tumbling_buf = []                  # reset — tidak overlap
```

Visualisasi:

```
Jendela 1: [e1][e2][e3][e4][e5] → flush → reset
Jendela 2: [e6][e7][e8][e9][e10] → flush → reset
           ↑ tidak ada irisan dengan jendela 1
```

### Perbandingan Sliding vs Tumbling Window

```
Sliding  : ─────────────────────────────────────────────────►
            [e1 e2 e3 e4 e5]
               [e2 e3 e4 e5 e6]
                  [e3 e4 e5 e6 e7]   ← overlap, bergeser 1 event tiap kali

Tumbling : ─────────────────────────────────────────────────►
            [e1 e2 e3 e4 e5] | [e6 e7 e8 e9 e10] | ...
                              ↑ tidak overlap, window lama dibuang
```

### Timing Eksekusi

```
t=0s   event #1 → trend=N/A, alert check, sliding=[1]
t=2s   event #2 → trend check, alert check, sliding=[1,2]
t=4s   event #3 → ...
t=6s   event #4 → ...
t=8s   event #5 → sliding=[1,2,3,4,5] → sliding stats dihitung
                   tumbling=[1,2,3,4,5] PENUH → flush → reset
t=10s  event #6 → sliding=[2,3,4,5,6] (1 dibuang)
```

---

## 3. Parallel Processing — `subscriber_parallel.py`

### Konsep

Setiap event di-dispatch ke **ThreadPoolExecutor** yang menjalankan beberapa
worker secara **bersamaan** (task parallelism). Setiap worker menangani
tugas yang berbeda terhadap data yang sama.

### Alur Kerja

```
Publisher (MQTT)
      │  1 pesan / 2 detik
      ▼
on_message()
      │
      ▼
ThreadPoolExecutor (4 thread)
      │
      ├── submit → Worker A: worker_suhu()        ─┐
      ├── submit → Worker B: worker_kelembaban()   ├─ berjalan BERSAMAAN
      ├── submit → Worker C: worker_anomali()      ├─ di thread berbeda
      └── submit → Worker D: worker_logger()      ─┘
                        │
                   as_completed()  ← tunggu semua selesai
                        │
                   kumpulkan hasil [A, B, C, D]
                        │
               setiap 5 event → print_summary()
```

### Worker A — Statistik Suhu

```python
def worker_suhu(payload, eid) -> str:
    suhu = payload["suhu_c"]
    with _lock:                   # Lock agar thread-safe
        s["n"]     += 1
        s["total"] += suhu
        if suhu < s["min"]: s["min"] = suhu
        if suhu > s["max"]: s["max"] = suhu
    return f"A:suhu={suhu:.2f}C"
```

Running statistics — min/max/avg terakumulasi tanpa menyimpan seluruh history data.

### Worker B — Statistik Kelembaban

```python
def worker_kelembaban(payload, eid) -> str:
    lembab = payload["kelembaban"]
    with _lock:
        # update min/max/total kelembaban
    return f"B:lembab={lembab:.2f}%"
```

Berjalan **paralel dengan Worker A** — keduanya akses `_stats` dengan perlindungan `Lock`.

### Worker C — Deteksi Anomali & Klasifikasi

```python
def worker_anomali(payload, eid) -> str:
    if suhu > 32:    kategori = "panas"
    elif suhu >= 26: kategori = "normal"
    else:            kategori = "dingin"

    is_anomali = (suhu >= 35.0) or (lembab >= 82.0)

    with _lock:
        _class_count[kategori] += 1
        if is_anomali: _anomali_count += 1

    return f"C:kategori={kategori}/{'ANOMALI' if is_anomali else 'ok'}"
```

### Worker D — I/O Logger (Simulasi)

```python
def worker_logger(payload, eid) -> str:
    time.sleep(0.002)        # simulasi latency I/O (disk/network)
    with _lock:
        _log.append(entry)
    return f"D:log#{len(_log)}"
```

Simulasi operasi **I/O-bound** — sleep merepresentasikan latency pengiriman
ke remote storage / log aggregator.

### Mekanisme Dispatch & Collect

```python
# Submit semua worker sekaligus (non-blocking)
future_to_name = {
    _executor.submit(fn, payload, eid): fn.__name__
    for fn in [worker_suhu, worker_kelembaban, worker_anomali, worker_logger]
}

# Iterasi sesuai urutan SELESAI (bukan urutan submit)
for future in as_completed(future_to_name):
    results.append(future.result())
```

- `submit()` → langsung return `Future`, worker langsung berjalan di background
- `as_completed()` → yield future yang selesai lebih dulu (tidak menunggu semua)

### Timing Per-Event (Dengan vs Tanpa Parallelism)

```
Tanpa parallelism (sequential):
    worker_suhu()        ~0.1ms
  + worker_kelembaban()  ~0.1ms
  + worker_anomali()     ~0.1ms
  + worker_logger()      ~2.1ms  (ada sleep 0.002s)
  = Total               ~2.4ms

Dengan parallelism (concurrent):
    Thread-1: worker_suhu()        ~0.1ms ─┐
    Thread-2: worker_kelembaban()  ~0.1ms  │ berjalan bersamaan
    Thread-3: worker_anomali()     ~0.1ms  │
    Thread-4: worker_logger()      ~2.1ms ─┘
  = Total  max(0.1, 0.1, 0.1, 2.1) = ~2.1ms   (penghematan ~13%)
```

> Manfaat parallelism makin besar jika worker lebih banyak atau I/O latency lebih tinggi.

### Perlindungan Race Condition

Semua worker yang mengakses shared state menggunakan `threading.Lock`:

```
Thread-1 (suhu)   ──► acquire(_lock) ──► update _stats["suhu"]  ──► release(_lock)
Thread-2 (lembab) ──► waiting...     ──► acquire(_lock) ──► update _stats["lembab"]
Thread-3 (anomali)──► waiting...              ...
Thread-4 (logger) ──► waiting...              ...
```

---

## Perbandingan Ringkas Ketiga Mekanisme

| Aspek | MapReduce | Stream | Parallel |
|---|---|---|---|
| **Kapan diproses** | Setelah 10 msg terkumpul | Langsung per event | Langsung per event |
| **Latensi** | Tinggi (~20 detik) | Sangat rendah (ms) | Rendah (ms) |
| **Model komputasi** | Map → Shuffle → Reduce | Per-event + windowing | Task parallelism |
| **Jumlah thread** | 1 (sequential) | 1 (sequential) | 4 (concurrent) |
| **Penampungan data** | `list` buffer 10 item | `deque` SLIDE + list TUMBLING | Running stats + log list |
| **Output** | Agregat per kategori suhu | Alert + window stats | Stats kumulatif + log |
| **Cocok untuk** | Laporan berkala, ETL | Monitoring real-time | Multi-task I/O bound |

---

## Catatan Tambahan

### Mengapa Thread, bukan Process?

`subscriber_parallel.py` menggunakan `ThreadPoolExecutor` (bukan `ProcessPoolExecutor`) karena:

- Worker D melakukan **I/O-bound** work (simulasi network/disk)
- Untuk I/O-bound, thread lebih efisien — GIL dilepas saat I/O berlangsung
- Overhead `multiprocessing` (fork + IPC) tidak sebanding untuk task ringan per event

### Mengapa MapReduce Tidak Benar-benar Paralel di Kode Ini?

```python
# Saat ini: sequential
mapped = [map_fn(r) for r in batch]

# Jika ingin true parallelism:
from multiprocessing import Pool
with Pool() as p:
    mapped = p.map(map_fn, batch)
```

Untuk batch 10 record, overhead process pool lebih besar dari manfaatnya.
True parallel Map baru signifikan untuk batch ribuan–jutaan record.
