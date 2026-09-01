# RF Engine — Layer 3

> Parent: [../main.md](../main.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
C99 real-time data plane: controls HackRF One SDR, ingests IQ samples, applies DSP (PSD, filtering, demodulation), and serves spectral data over ZMQ IPC with concurrent Opus audio streaming.

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
    lazy_tune_hackrf()                  // only if freq/gain/ppm changed
    ensure_audio_thread_once()          // pthread_create on first request
    start_rx_if_stopped()               // hackrf_start_rx + rx_callback
    rb_discard_all()                    // drop stale pre-request IQ
    wait_iq_with_timeout(5s)            // condvar wait
    dsp_pipeline()                      // IQ -> signal -> compensate -> filter -> PSD
    publish_results()                   // JSON reply with PSD + AM/FM metrics
```

## Key interactions
- **Python -> C:** ZMQ REQ/REP over `ipc:///tmp/rf_engine` — Python sends JSON config, C replies with PSD JSON
- **C -> Audio:** Opus TCP stream to `server_webrtc.py` on port 9000
- **C -> Shared state:** Calibration results written to `/dev/shm/persistent.json` via `shm_add_to_persistent()`

## Key Design Patterns
- Lock-free ring buffer for hot path (rx_callback -> consumers)
- Condvar wakeup (no polling)
- Workspace reuse (no malloc in DSP hot path)
- Lazy tuning (only touch HackRF registers when config changes)
- Request-scoped capture (discard stale data before each acquisition)
- Atomic signaling for cross-thread flags

## Common tasks & gotchas
- **Never degrade RF parameters** requested by server — user config is source of truth
- **OpenMP + thread-local storage** is a known hazard — be defensive in parallel regions
- `rx_callback` runs in HackRF driver thread — must be minimal (no malloc, no blocking)
- PPM correction applied to center frequency internally, but nominal frequency preserved for reporting
- 15-minute idle timeout closes HackRF to save power/thermal

## Open questions / TODO
- `am_radio.h`/`am_radio.c` is legacy, superseded by `am_radio_local` but still referenced in audio thread
- No unit tests for C code
- Build artifacts (`rf_app`) placed in repo root then gitignored
