# Python Services — Layer 2

> Parent: [../main.md](../main.md)
> Last audited: 2026-09-08 @ commit 2bcb560

## Purpose
Control plane orchestration: fetches configurations from backend API, drives C RF engine over ZMQ IPC, manages campaign scheduling via cron, streams audio via WebRTC, and handles status reporting and retry queues.

## Tech stack & conventions
- Python 3.11+ with asyncio for WebRTC
- pyzmq for ZMQ REQ/REP communication with C engine
- python-crontab for campaign scheduling
- websockets + GStreamer for WebRTC audio
- systemd timers for periodic tasks
- Global state machine (`GlobalSys`) enforcing mutual exclusion

## Structure
```
python-services/
├── orchestrator.py       # ★ MAIN ENTRY: infinite event loop, manages realtime/campaign modes
├── campaign_runner.py    # One-shot cron-triggered acquisition
├── status.py             # Status reporter (systemd timer, 30s interval)
├── retry_queue.py        # Failed upload retry (systemd timer, 300s interval)
├── server_webrtc.py      # WebRTC audio bridge (GStreamer + asyncio)
├── functions.py          # GlobalSys state machine + CronSchedulerCampaign + upload formatting
├── cfg.py                # Configuration + logging subsystem (AtomicRotator, run_and_capture)
└── init_sys.py           # Systemd unit generator (7 units)
```

## Entry points
- `orchestrator.py`: `Restart=always` systemd service, runs indefinitely
- `campaign_runner.py`: invoked by cron, one-shot execution
- `status.py`: invoked by systemd timer (30s interval)
- `retry_queue.py`: invoked by systemd timer (300s interval)
- `server_webrtc.py`: managed child process of orchestrator (started when demodulation active)
- `init_sys.py`: run once at install time

## Key interactions
- **Orchestrator -> Backend:** `GET /api/sensor/:mac/realtime` (poll config), `GET /api/sensor/:mac/campaigns` (poll campaigns)
- **Orchestrator -> C engine:** ZMQ REQ/REP (send config, receive PSD — orchestrator hardcodes `method_psd: "pfb"`)
  - Request payload: `json/rf-engine/params.jsonc` — all fields, types, defaults
  - Response payload: `json/POST-data.jsonc` — `Pxx`, `excursion_hz`, `depth`
  - Python validation: `utils/request_util.py` `ServerRealtimeConfig` class
- **Orchestrator -> Backend:** `POST /api/sensor/data` (upload spectrum), `POST /api/sensor/status` (upload status)
  - Upload logic: `functions.py` `format_data_for_upload()` — skips `Pxx` for IQ mode
- **Campaign runner -> Backend:** `POST /api/sensor/data` (upload with campaign_id)
- **Campaign runner -> C engine:** ZMQ REQ/REP (acquire spectrum)
- **Status reporter -> Backend:** `POST /api/sensor/status` (hardware metrics)
- **WebRTC -> C engine:** TCP :9000 (Opus frames) -> GStreamer -> WebRTC -> browser
- **Shared state:** `/dev/shm/persistent.json` (calibration, GPS, campaign params, locks)
- **IQ mode (dev only):** Test scripts can send `method_psd: "iq"` via ZMQ directly to get raw complex samples; Python validation accepts "iq" in `ServerRealtimeConfig`
- **Dry-run (dev only):** Test scripts send `dry_run: true` + `dry_run_iq: [...]` to inject synthetic IQ without HackRF
  - Tutorial: `Edge-Node/playground/TUTORIAL_IQ_DRY_RUN.md` — full developer guide with examples

## Key Design Patterns
- **Global state machine:** `GlobalSys` prevents concurrent acquisitions (IDLE/REALTIME/CAMPAIGN/KALIBRATING)
- **Atomic file writes:** `atomic_write_bytes` for all log/data persistence
- **fcntl-locked shared memory:** `ShmStore` with shared/exclusive locks + fsync
- **Socket recycling:** ZMQ controller destroys/recreates socket on any timeout
- **Escalating process kill:** SIGTERM -> 2s wait -> SIGKILL for WebRTC server
- **Guard flags:** `campaign_runner_running` prevents overlapping campaign executions

## Common tasks & gotchas
- Campaign cron scheduler clears ALL `CAMPAIGN_*` jobs and keeps only highest `campaign_id` in window — `campaign_runner.py`
- WebRTC server requires GStreamer system dependency — not in requirements.txt
- All timestamps are Colombia time (UTC-5) with manual offset — `cfg.py`
- `run_and_capture()` wraps every entrypoint for consistent error handling
- Status reporter retries up to 10 times with 0.5s delay — `status.py`
- **To change what the orchestrator sends to C:** `orchestrator.py` `_realtime_thread()` + `utils/request_util.py` `ServerRealtimeConfig`
- **To change upload data shape:** `functions.py` `format_data_for_upload()` — note IQ mode skips `Pxx`
- **To add a new IPC command:** `utils/request_util.py` `send_rf_request()`, C-side `parser.c`
- **To change campaign scheduling:** `campaign_runner.py`, `functions.py` campaign state machine

## Open questions / TODO
- WebRTC server depends on GStreamer — not documented in requirements.txt
- `server_webrtc.py` has complex async + threading (GLib main loop in daemon thread)
- No structured logging (all text-based)
- Campaign runner saves to Queue/ on failure, retry_queue processes later — but no priority handling
