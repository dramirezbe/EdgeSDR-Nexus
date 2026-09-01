# Core — Layer 3

> Parent: [../main.md](../main.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Central orchestrator: routes processing mode, runs the detection pipeline, matches licenses, evaluates compliance, and enriches output with regulatory data.

## Tech stack & conventions
- Python with type hints (`from __future__ import annotations`)
- Spanish comments and user-facing strings (Colombian regulatory context)
- `lru_cache` for file I/O with mtime-based invalidation
- Three processing modes: `all_emissions`, `peaks`, `compliance`

## Structure
```
core/
├── processor.py   # Central orchestrator (2,542 lines)
```

## Entry points
- `process_input()`: main entry point called by both server and CLI

## Processing Pipeline

```
JSON payload
  |
  v
unpack_input()           -- Normalizes list[json, picos, cumpl] or dict
  |
  v
route_mode()             -- Resolves mode: "peaks" | "compliance" | "all_emissions"
  |
  v
frame_from_payload()     -- Tolerant JSON -> SpectrumFrame (Pxx aliasing)
  |
  v
apply_gain_correction()  -- Interpolates correction CSV onto freq axis (optional)
  |
  v
_run_new_detector_on_frame()  -- THE DETECTOR:
  |   smooth_psd()              -- Savitzky-Golay smoothing
  |   detect_noise_floor_from_psd()  -- Global noise floor (percentile)
  |   detect_channels_from_psd() -- Initial region detection
  |   build_step_noise_floor()   -- Local NF refinement
  |   detect_channels_from_variable_threshold() -- Final detection
  |   split_wide_regions_by_internal_valleys()  -- Valley splitting
  |
  v
Mode-specific branch:
  |-- all_emissions: All detected regions as-is
  |-- peaks: Match requested peaks to nearest detection
  |-- compliance: Full regulatory check (FC/BW/Power vs license)
  |
  v
_enrich_output_with_rni()  -- Add RNI field strength + occupancy
```

## Key interactions
- **Called by:** `server_flask.py` (HTTP), `main.py` (CLI), `step2_test_router.py` (test)
- **Calls:** `spectral_analysis.py` (signal processing), `calibration_io.py` (license matching), `utils/*` (DSP pipeline)
- **License data:** `calibration_io.py` loads CSV with `lru_cache`, provides `_match_licencia()` function

## Common tasks & gotchas
- `_process_input_reference_legacy()` (lines 1145-1765) is dead code — old pipeline using legacy detector
- `_run_new_detector_on_frame()` is the current production pipeline using `utils/` modules
- `simple_detector.py` is imported but never called in production path
- Three processing modes have different output structures — `all_emissions` is simplest, `compliance` is most complex
- Colombia-specific logic: TDT band detection (470-698 MHz), 6 MHz raster channel snapping, DANE code filtering

## Open questions / TODO
- Legacy `_process_input_reference_legacy()` should be removed or clearly marked deprecated
- `simple_detector.py` integration is incomplete — never invoked in production
- 2,542 lines in single file — should be decomposed
- No function-level documentation for most functions
