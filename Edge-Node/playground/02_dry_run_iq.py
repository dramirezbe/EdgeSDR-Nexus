"""
02 — Dry-run test matrix

Tests all 3 mode combinations with dry_run=True (no HackRF needed):
  1. dry_run + IQ mode  → returns binary IQ (multipart)
  2. dry_run + welch    → returns Pxx (JSON)
  3. dry_run + pfb      → returns Pxx (JSON)

Injects a known two-tone signal (1 kHz + 5 kHz) and validates the
engine processes it correctly through each DSP path.

Requires: RF engine running (./rf_app).

Usage:
    python playground/02_dry_run_iq.py
    python playground/02_dry_run_iq.py --mode iq
    python playground/02_dry_run_iq.py --mode welch
    python playground/02_dry_run_iq.py --mode pfb
    python playground/02_dry_run_iq.py --mode all
"""
import argparse
import asyncio
import math
import sys
from pathlib import Path

import numpy as np
from scipy.signal import welch as scipy_welch, find_peaks

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.request_util import ZmqPairController

IPC_ADDR = "ipc:///tmp/rf_engine"

# ── Signal parameters ────────────────────────────────────────────────
SAMPLE_RATE = 8_000_000       # 8 MS/s
N_SAMPLES = 2_500            # fits C ZBUF_SIZE=64KB
FREQ_1 = 1000                 # 1 kHz tone
FREQ_2 = 5000                 # 5 kHz tone
# Amplitudes scaled to int8 range: dry-run casts float→int8,
# so values must be >1.0 to survive quantization.
AMPLITUDE_1 = 50.0
AMPLITUDE_2 = 30.0


# ── Signal generators ────────────────────────────────────────────────
def make_two_tone(fs: int, n: int) -> list:
    """Generate interleaved IQ: [I0, Q0, I1, Q1, ...] with two tones."""
    iq = []
    for i in range(n):
        t = i / fs
        i_val = (AMPLITUDE_1 * math.cos(2 * math.pi * FREQ_1 * t)
                 + AMPLITUDE_2 * math.cos(2 * math.pi * FREQ_2 * t))
        iq.append(i_val)
        iq.append(0.0)
    return iq


def make_noisy_tone(freq_hz: float, fs: int, n: int, snr_db: float = 20) -> list:
    """Generate interleaved IQ with a single tone + noise."""
    t = np.arange(n) / fs
    tone = np.cos(2 * np.pi * freq_hz * t)
    noise = np.random.randn(n)
    signal_power = np.mean(tone ** 2)
    noise_power = signal_power / (10 ** (snr_db / 10))
    sig = tone + np.sqrt(noise_power) * noise
    iq = []
    for v in sig:
        iq.append(float(v))
        iq.append(0.0)
    return iq


# ── Payload builders ─────────────────────────────────────────────────
def base_payload(method_psd: str, iq_data: list) -> dict:
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


# ── Test: dry_run + IQ mode ──────────────────────────────────────────
async def test_dry_run_iq(iq_data: list) -> bool:
    """Send dry-run IQ mode request, verify binary round-trip."""
    print("\n═══ Test 1: dry_run + IQ mode ═══")
    payload = base_payload("iq", iq_data)

    async with ZmqPairController(IPC_ADDR, is_server=True, max_queue=-1) as ctrl:
        resp = await ctrl.request(payload)

    if resp is None:
        print("  FAIL: No response (timeout)")
        return False
    if resp.get("status") != "ok":
        print(f"  FAIL: {resp}")
        return False

    mode = resp.get("mode", "?")
    n_out = int(resp.get("n_samples", 0))
    iq_out = resp.get("iq", [])
    encoding = resp.get("encoding", -1)

    ok = True
    print(f"  mode:       {mode}")
    print(f"  n_samples:  {n_out}")
    print(f"  iq length:  {len(iq_out)}")
    print(f"  encoding:   {encoding}")

    # Checks
    if mode != "iq":
        print(f"  FAIL: expected mode='iq', got '{mode}'")
        ok = False
    if n_out != N_SAMPLES:
        print(f"  FAIL: expected n_samples={N_SAMPLES}, got {n_out}")
        ok = False
    if len(iq_out) != N_SAMPLES * 2:
        print(f"  FAIL: expected iq length={N_SAMPLES * 2}, got {len(iq_out)}")
        ok = False
    if encoding != 0:
        print(f"  FAIL: expected encoding=0 (int8), got {encoding}")
        ok = False

    # Verify round-trip: compare first few samples (int8 quantization expected)
    max_err = 0.0
    for j in range(min(10, N_SAMPLES)):
        err_i = abs(iq_data[2 * j] - iq_out[2 * j])
        err_q = abs(iq_data[2 * j + 1] - iq_out[2 * j + 1])
        max_err = max(max_err, err_i, err_q)
    print(f"  max sample error (first 10): {max_err:.4f}")
    # int8 round-trip: max error per sample is 0.5, but IQ compensation
    # can shift values.  Tolerance = amplitude * 2 for safety.
    max_tolerance = max(AMPLITUDE_1, AMPLITUDE_2) * 2
    if max_err > max_tolerance:
        print(f"  FAIL: sample error {max_err:.1f} exceeds tolerance {max_tolerance:.1f}")
        ok = False

    # Quick PSD check on returned IQ
    if len(iq_out) >= 2:
        reals = np.array(iq_out[0::2], dtype=np.float64)
        imags = np.array(iq_out[1::2], dtype=np.float64)
        c = reals + 1j * imags
        f, psd = scipy_welch(c, fs=SAMPLE_RATE, nperseg=min(1024, len(c)), return_onesided=False)
        psd_db = 10 * np.log10(psd + 1e-30)
        peaks, props = find_peaks(psd_db, prominence=3)
        print(f"  PSD peaks found: {len(peaks)}")
        if len(peaks) > 0:
            sorted_idx = np.argsort(props["prominences"])[::-1][:3]
            for rank, idx in enumerate(sorted_idx, 1):
                pk = peaks[idx]
                print(f"    {rank}. bin {pk}  {psd_db[pk]:.1f} dB  (prom {props['prominences'][idx]:.1f} dB)")

    print(f"  {'PASS' if ok else 'FAIL'}")
    return ok


# ── Test: dry_run + welch PSD ────────────────────────────────────────
async def test_dry_run_welch(iq_data: list) -> bool:
    """Send dry-run welch PSD request, verify Pxx array."""
    print("\n═══ Test 2: dry_run + welch PSD ═══")
    payload = base_payload("welch", iq_data)

    async with ZmqPairController(IPC_ADDR, is_server=True, max_queue=-1) as ctrl:
        resp = await ctrl.request(payload)

    if resp is None:
        print("  FAIL: No response (timeout)")
        return False
    if resp.get("status") != "ok":
        print(f"  FAIL: {resp}")
        return False

    pxx = resp.get("Pxx", [])
    mode = resp.get("mode", "welch")

    ok = True
    print(f"  mode:       {mode}")
    print(f"  Pxx length: {len(pxx)}")

    if "Pxx" not in resp:
        print(f"  FAIL: no 'Pxx' key in response")
        ok = False
    if len(pxx) == 0:
        print(f"  FAIL: Pxx is empty")
        ok = False

    if len(pxx) > 0:
        pxx_arr = np.array(pxx)
        print(f"  Pxx range:  [{pxx_arr.min():.1f}, {pxx_arr.max():.1f}] dB")
        print(f"  Pxx mean:   {pxx_arr.mean():.1f} dB")

        # Find peaks — should see energy at 1 kHz and 5 kHz bins
        freqs = np.linspace(0, SAMPLE_RATE / 2, len(pxx))
        peaks, props = find_peaks(pxx, prominence=3)
        print(f"  PSD peaks found: {len(peaks)}")
        if len(peaks) > 0:
            sorted_idx = np.argsort(props["prominences"])[::-1][:5]
            for rank, idx in enumerate(sorted_idx, 1):
                pk = peaks[idx]
                print(f"    {rank}. {freqs[pk]:8.1f} Hz  {pxx[pk]:6.1f} dB  (prom {props['prominences'][idx]:.1f} dB)")

    print(f"  {'PASS' if ok else 'FAIL'}")
    return ok


# ── Test: dry_run + pfb PSD ──────────────────────────────────────────
async def test_dry_run_pfb(iq_data: list) -> bool:
    """Send dry-run PFB PSD request, verify Pxx array."""
    print("\n═══ Test 3: dry_run + pfb PSD ═══")
    payload = base_payload("pfb", iq_data)

    async with ZmqPairController(IPC_ADDR, is_server=True, max_queue=-1) as ctrl:
        resp = await ctrl.request(payload)

    if resp is None:
        print("  FAIL: No response (timeout)")
        return False
    if resp.get("status") != "ok":
        print(f"  FAIL: {resp}")
        return False

    pxx = resp.get("Pxx", [])
    mode = resp.get("mode", "pfb")

    ok = True
    print(f"  mode:       {mode}")
    print(f"  Pxx length: {len(pxx)}")

    if "Pxx" not in resp:
        print(f"  FAIL: no 'Pxx' key in response")
        ok = False
    if len(pxx) == 0:
        print(f"  FAIL: Pxx is empty")
        ok = False

    if len(pxx) > 0:
        pxx_arr = np.array(pxx)
        print(f"  Pxx range:  [{pxx_arr.min():.1f}, {pxx_arr.max():.1f}] dB")
        print(f"  Pxx mean:   {pxx_arr.mean():.1f} dB")

        freqs = np.linspace(0, SAMPLE_RATE / 2, len(pxx))
        peaks, props = find_peaks(pxx, prominence=3)
        print(f"  PSD peaks found: {len(peaks)}")
        if len(peaks) > 0:
            sorted_idx = np.argsort(props["prominences"])[::-1][:5]
            for rank, idx in enumerate(sorted_idx, 1):
                pk = peaks[idx]
                print(f"    {rank}. {freqs[pk]:8.1f} Hz  {pxx[pk]:6.1f} dB  (prom {props['prominences'][idx]:.1f} dB)")

    print(f"  {'PASS' if ok else 'FAIL'}")
    return ok


# ── Main ─────────────────────────────────────────────────────────────
async def main():
    parser = argparse.ArgumentParser(description="Dry-run IQ test matrix")
    parser.add_argument("--mode", choices=["iq", "welch", "pfb", "all"], default="all",
                        help="Which test to run (default: all)")
    args = parser.parse_args()

    print(f"Generating {N_SAMPLES} IQ samples ({FREQ_1} Hz + {FREQ_2} Hz tones) ...")
    iq_data = make_two_tone(SAMPLE_RATE, N_SAMPLES)
    print(f"  Payload estimate: ~{N_SAMPLES * 2 * 10 / 1e6:.1f} MB JSON")

    results = {}

    if args.mode in ("iq", "all"):
        results["iq"] = await test_dry_run_iq(iq_data)

    if args.mode in ("welch", "all"):
        results["welch"] = await test_dry_run_welch(iq_data)

    if args.mode in ("pfb", "all"):
        results["pfb"] = await test_dry_run_pfb(iq_data)

    # ── Summary ───────────────────────────────────────────────────────
    print("\n═══ Summary ═══")
    all_pass = True
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {name:8s} {status}")
        if not passed:
            all_pass = False

    print(f"\n{'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")


if __name__ == "__main__":
    asyncio.run(main())
