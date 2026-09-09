"""
02 — Dry-run IQ mode

Inject a synthetic two-tone signal into the RF engine via dry-run mode.
No HackRF needed — the engine skips all hardware operations and returns
raw complex IQ samples through the same DSP pipeline.

Requires: RF engine running (./rf_app).

Usage:
    python playground/02_dry_run_iq.py
"""
import asyncio
import math
import sys
from pathlib import Path

import numpy as np
from scipy.signal import welch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.request_util import ZmqPairController

IPC_ADDR = "ipc:///tmp/rf_engine"

# ── Signal parameters ────────────────────────────────────────────────
SAMPLE_RATE = 8_000_000       # 8 MS/s
N_SAMPLES = 2_500            # ~0.3 ms — fits C ZBUF_SIZE=64KB
FREQ_1 = 1000                 # 1 kHz tone
FREQ_2 = 5000                 # 5 kHz tone
# Amplitudes in int8 range: dry-run casts float→int8,
# so values must be >1.0 to survive quantization.
AMPLITUDE_1 = 50.0
AMPLITUDE_2 = 30.0


def generate_iq(fs: int, n: int) -> list:
    """Generate interleaved IQ: [I0, Q0, I1, Q1, ...]"""
    iq = []
    for i in range(n):
        t = i / fs
        i_val = (AMPLITUDE_1 * math.cos(2 * math.pi * FREQ_1 * t)
                 + AMPLITUDE_2 * math.cos(2 * math.pi * FREQ_2 * t))
        iq.append(i_val)
        iq.append(0.0)  # Q = 0 (real signal)
    return iq


async def run():
    # ── Generate signal ───────────────────────────────────────────────
    iq_data = generate_iq(SAMPLE_RATE, N_SAMPLES)
    print(f"Generated {N_SAMPLES} IQ samples ({FREQ_1} Hz + {FREQ_2} Hz tones)")
    print(f"  Payload estimate: ~{N_SAMPLES * 2 * 10 / 1e6:.1f} MB JSON")

    # ── Send dry-run request ──────────────────────────────────────────
    payload = {
        "center_freq_hz": 98_000_000,    # 98 MHz
        "sample_rate_hz": SAMPLE_RATE,
        "method_psd": "iq",              # IQ mode — raw complex samples
        "demodulation": None,
        "lna_gain": 0,
        "vga_gain": 0,
        "antenna_amp": False,
        "antenna_port": 1,
        "cooldown_request": 0.0,
        "ppm_error": 0.0,
        "filter": None,
        "dry_run": True,                 # bypass HackRF
        "dry_run_iq": iq_data,           # inject synthetic IQ
    }

    async with ZmqPairController(IPC_ADDR, is_server=True, max_queue=-1) as ctrl:
        print(f"\nSending dry-run IQ request to {IPC_ADDR} ...")
        try:
            resp = await ctrl.request(payload)
        except TimeoutError:
            print("ERROR: Timeout — no RF engine running?")
            return

    if resp is None:
        print("ERROR: No response (timeout)")
        return

    # ── Response ──────────────────────────────────────────────────────
    if resp.get("status") != "ok":
        print(f"ERROR: {resp}")
        return

    iq_out = resp.get("iq", [])
    n_out = int(resp.get("n_samples", 0))
    fs = resp.get("sample_rate_hz", 0)
    start_mhz = resp.get("start_freq_hz", 0) / 1e6
    end_mhz = resp.get("end_freq_hz", 0) / 1e6

    print(f"\n--- Dry-Run IQ Result ---")
    print(f"  Mode:       {resp.get('mode', '?')}")
    print(f"  Band:       {start_mhz:.2f} – {end_mhz:.2f} MHz")
    print(f"  Fs:         {fs / 1e6:.1f} MS/s")
    print(f"  Samples:    {n_out} complex ({len(iq_out)} values)")
    print(f"  Encoding:   {'int8 binary' if resp.get('encoding') == 0 else 'unknown'}")

    if len(iq_out) == 0:
        print("  No IQ data received.")
        return

    # ── Show first samples ────────────────────────────────────────────
    print(f"\n  First 6 values: {iq_out[:6]}")
    print(f"  Reconstructed complex samples:")
    for j in range(min(3, n_out)):
        re = iq_out[2 * j]
        im = iq_out[2 * j + 1]
        print(f"    [{j}] = {re:.1f} + {im:.1f}j  (|z| = {math.hypot(re, im):.1f})")

    # ── Quick PSD analysis ────────────────────────────────────────────
    reals = np.array(iq_out[0::2], dtype=np.float64)
    imags = np.array(iq_out[1::2], dtype=np.float64)
    c = reals + 1j * imags

    nperseg = min(1024, len(c))
    freqs, psd = welch(c, fs=fs, nperseg=nperseg, return_onesided=False)
    freqs = np.fft.fftshift(freqs)
    psd = np.fft.fftshift(psd)
    freqs_khz = freqs / 1e3

    print(f"\n--- Welch PSD (nperseg={nperseg}) ---")
    print(f"  Max PSD:  {10*np.log10(psd.max()):.1f} dB @ {freqs_khz[np.argmax(psd)]:.1f} kHz")
    print(f"  Mean PSD: {10*np.log10(psd.mean()):.1f} dB")


if __name__ == "__main__":
    asyncio.run(run())
