# Calibration — Layer 2

> Parent: [../main.md](../main.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
License database I/O and compliance matching: loads Colombian radio license CSV, indexes by DANE code and frequency, and matches detected emissions against licensed parameters.

## Tech stack & conventions
- pandas for CSV loading and manipulation
- NumPy for fast frequency matching (sorted array search)
- `lru_cache` with mtime-based invalidation for lazy loading
- Three-tier caching: raw DataFrame -> DANE-indexed -> NumPy arrays

## Structure
```
calibration/
├── calibration_io.py               # License CSV I/O + matching (625 lines)
└── consolidado_bbdd_asignación.csv # 117,522 Colombian radio licenses
```

## Entry points
- Called by `processor.py` via `_match_licencia()` function

## Key functions
- `comparar_parametros()` — compare measured emission against license parameters
- `_power_to_dbm()` — power unit conversion
- `_bandwidth_to_khz_series()` — bandwidth unit normalization
- License CSV loading with `lru_cache` keyed on `(abs_path, mtime)`

## Key interactions
- **Called by:** `processor.py` in peaks and compliance modes
- **License CSV:** `consolidado_bbdd_asignación.csv` (117,522 rows) contains Colombian radio licenses
- **CSV columns:** `codigo_dane`, `frecuencia`, `ancho_de_banda`, `unidad_ancho_de_banda`, `potencia`, `unidad_potencia`, etc.
- **Matching:** Frequency tolerance (default 100kHz), bandwidth tolerance (default 10kHz)

## Common tasks & gotchas
- License CSV filename contains accented character (`asignación`) — can cause encoding issues
- Three-tier caching: raw DataFrame -> DANE-indexed dict -> NumPy sorted arrays for fast search
- Cache invalidation: `lru_cache` keyed on `(abs_path, mtime)` — re-reads CSV when file changes
- Docker copies CSV to `/opt/ane-realtime/data/licencias.csv` — path configured via `ANE_LIC_CSV` env var

## Open questions / TODO
- License CSV is static — no mechanism to update without rebuilding Docker image
- No validation of CSV schema on load
- `lru_cache` doesn't handle concurrent access (not thread-safe for gunicorn gthread workers)
