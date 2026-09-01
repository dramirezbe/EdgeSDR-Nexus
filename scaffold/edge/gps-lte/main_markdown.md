# GPS/LTE — Layer 3

> Parent: [../main_markdown.md](../main_markdown.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
C99 GPS and LTE modules: acquires GPS location data and LTE signal information for sensor positioning and connectivity monitoring.

## Tech stack & conventions
- C99 with POSIX APIs
- Separate binary (`ltegps_app`) from RF engine
- Runs as independent systemd service
- Writes location to shared memory via `ShmStore` (Python-side)

## Structure
```
gps-lte/
├── gps-lte.c           # ★ C ENTRY: GPS + LTE acquisition loop
└── libs/
    ├── bacn_GPS.{c,h}  # GPS module (serial/NMEA parsing)
    ├── bacn_LTE.{c,h}  # LTE signal monitoring
    └── utils.{c,h}     # GPS/LTE utility functions
```

## Entry points
- `gps-lte/gps-lte.c` main(): GPS + LTE acquisition loop

## Key interactions
- **GPS data -> Backend:** Python orchestrator sends `POST /api/sensor/gps` with coordinates
- **GPS data -> Shared memory:** Written to `/dev/shm/persistent.json` via ShmStore
- **Independent from RF engine:** Runs as separate process, no direct C-to-C communication
- **LTE signal:** Monitored for connectivity quality reporting

## Common tasks & gotchas
- Runs as separate systemd service (`ltegps-ane2.service`)
- Not stopped during RF engine restarts (excluded from service stop sequence)
- Binary placed in repo root by `build.sh`, gitignored
- GPS coordinates used for sensor location tracking on frontend map

## Open questions / TODO
- GPS module details not fully documented in context/
- LTE module purpose unclear — may be for connectivity monitoring only
- No error recovery documentation for GPS hardware failures
