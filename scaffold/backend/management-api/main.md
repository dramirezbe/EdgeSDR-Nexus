# Management API — Layer 3

> Parent: [../main.md](../main.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Frontend-facing CRUD operations for sensors, antennas, users, alerts, and system configuration. Handles authentication, authorization, and user management.

## Tech stack & conventions
- Express routes at `/api/*`, `/api/auth/*`, `/api/config/*`
- JWT authentication via `jose` (Azure AD) and `jsonwebtoken` (local)
- bcrypt for password hashing
- Two roles: `administrador`, `tecnico`

## Structure
```
management-api/
├── management.ts   # Sensor + antenna + alert CRUD (/api/sensors, /api/antennas, /api/alerts)
├── auth.ts         # Authentication + user management (/api/auth/*)
└── config.ts       # System configuration key-value store (/api/config)
```

## Entry points
- `management.ts`: mounted at `/api` in app.ts (LAST to avoid route conflicts)
- `auth.ts`: mounted at `/api/auth` in app.ts
- `config.ts`: mounted at `/api/config` in app.ts

## Key interactions
- **Frontend -> Backend:** Full CRUD for sensors, antennas, users
- **Frontend -> Backend:** Login (local + Azure AD), get current user, change password
- **Frontend -> Backend:** Get/update system configuration
- **Auth middleware:** `authenticateToken` (JWT verification), `requireAdmin` (role check), `requireRoles(...roles)`
- **Azure AD flow:** Frontend sends Azure ID token -> backend validates via JWKS -> auto-creates user if not exists -> returns local JWT

## Common tasks & gotchas
- `management.ts` is mounted LAST in app.ts to prevent route conflicts with more specific routes
- `DELETE /api/sensors/:id` and `DELETE /api/antennas/:id` have NO auth middleware — security gap
- `GET/POST /api/config` has NO auth middleware — system config is world-readable/writable
- JWT_SECRET fallback is hardcoded string `'ane-secret-key-change-in-production'`
- CORS is wide open (`cors()` with no config) — any origin can call the API
- Alert deduplication: `shouldCreateAlert()` prevents same alert type within configurable timeout (30min default)

## Open questions / TODO
- Missing auth on DELETE endpoints is a security vulnerability
- No rate limiting on any endpoint
- No audit logging for user management actions
- `requireRoles` is implemented but not used anywhere — only `requireAdmin` is used
