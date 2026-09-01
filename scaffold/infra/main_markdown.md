# Infra — Layer 1

> Parent: [../INDEX.md](../INDEX.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Docker orchestration, nginx reverse proxy, and deployment/backup scripts for the ANE platform. Production target: single Debian server at `rsm.ane.gov.co`.

## Tech stack & conventions
- Docker Compose for multi-service orchestration
- nginx (alpine) for reverse proxy and static file serving
- Bash scripts for deployment and backup
- No CI/CD — entirely manual deployment
- Single bridge network (`ane-network`)

## Structure
```
(root level)
├── docker-compose.yml        # ★ PRIMARY: 3 services (frontend, backend, python-analysis)
├── Dockerfile                # ORPHANED: near-duplicate of frontend/Dockerfile (not used)
├── nginx.conf                # STALE: legacy copy (not used in builds)
├── .dockerignore             # Root-level ignore
├── deploy-server.sh          # Full server install (partially stale, references SQLite)
├── backup-production.sh      # Archive + delete source dirs (destructive)
├── install-backup-production.sh  # Copy fresh code to production
├── setup-backup-scheduler.sh # Cron template (prints instructions)
├── verify-backup-setup.sh    # 7-step backup health check
├── COMANDOS-SERVIDOR.txt     # Manual server commands reference
frontend/
├── Dockerfile                # Multi-stage: node build -> nginx serve
├── nginx.conf                # Active reverse proxy config (3600s API timeout)
├── .dockerignore
backend/
├── Dockerfile                # Multi-stage: node:18-alpine build
├── .dockerignore
postprocesamiento/
├── Dockerfile                # python:3.11-slim, gunicorn
└── (no .dockerignore)
```

## Docker Services

| Service | Container | Port | Depends On | Healthcheck |
|---------|-----------|------|------------|-------------|
| frontend | ane-frontend | 80:80 | backend | wget localhost |
| backend | ane-backend | 3000:3000 | python-analysis (healthy) | wget localhost:3000 |
| python-analysis | ane-python-analysis | 8000:8000 | — | curl /health |

## Network
- Single bridge: `ane-network`
- DNS: `backend`, `python-analysis` resolve within network
- `host.docker.internal:host-gateway` for backend to reach host services

## Nginx Routing

| Location | Target | Special |
|----------|--------|---------|
| `/` | Static SPA | `try_files $uri $uri/ /index.html` |
| `/api/` | `http://backend:3000/api/` | WebSocket upgrade, 3600s timeout |
| `/ws` | `http://backend:3000/ws` | WebSocket upgrade, 86400s timeout |
| `~*\.(jpg\|png\|css\|js\|...)$` | Cache | `expires 1y, immutable` |

## Deployment Flow
1. Build tar.gz locally
2. Copy to server
3. Run `deploy-server.sh` (installs Docker, builds, migrates, starts)

## Common tasks & gotchas
- **Hardcoded DB password** in docker-compose.yml (line 20)
- **Root Dockerfile is orphaned** — not referenced by compose
- **Two divergent nginx.conf** — root is stale, frontend is active
- **deploy-server.sh references SQLite** — stale from old architecture
- **No .dockerignore for postprocesamiento** — test files in image
- **No TLS/SSL** — port 80 exposed directly
- **Python service port 8000 exposed to host** — should be internal only

## Open questions / TODO
- Deploy script needs update for PostgreSQL architecture
- Add .dockerignore for postprocesamiento
- Implement TLS termination (Let's Encrypt or similar)
- Move DB password to Docker secrets or .env interpolation
- Remove orphaned root Dockerfile and stale nginx.conf
- Add database backup strategy (pg_dump)
- Consider CI/CD pipeline (GitHub Actions)
