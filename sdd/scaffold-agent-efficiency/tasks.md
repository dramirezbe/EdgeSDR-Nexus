# Tasks: Scaffold Agent Efficiency

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 700–900 |
| 400-line budget risk | Low (documentation only, no runtime code) |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | auto-chain |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Metadata + reference docs | PR 1 | `node scaffold/_meta/verify-scaffold.js` | N/A (docs only) | Delete 3 new _meta files, revert manifest.json |
| 2 | File criticality tables | PR 1 | `grep -r "## File Criticality" scaffold/` | N/A (docs only) | Remove appended sections from 29 files |

## Phase 1: Metadata & Infrastructure

- [ ] 1.1 Add `refresh_policy` object to `scaffold/_meta/manifest.json` with `max_age_days: 30`, `last_verified_commit: "2bcb560"`, and `verification_instructions` text
- [ ] 1.2 Add raw data warning header to `scaffold/_meta/exploration-log.md` — 3-line block before existing content: "RAW DATA — This file contains unstructured exploration findings. Do not use as primary reference. Use cross-references.md, api-contracts.md, or task-playbooks.md instead."

## Phase 2: New Reference Documents

- [ ] 2.1 Create `scaffold/_meta/cross-references.md` — section-to-section dependency map with Source/Target/Transport/Contract/Auth columns, plus "Sections with No Outbound Dependencies" table (~60 lines)
- [ ] 2.2 Create `scaffold/_meta/task-playbooks.md` — 10 pre-computed routing tables (Add REST Endpoint, Fix DSP Bug, Add WebSocket Event, Add Sensor Type, Add Campaign Field, Add Compliance Rule, Add Frontend Page, Modify nginx Config, Add Database Migration, Add Systemd Service) + fallback instructions (~180 lines)
- [ ] 2.3 Create `scaffold/_meta/api-contracts.md` — 43-endpoint index with Method/Path/Owner/Auth/Callers/Notes columns + Summary by Section table (~160 lines)

## Phase 3: Staleness Verification Script

- [ ] 3.1 Create `scaffold/_meta/verify-scaffold.js` — Node.js script: reads manifest.json `refresh_policy.last_verified_commit`, runs `git rev-parse HEAD`, compares, outputs FRESH/STALE/UNVERIFIED with exit codes 0/1 (~70 lines)

## Phase 4: File Criticality Tables — Frontend

- [ ] 4.1 Append `## File Criticality` table to `scaffold/frontend/main.md` — HOT/WARM/COLD/DEAD columns for src/ files (~20 lines)
- [ ] 4.2 Append `## File Criticality` table to `scaffold/frontend/auth/main.md`
- [ ] 4.3 Append `## File Criticality` table to `scaffold/frontend/monitoring/main.md`
- [ ] 4.4 Append `## File Criticality` table to `scaffold/frontend/campaigns/main.md`
- [ ] 4.5 Append `## File Criticality` table to `scaffold/frontend/network/main.md`
- [ ] 4.6 Append `## File Criticality` table to `scaffold/frontend/admin/main.md`
- [ ] 4.7 Append `## File Criticality` table to `scaffold/frontend/audio/main.md`
- [ ] 4.8 Append `## File Criticality` table to `scaffold/frontend/core/main.md`

## Phase 5: File Criticality Tables — Backend

- [ ] 5.1 Append `## File Criticality` table to `scaffold/backend/main.md`
- [ ] 5.2 Append `## File Criticality` table to `scaffold/backend/data-ingest/main.md`
- [ ] 5.3 Append `## File Criticality` table to `scaffold/backend/management-api/main.md`
- [ ] 5.4 Append `## File Criticality` table to `scaffold/backend/campaigns/main.md`
- [ ] 5.5 Append `## File Criticality` table to `scaffold/backend/reports/main.md`
- [ ] 5.6 Append `## File Criticality` table to `scaffold/backend/websocket/main.md`
- [ ] 5.7 Append `## File Criticality` table to `scaffold/backend/models/main.md`

## Phase 6: File Criticality Tables — Postprocesamiento

- [ ] 6.1 Append `## File Criticality` table to `scaffold/postprocesamiento/main.md`
- [ ] 6.2 Append `## File Criticality` table to `scaffold/postprocesamiento/server/main.md`
- [ ] 6.3 Append `## File Criticality` table to `scaffold/postprocesamiento/cli/main.md`
- [ ] 6.4 Append `## File Criticality` table to `scaffold/postprocesamiento/core/main.md`
- [ ] 6.5 Append `## File Criticality` table to `scaffold/postprocesamiento/spectral/main.md`
- [ ] 6.6 Append `## File Criticality` table to `scaffold/postprocesamiento/calibration/main.md`
- [ ] 6.7 Append `## File Criticality` table to `scaffold/postprocesamiento/utils/main.md`

## Phase 7: File Criticality Tables — Edge & Infra

- [ ] 7.1 Append `## File Criticality` table to `scaffold/edge/main.md`
- [ ] 7.2 Append `## File Criticality` table to `scaffold/edge/rf-engine/main.md`
- [ ] 7.3 Append `## File Criticality` table to `scaffold/edge/python-services/main.md`
- [ ] 7.4 Append `## File Criticality` table to `scaffold/edge/utils/main.md`
- [ ] 7.5 Append `## File Criticality` table to `scaffold/edge/build-deploy/main.md`
- [ ] 7.6 Append `## File Criticality` table to `scaffold/edge/gps-lte/main.md`
- [ ] 7.7 Append `## File Criticality` table to `scaffold/edge/context/main.md`
- [ ] 7.8 Append `## File Criticality` table to `scaffold/infra/main.md`

## Phase 8: Verification

- [ ] 8.1 Run `grep -r "## File Criticality" scaffold/` — verify all 29 Layer 1/2 files have the section
- [ ] 8.2 Run `node scaffold/_meta/verify-scaffold.js` — verify FRESH output (commit matches)
- [ ] 8.3 Count `## Playbook:` headings in task-playbooks.md — verify ≥10
- [ ] 8.4 Count rows in api-contracts.md Endpoints table — verify ≥43
- [ ] 8.5 Validate manifest.json parses as valid JSON
