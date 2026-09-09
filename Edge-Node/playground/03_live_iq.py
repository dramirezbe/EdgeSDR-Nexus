"""
03 — Live IQ mode

Sends an IQ mode request to the RF engine with real HackRF hardware.
Returns raw complex IQ samples instead of PSD.
Requires: RF engine running (./rf_app) + HackRF connected.

Usage:
    python playground/03_live_iq.py
"""
import asyncio
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.request_util import ZmqPairController

IPC_ADDR = "ipc:///tmp/rf_engine"

# ── Payload ───────────────────────────────────────────────────────────
PAYLOAD = {
    "center_freq_hz": 98_000_000,      # 98 MHz FM band
    "sample_rate_hz": 20_000_000,       # 20 MS/s
    "method_psd": "iq",                # IQ mode — raw complex samples
    "demodulation": None,              # no audio demod
    "lna_gain": 16,
    "vga_gain": 20,
    "antenna_amp": True,
    "antenna_port": 1,
    "cooldown_request": 1.0,
    "ppm_error": 0.0,
    "filter": None,
}


async def run():
    async with ZmqPairController(IPC_ADDR, is_server=True) as ctrl:
        print(f"Sending live IQ request to {IPC_ADDR} ...")
        try:
            resp = await ctrl.request(PAYLOAD)
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

    iq = resp.get("iq", [])
    n_samples = int(resp.get("n_samples", 0))
    mode = resp.get("mode", "?")
    fs = resp.get("sample_rate_hz", 0)
    start_mhz = resp.get("start_freq_hz", 0) / 1e6
    end_mhz = resp.get("end_freq_hz", 0) / 1e6

    print(f"\n--- Live IQ Result ---")
    print(f"  Mode:       {mode}")
    print(f"  Band:       {start_mhz:.2f} – {end_mhz:.2f} MHz")
    print(f"  Fs:         {fs / 1e6:.1f} MS/s")
    print(f"  Samples:    {n_samples} complex ({n_samples * 2} floats in array)")
    print(f"  IQ length:  {len(iq)}")

    if len(iq) == 0:
        print("  No IQ data received.")
        return

    # ── Quick stats ───────────────────────────────────────────────────
    reals = iq[0::2]
    imags = iq[1::2]
    power = sum(r**2 + i**2 for r, i in zip(reals[:1000], imags[:1000])) / min(1000, len(reals))

    print(f"  First 6:    {iq[:6]}")
    print(f"  Mean power: {power:.6f} (first 1000 samples)")


if __name__ == "__main__":
    asyncio.run(run())
