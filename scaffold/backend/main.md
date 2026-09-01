# Backend — Layer 1

> Parent: [../INDEX.md](../INDEX.md)
> Children: [data-ingest](./data-ingest/main.md), [management-api](./management-api/main.md), [campaigns](./campaigns/main.md), [reports](./reports/main.md), [websocket](./websocket/main.md), [models](./models/main.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Node.js/TypeScript REST API server: coordinates sensor data ingestion, user/frontend CRUD operations, campaign lifecycle, compliance reports, and real-time WebSocket communication.

## Tech stack & conventions
- Express ^4.18.2 + TypeScript ^5.3.3
- PostgreSQL via raw SQL (`pg` ^8.11.3) + TimescaleDB (optional)
- JWT auth (local + Azure AD via `jose`)
- WebSocket (`ws` ^8.18.3) for real-time data + audio
- Opus decoding (`opusscript`) for audio streaming
- Swagger/OpenAPI 3.0 for API documentation
- No ORM — raw SQL queries in static model classes

## Structure
```
backend/
├── src/
│   ├── app.ts              # ★ ENTRY POINT: Express, HTTP, WS, timers
│   ├── websocket.ts        # Main WebSocket (/ws)
│   ├── audioServer.ts      # Audio WebSocket (/ws/audio/*)
│   ├── swagger.ts          # Swagger setup
│   ├── middleware/          # auth.ts (JWT), azureAuth.ts (Azure AD JWKS)
│   ├── models/             # Sensor, Antenna, SensorData, SensorHistoryAlert
│   ├── routes/             # auth, sensor, management, campaign, reports, config
│   ├── types/              # TypeScript interfaces + Express augmentation
│   ├── database/           # connection, migrations, seed, ad-hoc scripts
│   ├── simulator/          # Sensor simulator for testing
│   └── scripts/            # Production migration runner
├── Dockerfile              # Multi-stage: node:18-alpine
├── package.json            # ane-backend v1.0.0
└── tsconfig.json           # ES2020, strict, commonjs
```

## Entry points
- `src/app.ts` -> `dist/app.js` (compiled)
- Startup: dotenv -> Express -> DB init -> Swagger -> routes -> WebSocket -> server.listen(3000)

## Key interactions
- **Physical sensors -> Backend:** POST status/gps/data, GET realtime/campaigns
- **Frontend -> Backend:** Full CRUD, auth, campaigns, reports, config
- **Backend -> Python:** POST /analyze_batch (compliance reports)
- **Backend -> Geolocation:** POST /localizar (DANE code resolution)
- **Backend -> Frontend:** WebSocket broadcasts (status, GPS, data, audio)

## Common tasks & gotchas
- No auth on sensor-facing endpoints (by design)
- CORS wide open — any origin can call API
- Hardcoded JWT_SECRET fallback
- Two migration systems (SQLite legacy + PostgreSQL current)
- ~20 ad-hoc SQL scripts at root level

## Open questions / TODO
- DELETE endpoints missing auth middleware
- No rate limiting
- Inconsistent time representation (BIGINT vs TIMESTAMP)
- No database backup strategy
