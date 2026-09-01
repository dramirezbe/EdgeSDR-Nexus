# Scaffold System — Full Explanation

## What Is the Scaffold?

The scaffold is a **machine-readable, layered documentation system** that maps the entire EdgeSDR-Nexus codebase without requiring you to read every source file. It exists at `scaffold/` and is designed so that AI agents (and humans) can navigate a large, multi-service monorepo efficiently — understanding structure, purpose, entry points, and gotchas before touching any code.

**Think of it as an architect's blueprint for a building.** You don't walk through every room to understand the floor plan — you read the blueprint first, then go to the specific room you need.

---

## Design Philosophy

The scaffold was built with three constraints:

1. **AI agents have finite context windows.** Reading 30,000+ lines of source code to answer a simple question wastes tokens. The scaffold compresses the essential information into ~2,500 lines of markdown.

2. **Structure first, details second.** Every file follows the same template: Purpose → Tech Stack → Structure → Entry Points → Key Interactions → Gotchas → Open Questions. This consistency means you always know where to look.

3. **Hierarchical, not flat.** A monorepo with 5 services and 30+ sub-sections would be unreadable as a single document. The scaffold uses 3 layers so you zoom in progressively.

---

## The Three-Layer Architecture

### Layer 0 — Master Index (`scaffold/INDEX.md`)

**Purpose:** One page that shows the entire system at a glance.

- Lists all 5 sections (frontend, backend, postprocesamiento, edge, infra)
- Shows the cross-section data flow diagram (how services communicate)
- Links to key files (docker-compose, AGENTS.md, manifest.json)

**When to read it:** First thing, always. It answers "what services exist and how do they talk to each other?"

### Layer 1 — Section Summaries (`scaffold/<section>/main.md`)

**Purpose:** One page per service that answers "what does this service do, what is it built with, and what should I know before editing it?"

Each Layer 1 file contains:
- **Purpose** — one sentence on what the service does
- **Tech stack** — languages, frameworks, key libraries
- **Structure** — directory tree with annotations
- **Entry points** — where execution starts
- **Key interactions** — what calls what (other services, databases, APIs)
- **Common tasks & gotchas** — known pain points, anti-patterns, things that will bite you
- **Open questions** — unresolved issues, dead code, TODOs

**When to read it:** Before touching any file in that service. It gives you the context to understand what you're looking at.

### Layer 3 — Sub-Section Details (`scaffold/<section>/<sub>/main.md`)

**Purpose:** Deep dive into a specific functional area within a service.

For example, the frontend has 7 sub-sections:
- `auth` — Azure AD SSO, JWT, login/logout
- `monitoring` — Real-time spectrum display, configuration
- `campaigns` — Campaign lifecycle, data viewing, reports
- `network` — Sensor map visualization
- `admin` — Antenna and user management
- `audio` — WebRTC audio streaming
- `core` — App shell, routing, API client

Each Layer 3 file follows the same template as Layer 1 but zoomed into a specific concern. It tells you exactly which files implement that feature, how they interact, and what to watch out for.

**When to read it:** When you're about to modify a specific feature. It tells you which files to touch and which to leave alone.

---

## Navigation Flow

Here's how you're supposed to use the scaffold:

```
START HERE
    |
    v
scaffold/INDEX.md                    # "What services exist?"
    |
    v
scaffold/<section>/main.md  # "How is this service structured?"
    |
    v
scaffold/<section>/<sub>/main.md  # "What does this feature do?"
    |
    v
Source code (only now)               # "Let me read the actual implementation"
```

**NEVER skip straight to grep/find.** Always read the scaffold first. This is a hard rule in `AGENTS.md`.

---

## Machine-Readable Index (`scaffold/_meta/manifest.json`)

The manifest is a JSON file that lets code (or AI agents) programmatically navigate the scaffold. It lists every section with:
- `path` — file location
- `layer` — 0, 1, or 3
- `parent` — the section above it in the hierarchy
- `children` — sub-sections below it
- `purpose` — one-line description
- `last_audited_commit` — git commit when this section was last verified

**Example entry:**
```json
{
  "path": "scaffold/frontend/main.md",
  "layer": 1,
  "parent": "scaffold/INDEX.md",
  "children": [
    "scaffold/frontend/auth/main.md",
    "scaffold/frontend/monitoring/main.md",
    ...
  ],
  "purpose": "React/Vite TypeScript SPA operator dashboard",
  "last_audited_commit": "dc6c386"
}
```

---

## Exploration Log (`scaffold/_meta/exploration-log.md`)

This is the raw research that went into building the scaffold. It contains:
- Full directory trees for each service
- Complete tech stack inventories
- Entry point analysis
- Cross-section interaction maps
- Ambiguities and dead code discoveries
- Layer 3 sub-section proposals

**When to read it:** When you need more detail than Layer 1/3 provides. It has the "why" behind the structure decisions.

---

## Cross-Section Data Flow

The scaffold documents how services communicate:

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

This diagram tells you:
- Frontend never talks to the database directly — always through backend
- Backend calls the Python microservice for spectral analysis
- Edge sensors POST data to the backend and receive config via GET
- Audio flows: Edge (Opus) → Backend (WebSocket) → Frontend (WebRTC)

---

## The Template Every File Follows

Every `main.md` uses this exact structure:

```markdown
# <Name> — Layer <N>

> Parent: [link to parent]
> Children: [links to children] (Layer 1 only)
> Last audited: <date> @ commit <hash>

## Purpose
[One sentence]

## Tech stack & conventions
[Language, framework, key libraries]

## Structure
[Directory tree with annotations]

## Entry points
[Where execution starts]

## Key interactions
[What calls what — other services, databases, APIs]

## Common tasks & gotchas
[Known pain points, anti-patterns]

## Open questions / TODO
[Unresolved issues, dead code]
```

This consistency means you can scan any section quickly. You always know: "The gotchas are in the 'Common tasks & gotchas' section."

---

## Audit Trail

Every file tracks `last_audited_commit`. This means:
- If the scaffold says something but the code looks different, **trust the code** — the scaffold is stale
- After fixing a discrepancy, update the scaffold to match reality
- The commit hash lets you diff what changed since the last audit

---

## How to Read This System (TL;DR)

1. **First visit:** Read `scaffold/INDEX.md` — get the full map
2. **Before editing a service:** Read `scaffold/<section>/main.md` — understand the service
3. **Before editing a feature:** Read `scaffold/<section>/<sub>/main.md` — understand the specific code area
4. **If something seems wrong:** Check `scaffold/_meta/exploration-log.md` for the original research
5. **For programmatic access:** Use `scaffold/_meta/manifest.json` to navigate the hierarchy
6. **After making changes:** Update the scaffold to reflect reality

**The scaffold is not documentation you read once. It's documentation you navigate every time you work on the codebase.**
