# Core — Layer 2

> Parent: [../main.md](../main.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Application shell: entry point, routing, main dashboard component, navigation sidebar, and shared API client.

## Tech stack & conventions
- React 19 with StrictMode
- react-router-dom ^7.10.1 for routing
- axios ^1.7.9 with interceptors for API communication
- Tailwind CSS for layout
- Tab-based navigation (state-driven, not route-driven)

## Structure
```
core/
├── main.tsx       # ★ ENTRY POINT: MSAL init, BrowserRouter, Routes (128 lines)
├── App.tsx        # ★ MAIN COMPONENT: AuthenticatedApp, dashboard, all tab views (1359 lines)
├── Sidebar.tsx    # Navigation sidebar (87 lines)
└── api.ts         # ★ API CLIENT: all REST endpoints, TypeScript interfaces (237 lines)
```

## Entry points
- `main.tsx`: initializes MSAL, renders BrowserRouter with Routes
- `App.tsx`: main dashboard component, manages all application state
- `api.ts`: exports `sensorAPI`, `antennaAPI`, `sensorDataAPI`, `statisticsAPI`, `configAPI`, `alertsAPI`

## Key interactions
- **Routing:** `/login` (public), `/azure-callback` (public), `/` (protected), `/audio/:sensorId` (protected)
- **Tab navigation:** `inicio`, `dispositivos`, `monitoreo`, `campañas`, `alertas`, `configuracion`, `ayuda`
- **State management:** No external library — all state in App.tsx via useState, passed as props
- **API client:** axios with Bearer token interceptor, base URL detection (localhost vs production)

## Common tasks & gotchas
- App.tsx at 1359 lines is the central hub — manages sensors, campaigns, config, WebSocket, waterfall state
- Tab navigation is state-driven (`activeTab`), not URL-based — only `/` route, no deep linking
- Monitoring stop requires confirmation dialog when switching tabs
- WebSocket connection is established in App.tsx when monitoring is active
- `API_BASE_URL` auto-detects: localhost uses direct backend, production uses relative `/api` (nginx proxy)

## Open questions / TODO
- App.tsx is monolithic — should be decomposed into smaller components
- No error boundaries for graceful error handling
- No loading states for initial data fetch
- No deep linking — all tabs are on the same URL
