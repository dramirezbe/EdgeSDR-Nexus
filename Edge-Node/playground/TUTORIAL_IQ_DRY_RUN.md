# Tutorial: IQ Mode & Dry-Run Mode

> Developer guide for testing DSP algorithms against the RF engine without or with real hardware.

## Prerequisites

- Raspberry Pi 5 with HackRF One connected (for live IQ mode), **or** any Linux desktop (for dry-run)
- Python 3.11+ with `pyzmq` and `numpy` installed
- RF engine built: `./build.sh -dev` from `Edge-Node/`

## Quick Reference

| Mode | `method_psd` | `dry_run` | Needs HackRF | Returns |
|------|-------------|-----------|-------------|---------|
| PSD (default) | `"welch"` / `"pfb"` | `false` | Yes | `Pxx` array (dBm/Hz) |
| **IQ** | `"iq"` | `false` | Yes | `iq` array (interleaved I,Q doubles) |
| **Dry-run PSD** | `"welch"` / `"pfb"` | `true` | No | `Pxx` array from synthetic IQ |
| **Dry-run IQ** | `"iq"` | `true` | No | `iq` array from synthetic IQ |

---

## 1. Build & Start the RF Engine

```bash
cd Edge-Node

# Desktop build (no GPIO, RF only)
./build.sh -dev

# Start the engine (blocks — run in a separate terminal)
./rf_app
```

The engine listens on `ipc:///tmp/rf_engine` (override with `IPC_ADDR` env var).

Output should look like:
```
[RF] Starting Engine. IPC=ipc:///tmp/rf_engine
[RF] Initializing HackRF Library...
[RF] HackRF Library Initialized.
```

> **No HackRF?** Use dry-run mode — the engine will skip hardware initialization entirely.

---

## 2. Connect via Python

All examples use the same connection pattern:

```python
import asyncio
import zmq
import zmq.asyncio
import json
import math

IPC_ADDR = "ipc:///tmp/rf_engine"

async def send_request(payload: dict) -> dict:
    """Send a JSON payload to the RF engine and return the response."""
    ctx = zmq.asyncio.Context()
    sock = ctx.socket(zmq.REQ)
    sock.setsockopt(zmq.LINGER, 0)
    sock.connect(IPC_ADDR)

    try:
        await sock.send_string(json.dumps(payload))
        resp = await sock.recv_string()
        return json.loads(resp)
    finally:
        sock.close()
        ctx.term()
```

---

## 3. IQ Mode (Live Hardware)

Returns raw complex IQ samples instead of PSD. Useful for developing your own DSP algorithms.

### Payload

```python
payload = {
    "center_freq_hz": 98_000_000,    # 98 MHz FM band
    "sample_rate_hz": 8_000_000,     # 8 MS/s
    "method_psd": "iq",              # ← IQ mode
    "demodulation": None,            # no audio demod
    "lna_gain": 16,
    "vga_gain": 20,
    "antenna_amp": True,
    "antenna_port": 1,
    "cooldown_request": 1.0,
}
```

### Run it

```python
async def test_iq_mode():
    resp = await send_request(payload)

    print(f"Status:   {resp['status']}")
    print(f"Mode:     {resp['mode']}")           # "iq"
    print(f"Fs:       {resp['sample_rate_hz']} Hz")
    print(f"Start:    {resp['start_freq_hz']} Hz")
    print(f"End:      {resp['end_freq_hz']} Hz")
    print(f"Samples:  {resp['n_samples']}")
    print(f"IQ pairs: {len(resp['iq']) // 2}")

    # Convert interleaved list to numpy complex array
    import numpy as np
    iq_flat = np.array(resp["iq"])
    iq_complex = iq_flat[0::2] + 1j * iq_flat[1::2]  # I + jQ

    print(f"Shape:    {iq_complex.shape}")
    print(f"Power:    {np.mean(np.abs(iq_complex)**2):.6f}")

asyncio.run(test_iq_mode())
```

### Expected response

```json
{
  "status": "ok",
  "mode": "iq",
  "start_freq_hz": 94000000,
  "end_freq_hz": 102000000,
  "sample_rate_hz": 8000000,
  "n_samples": 4000000,
  "iq": [0.123, -0.456, 0.789, -0.012, ...]
}
```

The `iq` array is interleaved: `[I0, Q0, I1, Q1, ...]`. Length is `n_samples * 2`.

---

## 4. Dry-Run Mode (No Hardware)

Inject a synthetic IQ vector into the RF engine. The engine skips HackRF entirely, processes your vector through the same DSP pipeline, and returns the result.

### 4a. Dry-run + PSD (verify your signal through Welch/PFB)

```python
import numpy as np

async def test_dry_run_psd():
    # Generate a 1 kHz tone at 8 MS/s
    fs = 8_000_000
    n = 100_000  # 12.5 ms of data
    t = np.arange(n) / fs
    tone = 0.8 * np.cos(2 * np.pi * 1000 * t)

    # Interleave as [I0, Q0, I1, Q1, ...]
    iq_list = []
    for i in range(n):
        iq_list.append(float(tone[i]))  # I
        iq_list.append(0.0)             # Q

    payload = {
        "center_freq_hz": 98_000_000,
        "sample_rate_hz": fs,
        "method_psd": "welch",           # PSD mode
        "demodulation": None,
        "lna_gain": 0,
        "vga_gain": 0,
        "antenna_amp": False,
        "antenna_port": 1,
        "cooldown_request": 0.0,
        "dry_run": True,                 # ← bypass HackRF
        "dry_run_iq": iq_list,           # ← your IQ vector
    }

    resp = await send_request(payload)

    print(f"Status: {resp['status']}")
    print(f"PSD bins: {len(resp['Pxx'])}")
    print(f"PSD range: [{min(resp['Pxx']):.1f}, {max(resp['Pxx']):.1f}] dBm")

asyncio.run(test_dry_run_psd())
```

### 4b. Dry-run + IQ (bypass hardware, get raw samples back)

```python
async def test_dry_run_iq():
    # Generate a known signal: two-tone (1 kHz + 5 kHz)
    fs = 8_000_000
    n = 50_000
    t = np.arange(n) / fs
    sig = 0.5 * np.cos(2 * np.pi * 1000 * t) + 0.3 * np.cos(2 * np.pi * 5000 * t)

    iq_list = []
    for i in range(n):
        iq_list.append(float(sig[i]))
        iq_list.append(0.0)

    payload = {
        "center_freq_hz": 98_000_000,
        "sample_rate_hz": fs,
        "method_psd": "iq",              # ← IQ mode
        "demodulation": None,
        "lna_gain": 0,
        "vga_gain": 0,
        "antenna_amp": False,
        "antenna_port": 1,
        "cooldown_request": 0.0,
        "dry_run": True,                 # ← bypass HackRF
        "dry_run_iq": iq_list,
    }

    resp = await send_request(payload)

    import numpy as np
    iq_flat = np.array(resp["iq"])
    iq_complex = iq_flat[0::2] + 1j * iq_flat[1::2]

    print(f"Mode: {resp['mode']}")             # "iq"
    print(f"Input samples:  {n}")
    print(f"Output samples: {resp['n_samples']}")
    print(f"Round-trip OK:  {resp['n_samples'] == n}")

asyncio.run(test_dry_run_iq())
```

---

## 5. Building Test Signals

### Pure tone

```python
def make_tone(freq_hz, fs, n_samples, amplitude=0.8):
    """Single tone at freq_hz, fs sample rate."""
    t = np.arange(n_samples) / fs
    return amplitude * np.cos(2 * np.pi * freq_hz * t)

iq_list = make_tone(1000, 8e6, 100_000).tolist()
# Interleave: each I sample paired with Q=0
iq_interleaved = [v for pair in zip(iq_list, [0.0]*len(iq_list)) for v in pair]
```

### Two-tone

```python
def make_two_tone(f1, f2, fs, n_samples, a1=0.5, a2=0.3):
    t = np.arange(n_samples) / fs
    return a1 * np.cos(2*np.pi*f1*t) + a2 * np.cos(2*np.pi*f2*t)
```

### Noise + tone (realistic)

```python
def make_noisy_tone(freq_hz, fs, n_samples, snr_db=20):
    t = np.arange(n_samples) / fs
    tone = np.cos(2 * np.pi * freq_hz * t)
    noise = np.random.randn(n_samples)
    signal_power = np.mean(tone**2)
    noise_power = signal_power / (10 ** (snr_db / 10))
    return tone + np.sqrt(noise_power) * noise
```

### FM-modulated signal

```python
def make_fm_signal(carrier_hz, mod_freq_hz, mod_dev_hz, fs, n_samples):
    t = np.arange(n_samples) / fs
    modulator = np.sin(2 * np.pi * mod_freq_hz * t)
    phase = 2 * np.pi * carrier_hz * t + (mod_dev_hz / mod_freq_hz) * (-np.cos(2 * np.pi * mod_freq_hz * t))
    return np.cos(phase)
```

---

## 6. What Each Mode Returns

### PSD mode (`method_psd: "welch"` or `"pfb"`)

```json
{
  "status": "ok",
  "start_freq_hz": 94000000,
  "end_freq_hz": 102000000,
  "Pxx": [-45.2, -42.1, -38.7, ...]
}
```

- `Pxx`: Power spectral density in dBm/Hz, one value per frequency bin
- Length equals `nperseg` (FFT size), determined by RBW

### IQ mode (`method_psd: "iq"`)

```json
{
  "status": "ok",
  "mode": "iq",
  "start_freq_hz": 94000000,
  "end_freq_hz": 102000000,
  "sample_rate_hz": 8000000,
  "n_samples": 4000000,
  "iq": [I0, Q0, I1, Q1, ...]
}
```

- `iq`: Interleaved real/imaginary doubles
- Length = `n_samples * 2`
- Values are normalized (raw ADC bytes / 128.0), after IQ compensation and optional filtering
- **No** PSD, **no** `Pxx` key

### FM/AM demodulation (existing, unchanged)

```json
{
  "status": "ok",
  "start_freq_hz": 94000000,
  "end_freq_hz": 102000000,
  "Pxx": [...],
  "excursion_hz": 3123
}
```

Or for AM:
```json
{
  "status": "ok",
  "Pxx": [...],
  "depth": 87.3
}
```

---

## 7. Error Responses

```json
{"status": "error", "reason": "hackrf_unavailable"}
{"status": "error", "reason": "hackrf_open_failed"}
{"status": "error", "reason": "rx_start_failed"}
{"status": "error", "reason": "acquisition_timeout"}
{"status": "error", "reason": "dry_run_alloc_failed"}
{"status": "error", "reason": "invalid_request"}
```

Dry-run mode should never return hardware errors — if you see `hackrf_unavailable` in dry-run, the `dry_run` flag didn't reach the C parser.

---

## 8. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Connection refused` on IPC | RF engine not running | Start `./rf_app` in another terminal |
| `Timeout waiting for data` | HackRF not connected or slow tune | Check USB, increase `cooldown_request` |
| IQ array length is 0 | `n_samples` too small for the workspace | Increase `sample_rate_hz` or check ring buffer size |
| Dry-run returns `hackrf_unavailable` | `dry_run` flag not parsed | Verify JSON has `"dry_run": true` (boolean, not string) |
| Dry-run returns empty `Pxx` | `dry_run_iq` array length is odd | Ensure array length is even: `len(dry_run_iq) % 2 == 0` |
| Python `KeyError: 'Pxx'` | IQ mode response has no `Pxx` | Check `resp.get("mode") == "iq"` before accessing `Pxx` |

---

## 9. Complete Example: Algorithm Development Workflow

```python
"""
Workflow: Develop a custom spectrum detector using dry-run + IQ mode.

1. Capture a known signal via dry-run
2. Process it with your algorithm
3. Validate the output
4. Switch to live hardware when ready
"""
import asyncio
import json
import math
import zmq
import zmq.asyncio
import numpy as np

IPC_ADDR = "ipc:///tmp/rf_engine"

async def send(payload):
    ctx = zmq.asyncio.Context()
    sock = ctx.socket(zmq.REQ)
    sock.setsockopt(zmq.LINGER, 0)
    sock.connect(IPC_ADDR)
    await sock.send_string(json.dumps(payload))
    resp = json.loads(await sock.recv_string())
    sock.close()
    ctx.term()
    return resp

async def main():
    # --- Step 1: Dry-run with synthetic signal ---
    fs = 8_000_000
    n = 200_000
    t = np.arange(n) / fs

    # Simulate a 100 MHz carrier with 1 kHz AM modulation
    carrier = 0.7 * np.cos(2 * np.pi * 1000 * t)  # baseband
    iq_list = []
    for i in range(n):
        iq_list.append(float(carrier[i]))
        iq_list.append(0.0)

    resp = await send({
        "center_freq_hz": 100_000_000,
        "sample_rate_hz": fs,
        "method_psd": "iq",
        "demodulation": None,
        "lna_gain": 0, "vga_gain": 0,
        "antenna_amp": False, "antenna_port": 1,
        "cooldown_request": 0.0,
        "dry_run": True,
        "dry_run_iq": iq_list,
    })

    assert resp["status"] == "ok"
    assert resp["mode"] == "iq"

    # --- Step 2: Process with your algorithm ---
    iq_flat = np.array(resp["iq"])
    iq_complex = iq_flat[0::2] + 1j * iq_flat[1::2]

    # Your custom PSD estimate
    from numpy.fft import fft, fftshift
    fft_result = fftshift(fft(iq_complex))
    psd_custom = 20 * np.log10(np.abs(fft_result) + 1e-12)

    print(f"Custom PSD: {psd_custom.shape} bins, range [{psd_custom.min():.1f}, {psd_custom.max():.1f}] dB")

    # --- Step 3: Compare with engine PSD ---
    resp_psd = await send({
        "center_freq_hz": 100_000_000,
        "sample_rate_hz": fs,
        "method_psd": "welch",
        "demodulation": None,
        "lna_gain": 0, "vga_gain": 0,
        "antenna_amp": False, "antenna_port": 1,
        "cooldown_request": 0.0,
        "dry_run": True,
        "dry_run_iq": iq_list,
    })

    engine_psd = np.array(resp_psd["Pxx"])
    print(f"Engine PSD: {engine_psd.shape} bins, range [{engine_psd.min():.1f}, {engine_psd.max():.1f}] dB")

    # --- Step 4: Switch to live hardware ---
    # Just remove dry_run and dry_run_iq from the payload:
    # resp_live = await send({
    #     "center_freq_hz": 100_000_000,
    #     "sample_rate_hz": fs,
    #     "method_psd": "iq",
    #     ... (no dry_run fields)
    # })

asyncio.run(main())
```

---

## 10. API Reference

### Request fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `center_freq_hz` | int | Yes | Center frequency in Hz |
| `sample_rate_hz` | int | Yes | Sample rate in Sps (2M–20M) |
| `method_psd` | string | No | `"welch"` (default), `"pfb"`, or `"iq"` |
| `demodulation` | string\|null | No | `"fm"`, `"am"`, or `null` (default) |
| `lna_gain` | int | No | LNA gain in dB (0–40) |
| `vga_gain` | int | No | VGA gain in dB (0–62) |
| `antenna_amp` | bool | No | RF amplifier enable |
| `antenna_port` | int | No | Antenna port (1–4) |
| `cooldown_request` | float | No | Seconds between acquisitions (default 1.0) |
| `rbw_hz` | int | No | Resolution bandwidth (default 100000) |
| `overlap` | float | No | PSD overlap 0.0–1.0 (default 0.5) |
| `window` | string | No | FFT window (default `"hamming"`) |
| `filter` | object\|null | No | `{"start_freq_hz": ..., "end_freq_hz": ...}` |
| `dry_run` | bool | No | Bypass HackRF hardware (default `false`) |
| `dry_run_iq` | float[] | No | Interleaved IQ vector (must be even length) |

### Response fields — PSD mode

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"ok"` or `"error"` |
| `start_freq_hz` | float | Spectrum start frequency |
| `end_freq_hz` | float | Spectrum end frequency |
| `Pxx` | float[] | PSD in dBm/Hz |
| `excursion_hz` | float | FM deviation (FM mode only) |
| `depth` | float | AM modulation depth % (AM mode only) |

### Response fields — IQ mode

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"ok"` or `"error"` |
| `mode` | string | `"iq"` |
| `start_freq_hz` | float | Band start frequency |
| `end_freq_hz` | float | Band end frequency |
| `sample_rate_hz` | float | Actual sample rate |
| `n_samples` | float | Number of complex samples |
| `iq` | float[] | Interleaved `[I0, Q0, I1, Q1, ...]` |
