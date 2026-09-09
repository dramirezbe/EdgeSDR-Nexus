"""
test_matrix.py — Comprehensive payload test matrix for the RF engine.

Tests every meaningful combination of payload fields using dry-run mode
(no HackRF required).  Validates response shape, data presence, and
basic sanity for each scenario.

Dimensions tested:
  method_psd  : welch | pfb | iq
  demodulation: null | fm | am       (PSD modes only)
  filter      : null | {start, end}  (PSD modes only)
  window      : hamming | hann | blackman
  sample_rate : 2M | 8M
  center_freq : 98M | 103M
  gains       : 0/0 | 16/20
  antenna_amp : true | false
  rbw_hz      : 100k | 250k
  overlap     : 0.5 | 0.75

Usage:
    python playground/test_matrix.py
    python playground/test_matrix.py --verbose
"""
import argparse
import asyncio
import math
import sys
import time
from pathlib import Path
from dataclasses import dataclass, field

import numpy as np
from scipy.signal import welch as scipy_welch, find_peaks

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.request_util import ZmqPairController

IPC_ADDR = "ipc:///tmp/rf_engine"


# ── Signal generator ─────────────────────────────────────────────────
def make_two_tone(fs: int, n: int, f1: float = 1000, f2: float = 5000,
                  a1: float = 50.0, a2: float = 30.0) -> list:
    """Interleaved IQ with two tones, amplitudes in int8 range."""
    iq = []
    for i in range(n):
        t = i / fs
        val = a1 * math.cos(2 * math.pi * f1 * t) + a2 * math.cos(2 * math.pi * f2 * t)
        iq.append(val)
        iq.append(0.0)
    return iq


# ── Test result ──────────────────────────────────────────────────────
@dataclass
class TestResult:
    name: str
    passed: bool
    details: str = ""
    duration_ms: float = 0.0
    response_keys: list = field(default_factory=list)


# ── Payload builder ──────────────────────────────────────────────────
def payload(
    method_psd: str = "welch",
    demodulation: str | None = None,
    dry_run: bool = True,
    dry_run_iq: list | None = None,
    center_freq_hz: int = 98_000_000,
    sample_rate_hz: int = 8_000_000,
    lna_gain: int = 0,
    vga_gain: int = 0,
    antenna_amp: bool = False,
    antenna_port: int = 1,
    rbw_hz: int = 100_000,
    overlap: float = 0.5,
    window: str = "hamming",
    ppm_error: float = 0.0,
    filter_cfg: dict | None = None,
    cooldown_request: float = 0.0,
) -> dict:
    p = {
        "center_freq_hz": center_freq_hz,
        "sample_rate_hz": sample_rate_hz,
        "method_psd": method_psd,
        "demodulation": demodulation,
        "lna_gain": lna_gain,
        "vga_gain": vga_gain,
        "antenna_amp": antenna_amp,
        "antenna_port": antenna_port,
        "cooldown_request": cooldown_request,
        "ppm_error": ppm_error,
        "rbw_hz": rbw_hz,
        "overlap": overlap,
        "window": window,
        "filter": filter_cfg,
        "dry_run": dry_run,
    }
    if dry_run_iq is not None:
        p["dry_run_iq"] = dry_run_iq
    return p


# ── Validators ───────────────────────────────────────────────────────
def validate_response(resp: dict, expect: dict) -> tuple[bool, str]:
    """Validate response against expected conditions.
    
    expect keys:
        status     : expected status string (default "ok")
        has_keys   : list of keys that must be present
        min_length : {key: min_length} for array fields
        mode       : expected mode string (for IQ)
        pxx_range  : (min, max) sanity range for Pxx values
    """
    if resp is None:
        return False, "No response (timeout)"

    errors = []

    # Status
    expected_status = expect.get("status", "ok")
    if resp.get("status") != expected_status:
        errors.append(f"status={resp.get('status')!r}, expected {expected_status!r}")
        if resp.get("status") == "error":
            errors.append(f"  error reason: {resp.get('reason', '?')}")
            return False, "; ".join(errors)

    # Required keys
    for key in expect.get("has_keys", []):
        if key not in resp:
            errors.append(f"missing key '{key}'")

    # Array minimum lengths
    for key, min_len in expect.get("min_length", {}).items():
        val = resp.get(key, [])
        if len(val) < min_len:
            errors.append(f"'{key}' length={len(val)}, expected >= {min_len}")

    # Mode check (IQ mode)
    if "mode" in expect:
        if resp.get("mode") != expect["mode"]:
            errors.append(f"mode={resp.get('mode')!r}, expected {expect['mode']!r}")

    # Pxx sanity range
    if "pxx_range" in expect and "Pxx" in resp:
        pxx = resp["Pxx"]
        if len(pxx) > 0:
            lo, hi = expect["pxx_range"]
            pxx_min, pxx_max = min(pxx), max(pxx)
            if pxx_min < lo or pxx_max > hi:
                errors.append(f"Pxx range [{pxx_min:.1f}, {pxx_max:.1f}] outside [{lo}, {hi}]")

    return (len(errors) == 0), "; ".join(errors)


# ── Send request ─────────────────────────────────────────────────────
async def send(p: dict) -> dict | None:
    try:
        async with ZmqPairController(IPC_ADDR, is_server=True, max_queue=-1) as ctrl:
            return await ctrl.request(p)
    except TimeoutError:
        return None


# ── Test definitions ─────────────────────────────────────────────────
async def define_tests(iq_data: list) -> list[tuple[str, dict, dict]]:
    """Return list of (name, payload, expected_validation) tuples."""
    N = len(iq_data) // 2  # complex samples
    tests = []

    # ─── 1. method_psd × demodulation (dry_run, no filter) ───────────
    for method in ("welch", "pfb"):
        for demod in (None, "fm", "am"):
            label = demod or "none"
            name = f"{method}+demod={label}"
            p = payload(method_psd=method, demodulation=demod, dry_run_iq=iq_data)
            exp = {"has_keys": ["Pxx"], "min_length": {"Pxx": 1}, "pxx_range": (-200, 20)}
            tests.append((name, p, exp))

    # IQ mode ignores demodulation
    name = "iq+demod=none"
    p = payload(method_psd="iq", dry_run_iq=iq_data)
    exp = {"mode": "iq", "has_keys": ["iq", "encoding", "n_samples"],
           "min_length": {"iq": 2}, "encoding": 0}
    tests.append((name, p, exp))

    # ─── 2. method_psd × filter (dry_run, no demod) ──────────────────
    for method in ("welch", "pfb"):
        # No filter
        name = f"{method}+filter=off"
        p = payload(method_psd=method, dry_run_iq=iq_data)
        exp = {"has_keys": ["Pxx"], "min_length": {"Pxx": 1}, "pxx_range": (-200, 20)}
        tests.append((name, p, exp))

        # With filter (center ±2 MHz)
        name = f"{method}+filter=on"
        p = payload(method_psd=method, dry_run_iq=iq_data,
                     filter_cfg={"start_freq_hz": 96_000_000, "end_freq_hz": 100_000_000})
        exp = {"has_keys": ["Pxx"], "min_length": {"Pxx": 1}, "pxx_range": (-200, 20)}
        tests.append((name, p, exp))

    # ─── 3. window types (dry_run + welch) ────────────────────────────
    for window in ("hamming", "hann", "blackman", "flattop", "kaiser", "tukey", "bartlett", "rectangular"):
        name = f"welch+window={window}"
        p = payload(method_psd="welch", window=window, dry_run_iq=iq_data)
        exp = {"has_keys": ["Pxx"], "min_length": {"Pxx": 1}, "pxx_range": (-200, 20)}
        tests.append((name, p, exp))

    # ─── 4. sample_rate (dry_run + welch) ─────────────────────────────
    for sr in (2_000_000, 8_000_000):
        iq = make_two_tone(sr, min(N, sr // 100))  # ~10 ms of data
        name = f"welch+sr={sr // 1_000_000}M"
        p = payload(method_psd="welch", sample_rate_hz=sr, dry_run_iq=iq)
        exp = {"has_keys": ["Pxx"], "min_length": {"Pxx": 1}, "pxx_range": (-200, 20)}
        tests.append((name, p, exp))

    # ─── 5. center_freq (dry_run + welch) ─────────────────────────────
    for fc in (98_000_000, 103_000_000):
        name = f"welch+fc={fc // 1_000_000}M"
        p = payload(method_psd="welch", center_freq_hz=fc, dry_run_iq=iq_data)
        exp = {"has_keys": ["Pxx"], "min_length": {"Pxx": 1}, "pxx_range": (-200, 20)}
        tests.append((name, p, exp))

    # ─── 6. gains (dry_run + welch) ───────────────────────────────────
    for lna, vga in ((0, 0), (16, 20)):
        name = f"welch+gain={lna}/{vga}"
        p = payload(method_psd="welch", lna_gain=lna, vga_gain=vga, dry_run_iq=iq_data)
        exp = {"has_keys": ["Pxx"], "min_length": {"Pxx": 1}, "pxx_range": (-200, 20)}
        tests.append((name, p, exp))

    # ─── 7. antenna_amp (dry_run + welch) ─────────────────────────────
    for amp in (True, False):
        name = f"welch+amp={amp}"
        p = payload(method_psd="welch", antenna_amp=amp, dry_run_iq=iq_data)
        exp = {"has_keys": ["Pxx"], "min_length": {"Pxx": 1}, "pxx_range": (-200, 20)}
        tests.append((name, p, exp))

    # ─── 8. rbw_hz (dry_run + welch) ──────────────────────────────────
    for rbw in (100_000, 250_000):
        name = f"welch+rbw={rbw // 1000}k"
        p = payload(method_psd="welch", rbw_hz=rbw, dry_run_iq=iq_data)
        exp = {"has_keys": ["Pxx"], "min_length": {"Pxx": 1}, "pxx_range": (-200, 20)}
        tests.append((name, p, exp))

    # ─── 9. overlap (dry_run + welch) ─────────────────────────────────
    for ovp in (0.5, 0.75):
        name = f"welch+overlap={ovp}"
        p = payload(method_psd="welch", overlap=ovp, dry_run_iq=iq_data)
        exp = {"has_keys": ["Pxx"], "min_length": {"Pxx": 1}, "pxx_range": (-200, 20)}
        tests.append((name, p, exp))

    # ─── 10. combined: welch + fm + filter + hann ─────────────────────
    name = "welch+fm+filter+hann"
    p = payload(method_psd="welch", demodulation="fm", window="hann",
                filter_cfg={"start_freq_hz": 96_000_000, "end_freq_hz": 100_000_000},
                dry_run_iq=iq_data)
    exp = {"has_keys": ["Pxx"], "min_length": {"Pxx": 1}, "pxx_range": (-200, 20)}
    tests.append((name, p, exp))

    # ─── 11. combined: pfb + am + filter + blackman ───────────────────
    name = "pfb+am+filter+blackman"
    p = payload(method_psd="pfb", demodulation="am", window="blackman",
                filter_cfg={"start_freq_hz": 96_000_000, "end_freq_hz": 100_000_000},
                dry_run_iq=iq_data)
    exp = {"has_keys": ["Pxx"], "min_length": {"Pxx": 1}, "pxx_range": (-200, 20)}
    tests.append((name, p, exp))

    # ─── 12. IQ mode: verify binary round-trip ────────────────────────
    name = "iq+binary_roundtrip"
    p = payload(method_psd="iq", dry_run_iq=iq_data)
    exp = {"mode": "iq", "has_keys": ["iq", "encoding", "n_samples", "center_freq_hz"],
           "min_length": {"iq": N * 2}}
    tests.append((name, p, exp))

    return tests


# ── Run all tests ────────────────────────────────────────────────────
async def run_tests(verbose: bool = False):
    SAMPLE_RATE = 8_000_000
    N_SAMPLES = 2_500

    print(f"Generating {N_SAMPLES} IQ samples (1 kHz + 5 kHz tones, int8-scaled) ...")
    iq_data = make_two_tone(SAMPLE_RATE, N_SAMPLES)

    tests = await define_tests(iq_data)
    print(f"Running {len(tests)} test scenarios ...\n")

    results: list[TestResult] = []
    for name, p, exp in tests:
        t0 = time.monotonic()
        resp = await send(p)
        dt = (time.monotonic() - t0) * 1000

        passed, details = validate_response(resp, exp)

        # Extra IQ round-trip check
        if passed and exp.get("mode") == "iq" and resp:
            iq_out = resp.get("iq", [])
            max_err = 0.0
            for j in range(min(10, N_SAMPLES)):
                ei = abs(iq_data[2*j] - iq_out[2*j])
                eq = abs(iq_data[2*j+1] - iq_out[2*j+1])
                max_err = max(max_err, ei, eq)
            if max_err > 100:
                passed = False
                details += f"; IQ round-trip error {max_err:.1f} too large"

        status = "PASS" if passed else "FAIL"
        icon = "✓" if passed else "✗"
        keys_str = ""
        if resp and verbose:
            keys_str = f"  keys={list(resp.keys())}"

        print(f"  {icon} {name:40s} {status:4s} ({dt:5.0f} ms){keys_str}")
        if not passed and details:
            print(f"    → {details}")

        results.append(TestResult(name=name, passed=passed, details=details,
                                  duration_ms=dt,
                                  response_keys=list(resp.keys()) if resp else []))

    # ── Summary ───────────────────────────────────────────────────────
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    total_ms = sum(r.duration_ms for r in results)

    print(f"\n{'═' * 56}")
    print(f"  {passed}/{total} passed, {failed} failed  ({total_ms:.0f} ms total)")

    if failed > 0:
        print(f"\n  Failed tests:")
        for r in results:
            if not r.passed:
                print(f"    ✗ {r.name}: {r.details}")

    return failed == 0


# ── Entry ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RF engine payload test matrix")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show response keys")
    args = parser.parse_args()
    ok = asyncio.run(run_tests(verbose=args.verbose))
    sys.exit(0 if ok else 1)
