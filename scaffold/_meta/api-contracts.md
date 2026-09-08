# API Contracts

> Centralized index of all HTTP endpoints and WebSocket paths across the platform.

## Auth Endpoints (`backend/src/routes/auth.ts`)

| Method | Path | Section | Auth | Purpose |
|---|---|---|---|---|
| POST | `/api/auth/login` | management-api | No | Legacy username/password login |
| POST | `/api/auth/azure-login` | management-api | No | Azure AD SSO callback |
| GET | `/api/auth/me` | management-api | Yes | Get current user profile |
| POST | `/api/auth/users` | management-api | Yes | Create new user |
| GET | `/api/auth/users` | management-api | Yes | List all users |
| PUT | `/api/auth/users/:id` | management-api | Yes | Update user |
| DELETE | `/api/auth/users/:id` | management-api | Yes | Delete user |
| POST | `/api/auth/users/:id/change-password` | management-api | Yes | Change user password |

## Sensor Data Endpoints (`backend/src/routes/sensor.ts`)

| Method | Path | Section | Auth | Purpose |
|---|---|---|---|---|
| POST | `/api/sensor/status` | data-ingest | No | Sensor posts health status |
| POST | `/api/sensor/gps` | data-ingest | No | Sensor posts GPS coordinates |
| POST | `/api/sensor/data` | data-ingest | No | Sensor posts spectrum data |
| GET | `/api/sensor/:mac/latest-data` | data-ingest | No | Get latest spectrum data |
| GET | `/api/sensor/:mac/latest-status` | data-ingest | No | Get latest sensor status |
| GET | `/api/sensor/:mac/latest-gps` | data-ingest | No | Get latest GPS coordinates |
| GET | `/api/sensor/:mac/data/range` | data-ingest | No | Get spectrum data by time range |
| GET | `/api/sensor/:mac/configuration` | data-ingest | No | Get current sensor configuration |
| POST | `/api/sensor/:mac/configure` | data-ingest | No | Send scan configuration |
| POST | `/api/sensor/:mac/stop` | data-ingest | No | Stop active scan |
| GET | `/api/sensor/:mac/realtime` | data-ingest | No | Poll realtime config (edge) |
| GET | `/api/sensor/:mac/campaigns` | data-ingest | No | Get active campaigns (edge) |
| GET | `/api/campaigns/sensor/:mac/signals` | data-ingest | No | NDJSON signal stream |
| GET | `/api/sensor/:mac/data` | data-ingest | No | Get all data for sensor |
| GET | `/api/sensors/validate-status` | data-ingest | No | Validate sensor status |
| POST | `/api/sensor/audio` | data-ingest | No | Upload audio data |

## Management Endpoints (`backend/src/routes/management.ts`)

| Method | Path | Section | Auth | Purpose |
|---|---|---|---|---|
| GET | `/api/sensors` | management-api | Yes | List all sensors |
| POST | `/api/sensors` | management-api | Yes | Create sensor |
| PUT | `/api/sensors/:id` | management-api | Yes | Update sensor |
| DELETE | `/api/sensors/:id` | management-api | No | Delete sensor |
| GET | `/api/sensors/:id/antennas` | management-api | Yes | List antennas for sensor |
| POST | `/api/sensors/:id/antennas` | management-api | Yes | Attach antenna to sensor |
| GET | `/api/antennas` | management-api | Yes | List all antennas |
| POST | `/api/antennas` | management-api | Yes | Create antenna |
| PUT | `/api/antennas/:id` | management-api | Yes | Update antenna |
| DELETE | `/api/antennas/:id` | management-api | No | Delete antenna |
| DELETE | `/api/sensors/:sensorId/antennas/:antennaId` | management-api | No | Remove antenna from sensor |
| GET | `/api/alerts` | management-api | Yes | Get alert history |
| GET | `/api/alerts/:id` | management-api | Yes | Get alert by ID |
| POST | `/api/alerts` | management-api | Yes | Create alert |
| DELETE | `/api/alerts/:id` | management-api | Yes | Delete alert |

## Campaign Endpoints (`backend/src/routes/campaign.ts`)

| Method | Path | Section | Auth | Purpose |
|---|---|---|---|---|
| GET | `/api/campaigns` | campaigns | Yes | List all campaigns |
| POST | `/api/campaigns` | campaigns | Yes | Create campaign |
| GET | `/api/campaigns/:id` | campaigns | Yes | Get campaign by ID |
| PUT | `/api/campaigns/:id` | campaigns | Yes | Update campaign |
| DELETE | `/api/campaigns/:id` | campaigns | Yes | Delete campaign |
| POST | `/api/campaigns/:id/start` | campaigns | Yes | Start campaign execution |
| POST | `/api/campaigns/:id/stop` | campaigns | Yes | Stop running campaign |
| GET | `/api/campaigns/:id/data` | campaigns | Yes | Get campaign data |
| GET | `/api/campaigns/statistics/summary` | campaigns | Yes | Campaign statistics summary |
| GET | `/api/campaigns/sensor/:mac/signals` | campaigns | No | NDJSON signal stream for sensor |
| POST | `/api/reports/compliance/:campaignId` | reports | Yes | Trigger compliance report |
| GET | `/api/campaigns/:id/report` | reports | Yes | Get campaign report |

## Reports Endpoints (`backend/src/routes/reports.ts`)

| Method | Path | Section | Auth | Purpose |
|---|---|---|---|---|
| POST | `/api/reports/compliance/:id` | reports | Yes | Generate compliance report (calls Python) |
| GET | `/api/reports/compliance/:id` | reports | Yes | Retrieve compliance report |
| GET | `/api/reports` | reports | Yes | List all reports |

## Config Endpoints (`backend/src/routes/config.ts`)

| Method | Path | Section | Auth | Purpose |
|---|---|---|---|---|
| GET | `/api/config` | config | Yes | Get system configuration |
| PUT | `/api/config` | config | Yes | Update system configuration |

## Internal HTTP Endpoints (Backend → Postprocesamiento)

| Method | Path | Transport | Auth | Purpose |
|---|---|---|---|---|
| POST | `http://python-analysis:8000/analyze_batch` | HTTP | No | Batch spectral analysis |

## External HTTP Endpoints (Backend → External)

| Method | Path | Transport | Auth | Purpose |
|---|---|---|---|---|
| POST | `http://172.23.80.220:4155/localizar` | HTTP | No | Address geocoding |

## WebSocket Paths

| Path | Protocol | Auth | Purpose |
|---|---|---|---|
| `/ws` | WebSocket | No | Main real-time data channel (sensor_data, sensor_gps, sensor_status, audio) |
| `/ws/audio/listen/:sensorId` | WebSocket | No | Legacy audio stream (frontend listens) |
| `/ws/audio/sensor/:id` | WebSocket | No | Opus→PCM audio bridge (edge sensor connects) |

## Auth Legend

| Marker | Meaning |
|---|---|
| Yes | Requires valid JWT or Azure AD token |
| No | No authentication required (sensor-facing or internal) |
| Missing | Auth middleware absent but should be present (see DELETE endpoints in management.ts) |

## Endpoint Count Summary

| Section | File | Endpoints | Auth Coverage |
|---|---|---|---|
| auth.ts | 8 | 100% |
| sensor.ts | 16 | 100% (sensor-facing: intentionally unauthenticated) |
| management.ts | 15 | 80% (DELETE endpoints missing auth) |
| campaign.ts | 12 | 92% |
| reports.ts | 3 | 100% |
| config.ts | 2 | 100% |
| **Total REST** | **56** | — |
| WebSocket | 3 paths | — |
| Internal HTTP | 1 | — |
| External HTTP | 1 | — |
| **Grand Total** | **61** | — |
