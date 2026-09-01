# Exploration Log

This file tracks raw findings during Phase 1 exploration. Each section gets its own heading.

---

## frontend

### Tech Stack
- **Language:** TypeScript ^5.3.3
- **Framework:** React ^19.0.0 + Vite ^5.4.2
- **CSS:** Tailwind CSS ^3.4.1 + PostCSS + Autoprefixer
- **Auth:** Azure AD via `@azure/msal-browser` ^5.0.2 + `@azure/msal-react` ^5.0.2
- **HTTP:** axios ^1.7.9
- **Maps:** Leaflet ^1.9.4 + react-leaflet ^5.0.0
- **Charts:** Plotly.js-dist-min ^3.4.0, Recharts ^3.5.1
- **Routing:** react-router-dom ^7.10.1
- **Icons:** lucide-react ^0.468.0
- **Backend client:** @supabase/supabase-js ^2.57.4 (imported but unclear usage)
- **Build:** Vite with @vitejs/plugin-react
- **Lint:** ESLint ^9.9.1 + typescript-eslint
- **Container:** node:18-alpine (build) -> nginx:alpine (runtime)

### Directory Tree
```
frontend/
├── Dockerfile                    # Multi-stage: node build -> nginx serve
├── nginx.conf                    # Reverse proxy to backend:3000
├── package.json                  # v0.0.0, vite-react-typescript-starter
├── vite.config.ts                # Vite config
├── tailwind.config.js            # Tailwind config
├── postcss.config.js             # PostCSS config
├── tsconfig.json / tsconfig.app.json / tsconfig.node.json
├── index.html                    # SPA entry
├── .env.production               # Production env vars
├── eslint.config.js
├── data/                         # Static data files
├── json/                         # JSON reference schemas
├── test-map.html                 # Standalone map test
└── src/
    ├── main.tsx                  # ★ ENTRY POINT: MSAL init, BrowserRouter, Routes
    ├── App.tsx                   # ★ MAIN COMPONENT: 1359 lines, full dashboard
    ├── index.css                 # Global styles
    ├── authConfig.ts             # Azure AD MSAL configuration
    ├── vite-env.d.ts
    ├── plotly-dist-min.d.ts
    ├── contexts/
    │   └── AuthContext.tsx        # Auth state: login, logout, Azure SSO, JWT
    ├── hooks/
    │   └── useSpectrumData.ts    # Polling hook for realtime spectrum data
    ├── services/
    │   └── api.ts                # ★ API CLIENT: all REST endpoints, TypeScript interfaces
    ├── components/
    │   ├── Login.tsx             # Login form (Azure + legacy)
    │   ├── AzureCallback.tsx     # Azure AD redirect handler
    │   ├── Sidebar.tsx           # Navigation sidebar
    │   ├── ConfigurationPanel.tsx # Scan configuration controls
    │   ├── AnalysisPanel.tsx     # Spectrum analysis display (683 lines)
    │   ├── SpectrumChart.tsx     # Plotly spectrum visualization (683 lines)
    │   ├── Waterfall.tsx         # Waterfall display (297 lines)
    │   ├── MonitoringNetwork.tsx # Sensor network map (789 lines)
    │   ├── CampaignsList.tsx     # Campaign list + management (662 lines)
    │   ├── CampaignModal.tsx     # Campaign create/edit modal
    │   ├── CampaignDataViewer.tsx # Campaign data viewer (1759 lines)
    │   ├── AlertsPanel.tsx       # Alert history (798 lines)
    │   ├── AntennaManagement.tsx # Antenna CRUD (410 lines)
    │   ├── UserManagement.tsx    # User CRUD (358 lines)
    │   ├── AudioPlayer.tsx       # Legacy audio player (181 lines)
    │   ├── AudioPlayerComponent.tsx # Advanced audio player (362 lines)
    │   ├── WebRTCAudioPlayer.tsx # WebRTC audio streaming (389 lines)
    │   ├── ComplianceReport.tsx  # Compliance report display (~1400 lines)
    │   ├── SpectrumChart.canvas.tsx.bak  # Dead code backup
    │   └── Waterfall.canvas.tsx.bak      # Dead code backup
    ├── pages/
    │   └── AudioPage.tsx         # Standalone audio page (97 lines)
    ├── images/                   # Static images
    ├── styles/                   # Additional styles
    └── utils/                    # Utility functions
```

### Entry Points
1. `index.html` -> loads `src/main.tsx`
2. `main.tsx`: initializes MSAL (Azure AD), sets up BrowserRouter with Routes:
   - `/login` -> Login (public)
   - `/azure-callback` -> AzureCallback (public)
   - `/` -> App (protected)
   - `/audio/:sensorId` -> AudioPage (protected)
3. `App.tsx`: renders AuthenticatedApp with sidebar navigation

### Cross-Section Interactions
- **Backend REST API** via `api.ts`:
  - Auth: `/api/auth/login`, `/api/auth/azure-login`, `/api/auth/me`
  - Sensors: `/api/sensors` (CRUD), `/api/sensors/:id/antennas`, `/api/sensors/validate-status`
  - Sensor data: `/api/sensor/:mac/latest-data`, `/api/sensor/:mac/data/range`, `/api/sensor/:mac/configuration`, `/api/sensor/:mac/latest-status`, `/api/sensor/:mac/latest-gps`
  - Campaigns: `/api/campaigns` (CRUD), `/api/campaigns/:id/data`, `/api/campaigns/:id/start|stop`, `/api/campaigns/statistics/summary`
  - Reports: `/api/reports/compliance/:campaignId`
  - Config: `/api/config`
  - Alerts: `/api/alerts`
- **WebSocket** at `/ws` (or `wss:...:12443/ws`):
  - Events: `sensor_data`, `sensor_gps`, `sensor_status`, `sensor_status_changed`
  - Audio subscribe/unsubscribe
- **WebSocket Audio** at `/ws/audio/listen/{sensorId}`

### Ambiguities
1. `@supabase/supabase-js` is imported but usage unclear — may be dead dependency
2. Two `.bak` files (SpectrumChart.canvas.tsx.bak, Waterfall.canvas.tsx.bak) are dead code
3. App.tsx is 1359 lines — single component doing too much
4. CampaignDataViewer.tsx is 1759 lines — largest component
5. No testing framework configured (no jest, vitest, or test files)
6. `signaling.ts` exists in the exploration but wasn't found in directory listing — may be inside a component

### Layer 3 Proposals
The frontend is large (~13,000+ lines) and heterogeneous. Proposed sub-sections:
- **auth** — Login, AzureCallback, AuthContext, authConfig
- **monitoring** — ConfigurationPanel, AnalysisPanel, SpectrumChart, Waterfall, useSpectrumData
- **campaigns** — CampaignsList, CampaignModal, CampaignDataViewer, ComplianceReport
- **network** — MonitoringNetwork (sensor map)
- **admin** — AntennaManagement, UserManagement
- **audio** — AudioPlayer, AudioPlayerComponent, WebRTCAudioPlayer, AudioPage
- **core** — App.tsx, Sidebar, main.tsx, api.ts

---

## backend

### Tech Stack
- **Language:** TypeScript ^5.3.3
- **Runtime:** Node.js 18 (Alpine Docker)
- **Framework:** Express ^4.18.2
- **Database:** PostgreSQL via `pg` ^8.11.3 + TimescaleDB (optional)
- **Auth (local):** jsonwebtoken ^9.0.2 + bcrypt ^5.1.1
- **Auth (Azure):** jose ^5.9.6 (JWKS/RS256)
- **WebSocket:** ws ^8.18.3
- **Audio:** opusscript ^0.1.1 (Opus decode)
- **HTTP client:** axios ^1.13.2
- **API docs:** swagger-jsdoc ^6.2.8 + swagger-ui-express ^5.0.1
- **CSV:** csv-parse ^6.1.0
- **Build:** tsc (plain TypeScript compiler)
- **Dev runner:** ts-node-dev ^2.0.0

### Directory Tree
```
backend/
├── Dockerfile                    # Multi-stage: node:18-alpine
├── package.json                  # ane-backend v1.0.0
├── tsconfig.json                 # ES2020, strict, commonjs
├── .env.example
├── src/
│   ├── app.ts                    # ★ ENTRY POINT: Express, HTTP server, WS init
│   ├── websocket.ts              # Main WebSocket (/ws) — sensor data + audio pub/sub
│   ├── audioServer.ts            # Audio WebSocket (/ws/audio/*) — Opus decode -> PCM
│   ├── swagger.ts                # Swagger/OpenAPI 3.0 setup
│   ├── middleware/
│   │   ├── auth.ts               # JWT authenticateToken + requireAdmin + requireRoles
│   │   └── azureAuth.ts          # Azure AD JWKS token validation
│   ├── models/
│   │   ├── Sensor.ts             # sensors table, CRUD + status validation
│   │   ├── Antenna.ts            # antennas + sensor_antennas tables
│   │   ├── SensorData.ts         # sensor_status, sensor_gps, sensor_data, sensor_configurations
│   │   └── SensorHistoryAlert.ts # sensor_history_alert, alert dedup
│   ├── routes/
│   │   ├── auth.ts               # /api/auth — login, Azure, user CRUD
│   │   ├── sensor.ts             # /api/sensor — data ingestion + queries
│   │   ├── management.ts         # /api — sensors, antennas, alerts CRUD
│   │   ├── campaign.ts           # /api/campaigns — lifecycle + data + NDJSON
│   │   ├── reports.ts            # /api/reports — compliance (calls Python)
│   │   └── config.ts             # /api/config — key-value settings
│   ├── types/
│   │   ├── index.ts              # TypeScript interfaces
│   │   └── express.d.ts          # Express User augmentation
│   ├── database/
│   │   ├── connection.ts         # pg.Pool, query(), getClient()
│   │   ├── migrate-postgres.ts   # PostgreSQL migration + TimescaleDB
│   │   ├── migrate.ts            # Legacy SQLite (excluded from build)
│   │   ├── seed.ts               # Seed data
│   │   └── [~20 ad-hoc scripts]  # One-off migrations
│   ├── simulator/
│   │   └── sensorSimulator.ts    # Simulated sensor for testing
│   └── scripts/
│       └── production-db-tool.ts # Production migration runner
├── [~10 SQL files]               # Ad-hoc ALTER TABLE scripts
├── [~8 test/utility scripts]     # .js/.mjs/.ps1 testing tools
└── [~5 documentation .md files]
```

### Route Inventory
**Management** (`/api`): GET/POST/PUT/DELETE sensors, antennas, alerts
**Sensor** (`/api/sensor`): POST status/gps/data/audio, GET latest-*, configure, stop, campaigns
**Campaigns** (`/api/campaigns`): CRUD + start/stop + data + statistics + NDJSON streaming
**Auth** (`/api/auth`): login, azure-login, me, user CRUD, change-password
**Reports** (`/api/reports`): compliance report generation (calls Python)
**Config** (`/api/config`): key-value settings

### Cross-Section Interactions
- **Physical sensors** POST to: `/api/sensor/status`, `/api/sensor/gps`, `/api/sensor/data`, `/ws/audio/sensor/{id}`
- **Physical sensors** GET from: `/api/sensor/:mac/realtime`, `/api/sensor/:mac/campaigns`
- **Frontend** calls all management + campaign + report + config endpoints
- **Python microservice** at `http://python-analysis:8000/analyze_batch` — called from reports.ts
- **External geolocation** at `http://172.23.80.220:4155/localizar` — called from reports.ts

### Ambiguities
1. Most sensor-facing endpoints have NO auth (by design — physical sensors can't carry JWT)
2. DELETE endpoints for sensors/antennas have no auth middleware
3. JWT_SECRET fallback is hardcoded string
4. CORS is wide open
5. `sensor_data.pxx` stored as TEXT, not native array
6. Two migration systems (SQLite legacy + PostgreSQL current)
7. ~20 ad-hoc SQL scripts at root level
8. Dynamic imports in campaign.ts suggest circular dependency issues

### Layer 3 Proposals
- **data-ingest** — sensor.ts (POST endpoints), SensorDataModel
- **management-api** — management.ts, auth.ts, config.ts
- **campaigns** — campaign.ts + campaign parts of sensor.ts
- **reports** — reports.ts (Python integration)
- **websocket** — websocket.ts + audioServer.ts
- **models** — models/*, types/*, database/*

---

## postprocesamiento

### Tech Stack
- **Language:** Python 3.11
- **Web framework:** Flask
- **WSGI server:** Gunicorn (gthread, 4 workers x 2 threads)
- **Package manager:** pip (requirements.txt, no version pinning)
- **Dependencies:** flask, gunicorn, numpy, pandas, scipy, matplotlib

### Directory Tree
```
postprocesamiento/
├── Dockerfile                    # python:3.11-slim, gunicorn
├── requirements.txt              # 6 deps, no pinning
├── main.py                       # CLI entry point (argparse)
├── server_flask.py               # Flask HTTP server (primary deployment)
├── consolidado_bbdd_asignación.csv # 117,522 Colombian radio licenses
├── step1_test_payload.py         # Unit test: parser
├── step2_test_router.py          # Integration test (near-duplicate of main.py)
├── __init__.py                   # Misleading comment "src/__init__.py"
├── src/
│   ├── __init__.py               # Empty
│   ├── spectrum_frame.py         # SpectrumFrame dataclass (76 lines)
│   ├── payload_parser.py         # Tolerant JSON->SpectrumFrame (46 lines)
│   ├── processor.py              # ★ CENTRAL ORCHESTRATOR (2,542 lines)
│   ├── spectral_analysis.py      # Signal processing engine (2,181 lines)
│   ├── simple_detector.py        # Preset-based detector (639 lines, unused in prod)
│   ├── calibration_io.py         # License CSV I/O + matching (625 lines)
│   ├── power_utils.py            # Power integration (131 lines)
│   └── utils/
│       ├── __init__.py           # Re-exports all utils
│       ├── signal_processing.py  # Savitzky-Golay smoothing (73 lines)
│       ├── noise_floor.py        # Percentile-histogram NF (48 lines)
│       ├── channel_detection.py  # Mask-based region detection (143 lines)
│       ├── region_analysis.py    # Valley splitting + adaptive NF (850 lines)
│       └── io_visualization.py   # JSON reader + matplotlib (120 lines, dead code)
```

### API Endpoints
- `GET /health` — health check
- `POST /analyze` — single-frame spectral analysis
- `POST /analyze_batch` — multi-frame batch processing (ThreadPoolExecutor)

### Processing Pipeline
JSON payload -> unpack_input -> route_mode -> frame_from_payload -> apply_gain_correction -> _run_new_detector_on_frame (smooth -> noise_floor -> detect_channels -> step_NF -> variable_threshold -> valley_split) -> mode-specific branch (all_emissions/peaks/compliance) -> _enrich_output_with_rni

### Cross-Section Interactions
- Backend sends `POST /analyze_batch` with spectrum frames + DANE codes + tolerances
- Returns peak detection results with license compliance matching
- License CSV loaded lazily with lru_cache keyed on (abs_path, mtime)

### Ambiguities
1. `parse_picos_arg` and `parse_danes_arg` copy-pasted across 3 files (main.py, server_flask.py, step2_test_router.py)
2. `step2_test_router.py` is near-duplicate of main.py
3. `_process_input_reference_legacy()` is dead code in processor.py
4. `simple_detector.py` is imported but never called in production
5. `io_visualization.py` expects different JSON schema — dead code
6. No version pinning in requirements.txt
7. No `.dockerignore` — test files baked into production image

### Layer 3 Proposals
- **server** — Flask app + routes
- **cli** — main.py
- **core** — processor.py orchestrator
- **spectral** — spectral_analysis.py, power_utils.py
- **calibration** — calibration_io.py, license matching
- **utils** — signal_processing, noise_floor, channel_detection, region_analysis

---

## edge (Edge-Node)

### Tech Stack
- **Data plane:** C99 (HackRF, FFTW3, OpenMP, ZMQ, cJSON, libusb, Opus)
- **Control plane:** Python 3.11+ (pyzmq, requests, numpy, pandas, python-crontab, websockets, ntplib)
- **Build system:** CMake + build.sh wrapper
- **IPC:** ZMQ REQ/REP over `ipc:///tmp/rf_engine`
- **Shared state:** `/dev/shm/persistent.json` via fcntl locking
- **Systemd:** 7 units (services + timers)
- **Target hardware:** Raspberry Pi 5

### Directory Tree
```
Edge-Node/
├── AGENTS.md                     # Existing comprehensive docs (DO NOT MODIFY)
├── CMakeLists.txt                # CMake build for C binaries
├── build.sh                      # Build wrapper (production + dev modes)
├── install.sh                    # Production deployment (7 steps)
├── install-local.sh              # Dev deployment (no systemd, no reboot)
├── requirements.txt              # Python deps (14 packages)
├── orchestrator.py               # ★ MAIN PYTHON ENTRY: event loop
├── campaign_runner.py            # One-shot cron-triggered acquisition
├── status.py                     # Status reporter (systemd timer)
├── server_webrtc.py              # WebRTC audio bridge (GStreamer)
├── retry_queue.py                # Failed upload retry (systemd timer)
├── init_sys.py                   # Systemd unit generator
├── functions.py                  # GlobalSys state machine + campaign scheduling
├── cfg.py                        # Configuration + logging subsystem
├── .env                          # Environment variables
├── rf/
│   ├── rf.c                      # ★ C ENTRY: RF engine main loop
│   └── libs/
│       ├── datatypes.h           # Central type registry
│       ├── sdr_HAL.{c,h}        # HackRF hardware abstraction
│       ├── ring_buffer.{c,h}    # Lock-free SPSC ring buffer
│       ├── zmq_util.{c,h}       # ZMQ REP socket wrapper
│       ├── parser.{c,h}         # JSON -> DesiredCfg_t deserializer
│       ├── psd.{c,h}            # PSD engine (Welch + PFB, FFTW3+OpenMP)
│       ├── chan_filter.{c,h}    # Frequency-domain brick-wall filter
│       ├── fm_radio.{c,h}      # FM demodulation chain
│       ├── am_radio.{c,h}      # Legacy AM demodulator
│       ├── am_radio_local.{c,h} # Production AM (CIC + AGC)
│       ├── iq_iir_filter.{c,h}  # Butterworth bandpass (biquad cascade)
│       ├── audio_stream_ctx.{c,h} # Audio path aggregator
│       ├── opus_tx.{c,h}        # Opus encoder + TCP sender
│       ├── net_audio_retry.{c,h} # TCP reconnect resilience
│       └── utils.{c,h}          # Shared memory + env helpers
├── gps-lte/
│   ├── gps-lte.c                 # GPS/LTE C entry
│   └── libs/
│       ├── bacn_GPS.{c,h}       # GPS module
│       ├── bacn_LTE.{c,h}       # LTE module
│       └── utils.{c,h}          # GPS/LTE utilities
├── common/
│   ├── bacn_gpio.{c,h}          # GPIO (libgpiod)
├── utils/
│   ├── __init__.py
│   ├── io_util.py                # ShmStore + atomic_write_bytes
│   ├── request_util.py           # RequestClient + ZmqPairController
│   ├── status_util.py            # StatusDevice hardware metrics
│   ├── dc_spike_detection.py     # DC spike region detector
│   ├── dc_spike_removal.py       # DC spike removal pipeline
│   ├── spectral_content_analysis.py # Low-content histogram detector
│   ├── libs_DSP.py               # NumPy DSP primitives
│   └── benchmarking.py           # Profiling module
├── daemons/                      # Generated systemd units (gitignored)
├── tools/                        # Developer tools (kalibrate, SFTP, UI)
├── test/                         # Manual test scripts
├── examples/                     # Benchmark examples
├── docs/                         # Sphinx/Doxygen documentation
├── json/                         # API/IPC contract schemas
│   ├── rf-engine/params.jsonc    # ZMQ request schema
│   └── shmstore.jsonc            # Shared memory schema
├── context/                      # Architecture docs
│   ├── RF_ENGINE.md              # C engine architecture (360 lines)
│   ├── PYTHON_SERVICES.md        # Python services architecture (518 lines)
│   ├── document/                 # Additional docs
│   └── issues/                   # Post-mortems
├── db/
│   └── ANE_db_reference.csv      # 117,522 Colombian spectrum assignments
└── backups/                      # Backup directory
```

### Entry Points
**C layer:**
- `rf/rf.c` main(): OpenMP tuning -> signal handlers -> ZMQ REP socket -> HackRF init -> ring buffers -> main loop (request-driven state machine)
- `gps-lte/gps-lte.c` main(): GPS + LTE acquisition

**Python layer:**
- `orchestrator.py` main(): infinite loop — poll realtime config, poll campaigns, sleep 100ms
- `campaign_runner.py`: one-shot cron-triggered acquisition
- `status.py`: systemd timer triggered, posts hardware metrics
- `retry_queue.py`: systemd timer triggered, retries failed uploads
- `server_webrtc.py`: WebRTC audio bridge (GStreamer + asyncio)
- `init_sys.py`: one-shot systemd unit generator

### IPC Contract
- Python `ZmqPairController` sends JSON config via `zmq.REQ`
- C `parser.c` receives via `zmq.REP`, processes, replies with PSD JSON
- Shared state in `/dev/shm/persistent.json` (tmpfs, fcntl-locked)

### Cross-Section Interactions
- **Sensors -> Backend:** POST `/api/sensor/status`, `/api/sensor/gps`, `/api/sensor/data`
- **Sensors <- Backend:** GET `/api/sensor/:mac/realtime`, `/api/sensor/:mac/campaigns`
- **Audio:** rf_app -> TCP :9000 (Opus) -> server_webrtc.py -> GStreamer -> WebRTC -> browser
- **Shared state:** `/dev/shm/persistent.json` (calibration ppm_error, GPS, campaign params, delta_t_ms)

### Ambiguities
1. `server_webrtc.py` requires GStreamer — not in requirements.txt (system dependency)
2. `daemons/` directory is gitignored but generated at install time
3. No lint/typecheck/CI commands configured
4. Build artifacts (`rf_app`, `ltegps_app`) placed in repo root then gitignored
5. `benchmarking.py` is standalone profiling, not used in production

### Layer 3 Proposals
This section is large and heterogeneous. Proposed sub-sections:
- **rf-engine** — rf/ directory (C99 DSP, SDR HAL, ring buffer, demodulators, Opus TX)
- **python-services** — orchestrator, campaign_runner, status, retry_queue, server_webrtc, functions, cfg
- **utils** — utils/ directory (ShmStore, ZMQ controller, DC spike removal, DSP)
- **build-deploy** — CMakeLists.txt, build.sh, install.sh, init_sys.py, daemons/
- **gps-lte** — gps-lte/ directory (GPS + LTE C modules)
- **context** — context/ directory (architecture docs, post-mortems)

---

## infra

### Tech Stack
- **Orchestration:** Docker Compose
- **Reverse proxy:** nginx (alpine)
- **Container runtime:** Docker
- **Deployment:** Manual shell scripts (no CI/CD)

### Docker Services
| Service | Container | Build | Port | Depends On |
|---|---|---|---|---|
| frontend | ane-frontend | ./frontend/Dockerfile | 80:80 | backend |
| backend | ane-backend | ./backend/Dockerfile | 3000:3000 | python-analysis (healthy) |
| python-analysis | ane-python-analysis | ./postprocesamiento/Dockerfile | 8000:8000 | — |

### Network
- Single bridge network: `ane-network`
- Backend has `host.docker.internal:host-gateway` for host access

### Deployment Scripts
- `deploy-server.sh` — Full server install (partially stale, references SQLite)
- `backup-production.sh` — Archive + delete source dirs (destructive)
- `install-backup-production.sh` — Copy fresh code to production
- `setup-backup-scheduler.sh` — Cron template (prints instructions, doesn't install)
- `verify-backup-setup.sh` — 7-step backup health check

### Ambiguities
1. **Hardcoded DB password** in docker-compose.yml (line 20)
2. **Root Dockerfile is orphaned** — not referenced by compose
3. **Two divergent nginx.conf** files (root stale, frontend active)
4. **deploy-server.sh references SQLite** but compose uses PostgreSQL
5. **No .dockerignore for postprocesamiento** — test files in production image
6. **No TLS/SSL configuration** — port 80 exposed directly
7. **No database backup strategy** — no pg_dump scripts
8. **Python service port 8000 exposed to host** — should be internal only
9. **No CI/CD** — entirely manual deployment
