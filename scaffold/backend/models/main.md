# Models — Layer 2

> Parent: [../main.md](../main.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Data layer: TypeScript models wrapping PostgreSQL queries, type definitions, and database migration/connection infrastructure.

## Tech stack & conventions
- Raw SQL via `pg` Pool (no ORM)
- Static class methods for all model operations
- PostgreSQL with TimescaleDB for time-series data
- `connection.ts` provides `query()`, `getClient()`, and legacy `dbRun/dbGet/dbAll` compatibility wrappers

## Structure
```
models/
├── Sensor.ts               # sensors table: CRUD + status validation + heartbeat logic
├── Antenna.ts              # antennas + sensor_antennas tables: CRUD + assignment
├── SensorData.ts           # sensor_status, sensor_gps, sensor_data, sensor_configurations
├── SensorHistoryAlert.ts   # sensor_history_alert: alert creation with dedup
types/
├── index.ts                # TypeScript interfaces: Sensor, Antenna, SensorData, Campaign, etc.
└── express.d.ts            # Express User augmentation (id, username, role, full_name, email)
database/
├── connection.ts           # pg.Pool, query(), getClient(), compatibility wrappers
├── migrate-postgres.ts     # PostgreSQL migration: all tables, indexes, TimescaleDB hypertable
├── migrate.ts              # Legacy SQLite migration (excluded from build)
├── seed.ts                 # Seed data: 3 sensors, 4 antennas, assignments
└── [~20 ad-hoc scripts]    # One-off ALTER TABLE migrations
```

## Entry points
- `migrate-postgres.ts`: called from app.ts `initDatabase()` on startup
- `connection.ts`: imported by all models

## Key interactions
- **All routes** import models for database operations
- **SensorData** has in-memory cache (100 items per MAC) for realtime polling
- **Sensor** has `validateAndUpdateStatus()` called every 30s by app.ts timer
- **SensorHistoryAlert** has `shouldCreateAlert()` for deduplication (30min default timeout)

## Database Schema

| Table | Purpose | Key Relationships |
|-------|---------|-------------------|
| `sensors` | Registered sensors | PK: id, UNIQUE: mac |
| `antennas` | Registered antennas | PK: id |
| `sensor_antennas` | Many-to-many sensor<->antenna with port | FK: sensor_id, antenna_id |
| `sensor_status` | Time-series heartbeat/metrics | FK: mac -> sensors(mac) |
| `sensor_gps` | GPS location history | FK: mac -> sensors(mac) |
| `sensor_data` | Spectrum measurements (TimescaleDB hypertable) | FK: mac -> sensors(mac) |
| `sensor_configurations` | Active scan configs per sensor | FK: mac -> sensors(mac) |
| `users` | Application users | PK: id, UNIQUE: username, email |
| `campaigns` | Measurement campaigns | PK: id, FK: created_by -> users |
| `campaign_sensors` | Many-to-many campaign<->sensor | FK: campaign_id, sensor_mac |
| `system_configurations` | Key-value system settings | PK: key |
| `sensor_history_alert` | Alert history with dedup | by sensor_mac + alert_type |
| `compliance_reports_cache` | Cached compliance reports | PK: campaign_id |

## Common tasks & gotchas
- `sensor_data.pxx` stores FFT arrays as TEXT (stringified JSON), not native PostgreSQL array
- `is_active` in `sensor_configurations` uses INTEGER (0/1), inconsistent with `users.is_active` BOOLEAN
- `created_at`/`updated_at` are BIGINT (epoch ms) for sensor tables, TIMESTAMP for users/campaigns
- TimescaleDB hypertable on `sensor_data` with 7-day compression policy
- Legacy SQLite migration (`migrate.ts`) is dead code — excluded from tsconfig build
- ~20 ad-hoc SQL scripts at root level — no proper migration system

## Open questions / TODO
- Inconsistent time representation (BIGINT vs TIMESTAMP) across schema
- No migration versioning system — ad-hoc scripts are fragile
- In-memory cache has no TTL — relies on sensor sending new data
- `seed.ts` still references SQLite patterns — needs PostgreSQL update
