# Edge Node — Layer 2

> Parent: [../INDEX.md](../INDEX.md)
> Children: [rf-engine](./rf-engine/main_markdown.md), [python-services](./python-services/main_markdown.md), [utils](./utils/main_markdown.md), [build-deploy](./build-deploy/main_markdown.md), [gps-lte](./gps-lte/main_markdown.md), [context](./context/main_markdown.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Raspberry Pi 5 sensor node: hybrid C99 data plane (HackRF One SDR control, real-time DSP, Opus audio) + Python 3.11+ control plane (orchestration, campaign scheduling, WebRTC, status reporting).

## Tech stack & conventions
- **Data plane:** C99, FFTW3, OpenMP, ZeroMQ, libhackrf, Opus, libgpiod
- **Control plane:** Python 3.11+, pyzmq, requests, numpy, pandas, python-crontab, websockets
- **Build:** CMake + Bash wrappers
- **IPC:** ZMQ REQ/REP over `ipc:///tmp/rf_engine` (JSON payloads)
- **Shared state:** `/dev/shm/persistent.json` (tmpfs, fcntl-locked)
- **Systemd:** 7 units (services + timers)
- **Target:** Raspberry Pi 5 (conservative CPU/memory)

## Structure
```
Edge-Node/
├── AGENTS.md               # AI agent entry point (DO NOT MODIFY)
├── rf/                     # C99 RF engine (see rf-engine sub-section)
├── gps-lte/                # C99 GPS/LTE modules (see gps-lte sub-section)
├── common/                 # Shared C code (GPIO)
├── utils/                  # Python utilities (see utils sub-section)
├── tools/                  # Developer tools (kalibrate, SFTP, UI)
├── test/                   # Manual test scripts
├── examples/               # Benchmark examples
├── docs/                   # Sphinx/Doxygen documentation
├── json/                   # API/IPC contract schemas
├── context/                # Architecture docs (see context sub-section)
├── daemons/                # Generated systemd units (gitignored)
├── db/                     # Reference data (117,522 Colombian spectrum assignments)
├── orchestrator.py         # Main Python entry (see python-services)
├── campaign_runner.py      # One-shot cron acquisition (see python-services)
├── status.py               # Status reporter (see python-services)
├── retry_queue.py          # Upload retry (see python-services)
├── server_webrtc.py        # WebRTC audio bridge (see python-services)
├── functions.py            # State machine + campaign scheduling
├── cfg.py                  # Configuration + logging
├── init_sys.py             # Systemd unit generator (see build-deploy)
├── build.sh                # Build wrapper (see build-deploy)
├── install.sh              # Production deployment (see build-deploy)
├── CMakeLists.txt          # CMake build (see build-deploy)
└── requirements.txt        # Python dependencies
```

## Entry points
- **C:** `rf/rf.c` main() (RF engine), `gps-lte/gps-lte.c` main() (GPS/LTE)
- **Python:** `orchestrator.py` (always-on), `campaign_runner.py` (cron), `status.py` (timer), `retry_queue.py` (timer)

## Key interactions
- **Sensors -> Backend:** POST status/gps/data, GET realtime/campaigns (via Python HTTP client)
- **Python -> C:** ZMQ REQ/REP (send config, receive PSD)
- **C -> Audio:** Opus TCP to port 9000 -> server_webrtc.py -> GStreamer -> WebRTC -> browser
- **Shared state:** `/dev/shm/persistent.json` (calibration, GPS, campaign params, locks)

## Common tasks & gotchas
- Global state machine prevents concurrent acquisitions
- `install.sh` logs every run, restarts services on failure
- Build artifacts placed in repo root, gitignored
- No lint/typecheck/CI configured
- All timestamps are Colombia time (UTC-5)

## Open questions / TODO
- WebRTC depends on GStreamer (system dependency, not in requirements.txt)
- No unit tests for C or Python code
- `daemons/` directory gitignored but referenced by install scripts
- `benchmarking.py` is dead code
