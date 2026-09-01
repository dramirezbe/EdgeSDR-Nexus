# Scaffold INDEX

> Last audited: 2026-08-31 @ commit dc6c386

## Section Map

| Section | Purpose | Docs |
|---------|---------|------|
| frontend | React/Vite TypeScript SPA — operator dashboard for monitoring, campaigns, alerts | [scaffold/frontend/main.md](scaffold/frontend/main.md) |
| backend | Node.js/TypeScript API — sensor ingestion, CRUD, campaigns, reports, WebSocket | [scaffold/backend/main.md](scaffold/backend/main.md) |
| postprocesamiento | Python Flask microservice — spectral analysis, emission detection, compliance | [scaffold/postprocesamiento/main.md](scaffold/postprocesamiento/main.md) |
| edge | Raspberry Pi 5 sensor — C99 RF engine + Python orchestrator | [scaffold/edge/main.md](scaffold/edge/main.md) |
| infra | Docker Compose, nginx, deployment scripts | [scaffold/infra/main.md](scaffold/infra/main.md) |

## Section Summaries

### frontend
7 sub-sections: [auth](scaffold/frontend/auth/main.md) | [monitoring](scaffold/frontend/monitoring/main.md) | [campaigns](scaffold/frontend/campaigns/main.md) | [network](scaffold/frontend/network/main.md) | [admin](scaffold/frontend/admin/main.md) | [audio](scaffold/frontend/audio/main.md) | [core](scaffold/frontend/core/main.md)

### backend
6 sub-sections: [data-ingest](scaffold/backend/data-ingest/main.md) | [management-api](scaffold/backend/management-api/main.md) | [campaigns](scaffold/backend/campaigns/main.md) | [reports](scaffold/backend/reports/main.md) | [websocket](scaffold/backend/websocket/main.md) | [models](scaffold/backend/models/main.md)

### postprocesamiento
6 sub-sections: [server](scaffold/postprocesamiento/server/main.md) | [cli](scaffold/postprocesamiento/cli/main.md) | [core](scaffold/postprocesamiento/core/main.md) | [spectral](scaffold/postprocesamiento/spectral/main.md) | [calibration](scaffold/postprocesamiento/calibration/main.md) | [utils](scaffold/postprocesamiento/utils/main.md)

### edge
6 sub-sections: [rf-engine](scaffold/edge/rf-engine/main.md) | [python-services](scaffold/edge/python-services/main.md) | [utils](scaffold/edge/utils/main.md) | [build-deploy](scaffold/edge/build-deploy/main.md) | [gps-lte](scaffold/edge/gps-lte/main.md) | [context](scaffold/edge/context/main.md)

## Cross-Section Data Flow

```
Internet/Intranet :80
    |
    v
[frontend] (nginx:alpine, port 80)
    |--- /api/*  --->  [backend]  (Node.js/Express, port 3000)
    |--- /ws     --->  [backend]  (WebSocket upgrade)
    |--- /        --->  (static SPA assets)
                            |
                            |--- HTTP ---> [postprocesamiento] (Flask/gunicorn, port 8000)
                            |--- TCP ----> [PostgreSQL] (external, 172.23.90.25:5432)

[edge sensors] (Raspberry Pi 5, remote)
    |--- POST status/gps/data --->  [backend]
    |--- GET realtime/campaigns  <---  [backend]
    |--- Opus audio ---> [backend WebSocket] ---> [frontend WebRTC]
```

## Key Files

| File | Purpose |
|------|---------|
| `README.md` | High-level platform overview |
| `docker-compose.yml` | Service orchestration |
| `Edge-Node/AGENTS.md` | AI agent entry point for edge node |
| `scaffold/_meta/manifest.json` | Machine-readable scaffold index |
| `scaffold/_meta/exploration-log.md` | Raw exploration findings |
