# Python Services — Layer 3

> Parent: [../main.md](../main.md)
> Last audited: 2026-08-31 @ commit dc6c386

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
- **Orchestrator -> C engine:** ZMQ REQ/REP (send config, receive PSD)
- **Orchestrator -> Backend:** `POST /api/sensor/data` (upload spectrum), `POST /api/sensor/status` (upload status)
- **Campaign runner -> Backend:** `POST /api/sensor/data` (upload with campaign_id)
- **Campaign runner -> C engine:** ZMQ REQ/REP (acquire spectrum)
- **Status reporter -> Backend:** `POST /api/sensor/status` (hardware metrics)
- **WebRTC -> C engine:** TCP :9000 (Opus frames) -> GStreamer -> WebRTC -> browser
- **Shared state:** `/dev/shm/persistent.json` (calibration, GPS, campaign params, locks)

## Key Design Patterns
- **Global state machine:** `GlobalSys` prevents concurrent acquisitions (IDLE/REALTIME/CAMPAIGN/KALIBRATING)
- **Atomic file writes:** `atomic_write_bytes` for all log/data persistence
- **fcntl-locked shared memory:** `ShmStore` with shared/exclusive locks + fsync
- **Socket recycling:** ZMQ controller destroys/recreates socket on any timeout
- **Escalating process kill:** SIGTERM -> 2s wait -> SIGKILL for WebRTC server
- **Guard flags:** `campaign_runner_running` prevents overlapping campaign executions

## Common tasks & gotchas
- Campaign cron scheduler clears ALL `CAMPAIGN_*` jobs and keeps only highest `campaign_id` in window
- WebRTC server requires GStreamer system dependency — not in requirements.txt
- All timestamps are Colombia time (UTC-5) with manual offset
- `run_and_capture()` wraps every entrypoint for consistent error handling
- Status reporter retries up to 10 times with 0.5s delay

## Open questions / TODO
- WebRTC server depends on GStreamer — not documented in requirements.txt
- `server_webrtc.py` has complex async + threading (GLib main loop in daemon thread)
- No structured logging (all text-based)
- Campaign runner saves to Queue/ on failure, retry_queue processes later — but no priority handling
