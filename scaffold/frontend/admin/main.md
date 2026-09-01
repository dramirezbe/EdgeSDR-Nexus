# Admin — Layer 3

> Parent: [../main.md](../main.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Administrative management: antenna CRUD, sensor CRUD, user management, and system configuration.

## Tech stack & conventions
- Standard CRUD forms with validation
- Admin-only features gated by `isAdmin` prop from AuthContext
- Tailwind CSS for form layout

## Structure
```
admin/
├── AntennaManagement.tsx   # Antenna CRUD (410 lines)
└── UserManagement.tsx      # User CRUD + role management (358 lines)
```

## Entry points
- `AntennaManagement.tsx`: rendered in App.tsx when `activeTab === 'configuracion'`
- `UserManagement.tsx`: rendered in App.tsx when `activeTab === 'configuracion'`

## Key interactions
- **Frontend -> Backend:** `GET/POST/PUT/DELETE /api/antennas` (antenna CRUD)
- **Frontend -> Backend:** `GET/POST/PUT/DELETE /api/auth/users` (user CRUD, admin only)
- **Frontend -> Backend:** `POST /api/auth/change-password` (self-service password change)
- **Frontend -> Backend:** `GET/POST /api/config` (system configuration key-value)
- **Sensor management:** Also in App.tsx config tab (add/edit/delete sensors)

## Common tasks & gotchas
- Antenna management includes sensor-antenna assignment (port-based)
- User management requires `administrador` role — enforced by backend middleware
- System configuration includes: max_monitoring_time_min, center_freq_tolerance_khz, bandwidth_tolerance_khz
- Sensor CRUD is in App.tsx directly, not in a separate component

## Open questions / TODO
- Sensor management code is embedded in App.tsx (1359 lines) — should be extracted to a dedicated component
- No bulk operations for antennas or users
- No audit log display in the UI (backend has sensor_history_alert table)
