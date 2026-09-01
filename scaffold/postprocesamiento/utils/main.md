# Utils — Layer 2

> Parent: [../main.md](../main.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Low-level DSP utilities: PSD smoothing, noise floor estimation, channel detection, region analysis, and visualization helpers.

## Tech stack & conventions
- NumPy for numerical computation
- SciPy for Savitzky-Golay filtering
- matplotlib for visualization (optional, not used in production)
- Pure functions — no I/O or network calls

## Structure
```
utils/
├── __init__.py               # Re-exports all util functions
├── signal_processing.py      # Savitzky-Golay smoothing + basic DSP (73 lines)
├── noise_floor.py            # Percentile-histogram noise floor (48 lines)
├── channel_detection.py      # Mask-based region detection (143 lines)
├── region_analysis.py        # Valley splitting + adaptive NF (850 lines)
└── io_visualization.py       # JSON reader + matplotlib plotting (120 lines, dead code)
```

## Entry points
- Called by `processor.py` via `_run_new_detector_on_frame()`
- All functions are imported via `utils/__init__.py`

## Key functions

### signal_processing.py
- `smooth_psd()` — Savitzky-Golay smoothing with configurable window
- `estimate_local_trend()` — local polynomial trend estimation
- `find_local_minima_indices()` — find valleys in PSD

### noise_floor.py
- `detect_noise_floor_from_psd()` — percentile-histogram noise floor estimation

### channel_detection.py
- `detect_channels_from_psd()` — initial region detection with scalar threshold
- `detect_channels_from_variable_threshold()` — detection with adaptive step noise floor
- `contiguous_regions()` — find contiguous above-threshold regions
- `merge_and_filter_regions()` — merge close regions, filter by minimum width

### region_analysis.py
- `build_step_noise_floor()` — local noise floor refinement per region
- `split_wide_regions_by_internal_valleys()` — split multi-emission regions
- `find_adaptive_expansion_bins()` — adaptive region expansion
- `expand_region_adaptively()` — expand region boundaries

### io_visualization.py (dead code)
- `read_psd_json()` — reads different JSON schema (not used by server/CLI)
- `plot_psd_result()` — matplotlib visualization (not used in production)

## Key interactions
- **Called by:** `processor.py` (`_run_new_detector_on_frame()`)
- **Calls:** Nothing (leaf functions, pure computation)

## Common tasks & gotchas
- `io_visualization.py` expects a different JSON schema than the sensor payload format — dead code from notebook workflow
- `region_analysis.py` at 850 lines is the largest utility — handles complex region splitting logic
- All functions are stateless — no shared state between calls

## Open questions / TODO
- `io_visualization.py` should be removed or moved to a separate notebook/tools directory
- No unit tests for any utility functions
- `region_analysis.py` is complex — should be documented or decomposed
