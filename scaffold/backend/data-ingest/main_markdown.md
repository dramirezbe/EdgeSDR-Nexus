# Data Ingest — Layer 3

> Parent: [../main_markdown.md](../main_markdown.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Sensor-to-server data ingestion: receiving heartbeat status, GPS location, spectrum data, and scan configuration from physical sensors. Also handles the realtime config endpoint that sensors poll.

## Tech stack & conventions
- Express routes at `/api/sensor/*`
- PostgreSQL via raw SQL (`pg` Pool)
- In-memory LRU-like cache (100 items per MAC) for realtime polling
- 30s heartbeat-based status validation with alert generation

## Structure
```
data-ingest/
└── sensor.ts   # Sensor data routes: POST status/gps/data/audio, GET config/realtime/campaigns
```

## Entry points
- `sensor.ts`: mounted at `/api/sensor` in app.ts

## Key interactions
- **Physical sensors -> Backend:** `POST /api/sensor/status` (heartbeat every ~10s), `POST /api/sensor/gps`, `POST /api/sensor/data` (spectrum frames every 1-2s)
- **Physical sensors <- Backend:** `GET /api/sensor/:mac/realtime` (polling for active config), `GET /api/sensor/:mac/campaigns` (polling for assigned campaigns)
- **Frontend <- Backend:** `GET /api/sensor/:mac/latest-data` (polling for monitoring display), `GET /api/sensor/:mac/latest-status`, `GET /api/sensor/:mac/latest-gps`
- **Data storage:** spectrum data stored in `sensor_data` table (TimescaleDB hypertable), status in `sensor_status`, GPS in `sensor_gps`
- **WebSocket broadcast:** status, GPS, and spectrum data broadcast to all connected frontend clients

## Common tasks & gotchas
- Sensor data endpoint (`POST /api/sensor/data`) has complex logic: auto-detects campaign_id by matching center frequency within 5kHz tolerance
- `sensor_configurations` table stores active config per sensor — sensors poll this via `GET /api/sensor/:mac/realtime`
- `POST /api/sensor/:mac/configure` broadcasts config via WebSocket AND saves to database
- `POST /api/sensor/:mac/stop` broadcasts stop command AND resets configuration
- Auto-stop monitoring: `setInterval` checks if monitoring has exceeded max time

## Open questions / TODO
- No authentication on sensor-facing endpoints (by design — physical sensors can't carry JWT)
- `pxx` column stores FFT arrays as TEXT (stringified JSON), not native PostgreSQL array
- Duplicate route definition for `GET /api/sensor/:mac/latest-data` — may cause Express routing issues
- Campaign ID auto-detection uses 5kHz frequency tolerance — undocumented in API contract
