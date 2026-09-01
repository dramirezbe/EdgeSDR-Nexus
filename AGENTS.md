# AGENTS.md — EdgeSDR-Nexus Monorepo

## Exploration Protocol (MANDATORY)

**Every AI agent MUST follow this order. No exceptions.**

### Step 1: Scaffold First (always)

Before touching any source code, read the scaffold:

1. `scaffold/INDEX.md` — full map of all sections and sub-sections
2. `scaffold/<section>/main_markdown.md` — Layer 1 overview of the section you need
3. `scaffold/<section>/<sub>/main_markdown.md` — Layer 3 detail of the specific sub-section

**Why:** The scaffold was built to let you understand structure without reading every file. It contains purpose, tech stack, file structure, entry points, key interactions, common tasks, and open questions for every section.

### Step 2: Source Code (only after scaffold)

Only after reading the relevant scaffold docs, use standard tools:
- `Grep` / `rg` — find symbols, functions, patterns
- `Glob` — find files by name
- `Read` — read specific files for implementation details

**Never skip scaffold to go straight to grep.** You'll waste tokens and miss context.

### Step 3: Verify claims

If the scaffold says something and the code seems different, trust the code — but update the scaffold afterward.

## Repo Map

| Section | Purpose | Docs |
|---------|---------|------|
| frontend | React/Vite TypeScript SPA — operator dashboard | [scaffold/frontend/main_markdown.md](scaffold/frontend/main_markdown.md) |
| backend | Node.js/TypeScript REST API — sensor ingestion, CRUD, campaigns, reports | [scaffold/backend/main_markdown.md](scaffold/backend/main_markdown.md) |
| postprocesamiento | Python Flask microservice — spectral analysis, compliance | [scaffold/postprocesamiento/main_markdown.md](scaffold/postprocesamiento/main_markdown.md) |
| edge | Raspberry Pi 5 sensor — C99 RF engine + Python orchestrator | [scaffold/edge/main_markdown.md](scaffold/edge/main_markdown.md) |
| infra | Docker Compose, nginx, deployment scripts | [scaffold/infra/main_markdown.md](scaffold/infra/main_markdown.md) |

Full index: [scaffold/INDEX.md](scaffold/INDEX.md)

## Key Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview and quick start |
| `README_PLATFORM.md` | Platform overview (ANE, data flow, Spanish) |
| `docker-compose.yml` | Service orchestration |
| `Edge-Node/AGENTS.md` | AI agent entry point for edge node only |
| `scaffold/_meta/manifest.json` | Machine-readable scaffold index |
| `scaffold/_meta/exploration-log.md` | Raw exploration findings |
