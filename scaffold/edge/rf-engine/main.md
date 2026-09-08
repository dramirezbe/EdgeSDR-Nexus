# RF Engine — Layer 2

> Parent: [../main.md](../main.md)
> Last audited: 2026-09-08 @ commit 2bcb560

## Purpose
C99 real-time data plane: controls HackRF One SDR, ingests IQ samples, applies DSP (PSD, filtering, demodulation), and serves spectral data over ZMQ IPC with concurrent Opus audio streaming. Supports three `method_psd` modes: `welch` (default), `pfb`, and `iq` (raw complex samples). Also supports `dry_run` mode for injecting synthetic IQ vectors without hardware.

## Tech stack & conventions
- C99 with OpenMP parallelism
- FFTW3 for FFT operations
- ZeroMQ REQ/REP for IPC with Python control plane
- libhackrf for SDR hardware access
- Opus codec for audio compression
- Lock-free ring buffer for hot-path data transfer
- Target: Raspberry Pi 5 (conservative CPU/memory usage)

## Structure
```
rf-engine/
├── rf.c                     # ★ C ENTRY: main loop, request-driven state machine
└── libs/
    ├── datatypes.h           # Central type registry (structs, enums)
    ├── sdr_HAL.{c,h}        # HackRF hardware abstraction
    ├── ring_buffer.{c,h}    # Lock-free SPSC circular buffer
    ├── zmq_util.{c,h}       # ZMQ REP socket wrapper
    ├── parser.{c,h}         # JSON -> DesiredCfg_t deserializer
    ├── psd.{c,h}            # PSD engine (Welch + PFB, FFTW3+OpenMP)
    ├── chan_filter.{c,h}    # Frequency-domain brick-wall filter
    ├── fm_radio.{c,h}      # FM demodulation chain
    ├── am_radio.{c,h}      # Legacy AM demodulator
    ├── am_radio_local.{c,h} # Production AM (CIC + AGC)
    ├── iq_iir_filter.{c,h}  # Butterworth bandpass (biquad cascade)
    ├── audio_stream_ctx.{c,h} # Audio path aggregator
    ├── opus_tx.{c,h}        # Opus encoder + TCP sender
    ├── net_audio_retry.{c,h} # TCP reconnect resilience
    └── utils.{c,h}          # Shared memory + env helpers
```

## Entry points
- `rf/rf.c` main(): OpenMP tuning -> signal handlers -> ZMQ REP socket -> HackRF init -> ring buffers -> main loop

## Main Loop Flow
```
while (keep_running):
    req = zpair_recv(zmq_channel)     // 100 ms timeout
    if timeout: idle check -> close HackRF after 15s
    parse_config_rf(buffer, &desired)
    if desired.calibrate: run 3-stage calibration -> reply
    apply_runtime_request()             // audio on/off, find_params_psd()
    if desired.dry_run: inject IQ into ring buffer, set local_rb.total_bytes
    if !dry_run:
        lazy_tune_hackrf()              // only if freq/gain/ppm changed
        ensure_audio_thread_once()      // pthread_create on first request
        start_rx_if_stopped()           // hackrf_start_rx + rx_callback
        rb_discard_all()                // drop stale pre-request IQ
    wait_iq_with_timeout(5s)            // condvar wait
    dsp_pipeline()                      // IQ -> signal -> compensate -> filter
    if method_psd == IQ:
        publish_iq_results()            // JSON reply with raw complex IQ array
    else:
        execute_psd()                   // Welch or PFB
        publish_results()               // JSON reply with PSD + AM/FM metrics
    free dry_run_iq if allocated
```

## Key interactions
- **Python -> C:** ZMQ REQ/REP over `ipc:///tmp/rf_engine` — Python sends JSON config, C replies with PSD JSON (or IQ JSON when `method_psd: "iq"`)
  - Request contract: `json/rf-engine/params.jsonc` — all fields, types, defaults
  - Response contract (PSD): `json/POST-data.jsonc` — `Pxx`, `excursion_hz`, `depth`
  - Response contract (IQ): `json/POST-data.jsonc` — `mode: "iq"`, `iq[]`, `n_samples`
- **C -> Audio:** Opus TCP stream to `server_webrtc.py` on port 9000
- **C -> Shared state:** Calibration results written to `/dev/shm/persistent.json` via `shm_add_to_persistent()`
- **Dry-run:** Python test scripts can send `"dry_run": true` + `"dry_run_iq": [...]` to inject synthetic IQ, bypassing HackRF hardware entirely
- **Tutorial:** `playground/TUTORIAL_IQ_DRY_RUN.md` — step-by-step developer guide for IQ and dry-run modes

## Key Design Patterns
- Lock-free ring buffer for hot path (rx_callback -> consumers)
- Condvar wakeup (no polling)
- Workspace reuse (no malloc in DSP hot path)
- Lazy tuning (only touch HackRF registers when config changes)
- Request-scoped capture (discard stale data before each acquisition)
- Atomic signaling for cross-thread flags

## Common tasks & gotchas
- **Never degrade RF parameters** requested by server — user config is source of truth (`rf.c` -> `parse_config_rf`)
- **OpenMP + thread-local storage** is a known hazard — be defensive in parallel regions
- `rx_callback` runs in HackRF driver thread — must be minimal (no malloc, no blocking)
- PPM correction applied to center frequency internally, but nominal frequency preserved for reporting
- 15-minute idle timeout closes HackRF to save power/thermal
- **IQ mode** (`method_psd: "iq"`): skips PSD, returns raw complex interleaved `[I0,Q0,...]`. Ring buffer sizing still uses `find_params_psd()` — PSD config values computed but unused
  - **To add a new IQ-side feature:** `rf.c` `publish_iq_results()`, `datatypes.h` (response fields), `json/POST-data.jsonc` (contract)
- **Dry-run** (`dry_run: true`): injects IQ via `dry_run_iq` array, gates all hardware operations. Memory: `dry_run_iq` is heap-allocated by parser, freed after each DSP cycle. `set_default_config()` also frees as safety net against leaks
  - **To modify dry-run behavior:** `parser.c` `parse_config_rf()`, `rf.c` dry-run injection block (lines ~1137–1149)
- **To change PSD algorithm:** `psd.c` — `welch_init/execute` and `pfb_init/execute` are separate functions
- **To add a new demodulation mode:** `datatypes.h` `Demod_type` enum, `parser.c` demod lookup, `rf.c` demodulation block (lines ~1178–1210)
- **To change JSON contracts:** edit `json/rf-engine/params.jsonc` (request) or `json/POST-data.jsonc` (response), then update `parser.c` and `publish_results()`/`publish_iq_results()` in `rf.c`
- **To test changes:** `playground/01_pfb_request.py` (PSD), `playground/02_dry_run_iq.py` (dry-run IQ), `playground/03_live_iq.py` (live IQ)

## File Criticality

| File | Lines | Status | Notes |
|------|-------|--------|-------|
| `rf.c` | ~1200 | Active — CRITICAL | Main loop, state machine, DSP orchestration |
| `libs/datatypes.h` | ~200 | Active | Central type registry |
| `libs/psd.c` | ~400 | Active | Welch + PFB PSD engines |
| `libs/ring_buffer.{c,h}` | ~200 | Active | Lock-free SPSC, hot path |
| `libs/sdr_HAL.{c,h}` | ~300 | Active | HackRF abstraction |
| `libs/parser.{c,h}` | ~200 | Active | JSON config deserializer |

## Open questions / TODO
- `am_radio.h`/`am_radio.c` is legacy, superseded by `am_radio_local` but still referenced in audio thread
- No unit tests for C code
- Build artifacts (`rf_app`) placed in repo root then gitignored
