"""
02 — Dry-run modes

Inject a synthetic two-tone signal into the RF engine via dry-run mode.
No HackRF needed — the engine skips all hardware operations.

Demonstrates all 3 processing paths:
  1. IQ mode   → raw complex samples (binary, int8)
  2. Welch PSD → power spectral density via Welch's method
  3. PFB PSD   → power spectral density via polyphase filterbank

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


def build_payload(method_psd: str, iq_data: list) -> dict:
    """Build a dry-run payload for the given processing mode."""
    return {
        "center_freq_hz": 98_000_000,
        "sample_rate_hz": SAMPLE_RATE,
        "method_psd": method_psd,
        "demodulation": None,
        "lna_gain": 0,
        "vga_gain": 0,
        "antenna_amp": False,
        "antenna_port": 1,
        "cooldown_request": 0.0,
        "ppm_error": 0.0,
        "filter": None,
        "dry_run": True,
        "dry_run_iq": iq_data,
    }


async def send(payload: dict) -> dict | None:
    """Send a request to the RF engine and return the response."""
    try:
        async with ZmqPairController(IPC_ADDR, is_server=True, max_queue=-1) as ctrl:
            return await ctrl.request(payload)
    except TimeoutError:
        return None


# ── 1. IQ mode ───────────────────────────────────────────────────────
async def demo_iq(iq_data: list):
    """Dry-run IQ mode: returns raw complex samples as binary."""
    print("\n═══ IQ Mode (raw complex samples) ═══")
    resp = await send(build_payload("iq", iq_data))

    if resp is None or resp.get("status") != "ok":
        print(f"  ERROR: {resp}")
        return

    iq_out = resp.get("iq", [])
    n_out = int(resp.get("n_samples", 0))
    fs = resp.get("sample_rate_hz", 0)

    print(f"  Band:     {resp.get('start_freq_hz', 0)/1e6:.2f} – {resp.get('end_freq_hz', 0)/1e6:.2f} MHz")
    print(f"  Fs:       {fs/1e6:.1f} MS/s")
    print(f"  Samples:  {n_out} complex ({len(iq_out)} values)")
    print(f"  Encoding: {'int8 binary' if resp.get('encoding') == 0 else 'unknown'}")

    if len(iq_out) == 0:
        print("  No IQ data received.")
        return

    # Show first samples
    print(f"  First 6:  {iq_out[:6]}")
    for j in range(min(3, n_out)):
        re, im = iq_out[2*j], iq_out[2*j+1]
        print(f"    [{j}] = {re:.1f} + {im:.1f}j  (|z| = {math.hypot(re, im):.1f})")


# ── 2. Welch PSD ─────────────────────────────────────────────────────
async def demo_welch(iq_data: list):
    """Dry-run Welch PSD: engine computes PSD via Welch's method."""
    print("\n═══ Welch PSD ═══")
    resp = await send(build_payload("welch", iq_data))

    if resp is None or resp.get("status") != "ok":
        print(f"  ERROR: {resp}")
        return

    pxx = resp.get("Pxx", [])
    print(f"  Band:     {resp.get('start_freq_hz', 0)/1e6:.2f} – {resp.get('end_freq_hz', 0)/1e6:.2f} MHz")
    print(f"  Pxx bins: {len(pxx)}")

    if len(pxx) > 0:
        pxx_arr = np.array(pxx)
        print(f"  Range:    [{pxx_arr.min():.1f}, {pxx_arr.max():.1f}] dB")
        print(f"  Mean:     {pxx_arr.mean():.1f} dB")

        # Find top peaks
        freqs = np.linspace(0, SAMPLE_RATE / 2, len(pxx))
        from scipy.signal import find_peaks
        peaks, props = find_peaks(pxx, prominence=3)
        if len(peaks) > 0:
            top = np.argsort(props["prominences"])[::-1][:3]
            print("  Top peaks:")
            for rank, idx in enumerate(top, 1):
                pk = peaks[idx]
                print(f"    {rank}. {freqs[pk]:8.1f} Hz  {pxx[pk]:6.1f} dB")


# ── 3. PFB PSD ───────────────────────────────────────────────────────
async def demo_pfb(iq_data: list):
    """Dry-run PFB PSD: engine computes PSD via polyphase filterbank."""
    print("\n═══ PFB PSD ═══")
    resp = await send(build_payload("pfb", iq_data))

    if resp is None or resp.get("status") != "ok":
        print(f"  ERROR: {resp}")
        return

    pxx = resp.get("Pxx", [])
    print(f"  Band:     {resp.get('start_freq_hz', 0)/1e6:.2f} – {resp.get('end_freq_hz', 0)/1e6:.2f} MHz")
    print(f"  Pxx bins: {len(pxx)}")

    if len(pxx) > 0:
        pxx_arr = np.array(pxx)
        print(f"  Range:    [{pxx_arr.min():.1f}, {pxx_arr.max():.1f}] dB")
        print(f"  Mean:     {pxx_arr.mean():.1f} dB")

        freqs = np.linspace(0, SAMPLE_RATE / 2, len(pxx))
        from scipy.signal import find_peaks
        peaks, props = find_peaks(pxx, prominence=3)
        if len(peaks) > 0:
            top = np.argsort(props["prominences"])[::-1][:3]
            print("  Top peaks:")
            for rank, idx in enumerate(top, 1):
                pk = peaks[idx]
                print(f"    {rank}. {freqs[pk]:8.1f} Hz  {pxx[pk]:6.1f} dB")


# ── Main ─────────────────────────────────────────────────────────────
async def run():
    iq_data = generate_iq(SAMPLE_RATE, N_SAMPLES)
    print(f"Generated {N_SAMPLES} IQ samples ({FREQ_1} Hz + {FREQ_2} Hz tones)")

    await demo_iq(iq_data)
    await demo_welch(iq_data)
    await demo_pfb(iq_data)

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(run())
