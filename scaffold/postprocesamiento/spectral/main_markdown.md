# Spectral — Layer 3

> Parent: [../main_markdown.md](../main_markdown.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Signal processing engine: peak detection, emission parameter measurement, bandwidth analysis, noise floor estimation, and Colombia-specific broadband/TDT logic.

## Tech stack & conventions
- NumPy for numerical computation
- SciPy for signal processing (Savitzky-Golay, interpolation)
- Pure math functions — no I/O or network calls
- Colombia-specific: TDT (digital TV) band detection, 6 MHz raster

## Structure
```
spectral/
├── spectral_analysis.py   # Signal processing engine (2,181 lines)
├── simple_detector.py     # Preset-based detector (639 lines, unused in prod)
└── power_utils.py         # Power integration (131 lines)
```

## Entry points
- Called by `processor.py` during the detection pipeline

## Key functions

### spectral_analysis.py
- `detect_peak_bins()` — find peak frequencies in PSD
- `measure_emission_parameters()` — fc, bandwidth, power for each emission
- `measure_obw()` — occupied bandwidth measurement
- `measure_bandwidth_xdb()` — x-dB bandwidth measurement
- `estimate_noise_floor()` — global noise floor estimation
- `adaptive_threshold()` — dynamic detection threshold
- `find_emission_span()` — emission start/end frequency
- `slice_spectrum_frame()` — extract sub-band from full spectrum
- `estimate_ber_in_band_mqam()` — MER/BER for TDT signals
- `analyze_colombia_broadband_segments()` — Colombia broadband analysis

### simple_detector.py
- `detect_emissions()` — preset-based detection (4 presets: general, fm_dense, high_res, uhf_tv)
- `SimpleDetectorConfig` dataclass for preset configuration

### power_utils.py
- `channel_power_dbm_uniform_bins()` — power integration over frequency range
- `trapz_compat()` — trapezoidal integration compatibility wrapper

## Key interactions
- **Called by:** `processor.py` (`_run_new_detector_on_frame()` and mode-specific branches)
- **Calls:** `utils/signal_processing.py`, `utils/noise_floor.py`, `utils/channel_detection.py`, `utils/region_analysis.py`

## Common tasks & gotchas
- `simple_detector.py` is imported but never called in production — experimental alternative
- TDT band detection hardcodes 470-698 MHz range
- 6 MHz channel raster snapping for Colombian digital TV
- BER estimation assumes M-QAM modulation

## Open questions / TODO
- `simple_detector.py` should either be integrated or removed
- 2,181 lines in single file — should be decomposed
- No unit tests for signal processing functions
- TDT-specific logic tightly coupled with general-purpose analysis
