# Frontend — Layer 1

> Parent: [../INDEX.md](../INDEX.md)
> Children: [auth](./auth/main.md), [monitoring](./monitoring/main.md), [campaigns](./campaigns/main.md), [network](./network/main.md), [admin](./admin/main.md), [audio](./audio/main.md), [core](./core/main.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
React/Vite TypeScript single-page application providing the operator dashboard for spectrum monitoring, campaign management, alerts, and administrative configuration.

## Tech stack & conventions
- React ^19.0.0 + TypeScript ^5.3.3 + Vite ^5.4.2
- Tailwind CSS ^3.4.1 for styling
- Azure AD SSO via MSAL ^5.0.2 (primary auth)
- Leaflet for maps, Plotly for charts, Recharts for statistics
- WebSocket for real-time data, HTTP polling for spectrum (200ms)
- State management: React Context + useState (no Redux/Zustand)

## Structure
```
frontend/
├── src/
│   ├── main.tsx           # Entry point: MSAL init, routing
│   ├── App.tsx            # Main dashboard (1359 lines, tab-based navigation)
│   ├── authConfig.ts      # Azure AD configuration
│   ├── contexts/          # AuthContext (login, logout, user state)
│   ├── hooks/             # useSpectrumData (polling hook)
│   ├── services/          # api.ts (all REST endpoints)
│   ├── components/        # 20 components (see sub-sections)
│   ├── pages/             # AudioPage (standalone route)
│   ├── images/            # Static assets
│   ├── styles/            # Additional CSS
│   └── utils/             # Utility functions
├── Dockerfile             # Multi-stage: node build -> nginx serve
├── nginx.conf             # Reverse proxy to backend:3000
├── package.json           # Dependencies and scripts
├── vite.config.ts         # Vite build configuration
├── tailwind.config.js     # Tailwind configuration
├── tsconfig.json          # TypeScript configuration
├── eslint.config.js       # ESLint configuration
├── .env.production        # Production environment variables
├── data/                  # Static data files
└── json/                  # JSON reference schemas
```

## Entry points
- `index.html` -> `src/main.tsx` -> MSAL init -> BrowserRouter -> Routes
- Protected route `/` renders `App.tsx` (requires authentication)
- Public routes: `/login`, `/azure-callback`

## Key interactions
- **Backend REST API:** Auth, sensors, campaigns, reports, config, alerts (see `api.ts`)
- **Backend WebSocket:** `/ws` for sensor data/status/GPS, `/ws/audio/listen/{id}` for audio
- **No direct database access** — all data via backend API
- **nginx proxy:** `/api/*` -> backend:3000, `/ws` -> backend:3000

## Common tasks & gotchas
- Tab-based navigation (state-driven, not URL-based) — no deep linking
- Spectrum monitoring uses HTTP polling (200ms), NOT WebSocket
- App.tsx is monolithic (1359 lines) — manages all dashboard state
- Two dead `.bak` files in components (SpectrumChart.canvas, Waterfall.canvas)
- No testing framework configured

## Open questions / TODO
- `@supabase/supabase-js` dependency — usage unclear, may be dead
- No error boundaries for graceful error handling
- No deep linking for tabs
- App.tsx should be decomposed into smaller components
