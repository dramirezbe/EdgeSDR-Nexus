# Network — Layer 3

> Parent: [../main_markdown.md](../main_markdown.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Sensor network visualization: interactive map showing all registered sensors with their locations, status, and basic info.

## Tech stack & conventions
- Leaflet ^1.9.4 + react-leaflet ^5.0.0 for map rendering
- OpenStreetMap tiles
- Sensor status color coding: green (online), red (offline/other)

## Structure
```
network/
└── MonitoringNetwork.tsx   # Interactive map with sensor markers (789 lines)
```

## Entry points
- `MonitoringNetwork.tsx`: rendered in App.tsx when `activeTab === 'dispositivos'`

## Key interactions
- **Frontend -> Backend:** `GET /api/sensors` (list all sensors with lat/lng/status)
- **Frontend -> Backend:** `POST /api/sensors/validate-status` (trigger status check before display)
- **Map interaction:** Click marker -> popup with sensor name + description
- **Sensor selection:** Selecting a sensor updates App.tsx state for monitoring/campaigns

## Common tasks & gotchas
- Map centered on Colombia `[4.6097, -74.0817]` zoom level 6
- Sensors without lat/lng are not rendered on map
- Status validation is called on tab switch to ensure fresh status
- The component handles its own sensor list loading independently from App.tsx

## Open questions / TODO
- No clustering for dense sensor areas
- No sensor detail view (only popup with name/description)
- Map tile provider is hardcoded to OpenStreetMap (no offline/styled option)
