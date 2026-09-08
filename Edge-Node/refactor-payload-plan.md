# Refactor: IQ Mode + Dry-Run Payload

> **Goal:** Add `"method_psd": "iq"` support to the RF engine, returning raw complex IQ samples instead of PSD. Add `"dry_run": true` support to inject IQ vectors, bypassing the HackRF hardware.
>
> **Scope:** `Edge-Node/rf/` (C data plane) + `Edge-Node/utils/` + `Edge-Node/functions.py` (Python control plane)
>
> **Constraint:** No new threads, no new ZMQ protocol, no structural changes to the main loop. All changes are additive branches inside existing functions.

---

## 1. New IPC Contract

### 1.1 Request — IQ mode

```json
{
  "center_freq_hz": 98000000,
  "sample_rate_hz": 8000000,
  "method_psd": "iq",
  "demodulation": null,
  "lna_gain": 16,
  "vga_gain": 20,
  "antenna_amp": true,
  "antenna_port": 1,
  "cooldown_request": 1.0
}
```

### 1.2 Request — Dry-run (works with any method_psd)

```json
{
  "center_freq_hz": 98000000,
  "sample_rate_hz": 8000000,
  "method_psd": "welch",
  "demodulation": null,
  "dry_run": true,
  "dry_run_iq": [0.12, -0.34, 0.56, -0.78]
}
```

### 1.3 Response — IQ mode

```json
{
  "status": "ok",
  "mode": "iq",
  "start_freq_hz": 94000000,
  "end_freq_hz": 102000000,
  "sample_rate_hz": 8000000,
  "n_samples": 4000000,
  "iq": [0.123, -0.456, 0.789]
}
```

### 1.4 Response — PSD mode (unchanged)

```json
{
  "status": "ok",
  "start_freq_hz": 94000000,
  "end_freq_hz": 102000000,
  "Pxx": [-12.3, -14.1]
}
```

---

## 2. Work Units

### WU-1: Add `IQ` to `Psd_method` enum

**File:** `rf/libs/datatypes.h`

**Change:**
```c
typedef enum {
    WELCH,  // existing
    PFB,    // existing
    IQ      // new: return raw complex IQ samples
} Psd_method;
```

**Validation:** Compile check — no logic change.

---

### WU-2: Parse `"method_psd": "iq"` in `parser.c`

**File:** `rf/libs/parser.c`

**Change:** Replace the binary PFB/Welch parse with a three-way:

```c
cJSON *m_psd = cJSON_GetObjectItemCaseSensitive(root, "method_psd");
if (cJSON_IsString(m_psd)) {
    if (strcasecmp(m_psd->valuestring, "pfb") == 0)     target->method_psd = PFB;
    else if (strcasecmp(m_psd->valuestring, "iq") == 0) target->method_psd = IQ;
    else                                                 target->method_psd = WELCH;
}
```

**Also update** `print_config_summary_DEBUG` and `print_config_summary_DEPLOY`:
- Add `"IQ"` to the `psd_methods[]` lookup table (index 2).

**Validation:** Compile check + run `rf_app` with a test JSON containing `"method_psd": "iq"` and verify the config summary prints `IQ`.

---

### WU-3: Add `publish_iq_results()` to `rf.c`

**File:** `rf/rf.c`

**New function** (placed next to `publish_results()`):

```c
static int publish_iq_results(
    const double complex *iq_data,
    size_t n_samples,
    SDR_cfg_t *local_hack,
    uint64_t original_center_freq
) {
    if (!zmq_channel || !iq_data || n_samples == 0) return -1;

    cJSON *root = cJSON_CreateObject();
    if (!root) return -1;

    double fs = local_hack->sample_rate;
    double start_freq = (double)original_center_freq - (fs / 2.0);
    double end_freq   = (double)original_center_freq + (fs / 2.0);

    cJSON_AddStringToObject(root, "status", "ok");
    cJSON_AddStringToObject(root, "mode", "iq");
    cJSON_AddNumberToObject(root, "start_freq_hz", start_freq);
    cJSON_AddNumberToObject(root, "end_freq_hz", end_freq);
    cJSON_AddNumberToObject(root, "sample_rate_hz", fs);
    cJSON_AddNumberToObject(root, "n_samples", (double)n_samples);

    // Serialize interleaved [I0, Q0, I1, Q1, ...]
    double *interleaved = (double*)malloc(n_samples * 2 * sizeof(double));
    if (!interleaved) { cJSON_Delete(root); return -1; }
    for (size_t i = 0; i < n_samples; ++i) {
        interleaved[2*i]     = creal(iq_data[i]);
        interleaved[2*i + 1] = cimag(iq_data[i]);
    }
    cJSON_AddItemToObject(root, "iq",
        cJSON_CreateDoubleArray(interleaved, (int)(n_samples * 2)));
    free(interleaved);

    int rc = send_json_reply(root);
    cJSON_Delete(root);
    return rc;
}
```

**Validation:** Compile check + verify cJSON API usage matches existing `publish_results()` pattern.

---

### WU-4: Branch IQ mode in `rf.c` main loop

**File:** `rf/rf.c` — main loop, after `load_iq_into_signal` + `iq_compensation` + optional filter.

**Current flow (lines ~1466-1500):**
```c
if (load_iq_into_signal(...) == 0) {
    iq_compensation(&proc_ws.sig);
    if (local_desired.filter_enabled) { chan_filter_apply_inplace_abs(...); }

    if (local_desired.method_psd == PFB) {
        execute_pfb_psd(...);
    } else {
        execute_welch_psd(...);
    }

    if (publish_results(...) != 0) { ... }
}
```

**New flow:**
```c
if (load_iq_into_signal(...) == 0) {
    iq_compensation(&proc_ws.sig);
    if (local_desired.filter_enabled) { chan_filter_apply_inplace_abs(...); }

    if (local_desired.method_psd == IQ) {
        // IQ mode: skip PSD, publish raw complex samples
        if (publish_iq_results(
                proc_ws.sig.signal_iq,
                proc_ws.sig.n_signal,
                &local_hack,
                local_desired.center_freq
            ) != 0) {
            fprintf(stderr, "[RF] Error: Failed to send IQ reply.\n");
            clock_gettime(CLOCK_MONOTONIC, &last_activity_time);
            continue;
        }
    } else {
        // PSD mode: existing path unchanged
        if (local_desired.method_psd == PFB) {
            execute_pfb_psd(...);
        } else {
            execute_welch_psd(...);
        }

        if (publish_results(...) != 0) { ... }
    }
}
```

**Also update** `print_config_summary_DEBUG` and `print_config_summary_DEPLOY` in `parser.c`:
- Add `"IQ"` to the `psd_methods[]` lookup table:
  ```c
  const char* psd_methods[] = {"Welch", "PFB", "IQ"};
  ```

**Validation:** Compile check + verify no regression in PSD mode.

---

### WU-5: Python — accept `"iq"` in `method_psd` validation

**File:** `utils/request_util.py`

**Change** (line 78):
```python
# Before:
if self.method_psd not in ["pfb", "welch"]:
    self.method_psd = "pfb"
    raise ValueError(f"Metodo PSD {self.method_psd} invalido. Debe ser pfb o welch.")

# After:
if self.method_psd not in ["pfb", "welch", "iq"]:
    self.method_psd = "pfb"
    raise ValueError(f"Metodo PSD {self.method_psd} invalido. Debe ser pfb, welch o iq.")
```

**Validation:** Python syntax check.

---

### WU-6: Python — skip DC correction when mode is IQ

**File:** `functions.py` — `_apply_dc_correction_to_acquisition()`

**Change:** Early return when the response indicates IQ mode:

```python
def _apply_dc_correction_to_acquisition(self, acquisition_result):
    if not isinstance(acquisition_result, dict):
        raise TypeError("Se esperaba que _single_acquire devolviera un dict.")

    # IQ mode returns raw complex samples, not PSD — skip DC correction
    if acquisition_result.get("mode") == "iq":
        return acquisition_result

    if "Pxx" not in acquisition_result:
        raise KeyError("No se encontro la llave 'Pxx' en acquisition_result.")
    # ... rest unchanged
```

**Validation:** Python syntax check.

---

### WU-7: Dry-run — add fields to `DesiredCfg_t`

**File:** `rf/libs/datatypes.h`

**Add to `DesiredCfg_t`:**
```c
typedef struct {
    // ... existing fields ...

    /** @name Dry-run injection */
    /**@{*/
    bool     dry_run;           /**< Bypass HackRF, use injected IQ vector. */
    double  *dry_run_iq;        /**< Injected IQ samples (interleaved I,Q). */
    size_t   dry_run_iq_len;    /**< Number of complex samples in dry_run_iq. */
    /**@}*/
} DesiredCfg_t;
```

**Note:** `dry_run_iq` is a heap-allocated array parsed from JSON. Must be freed after use or on config reset.

**Validation:** Compile check.

---

### WU-8: Dry-run — parse `"dry_run"` and `"dry_run_iq"` in `parser.c`

**File:** `rf/libs/parser.c`

**Add to `parse_config_rf()`** (after existing parsing, before `cJSON_Delete(root)`):

```c
// Dry-run injection
cJSON *dry = cJSON_GetObjectItemCaseSensitive(root, "dry_run");
if (cJSON_IsBool(dry)) target->dry_run = cJSON_IsTrue(dry);

cJSON *dry_iq = cJSON_GetObjectItemCaseSensitive(root, "dry_run_iq");
if (cJSON_IsArray(dry_iq) && target->dry_run) {
    int arr_len = cJSON_GetArraySize(dry_iq);
    if (arr_len > 0 && (arr_len % 2) == 0) {
        size_t n_complex = (size_t)(arr_len / 2);
        target->dry_run_iq = (double*)malloc(arr_len * sizeof(double));
        if (target->dry_run_iq) {
            target->dry_run_iq_len = n_complex;
            for (int i = 0; i < arr_len; ++i) {
                cJSON *item = cJSON_GetArrayItem(dry_iq, i);
                target->dry_run_iq[i] = cJSON_IsNumber(item) ? item->valuedouble : 0.0;
            }
        }
    }
}
```

**Also update** `set_default_config()`:
```c
target->dry_run = false;
target->dry_run_iq = NULL;
target->dry_run_iq_len = 0;
```

**Validation:** Compile check + verify JSON parse doesn't leak on repeated calls.

---

### WU-9: Dry-run — inject IQ into ring buffer in `rf.c` main loop

**File:** `rf/rf.c` — main loop, before the HackRF open/tune/start sequence.

**Insert** after `apply_runtime_request()` and before `ensure_hackrf_session_is_healthy()`:

```c
if (local_desired.dry_run && local_desired.dry_run_iq && local_desired.dry_run_iq_len > 0) {
    printf("[RF] DRY-RUN: injecting %zu complex samples\n", local_desired.dry_run_iq_len);

    // Convert double complex IQ to int8 interleaved bytes for ring buffer
    size_t n_bytes = local_desired.dry_run_iq_len * 2; // I,Q as int8 pairs
    int8_t *dry_bytes = (int8_t*)malloc(n_bytes);
    if (dry_bytes) {
        for (size_t i = 0; i < local_desired.dry_run_iq_len; ++i) {
            double i_val = local_desired.dry_run_iq[2*i];
            double q_val = local_desired.dry_run_iq[2*i + 1];
            // Clamp to int8 range [-128, 127]
            dry_bytes[2*i]     = (int8_t)(i_val > 127.0 ? 127.0 : (i_val < -128.0 ? -128.0 : i_val));
            dry_bytes[2*i + 1] = (int8_t)(q_val > 127.0 ? 127.0 : (q_val < -128.0 ? -128.0 : q_val));
        }

        rb_reset(&rb);
        rb_write(&rb, dry_bytes, n_bytes);
        free(dry_bytes);

        // Signal main thread that data is available
        pthread_mutex_lock(&rb_mutex);
        pthread_cond_signal(&rb_cond);
        pthread_mutex_unlock(&rb_mutex);

        // Skip hardware entirely — jump straight to DSP pipeline
        // by falling through to the existing wait/consume logic below
    } else {
        fprintf(stderr, "[RF] DRY-RUN: malloc failed\n");
        send_status_reply("error", "dry_run_alloc_failed");
        clock_gettime(CLOCK_MONOTONIC, &last_activity_time);
        continue;
    }
}
```

**After the dry-run block**, the existing code continues:
- `ensure_hackrf_session_is_healthy()` — skip in dry-run? **No**, keep it. If `device == NULL` it returns 0, and the dry-run path never opens the device. The health check is harmless.
- `hackrf_open` — skip in dry-run? **Yes**, wrap in `if (!local_desired.dry_run)`.
- `hackrf_apply_cfg` / `hackrf_start_rx` — skip in dry-run? **Yes**, wrap in `if (!local_desired.dry_run)`.
- `rb_discard_all(&rb)` — skip in dry-run? **Yes**, we just wrote to it. Wrap in `if (!local_desired.dry_run)`.
- `wait_iq_with_timeout` — in dry-run, the data is already in the ring buffer, so `rb_available(&rb) >= local_rb.total_bytes` will be true immediately. No change needed.
- `rf_workspace_ensure` — needs `local_rb.total_bytes` to match the injected data size. In dry-run, set `local_rb.total_bytes = local_desired.dry_run_iq_len * 2` before the workspace check.

**Full dry-run gate:**
```c
// --- DRY-RUN: bypass hardware ---
if (local_desired.dry_run) {
    // Inject IQ into ring buffer (code above)
    // Set buffer size to match injected data
    local_rb.total_bytes = local_desired.dry_run_iq_len * 2;
    // Skip all hardware operations
} else {
    // Existing hardware path: open, tune, start_rx, discard stale
    if (ensure_hackrf_session_is_healthy() != 0) { ... }
    if (device == NULL) { ... }
    if (needs_tune) { ... }
    if (stop_streaming) { ... }
    rb_discard_all(&rb);
}
```

**Free dry_run_iq after use:**
```c
// After the DSP pipeline completes (after publish_results or publish_iq_results)
if (local_desired.dry_run_iq) {
    free(local_desired.dry_run_iq);
    local_desired.dry_run_iq = NULL;
    local_desired.dry_run_iq_len = 0;
}
```

**Validation:** Compile check + manual test with a known IQ vector.

---

### WU-10: Update JSON contract documentation

**File:** `json/rf-engine/params.jsonc`

Add `"iq"` as a valid `method_psd` value and document `dry_run` / `dry_run_iq`.

**File:** `json/POST-data.jsonc`

Add the IQ response format alongside the PSD format.

**Validation:** JSON syntax check.

---

## 3. Implementation Order

```
WU-1 (enum)          ─┐
WU-2 (parser)         ├─ C IQ mode (compileable after WU-1..4)
WU-3 (publish_iq)     │
WU-4 (main loop)     ─┘
WU-5 (python valid)  ─┐
WU-6 (python dc)     ─┘─ Python IQ mode
WU-7 (dry fields)    ─┐
WU-8 (dry parser)     ├─ C dry-run (compileable after WU-7..9)
WU-9 (dry inject)    ─┘
WU-10 (docs)         ── Documentation
```

**Recommended order:** WU-1 → WU-2 → WU-3 → WU-4 → WU-5 → WU-6 → WU-7 → WU-8 → WU-9 → WU-10

IQ mode (WU-1..6) is independent of dry-run (WU-7..9). Either can be done first.

---

## 4. Files Changed

| File | WU | Lines | Nature |
|------|----|-------|--------|
| `rf/libs/datatypes.h` | WU-1, WU-7 | +4 | Add `IQ` enum + dry-run fields |
| `rf/libs/parser.c` | WU-2, WU-8 | +25 | Parse `"iq"` + dry-run JSON |
| `rf/rf.c` | WU-3, WU-4, WU-9 | +80 | `publish_iq_results()` + IQ branch + dry-run injection |
| `utils/request_util.py` | WU-5 | +1 | Add `"iq"` to validation |
| `functions.py` | WU-6 | +3 | Skip DC correction for IQ mode |
| `json/rf-engine/params.jsonc` | WU-10 | +5 | Document new fields |
| `json/POST-data.jsonc` | WU-10 | +8 | Document IQ response |

**Total: ~126 lines added, ~0 lines removed.**

---

## 5. Testing Plan

### 5.1 Compile check
```bash
cd Edge-Node
./build.sh -dev
```

### 5.2 IQ mode — manual test via Python REPL
```python
import asyncio, zmq, json

async def test_iq():
    ctx = zmq.asyncio.Context()
    sock = ctx.socket(zmq.REQ)
    sock.connect("ipc:///tmp/rf_engine")
    await sock.send_string(json.dumps({
        "center_freq_hz": 98000000,
        "sample_rate_hz": 8000000,
        "method_psd": "iq",
        "demodulation": None,
        "lna_gain": 16,
        "vga_gain": 20,
        "antenna_amp": True,
        "antenna_port": 1,
        "cooldown_request": 1.0
    }))
    resp = await sock.recv_string()
    data = json.loads(resp)
    assert data["status"] == "ok"
    assert data["mode"] == "iq"
    assert "iq" in data
    assert "Pxx" not in data
    print(f"IQ mode OK: {data['n_samples']} samples")

asyncio.run(test_iq())
```

### 5.3 Dry-run — manual test
```python
import asyncio, zmq, json, math

async def test_dry_run():
    # Generate a simple sine wave IQ vector
    n = 10000
    iq = []
    for i in range(n):
        t = i / 8000000.0
        iq.append(math.cos(2 * math.pi * 1000 * t))  # I
        iq.append(math.sin(2 * math.pi * 1000 * t))  # Q

    ctx = zmq.asyncio.Context()
    sock = ctx.socket(zmq.REQ)
    sock.connect("ipc:///tmp/rf_engine")
    await sock.send_string(json.dumps({
        "center_freq_hz": 98000000,
        "sample_rate_hz": 8000000,
        "method_psd": "welch",
        "demodulation": None,
        "dry_run": True,
        "dry_run_iq": iq
    }))
    resp = await sock.recv_string()
    data = json.loads(resp)
    assert data["status"] == "ok"
    assert "Pxx" in data
    print(f"Dry-run OK: {len(data['Pxx'])} PSD bins")

asyncio.run(test_dry_run())
```

### 5.4 Regression — PSD mode unchanged
Run existing `test/tester.py` and verify no behavioral change.

---

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large IQ JSON payload saturates ZMQ IPC | High | Add `iq_decimation` parameter in a follow-up; start with small `sample_rate` in tests |
| `dry_run_iq` memory leak on repeated requests | Medium | Free after each use in main loop; `set_default_config` resets to NULL |
| Calibration (`calibrate_hackrf`) assumes real hardware | Low | Dry-run skips calibration path entirely (separate `if (local_desired.calibrate)` branch) |
| Python DC correction crashes on IQ response | Low | WU-6 adds early return before `Pxx` access |
| `int8` quantization loses precision in dry-run | Low | Document that dry-run IQ is clamped to int8 range; use values in [-128, 127] |

---

## 7. Follow-up (not in this plan)

- `iq_decimation` parameter to reduce IQ payload size
- Binary ZMQ frames for IQ payloads (instead of JSON doubles)
- Python helper to load IQ vectors from `.npy` / `.cfile` for dry-run testing
- `campaign_runner.py` support for IQ mode captures
