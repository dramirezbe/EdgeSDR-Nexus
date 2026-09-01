# Monitoring — Layer 2

> Parent: [../main.md](../main.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Real-time spectrum monitoring: configuration panel for scan parameters, spectrum visualization (Plotly), waterfall display, and data polling hook.

## Tech stack & conventions
- Plotly.js-dist-min ^3.4.0 for spectrum charts
- Custom waterfall component (canvas-based, no library)
- `useSpectrumData` hook for polling-based data fetching (200ms interval)
- WebSocket for supplementary data (GPS, status) — not primary spectrum
- Tailwind CSS for layout

## Structure
```
monitoring/
├── ConfigurationPanel.tsx   # Scan parameter controls (freq, span, gain, etc.)
├── AnalysisPanel.tsx        # Main monitoring display (683 lines)
├── SpectrumChart.tsx        # Plotly spectrum visualization (683 lines)
├── Waterfall.tsx            # Waterfall display (297 lines)
└── useSpectrumData.ts       # Polling hook: fetches spectrum data at 200ms intervals
```

## Entry points
- `AnalysisPanel.tsx`: rendered in App.tsx when `activeTab === 'monitoreo'`
- `useSpectrumData.ts`: called by App.tsx when monitoring is active

## Key interactions
- **Frontend -> Backend:** `GET /api/sensor/:mac/latest-data` (polling every 200ms via useSpectrumData)
- **Frontend -> Backend:** `POST /api/sensor/:mac/configure` (send scan configuration)
- **Frontend -> Backend:** `POST /api/sensor/:mac/stop` (stop acquisition)
- **Frontend <- Backend:** WebSocket `/ws` for `sensor_data`, `sensor_gps`, `sensor_status_changed` events
- **Configuration state:** managed in App.tsx, passed down as props to ConfigurationPanel
- **Spectrum data flow:** useSpectrumData -> App.tsx state -> AnalysisPanel -> SpectrumChart + Waterfall

## Common tasks & gotchas
- Spectrum data is fetched via HTTP polling (200ms), NOT WebSocket — WebSocket is used for audio and status
- Waterfall uses a grace window (3 frames) after config change to avoid stale data
- `cacheScopeKey` combines sensor MAC + preset to clear spectrum cache on scope changes
- Demodulation metrics (excursion_hz, depth) come from polling data, not WebSocket

## Open questions / TODO
- No WebSocket-based spectrum streaming (polling only) — may cause latency on slow networks
- Waterfall max 200 rows, oldest trimmed automatically
- AnalysisPanel manages audio playback via ref — cross-cutting concern with audio section
