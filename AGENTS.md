# AGENTS.md — EdgeSDR-Nexus Monorepo

## Exploration Protocol (MANDATORY)

**Every AI agent MUST follow this order. No exceptions.**

### Step 1: Scaffold First (always)

Before touching ANY source code, grep, glob, or read a single file — read the scaffold. This is not optional. The scaffold IS your first exploration tool.

1. `scaffold/INDEX.md` — full map of all sections and sub-sections
2. `scaffold/_meta/cross-references.md` — section-to-section dependency map (which section calls which)
3. `scaffold/_meta/api-contracts.md` — all API endpoints in one table (find any endpoint instantly)
4. `scaffold/_meta/task-playbooks.md` — decision-tree playbooks for common tasks (finds exact files to touch)
5. `scaffold/<section>/main.md` — Layer 1 overview of the section you need
6. `scaffold/<section>/<sub>/main.md` — Layer 2 detail of the specific sub-section

**Why:** The scaffold contains purpose, tech stack, file structure, entry points, key interactions, common tasks, file criticality (hot paths + dead code), and open questions for every section. It was built so you understand structure WITHOUT reading source files.

### Step 2: Source Code (only after scaffold)

**Only after** reading the relevant scaffold docs, use standard tools as a FALLBACK:
- `Grep` / `rg` — find symbols, functions, patterns
- `Glob` — find files by name
- `Read` — read specific files for implementation details

**Never skip scaffold to go straight to grep.** You'll waste tokens and miss context. The scaffold already has what you need — use it.

### Step 3: Verify claims

If the scaffold says something and the code seems different, trust the code — but update the scaffold afterward.

## Repo Map

| Section | Purpose | Docs |
|---------|---------|------|
| frontend | React/Vite TypeScript SPA — operator dashboard | [scaffold/frontend/main.md](scaffold/frontend/main.md) |
| backend | Node.js/TypeScript REST API — sensor ingestion, CRUD, campaigns, reports | [scaffold/backend/main.md](scaffold/backend/main.md) |
| postprocesamiento | Python Flask microservice — spectral analysis, compliance | [scaffold/postprocesamiento/main.md](scaffold/postprocesamiento/main.md) |
| edge | Raspberry Pi 5 sensor — C99 RF engine + Python orchestrator | [scaffold/edge/main.md](scaffold/edge/main.md) |
| infra | Docker Compose, nginx, deployment scripts | [scaffold/infra/main.md](scaffold/infra/main.md) |

Full index: [scaffold/INDEX.md](scaffold/INDEX.md)

## Key Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview and quick start |
| `README_PLATFORM.md` | Platform overview (regulatory body, data flow, Spanish) |
| `docker-compose.yml` | Service orchestration |
| `Edge-Node/AGENTS.md` | AI agent entry point for edge node only |
| `scaffold/_meta/manifest.json` | Machine-readable scaffold index |
| `scaffold/_meta/cross-references.md` | Section-to-section dependency map |
| `scaffold/_meta/api-contracts.md` | Centralized API endpoint index (43 endpoints) |
| `scaffold/_meta/task-playbooks.md` | Common task decision trees |
| `scaffold/_meta/verify-scaffold.js` | Scaffold integrity checker |
| `scaffold/_meta/exploration-log.md` | Raw exploration findings (use scaffold instead) |
