# Server — Layer 3

> Parent: [../main.md](../main.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Flask HTTP server: exposes spectral analysis as REST endpoints for the backend to consume. Handles single-frame and batch processing with configurable defaults.

## Tech stack & conventions
- Flask (development) + Gunicorn (production, gthread worker class)
- 4 workers x 2 threads, 1-hour timeout
- `ThreadPoolExecutor` for batch parallelism
- Environment-based configuration (`ANE_LIC_CSV`, `ANE_CORR_CSV`, etc.)

## Structure
```
server/
└── server_flask.py   # Flask app: /health, /analyze, /analyze_batch (594 lines)
```

## Entry points
- Development: `python server_flask.py --host 127.0.0.1 --port 8000`
- Production: `gunicorn server_flask:app` (Dockerfile CMD)

## Key interactions
- **Backend -> This service:** `POST /analyze` (single frame), `POST /analyze_batch` (multi-frame)
- **Input format:** Wrapper `{frame, cumplimiento, picos, dane, danes, umbral_db, delta_fc_khz, delta_bw_khz}` or raw frame with query params
- **Output format:** `{mode, results[], results_by_dane{}, num_emission, umbral, timestamp, mac}`
- **License CSV:** loaded lazily via `lru_cache` keyed on `(abs_path, mtime)`

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Health check: `{"ok": true}` |
| `POST` | `/analyze` | Single-frame spectral analysis |
| `POST` | `/analyze_batch` | Multi-frame batch (ThreadPoolExecutor) |

## Common tasks & gotchas
- `parse_picos_arg` and `parse_danes_arg` are copy-pasted from `main.py` — DRY violation
- `ALLOW_JSON_PATH` env var disables `json_path` input for security (default: disabled)
- `VERBOSE_LOGS` env var controls server logging (default: enabled)
- Batch mode uses `max_workers` (default 8, max 32) — should match gunicorn workers

## Open questions / TODO
- No request validation beyond basic type checks
- No rate limiting or authentication
- No request ID for tracing across batch workers
- `parse_picos_arg`/`parse_danes_arg` duplicated in 3 files
