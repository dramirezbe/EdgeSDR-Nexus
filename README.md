# EdgeSDR-Nexus

Spectral monitoring platform for Colombia's regulatory body (regulatory body). Operates RF sensors, receives measurements, analyzes them, and produces monitoring, campaign, and compliance reports.

## Quick Start

1. **Understand the codebase first** — read `scaffold/INDEX.md` (the full map)
2. **For AI agents** — see `AGENTS.md` for mandatory exploration order
3. **Platform overview** — see `README_PLATFORM.md` (Spanish)

## Architecture

| Section | Purpose | Docs |
|---------|---------|------|
| frontend | React/Vite TypeScript SPA — operator dashboard | [scaffold/frontend/main.md](scaffold/frontend/main.md) |
| backend | Node.js/TypeScript REST API — sensor ingestion, CRUD, campaigns, reports | [scaffold/backend/main.md](scaffold/backend/main.md) |
| postprocesamiento | Python Flask microservice — spectral analysis, compliance | [scaffold/postprocesamiento/main.md](scaffold/postprocesamiento/main.md) |
| edge | Raspberry Pi 5 sensor — C99 RF engine + Python orchestrator | [scaffold/edge/main.md](scaffold/edge/main.md) |
| infra | Docker Compose, nginx, deployment scripts | [scaffold/infra/main.md](scaffold/infra/main.md) |

Full scaffold index: [scaffold/INDEX.md](scaffold/INDEX.md)

## Data Flow

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

## Documentation Map

### Core References

| File | Description |
|------|-------------|
| [AGENTS.md](AGENTS.md) | AI agent exploration protocol (scaffold-first) |
| [README_PLATFORM.md](README_PLATFORM.md) | Platform overview in Spanish |
| [scaffold/INDEX.md](scaffold/INDEX.md) | Full codebase map (all sections and sub-sections) |
| [scaffold/_meta/manifest.json](scaffold/_meta/manifest.json) | Machine-readable scaffold index |
| [scaffold/_meta/exploration-log.md](scaffold/_meta/exploration-log.md) | Raw exploration findings |

### Frontend

| File | Description |
|------|-------------|
| [frontend/DIAGRAM.md](frontend/DIAGRAM.md) | Frontend architecture diagram |
| [scaffold/frontend/main.md](scaffold/frontend/main.md) | Section overview |
| [scaffold/frontend/auth/main.md](scaffold/frontend/auth/main.md) | Authentication (Azure AD SSO) |
| [scaffold/frontend/monitoring/main.md](scaffold/frontend/monitoring/main.md) | Real-time spectrum monitoring |
| [scaffold/frontend/campaigns/main.md](scaffold/frontend/campaigns/main.md) | Campaign management |
| [scaffold/frontend/network/main.md](scaffold/frontend/network/main.md) | Sensor network map |
| [scaffold/frontend/admin/main.md](scaffold/frontend/admin/main.md) | Admin configuration |
| [scaffold/frontend/audio/main.md](scaffold/frontend/audio/main.md) | WebRTC audio streaming |
| [scaffold/frontend/core/main.md](scaffold/frontend/core/main.md) | App shell, routing, API client |

### Backend

| File | Description |
|------|-------------|
| [backend/README.md](backend/README.md) | Backend documentation |
| [backend/DIAGRAM.md](backend/DIAGRAM.md) | Backend architecture diagram |
| [backend/API-DOCUMENTATION.md](backend/API-DOCUMENTATION.md) | REST API reference |
| [backend/MIGRACION_POSTGRESQL.md](backend/MIGRACION_POSTGRESQL.md) | PostgreSQL migration guide |
| [backend/ENDPOINT_CAMPAIGNS_CAMBIOS.md](backend/ENDPOINT_CAMPAIGNS_CAMBIOS.md) | Campaigns endpoint changes |
| [backend/EJEMPLOS_CAMPAIGNS_ENDPOINT.md](backend/EJEMPLOS_CAMPAIGNS_ENDPOINT.md) | Campaigns endpoint examples |
| [backend/SIMULADOR_AM_FM.md](backend/SIMULADOR_AM_FM.md) | AM/FM simulator |
| [scaffold/backend/main.md](scaffold/backend/main.md) | Section overview |
| [scaffold/backend/data-ingest/main.md](scaffold/backend/data-ingest/main.md) | Sensor data ingestion |
| [scaffold/backend/management-api/main.md](scaffold/backend/management-api/main.md) | Management CRUD API |
| [scaffold/backend/campaigns/main.md](scaffold/backend/campaigns/main.md) | Campaign lifecycle |
| [scaffold/backend/reports/main.md](scaffold/backend/reports/main.md) | Compliance reports |
| [scaffold/backend/websocket/main.md](scaffold/backend/websocket/main.md) | WebSocket real-time |
| [scaffold/backend/models/main.md](scaffold/backend/models/main.md) | Data models and types |

### Postprocesamiento

| File | Description |
|------|-------------|
| [scaffold/postprocesamiento/main.md](scaffold/postprocesamiento/main.md) | Section overview |
| [scaffold/postprocesamiento/server/main.md](scaffold/postprocesamiento/server/main.md) | Flask HTTP server |
| [scaffold/postprocesamiento/cli/main.md](scaffold/postprocesamiento/cli/main.md) | Command-line interface |
| [scaffold/postprocesamiento/core/main.md](scaffold/postprocesamiento/core/main.md) | Detection pipeline |
| [scaffold/postprocesamiento/spectral/main.md](scaffold/postprocesamiento/spectral/main.md) | Signal processing |
| [scaffold/postprocesamiento/calibration/main.md](scaffold/postprocesamiento/calibration/main.md) | License compliance |
| [scaffold/postprocesamiento/utils/main.md](scaffold/postprocesamiento/utils/main.md) | DSP utilities |

### Edge Node

| File | Description |
|------|-------------|
| [Edge-Node/README.md](Edge-Node/README.md) | Edge node documentation |
| [Edge-Node/AGENTS.md](Edge-Node/AGENTS.md) | AI agent entry point for edge |
| [Edge-Node/context/RF_ENGINE.md](Edge-Node/context/RF_ENGINE.md) | RF engine architecture |
| [Edge-Node/context/PYTHON_SERVICES.md](Edge-Node/context/PYTHON_SERVICES.md) | Python services architecture |
| [Edge-Node/PROJECT_CONCEPTUAL_SUMMARY.md](Edge-Node/PROJECT_CONCEPTUAL_SUMMARY.md) | Project conceptual summary |
| [Edge-Node/daemons/README.md](Edge-Node/daemons/README.md) | Systemd units documentation |
| [Edge-Node/examples/BPFTRACE_USAGE.md](Edge-Node/examples/BPFTRACE_USAGE.md) | BPF tracing examples |
| [scaffold/edge/main.md](scaffold/edge/main.md) | Section overview |
| [scaffold/edge/rf-engine/main.md](scaffold/edge/rf-engine/main.md) | C99 RF engine |
| [scaffold/edge/python-services/main.md](scaffold/edge/python-services/main.md) | Python control plane |
| [scaffold/edge/utils/main.md](scaffold/edge/utils/main.md) | Shared utilities |
| [scaffold/edge/build-deploy/main.md](scaffold/edge/build-deploy/main.md) | Build and deployment |
| [scaffold/edge/gps-lte/main.md](scaffold/edge/gps-lte/main.md) | GPS/LTE modules |
| [scaffold/edge/context/main.md](scaffold/edge/context/main.md) | Architecture docs |

### Context & Analysis

| File | Description |
|------|-------------|
| [context/CURRENT_PLAT.md](context/CURRENT_PLAT.md) | Current platform state |
| [context/PLAT_PROCESSING.md](context/PLAT_PROCESSING.md) | Platform processing details |
| [context/PLATFORM_FRONTEND_CONTEXT.md](context/PLATFORM_FRONTEND_CONTEXT.md) | Frontend context |
| [context/PLATFORM_BACKEND_CONTEXT.md](context/PLATFORM_BACKEND_CONTEXT.md) | Backend context |
| [context/EDGE_NODE_PROCESSING.md](context/EDGE_NODE_PROCESSING.md) | Edge node processing |
| [context/DIAGRAM-FRONTEND.md](context/DIAGRAM-FRONTEND.md) | Frontend diagram |
| [context/DIAGRAM-BACKEND.md](context/DIAGRAM-BACKEND.md) | Backend diagram |
| [context/API-DOCUMENTATION-BACKEND.md](context/API-DOCUMENTATION-BACKEND.md) | API documentation |
| [context/db/README.md](context/db/README.md) | Database documentation |
| [context/db/tables.md](context/db/tables.md) | Database tables |
| [context/db/constraints.md](context/db/constraints.md) | Database constraints |
| [context/db/hypertables.md](context/db/hypertables.md) | TimescaleDB hypertables |
| [context/db/diagram.md](context/db/diagram.md) | Database diagram |
| [context/db/inventory.md](context/db/inventory.md) | Database inventory |

## Build & Run

```bash
# Docker (recommended)
docker-compose up -d

# Edge node (on Raspberry Pi 5)
cd Edge-Node
sudo ./install.sh
```
