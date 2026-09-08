# Task Playbooks

> Decision-tree playbooks for common development tasks. Each playbook maps a goal to the files to touch and verification steps.

---

## 1. Add a New REST Endpoint

**Goal:** Expose a new API route from backend to frontend.

1. **Define route** in `backend/src/routes/<section>.ts` — add `router.get/post/put/delete(...)` handler
2. **Add model** in `backend/src/models/<Model>.ts` — SQL query functions
3. **Add types** in `backend/src/types/index.ts` — request/response interfaces
4. **Add client method** in `frontend/src/services/api.ts` — axios call matching the route
5. **Wire to UI** in `frontend/src/components/<Component>.tsx` — call the api.ts method, render result

**Verify:**
```bash
curl -X GET http://localhost:3000/api/<new-endpoint>
```

---

## 2. Add a New WebSocket Event

**Goal:** Push a new event type from backend to frontend via WebSocket.

1. **Broadcast** from `backend/src/websocket.ts` — `broadcastToAll('event_name', payload)`
2. **Emit** from route handler in `backend/src/routes/<section>.ts` — call the broadcast function
3. **Subscribe** in `frontend/src/components/<Component>.tsx` — `socket.on('event_name', handler)`
4. **Handle state** — update React state or ref

**Verify:**
```bash
wscat -c ws://localhost:3000/ws
# send test message, confirm event received
```

---

## 3. Fix a DSP Bug in Edge

**Goal:** Fix a signal processing issue in the C99 RF engine.

1. **Locate** in `Edge-Node/rf/libs/<module>.c` — identify the affected function
2. **Write test** in `Edge-Node/test/` — standalone C script or Python wrapper
3. **Fix** in the C source — preserve OpenMP/FFTW3 patterns
4. **Build** — `./build.sh --dev`
5. **Dry-run verify** — `./test/<test_script>` with known input data

**Verify:**
```bash
cd Edge-Node && ./build.sh --dev && ./test/<test_script>
```

---

## 4. Add a Compliance Rule

**Goal:** Add a new spectral compliance detection rule.

1. **Add rule logic** in `postprocesamiento/src/processor.py` — in the compliance mode branch
2. **Add calibration** in `postprocesamiento/src/calibration_io.py` — if rule needs license data
3. **Add CLI flag** in `postprocesamiento/main.py` — expose via argparse
4. **Test** with sample payload: `python main.py --mode compliance --input test.json`

**Verify:**
```bash
cd postprocesamiento && python main.py --mode compliance --input examples/sample.json
```

---

## 5. Add a New Frontend Component

**Goal:** Add a new UI panel or page to the operator dashboard.

1. **Create component** in `frontend/src/components/<NewPanel>.tsx`
2. **Add API method** in `frontend/src/services/api.ts` — if it needs backend data
3. **Add route/tab** in `frontend/src/App.tsx` — add to sidebar nav and Routes
4. **Verify render** — open browser, navigate to new tab/panel

**Verify:**
```bash
cd frontend && npm run build
# No TypeScript or build errors
```

---

## 6. Modify Sensor Data Flow

**Goal:** Change how sensor data flows from backend to frontend display.

1. **Update model** in `backend/src/models/SensorData.ts` — modify SQL query or transform
2. **Update route** in `backend/src/routes/sensor.ts` — change response shape if needed
3. **Update WebSocket** in `backend/src/websocket.ts` — if real-time push changes
4. **Update frontend** in `frontend/src/hooks/useSpectrumData.ts` or `<Component>.tsx` — adapt to new shape
5. **Verify** — connect real sensor or use simulator

**Verify:**
```bash
curl -X GET http://localhost:3000/api/sensor/:mac/latest-data | jq .
# Confirm expected shape
```

---

## 7. Update Deployment

**Goal:** Change Docker, nginx, or deployment configuration.

1. **Edit** `docker-compose.yml` — service config, networks, volumes
2. **Edit Dockerfiles** — `frontend/Dockerfile`, `backend/Dockerfile`, `postprocesamiento/Dockerfile`
3. **Edit deploy script** — `infra/deploy-server.sh` if deployment steps change
4. **Rebuild** — `docker compose build <service>`
5. **Test** — `docker compose up <service>` and verify

**Verify:**
```bash
docker compose build <service> && docker compose up <service>
# Check logs for errors
```

---

## 8. Add a New Systemd Service

**Goal:** Add a new daemon or timer to the Raspberry Pi edge node.

1. **Create Python entry** in `Edge-Node/<new_service>.py`
2. **Add to init** in `Edge-Node/init_sys.py` — register the unit template
3. **Add install step** in `Edge-Node/install.sh` — enable and start the service
4. **Test locally** — run the script directly, check output
5. **Verify** — `systemctl status ane-<service>`

**Verify:**
```bash
cd Edge-Node && python3 init_sys.py && systemctl status ane-<service>
```

---

## 9. Debug Auth Issues

**Goal:** Debug Azure AD SSO or legacy JWT authentication failures.

1. **Check middleware** in `backend/src/middleware/auth.ts` — verify JWT validation logic
2. **Check Azure flow** in `backend/src/middleware/azureAuth.ts` — JWKS fetch, token decode
3. **Check frontend** in `frontend/src/components/AzureCallback.tsx` — redirect handling
4. **Check state** in `frontend/src/contexts/AuthContext.tsx` — login/logout/token storage
5. **Test token** — `curl -H "Authorization: Bearer <token>" http://localhost:3000/api/auth/me`

**Verify:**
```bash
curl -H "Authorization: Bearer <valid-token>" http://localhost:3000/api/auth/me
# Should return user object, not 401
```

---

## 10. Verify Dead Code

**Goal:** Confirm a file or function is unused before deleting it.

1. **Grep imports** — `rg "from.*<module>" --include="*.ts" --include="*.tsx" --include="*.py"` in the section directory
2. **Check scaffold criticality** — search in `scaffold/_meta/manifest.json` and relevant `main.md`
3. **Check build** — remove/comment the import, run `npm run build` or `python -c "import <module>"`
4. **Confirm** — no errors from removal
5. **Delete** — remove file and update any scaffold references

**Verify:**
```bash
rg "from.*<module_name>" --include="*.ts" --include="*.tsx" --include="*.py"
# Should return zero results after removal
```
