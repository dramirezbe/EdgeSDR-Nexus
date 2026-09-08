"""
02 — Dry-run IQ mode

Generates a synthetic two-tone signal (1 kHz + 5 kHz), injects it into the
RF engine via dry-run, and gets back raw complex IQ samples.
No HackRF needed — the engine skips all hardware operations.

Requires: RF engine running (./rf_app).

Usage:
    python playground/02_dry_run_iq.py
"""
import asyncio
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.request_util import ZmqPairController

IPC_ADDR = "ipc:///tmp/rf_engine"

# ── Signal parameters ────────────────────────────────────────────────
SAMPLE_RATE = 8_000_000       # 8 MS/s
N_SAMPLES = 20_000_000        # 2.5 s of data (~400 MB JSON payload)
FREQ_1 = 1000                 # 1 kHz tone
FREQ_2 = 5000                 # 5 kHz tone
AMPLITUDE_1 = 0.5
AMPLITUDE_2 = 0.3


def generate_iq(sample_rate: int, n_samples: int) -> list:
    """Generate interleaved IQ: [I0, Q0, I1, Q1, ...]"""
    iq = []
    for i in range(n_samples):
        t = i / sample_rate
        i_val = (AMPLITUDE_1 * math.cos(2 * math.pi * FREQ_1 * t)
                 + AMPLITUDE_2 * math.cos(2 * math.pi * FREQ_2 * t))
        q_val = 0.0
        iq.append(i_val)
        iq.append(q_val)
    return iq


def build_payload(iq_data: list) -> dict:
    return {
        "center_freq_hz": 98_000_000,
        "sample_rate_hz": SAMPLE_RATE,
        "method_psd": "iq",            # IQ mode
        "demodulation": None,
        "lna_gain": 0,
        "vga_gain": 0,
        "antenna_amp": False,
        "antenna_port": 1,
        "cooldown_request": 0.0,
        "ppm_error": 0.0,
        "filter": None,
        "dry_run": True,               # bypass HackRF
        "dry_run_iq": iq_data,         # inject synthetic IQ
    }


async def run():
    payload_bytes = N_SAMPLES * 2 * 10  # rough JSON estimate: 40M floats × ~10 chars
    print(f"Generating {N_SAMPLES} IQ samples ({FREQ_1} Hz + {FREQ_2} Hz tones) ...")
    print(f"  Payload estimate: ~{payload_bytes / 1e6:.0f} MB JSON")

    iq_data = generate_iq(SAMPLE_RATE, N_SAMPLES)
    payload = build_payload(iq_data)

    # max_queue=-1: lift SNDHWM/RCVHWM limits for large IQ payloads
    async with ZmqPairController(IPC_ADDR, is_server=False, max_queue=-1) as ctrl:
        print(f"Sending dry-run IQ request to {IPC_ADDR} ...")
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
    mode = resp.get("mode", "?")
    fs = resp.get("sample_rate_hz", 0)
    start_mhz = resp.get("start_freq_hz", 0) / 1e6
    end_mhz = resp.get("end_freq_hz", 0) / 1e6

    print(f"\n--- Dry-Run IQ Result ---")
    print(f"  Mode:       {mode}")
    print(f"  Band:       {start_mhz:.2f} – {end_mhz:.2f} MHz")
    print(f"  Fs:         {fs / 1e6:.1f} MS/s")
    print(f"  Samples:    {n_out} complex ({n_out * 2} floats in array)")
    print(f"  IQ length:  {len(iq_out)}")
    print(f"  First 6:    {iq_out[:6]}")

    # ── Sanity check: convert back to complex ─────────────────────────
    if len(iq_out) >= 2 * 6:
        print(f"\n  Reconstructed complex samples:")
        for j in range(min(3, n_out)):
            re = iq_out[2 * j]
            im = iq_out[2 * j + 1]
            print(f"    [{j}] = {re:.6f} + {im:.6f}j  (|z| = {math.hypot(re, im):.6f})")


if __name__ == "__main__":
    asyncio.run(run())
