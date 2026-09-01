# Campaigns — Layer 3

> Parent: [../main_markdown.md](../main_markdown.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Campaign lifecycle management: CRUD, start/stop, status transitions, measurement data queries, and NDJSON streaming for large datasets.

## Tech stack & conventions
- Express routes at `/api/campaigns/*`
- PostgreSQL with transactions for campaign creation
- NDJSON streaming for large data responses
- America/Bogota timezone for status transitions
- `setInterval` (60s) for automatic status updates

## Structure
```
campaigns/
└── campaign.ts   # Campaign routes: CRUD + start/stop + data + statistics + NDJSON streaming
```

## Entry points
- `campaign.ts`: mounted at `/api/campaigns` in app.ts

## Key interactions
- **Frontend -> Backend:** Full campaign lifecycle (create, read, update, delete, start, stop)
- **Frontend -> Backend:** `GET /api/campaigns/:id/data` (measurement data for campaign+sensor)
- **Frontend -> Backend:** `GET /api/campaigns/statistics/summary` (dashboard stats)
- **Frontend -> Backend:** `GET /api/campaigns/sensor/:mac/signals` (NDJSON streaming for large datasets)
- **Physical sensors <- Backend:** `GET /api/sensor/:mac/campaigns` (sensor-facing format with RF params)
- **Auto-status:** `setInterval` (60s) checks campaign dates and transitions status automatically

## Common tasks & gotchas
- Campaign creation has conflict detection — checks for overlapping campaigns on the same sensor
- Status lifecycle: `scheduled -> running -> completed` with automatic date-based transitions
- `POST /api/campaigns/:id/start` sets status=running, `POST /api/campaigns/:id/stop` sets status=completed
- NDJSON streaming endpoint (`/signals`) supports both paginated JSON and streaming modes
- `requireAdmin` middleware on delete and stop operations
- Dynamic import `require('../models/Sensor')` used to avoid circular dependency — architectural smell

## Open questions / TODO
- Campaign data query (`/:id/data`) requires both campaignId and sensorMac — could be simplified
- No real-time campaign progress updates to frontend
- Automatic status transitions use `America/Bogota` timezone — hardcoded, not configurable
- Debug endpoint `/:mac/campaigns-debug` left in production code
