# Scaffold INDEX

> Last audited: 2026-08-31 @ commit dc6c386

## Layer 1 — Section Map

| Section | Purpose | Docs |
|---------|---------|------|
| frontend | React/Vite TypeScript SPA — operator dashboard for monitoring, campaigns, alerts | [scaffold/frontend/main_markdown.md](scaffold/frontend/main_markdown.md) |
| backend | Node.js/TypeScript API — sensor ingestion, CRUD, campaigns, reports, WebSocket | [scaffold/backend/main_markdown.md](scaffold/backend/main_markdown.md) |
| postprocesamiento | Python Flask microservice — spectral analysis, emission detection, compliance | [scaffold/postprocesamiento/main_markdown.md](scaffold/postprocesamiento/main_markdown.md) |
| edge | Raspberry Pi 5 sensor — C99 RF engine + Python orchestrator | [scaffold/edge/main_markdown.md](scaffold/edge/main_markdown.md) |
| infra | Docker Compose, nginx, deployment scripts | [scaffold/infra/main_markdown.md](scaffold/infra/main_markdown.md) |

## Layer 2 — Section Summaries

### frontend
7 sub-sections: [auth](scaffold/frontend/auth/main_markdown.md) | [monitoring](scaffold/frontend/monitoring/main_markdown.md) | [campaigns](scaffold/frontend/campaigns/main_markdown.md) | [network](scaffold/frontend/network/main_markdown.md) | [admin](scaffold/frontend/admin/main_markdown.md) | [audio](scaffold/frontend/audio/main_markdown.md) | [core](scaffold/frontend/core/main_markdown.md)

### backend
6 sub-sections: [data-ingest](scaffold/backend/data-ingest/main_markdown.md) | [management-api](scaffold/backend/management-api/main_markdown.md) | [campaigns](scaffold/backend/campaigns/main_markdown.md) | [reports](scaffold/backend/reports/main_markdown.md) | [websocket](scaffold/backend/websocket/main_markdown.md) | [models](scaffold/backend/models/main_markdown.md)

### postprocesamiento
6 sub-sections: [server](scaffold/postprocesamiento/server/main_markdown.md) | [cli](scaffold/postprocesamiento/cli/main_markdown.md) | [core](scaffold/postprocesamiento/core/main_markdown.md) | [spectral](scaffold/postprocesamiento/spectral/main_markdown.md) | [calibration](scaffold/postprocesamiento/calibration/main_markdown.md) | [utils](scaffold/postprocesamiento/utils/main_markdown.md)

### edge
6 sub-sections: [rf-engine](scaffold/edge/rf-engine/main_markdown.md) | [python-services](scaffold/edge/python-services/main_markdown.md) | [utils](scaffold/edge/utils/main_markdown.md) | [build-deploy](scaffold/edge/build-deploy/main_markdown.md) | [gps-lte](scaffold/edge/gps-lte/main_markdown.md) | [context](scaffold/edge/context/main_markdown.md)

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
| `SCAFFOLD_PLAN.md` | Task tracking for this scaffold system |
| `docker-compose.yml` | Service orchestration |
| `Edge-Node/AGENTS.md` | AI agent entry point for edge node |
| `scaffold/_meta/manifest.json` | Machine-readable scaffold index |
| `scaffold/_meta/exploration-log.md` | Raw exploration findings |
