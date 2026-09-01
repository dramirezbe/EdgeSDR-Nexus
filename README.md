# EdgeSDR-Nexus

Spectral monitoring platform for Colombia's National Spectrum Agency (ANE). Operates RF sensors, receives measurements, analyzes them, and produces monitoring, campaign, and compliance reports.

## Quick Start

1. **Understand the codebase first** — read `scaffold/INDEX.md` (the full map)
2. **For AI agents** — see `AGENTS.md` for mandatory exploration order
3. **Platform overview** — see `README_PLATFORM.md`

## Architecture

| Section | Purpose | Docs |
|---------|---------|------|
| frontend | React/Vite TypeScript SPA — operator dashboard | [scaffold/frontend/main_markdown.md](scaffold/frontend/main_markdown.md) |
| backend | Node.js/TypeScript REST API — sensor ingestion, CRUD, campaigns, reports | [scaffold/backend/main_markdown.md](scaffold/backend/main_markdown.md) |
| postprocesamiento | Python Flask microservice — spectral analysis, compliance | [scaffold/postprocesamiento/main_markdown.md](scaffold/postprocesamiento/main_markdown.md) |
| edge | Raspberry Pi 5 sensor — C99 RF engine + Python orchestrator | [scaffold/edge/main_markdown.md](scaffold/edge/main_markdown.md) |
| infra | Docker Compose, nginx, deployment scripts | [scaffold/infra/main_markdown.md](scaffold/infra/main_markdown.md) |

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

## Build & Run

```bash
# Docker (recommended)
docker-compose up -d

# Edge node (on Raspberry Pi 5)
cd Edge-Node
sudo ./install.sh
```
