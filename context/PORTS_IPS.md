# PORTS_IPS.md — Server Network Inventory & Firewall Requirements

> Last verified: 2026-09-18 @ commit `530910f`
> Scope: frontend, nginx, backend, database, python-analysis, and the edge→backend
> boundary. Edge-internal DSP/RF subsystems are out of scope.
> All entries are derived from source code, compose files, and deployment docs —
> not from the scaffold prose. Evidence (`file:line`) is cited throughout.

---

## 1. Purpose

Single reference for:

- the runtime topology and end-to-end flows of the platform,
- every IP address and port the deployment uses,
- the ingress/egress rules the server needs to operate,
- the drift between documented behavior and actual code.

---

## 2. Service topology

```
Browser ── HTTPS :12443 ──▶ [external TLS proxy — NOT in this repo]
                                   │
                                   ▼
                         frontend nginx container :80
                         ├── /            → static React/Vite SPA
                         ├── /api/        → http://backend:3000/api/
                         └── /ws          → http://backend:3000/ws   (prefix match)
                                                  │
                                          ane-backend :3000  (Express + ws)
                                          ├── TCP ──▶ PostgreSQL   DB_HOST:DB_PORT
                                          ├── HTTP ─▶ python-analysis:8000 /analyze_batch
                                          └── HTTP ─▶ 172.23.80.220:4155 /localizar

Edge sensors ── HTTPS/WSS :12443 ──▶ [external entry] ──▶ frontend nginx :80 ──▶ backend :3000
```

nginx `location /ws` is a **prefix**, not an exact match, so it proxies `/ws`,
`/ws/audio/sensor/{id}`, `/ws/audio/listen/{id}` and `/ws/signal/{id}` all to
`backend:3000`.

---

## 3. Full flows

### 3.1 Frontend flow

```
index.html → main.tsx
   ├─ new PublicClientApplication(msalConfig)
   ├─ msalInstance.initialize() → handleRedirectPromise()
   │    └─ if redirect result: POST /api/auth/azure-login { access_token: idToken }
   │         → store localStorage.token/user → window.location='/' (hard reload)
   └─ renderApp(): StrictMode → MsalProvider → AuthProvider → BrowserRouter → Routes
        /login            → Login
        /azure-callback   → AzureCallback   (effectively shadowed — see §8)
        /                 → App  (soft-guarded: renders <Login> if !isAuthenticated)
        /audio/:sensorId  → AudioPage (no auth check)
```

- **Auth**: MSAL redirect → `main.tsx` consumes it and posts the **ID token** to
  `/api/auth/azure-login`; backend returns a local JWT stored in `localStorage.token`.
  Legacy form posts `/api/auth/login`. `GET /api/auth/me` validates on mount.
- **Navigation**: top-level is URL-based; the dashboard is **state-driven tabs**
  (`activeTab` in `App.tsx:48`) — no deep linking.
- **Data strategy**:
  - HTTP polling: spectrum `GET /sensor/:mac/latest-data` every **200 ms**
    (`useSpectrumData`), stats every **30 s**, sensor list every **30 s**.
  - WebSocket push on `/ws`: `sensor_status`, `sensor_gps`, `sensor_data`, `audio_data`.
  - WebRTC signaling on `/ws/signal/:id`; legacy PCM audio on `/ws/audio/listen/:id`.
- **42 distinct backend endpoints** reachable; 6 `api.ts` exports are never invoked.

### 3.2 Backend flow

```
app.ts
  imports evaluate FIRST (module-level side effects)
   ├─ sensor.ts:   setInterval(autoStopExpiredMonitoring, 15s)
   └─ campaign.ts: setInterval(updateCampaignStatuses, 60s) + immediate call
  dotenv.config()
  → express() + cors(open) + json(50mb) + logger
  → initDatabase()          ← NOT awaited (fire-and-forget)
  → setupSwagger()          → /api-docs, /api-docs.json
  → mount: /api/auth, /api/sensor, /api/campaigns, /api/reports, /api/config,
           then /api (management LAST)
  → /api/audio/status
  → 404 + error handler
  → http.createServer + setTimeout(1h)
  → initWebSocket (/ws) + setupAudioWebSocket (/ws/audio/sensor, /ws/audio/listen)
  → setInterval(validateStatus, 30s)
  → server.listen(3000)
```

- **Auth**: `POST /api/auth/azure-login` verifies Azure RS256 against remote JWKS,
  enforces `@ane.gov.co`, auto-creates users as `tecnico`, issues a **local** JWT (24h).
  Local login uses bcrypt. `authenticateToken` + `requireAdmin` guard ~24 routes.
  **All WebSockets are unauthenticated.**
- **Timers**: status validation 30 s (`app.ts`), monitoring auto-stop 15 s
  (`sensor.ts`), campaign status sweep 60 s (`campaign.ts`).
- **Outbound**: PostgreSQL `DB_HOST:5432`; Python `PYTHON_SERVICE_URL/analyze_batch`
  (4 parallel sub-batches, 1 h timeout); geolocation hardcoded at
  `172.23.80.220:4155`.

### 3.3 Cross-service integration

| Flow | Contract | Reality |
|---|---|---|
| **Edge → backend REST** | base `https://rsm.ane.gov.co:12443/api/sensor` | `GET /{mac}/realtime` (5 s), `GET /{mac}/campaigns` (60 s), `POST /data`, `POST /status` (30 s), `POST /gps` (C daemon, every 10 fixes) |
| **Edge → backend WS** | `wss://rsm.ane.gov.co:12443/ws/signal/{id}` | **backend does NOT implement `/ws/signal`** |
| **Backend → Python** | `PYTHON_SERVICE_URL/analyze_batch`; payload `{max_workers, frames:[{frame, cumplimiento, dane, danes, picos, umbral_db, delta_fc_khz, delta_bw_khz}]}`; response `{results:[...]}` | accurate; `/health` only used by Docker/compose healthchecks |
| **Backend → geolocation** | `http://172.23.80.220:4155/localizar` `{lat, lon}` → `resultado.central.codigo_dane` | accurate; 10 s timeout, no retry |
| **Backend → frontend** | `/ws` events | 8 emitted: `connected`, `sensor_status`, `sensor_gps`, `sensor_data`, `sensor_configure`, `sensor_stop`, `sensor_status_changed`, `audio_data` |

---

## 4. What each service needs / consumes

| Service | Needs (outbound) | Provides (inbound) |
|---|---|---|
| **frontend (nginx)** | `backend:3000`; browser needs `login.microsoftonline.com:443` | `80` — SPA + `/api/` + `/ws` proxy |
| **backend (Node)** | PostgreSQL `DB_HOST:DB_PORT`; `PYTHON_SERVICE_URL` (`8000`); geolocation `172.23.80.220:4155` | `3000` HTTP REST + `/ws`, `/ws/audio/sensor/{id}`, `/ws/audio/listen/{id}`, `/api-docs` |
| **python-analysis (gunicorn)** | nothing external (stateless; reads `licencias.csv`) | `8000` — `/health`, `/analyze_batch` |
| **PostgreSQL** | — | `5432` (data store) |
| **edge → backend only** | `https://rsm.ane.gov.co:12443/api/sensor` (`/data`, `/status`, `/gps`, `/campaigns`, `/realtime`) and `wss://rsm.ane.gov.co:12443/ws/signal/{id}` | — |
| **browser** | `rsm.ane.gov.co:12443`; Azure AD `:443`; OSM tiles `:443`; unpkg `:443` | — |

---

## 5. Final IP & port inventory

### 5.1 Published host ports (`docker-compose.yml`)

| Host port | Container port | Service |
|---|---|---|
| `80` | `80` | frontend / nginx |
| `3000` | `3000` | backend API + WebSocket |
| `8000` | `8000` | python-analysis |
| `5432` | `5432` | **local stack only** (`docker-compose.local.yml`) |

### 5.2 Container listeners

| Process | Listen |
|---|---|
| nginx | `80` (HTTP) |
| Node backend | `0.0.0.0:3000` (HTTP + WS upgrade) |
| gunicorn / Flask | `0.0.0.0:8000` |
| postgres:16 (local compose) | `5432` |

### 5.3 Production external endpoints

| Endpoint | Port | Used by |
|---|---|---|
| `https://rsm.ane.gov.co:12443` | **12443** | SPA, `/api/`, Azure redirect `…:12443/azure-callback` |
| `wss://rsm.ane.gov.co:12443/ws` + `/ws/audio/*` + `/ws/signal/*` | **12443** | frontend realtime/audio; edge WSS |
| `https://rsm.ane.gov.co:12443/api/sensor` | **12443** | edge REST (`Edge-Node/cfg.py`) |
| `http://rsm.ane.gov.co:3000` / `ws://…:3000/ws` | `3000` | listed in Swagger + API docs (direct backend) |

### 5.4 IPs

| IP | Role | Ports |
|---|---|---|
| `172.23.90.25` | Production app server (backend + Swagger + PostgreSQL) | `3000`, `5432` |
| `172.23.80.220` | Geolocation service (DANE code lookup) | `4155` |
| `127.0.0.1` | Dev loopback (backend / python / pg defaults) | `3000`, `8000`, `5432` |
| `login.microsoftonline.com` | Azure AD identity (outbound) | `443` |

### 5.5 Internal Docker DNS (`ane-network`)

`backend:3000` · `python-analysis:8000` · `postgres:5432` (local compose only)

---

## 6. Firewall requirements

### 6.1 Egress — external IPs/hosts the server MUST reach

| Destination | Port | Proto | Service | Evidence |
|---|---|---|---|---|
| `172.23.90.25` | `5432` | TCP | PostgreSQL (backend DB) | `docker-compose.yml` `DB_HOST`; README |
| `172.23.80.220` | `4155` | TCP | Geolocation / DANE lookup | hardcoded `backend/src/routes/reports.ts:227` |
| `login.microsoftonline.com` | `443` | TCP | Azure AD JWKS / token validation | `backend/src/middleware/azureAuth.ts:8` |
| `registry-1.docker.io`, `registry.npmjs.org`, `pypi.org` | `443` | TCP | **build-time only** (image builds) | Dockerfile / npm / pip |

That is the complete runtime egress set. Nothing else leaves the server.

> `172.23.90.25` appears to be the server itself (same IP as the Swagger host).
> If PostgreSQL is co-located, `5432` is host-local rather than a firewall rule —
> but the backend container resolves it as an external IP, so keep the path open.

### 6.2 Ingress — ports that must be OPEN on the server

| Port | Proto | Who connects | Purpose | Exposure |
|---|---|---|---|---|
| **`12443`** | TCP | Operator browsers (intranet/VPN) **and** edge sensors (field/LTE) | HTTPS SPA + `/api/*` + `/ws*` (incl. `/ws/signal`) | **PUBLIC / external — the only app port that must be reachable** |
| `80` | TCP | External TLS terminator on `12443` | frontend nginx (`80:80`) | Only if the terminator is a different host; a host-local proxy can use loopback |
| `3000` | TCP | — | backend direct | **Must be internal only.** Currently published; bypasses nginx |
| `8000` | TCP | backend → python | python-analysis | **Must be internal only.** Currently published |
| `5432` | TCP | backend/subnet only | PostgreSQL | **Restrict to the app subnet** |

### 6.3 Browser-side external (client network — NOT the server firewall)

| Destination | Port | Why |
|---|---|---|
| server on `12443` | TCP | the app itself |
| `login.microsoftonline.com` | `443` | Azure AD login/redirect |
| `{s}.tile.openstreetmap.org` | `443` | map tiles (`App.tsx:573`, `MonitoringNetwork.tsx:359`, `AlertsPanel.tsx:356`, `CampaignsList.tsx:614`) |
| `unpkg.com` | `443` | Leaflet marker icons (`MonitoringNetwork.tsx:11-13`) — markers break if blocked |

### 6.4 Copy-paste firewall summary

**Inbound (allow):**
```
12443/tcp  ← browsers + edge sensors   (public/VPN)
80/tcp     ← TLS terminator only       (if remote proxy)
3000/tcp, 8000/tcp, 5432/tcp  ← app subnet ONLY
```

**Outbound (allow):**
```
172.23.90.25:5432/tcp                PostgreSQL
172.23.80.220:4155/tcp               Geolocation/DANE
login.microsoftonline.com:443/tcp    Azure AD JWKS
*.docker.io, *.npmjs.org, pypi.org:443/tcp   (build only)
```

---

## 7. Documented vs actual (drift)

| Topic | Docs claim | Code reality |
|---|---|---|
| Whole-API auth | `API-DOCUMENTATION.md:172`: "requires no authentication, all endpoints public" | Full JWT + Azure AD implemented on ~24 routes |
| Management auth coverage | api-contracts: **80%** | **5/16 = 31%**; 3 DELETEs + all reads open |
| Reports auth | api-contracts: **100%** | **0/3** — no auth at all |
| Config auth | api-contracts: **100%**, `PUT` | **0/2**, actual method is `POST` |
| Campaign auth | api-contracts: **92%** | **77%**; `/parameters`, `/sensor/:mac/realtime`, `/signals` open |
| Endpoint inventory | api-contracts: 56 REST / 61 total; AGENTS/README: 43; cross-refs: 40+ | **59 real handlers**; 9 fabricated, 9 undocumented |
| Edge audio WS path | cross-refs: edge uses `/ws/audio/sensor/:id` | edge actually dials **`/ws/signal/{id}`** — handler absent everywhere |
| WS event catalog | 7 events | 10 events |
| DB backend | PostgreSQL, but env/structure still shows `DB_PATH=./data/ane.db` | PostgreSQL only at runtime |
| Build config | scaffold: "`migrate.ts` dead, excluded from build" | **inverted**: `tsconfig.json` includes SQLite `migrate.ts`, excludes `migrate-postgres.ts`; `seed.ts` requires `./migrate` |
| API URL strategy | "auto-detects localhost vs relative `/api`" | only `api.ts` does; `AuthContext`/`UserManagement`/`main.tsx` hardcode `/api` |
| WS URL strategy | "nginx proxies `/ws` → backend:3000"; `VITE_WS_URL=/ws` | `VITE_WS_URL` never read; ports hardcoded (`:12443` https, `:3000` http, unconditional `:12443` in signaling/AnalysisPanel/WebRTCAudioPlayer) |
| Port | manual ops: `rsm.ane.gov.co:1280`; edge/frontend: `12443`; nginx/compose: `80`/`3000` | `1280` is stale; `12443` TLS terminator **not in repo** (nginx listens `80` only) |
| Dead code | "two `.bak` files; legacy AudioPlayer may be dead" | + `AudioPlayer.tsx` unused, 2 hooks unused, 6 api methods unused; `/change-password`, `/campaigns/:id/start`, `/signals` never called |

---

## 8. Known defects & open questions

1. **WebRTC audio signaling is dead.** Edge (`server_webrtc.py:37`) and frontend
   (`signaling.ts:32`) use `/ws/signal/{id}`; the backend registers only `/ws`,
   `/ws/audio/sensor/`, `/ws/audio/listen/`. The nginx `/ws` prefix forwards the
   path to `backend:3000`, where the upgrade falls through with no handler.
2. **Demod metrics silently dropped.** Edge sends scalar `excursion_hz`/`depth`;
   backend expects objects `data.excursion.{peak_to_peak_hz,…}` /
   `data.depth.{peak_to_peak,…}` → broadcast fields and DB columns stay null.
3. **Security gaps.** 3 unauthenticated DELETEs (`management.ts:236/395/587`),
   open `POST /api/config`, fully open reports router, unprotected campaign
   params/signals, zero WebSocket authentication.
4. **Latent build hazard.** `tsconfig.json` includes SQLite `migrate.ts` and
   excludes `migrate-postgres.ts`; `seed.ts` calls the SQLite path.
5. **Boot ordering.** Route modules' timers run during import, before
   `dotenv.config()` and before `initDatabase()` (not awaited).
6. **Frontend auth inconsistencies.** `/azure-callback` route is shadowed;
   `AzureCallback` waits on a `sessionStorage` key nothing writes; redirect sends
   an ID token while `AzureCallback` sends an access token; no MSAL logout, no
   refresh; `/audio/:sensorId` unauthenticated; 401/403 interceptor logs but does
   not log out.

### Open questions for the deployment/network team

- **What terminates TLS on `12443`?** It is absent from this repository
  (nginx `listen 80`; compose publishes `80/3000/8000/5432`).
- **Is `/ws/signal/{id}` served by that external proxy?** If not, edge WebRTC
  audio cannot work as checked in.

---

## 9. Evidence index

| Area | Files |
|---|---|
| Compose / orchestration | `docker-compose.yml`, `docker-compose.local.yml` |
| nginx | `frontend/nginx.conf`, `nginx.conf` (stale) |
| Frontend entry/auth | `frontend/src/main.tsx`, `authConfig.ts`, `contexts/AuthContext.tsx` |
| Frontend API/WS | `frontend/src/services/api.ts`, `hooks/useSpectrumData.ts`, `utils/signaling.ts`, `components/{MonitoringNetwork,AnalysisPanel,WebRTCAudioPlayer,AudioPlayer,AudioPlayerComponent}.tsx`, `pages/AudioPage.tsx` |
| Backend entry/WS | `backend/src/app.ts`, `websocket.ts`, `audioServer.ts`, `middleware/azureAuth.ts` |
| Backend routes/config | `backend/src/routes/*.ts`, `database/connection.ts`, `swagger.ts` |
| Outbound integrations | `backend/src/routes/reports.ts`, `backend/tsconfig.json`, `backend/src/database/seed.ts` |
| Python service | `postprocesamiento/server_flask.py`, `Dockerfile` |
| Edge → backend only | `Edge-Node/cfg.py`, `orchestrator.py`, `status.py`, `server_webrtc.py`, `gps-lte/gps-lte.c` |
