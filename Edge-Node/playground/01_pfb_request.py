"""
01 — PFB PSD request (no server needed)

Sends a standard PSD request via ZMQ to the RF engine using PFB method.
Requires: RF engine running (./rf_app) + HackRF connected.

Usage:
    python playground/01_pfb_request.py
"""
import asyncio
import json
import zmq
import zmq.asyncio

IPC_ADDR = "ipc:///tmp/rf_engine"

# ── Payload ───────────────────────────────────────────────────────────
PAYLOAD = {
    "center_freq_hz": 98_000_000,      # 98 MHz FM band
    "sample_rate_hz": 8_000_000,       # 8 MS/s
    "method_psd": "pfb",               # PFB PSD method
    "rbw_hz": 100_000,                 # 100 kHz resolution
    "overlap": 0.5,
    "window": "hamming",
    "lna_gain": 16,
    "vga_gain": 20,
    "antenna_amp": True,
    "antenna_port": 1,
    "cooldown_request": 1.0,
    "ppm_error": 0.0,
    "demodulation": None,              # no audio demod
    "filter": None,
}


async def run():
    ctx = zmq.asyncio.Context()
    sock = ctx.socket(zmq.REQ)
    sock.setsockopt(zmq.LINGER, 0)
    sock.connect(IPC_ADDR)

    print(f"Sending PFB request to {IPC_ADDR} ...")
    await sock.send_string(json.dumps(PAYLOAD))

    resp_raw = await sock.recv_string()
    resp = json.loads(resp_raw)
    sock.close()
    ctx.term()

    # ── Response ──────────────────────────────────────────────────────
    if resp.get("status") != "ok":
        print(f"ERROR: {resp}")
        return

    pxx = resp.get("Pxx", [])
    start_mhz = resp.get("start_freq_hz", 0) / 1e6
    end_mhz = resp.get("end_freq_hz", 0) / 1e6

    print(f"\n--- PFB PSD Result ---")
    print(f"  Band:       {start_mhz:.2f} – {end_mhz:.2f} MHz")
    print(f"  Bins:       {len(pxx)}")
    print(f"  PSD range:  [{min(pxx):.1f}, {max(pxx):.1f}] dBm/Hz")
    print(f"  First 5:    {pxx[:5]}")


if __name__ == "__main__":
    asyncio.run(run())
