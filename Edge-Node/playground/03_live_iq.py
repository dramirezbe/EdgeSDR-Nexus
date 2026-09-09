"""
03 — Live IQ mode

Sends an IQ mode request to the RF engine with real HackRF hardware.
Returns raw complex IQ samples instead of PSD.
Requires: RF engine running (./rf_app) + HackRF connected.

Usage:
    python playground/03_live_iq.py
"""
import asyncio
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import welch, find_peaks
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.request_util import ZmqPairController

IPC_ADDR = "ipc:///tmp/rf_engine"

# ── Payload ───────────────────────────────────────────────────────────
PAYLOAD = {
    "center_freq_hz": 98_000_000,      # 98 MHz FM band
    "sample_rate_hz": 20_000_000,       # 20 MS/s
    "method_psd": "iq",                # IQ mode — raw complex samples
    "demodulation": None,              # no audio demod
    "lna_gain": 8,
    "vga_gain": 8,
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
    print(f"  Samples:    {n_samples} complex ({n_samples * 2} int8 in wire format)")
    print(f"  IQ length:  {len(iq)}")
    encoding = resp.get("encoding", -1)
    print(f"  Encoding:   {'int8 interleaved (binary)' if encoding == 0 else f'unknown ({encoding})'}")

    if len(iq) == 0:
        print("  No IQ data received.")
        return

    # ── Quick stats ───────────────────────────────────────────────────
    reals = iq[0::2]
    imags = iq[1::2]
    power = sum(r**2 + i**2 for r, i in zip(reals[:1000], imags[:1000])) / min(1000, len(reals))

    print(f"  First 6:    {iq[:6]}")
    print(f"  Mean power: {power:.6f} (first 1000 samples)")

    # ── Welch PSD (scipy) ─────────────────────────────────────────────
    complex_iq = np.array(reals, dtype=np.float64) + 1j * np.array(imags, dtype=np.float64)
    center_freq = resp.get("center_freq_hz", 0)
    nperseg = 4096
    freqs, psd = welch(complex_iq, fs=fs, nperseg=nperseg, return_onesided=False)
    # Shift to center frequency ordering and offset to absolute frequency
    freqs = np.fft.fftshift(freqs) + center_freq
    psd = np.fft.fftshift(psd)
    freqs_mhz = freqs / 1e6

    print(f"\n--- Welch PSD (nperseg={nperseg}) ---")
    print(f"  Freq range:  {freqs_mhz[0]:.2f} – {freqs_mhz[-1]:.2f} MHz")
    print(f"  Max PSD:     {10*np.log10(psd.max()):.1f} dBFS @ {freqs_mhz[np.argmax(psd)]:.2f} MHz")
    print(f"  Mean PSD:    {10*np.log10(psd.mean()):.1f} dBFS")

    # Print top 5 peaks
    peaks, props = find_peaks(10*np.log10(psd), prominence=3)
    if len(peaks) > 0:
        sorted_idx = np.argsort(props["prominences"])[::-1][:5]
        print(f"\n  Top {len(sorted_idx)} peaks:")
        for rank, idx in enumerate(sorted_idx, 1):
            pk = peaks[idx]
            print(f"    {rank}. {freqs_mhz[pk]:8.2f} MHz  {10*np.log10(psd[pk]):6.1f} dBFS  (prominence: {props['prominences'][idx]:.1f} dB)")
    else:
        print("  No significant peaks detected.")

    # ── Plot ───────────────────────────────────────────────────────────
    psd_db = 10 * np.log10(psd)
    y_min = max(np.floor(psd_db.min() / 10) * 10, -120)
    y_max = min(np.ceil(psd_db.max() / 10) * 10 + 10, 10)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(freqs_mhz, psd_db, linewidth=0.6)
    ax.set_title(f"Welch PSD — {mode.upper()} mode  (Fs={fs/1e6:.0f} MS/s, nperseg={nperseg})")
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel("Power (dB)")
    ax.set_xlim(start_mhz, end_mhz)
    ax.set_ylim(y_min, y_max)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig("playground/03_live_iq_psd.png", dpi=150)
    print(f"\n  Plot saved: playground/03_live_iq_psd.png")


if __name__ == "__main__":
    asyncio.run(run())
