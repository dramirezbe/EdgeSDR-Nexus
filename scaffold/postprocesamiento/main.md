# Postprocesamiento — Layer 1

> Parent: [../INDEX.md](../INDEX.md)
> Children: [server](./server/main.md), [cli](./cli/main.md), [core](./core/main.md), [spectral](./spectral/main.md), [calibration](./calibration/main.md), [utils](./utils/main.md)
> Last audited: 2026-09-08 @ commit 2bcb560

## Purpose
Python Flask microservice for spectral analysis and regulatory compliance evaluation: receives measurement frames from the backend, detects emissions, measures parameters, and evaluates compliance against Colombian radio licenses.

## Tech stack & conventions
- Python 3.11 + Flask + Gunicorn (gthread, 4 workers x 2 threads)
- NumPy, SciPy, pandas for signal processing and data manipulation
- matplotlib for visualization (optional, not used in production)
- No version pinning in requirements.txt
- Spanish comments and user-facing strings (Colombian regulatory context)
- `lru_cache` with mtime-based invalidation for file I/O

## Structure
```
postprocesamiento/
├── main.py                       # CLI entry point
├── server_flask.py               # Flask HTTP server (primary deployment)
├── Dockerfile                    # python:3.11-slim, gunicorn
├── requirements.txt              # 6 deps, no pinning
├── consolidado_bbdd_asignación.csv  # 117,522 Colombian radio licenses
├── src/
│   ├── spectrum_frame.py         # Domain model (SpectrumFrame dataclass)
│   ├── payload_parser.py         # Tolerant JSON -> SpectrumFrame
│   ├── processor.py              # ★ CENTRAL ORCHESTRATOR (2,542 lines)
│   ├── spectral_analysis.py      # Signal processing engine (2,181 lines)
│   ├── simple_detector.py        # Preset-based detector (unused in prod)
│   ├── calibration_io.py         # License CSV I/O + matching
│   ├── power_utils.py            # Power integration
│   └── utils/                    # DSP utilities (smoothing, NF, detection, regions)
```

## Entry points
- HTTP: `gunicorn server_flask:app` on port 8000
- CLI: `python main.py --json FILE.json [options]`
- Health: `GET /health`, Analysis: `POST /analyze`, Batch: `POST /analyze_batch`

## Key interactions
- **Backend -> This service:** POST /analyze_batch with spectrum frames + DANE codes
- **Returns:** Peak detection results with license compliance matching
- **License CSV:** loaded lazily, 117,522 Colombian radio licenses
- **Three modes:** all_emissions (detection only), peaks (match requested), compliance (regulatory check)

## Common tasks & gotchas
- `parse_picos_arg`/`parse_danes_arg` duplicated across 3 files
- `simple_detector.py` imported but never called in production
- Legacy `_process_input_reference_legacy()` is dead code
- No `.dockerignore` — test files baked into production image
- No version pinning — fragile for production

## File Criticality

| File | Lines | Status | Imports | Notes |
|------|-------|--------|---------|-------|
| `src/processor.py` | ~400 | Active | 2 | Central orchestrator, mode routing |
| `src/spectral_analysis.py` | ~300 | Active | 1 | Peak detection, bandwidth, noise floor |
| `src/calibration_io.py` | ~150 | Active | 1 | License CSV I/O |
| `src/server_flask.py` | ~100 | Active | 1 | Flask HTTP server |
| `src/simple_detector.py` | ~200 | DEAD | 0 | Imported but never called in production |
| `src/utils/io_visualization.py` | ~100 | DEAD | 0 | Expects different JSON schema |
| `step1_test_payload.py` | ~50 | DEAD | 0 | Test file, no production import |
| `step2_test_router.py` | ~80 | DEAD | 0 | Near-duplicate of main.py |

## Open questions / TODO
- Should decompose processor.py (2,542 lines) into smaller modules
- Remove dead code (legacy pipeline, simple_detector, io_visualization)
- Add version pinning to requirements.txt
- Add .dockerignore for build hygiene
