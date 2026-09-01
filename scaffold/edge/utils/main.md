# Utils — Layer 3

> Parent: [../main.md](../main.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Shared Python utilities: IPC communication with C engine, shared memory management, system status collection, DC spike detection/removal, and DSP primitives.

## Tech stack & conventions
- pyzmq for ZMQ REQ/REP communication
- fcntl for file locking on shared memory
- NumPy for DSP operations
- Atomic file writes (temp + fsync + replace)
- Read-only access to Linux virtual filesystems for hardware metrics

## Structure
```
utils/
├── __init__.py                  # Package marker
├── io_util.py                   # ShmStore + atomic_write_bytes + ElapsedTimer
├── request_util.py              # RequestClient + ZmqPairController + ServerRealtimeConfig
├── status_util.py               # StatusDevice (CPU, RAM, disk, temp, ping) + StatusPost
├── dc_spike_detection.py        # DC spike region detector (slope-based)
├── dc_spike_removal.py          # DC spike removal pipeline
├── spectral_content_analysis.py # Low-content histogram detector
├── libs_DSP.py                  # NumPy DSP primitives (moving average, MAD, polynomial fit)
└── benchmarking.py              # Profiling module (not used in production)
```

## Entry points
- Imported by all Python services as needed

## Key modules

### io_util.py
- `atomic_write_bytes(path, data)` — atomic file write (temp + fsync + replace)
- `ShmStore` — `/dev/shm/persistent.json` manager with fcntl locking
  - `add_to_persistent(key, value)` — exclusive-locked read-modify-write
  - `consult_persistent(key)` — shared-locked read
  - `update_from_dict(dict)` — merge under exclusive lock
  - `clear_persistent()` — wipe all state
- `ElapsedTimer` — non-blocking countdown timer

### request_util.py
- `RequestClient` — HTTP client with unified return codes (0=success, 1=network, 2=internal)
- `ZmqPairController` — async context manager for ZMQ REQ/REP (despite name, uses REQ not PAIR)
  - 15s timeout, socket recycling on error
  - Removes stale IPC socket files before binding
- `ServerRealtimeConfig` / `FilterConfig` — dataclasses with hardware constraint validation

### status_util.py
- `StatusDevice` — reads `/proc/stat`, `/proc/meminfo`, `/sys/class/thermal/`, `os.statvfs`
- `StatusPost` — DTO matching API contract (cpu_0, cpu_1, ..., ram_mb, disk_mb, temp_c, etc.)

### DC Spike Detection/Removal
- `detect_dc_spike_region_by_symmetric_slope()` — analyzes PSD from center outward
- `remove_dc_spike_adaptive_symmetric()` — full pipeline: detect -> expand -> reconstruct
- Reconstruction strategies: linear interpolation (noise floor) or polynomial fit (emission detected)

### libs_DSP.py
- `SignalProcessingUtils` — moving average, MAD scale estimation, discrete differences
- `WindowReconstructionUtils` — polynomial reconstruction, linear reconstruction

## Key interactions
- **Called by:** orchestrator.py, campaign_runner.py, status.py, retry_queue.py
- **ZmqPairController:** sends JSON to C engine via `ipc:///tmp/rf_engine`
- **ShmStore:** reads/writes `/dev/shm/persistent.json` (calibration, GPS, campaign params)
- **StatusDevice:** reads Linux virtual filesystems (no external calls)

## Common tasks & gotchas
- `ZmqPairController` name is misleading — it uses `zmq.REQ`, not `zmq.PAIR`
- `benchmarking.py` is standalone profiling — not used in production flows
- DC spike removal has two reconstruction strategies — choice depends on detector's `termination_mode`
- All file writes must go through `atomic_write_bytes` — never write directly

## Open questions / TODO
- `benchmarking.py` should be moved to tools/ or removed
- No retry logic in `RequestClient` — caller must handle retries
- `ShmStore` is not thread-safe for concurrent writes (fcntl is process-level, not thread-level)
