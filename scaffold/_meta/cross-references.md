# Cross-Section References

> Dependency map between scaffold sections. Shows which section calls which other section, via what transport, and whether auth is required.

## Frontend → Backend

| Frontend Section | Backend Section | Method | Path | Auth | Notes |
|---|---|---|---|---|---|
| auth | management-api | POST | `/api/auth/azure-login` | No | Azure AD redirect handler |
| auth | management-api | POST | `/api/auth/login` | No | Legacy username/password |
| auth | management-api | GET | `/api/auth/me` | Yes | Current user profile |
| monitoring | data-ingest | GET | `/api/sensor/:mac/latest-data` | No | Polls latest spectrum data |
| monitoring | data-ingest | GET | `/api/sensor/:mac/latest-status` | No | Sensor health status |
| monitoring | data-ingest | GET | `/api/sensor/:mac/latest-gps` | No | GPS coordinates |
| monitoring | data-ingest | POST | `/api/sensor/:mac/configure` | No | Send scan config to sensor |
| monitoring | data-ingest | POST | `/api/sensor/:mac/stop` | No | Stop active scan |
| monitoring | management-api | GET | `/api/sensors` | Yes | List all sensors |
| monitoring | management-api | GET | `/api/sensors/:id/antennas` | Yes | Antenna list for sensor |
| monitoring | management-api | POST | `/api/sensors/:id/antennas` | Yes | Attach antenna |
| monitoring | management-api | DELETE | `/api/sensors/:sensorId/antennas/:antennaId` | No | Remove antenna |
| campaigns | campaigns | GET | `/api/campaigns` | Yes | List campaigns |
| campaigns | campaigns | POST | `/api/campaigns` | Yes | Create campaign |
| campaigns | campaigns | PUT | `/api/campaigns/:id` | Yes | Update campaign |
| campaigns | campaigns | DELETE | `/api/campaigns/:id` | Yes | Delete campaign |
| campaigns | campaigns | POST | `/api/campaigns/:id/start` | Yes | Start campaign |
| campaigns | campaigns | POST | `/api/campaigns/:id/stop` | Yes | Stop campaign |
| campaigns | campaigns | GET | `/api/campaigns/:id/data` | Yes | Campaign data |
| campaigns | campaigns | POST | `/api/reports/compliance/:id` | Yes | Trigger compliance report |
| campaigns | data-ingest | GET | `/api/campaigns/sensor/:mac/signals` | No | NDJSON signal stream |
| admin | management-api | GET | `/api/sensors` | Yes | Sensor list |
| admin | management-api | POST | `/api/sensors` | Yes | Create sensor |
| admin | management-api | PUT | `/api/sensors/:id` | Yes | Update sensor |
| admin | management-api | DELETE | `/api/sensors/:id` | No | Delete sensor |
| admin | management-api | GET | `/api/antennas` | Yes | Antenna list |
| admin | management-api | POST | `/api/antennas` | Yes | Create antenna |
| admin | management-api | PUT | `/api/antennas/:id` | Yes | Update antenna |
| admin | management-api | DELETE | `/api/antennas/:id` | No | Delete antenna |
| admin | config | GET | `/api/config` | Yes | System config |
| core | campaigns | GET | `/api/campaigns/statistics/summary` | Yes | Campaign summary stats |
| core | alerts | GET | `/api/alerts` | Yes | Alert history |
| audio | websocket | WS | `/ws` | No | subscribe_audio / unsubscribe_audio / audio_data |
| audio | audioServer | WS | `/ws/audio/listen/:sensorId` | No | WebRTC audio bridge |

## Edge → Backend

| Edge Component | Backend Section | Method | Path | Transport | Auth | Frequency |
|---|---|---|---|---|---|---|
| orchestrator.py | data-ingest | GET | `/api/sensor/:mac/realtime` | HTTP REST | No | Every 5s |
| orchestrator.py | data-ingest | GET | `/api/sensor/:mac/campaigns` | HTTP REST | No | Every 60s |
| orchestrator.py | data-ingest | POST | `/api/sensor/data` | HTTP REST | No | Each acquisition |
| campaign_runner.py | data-ingest | POST | `/api/sensor/data` | HTTP REST | No | Each campaign frame |
| status.py | data-ingest | POST | `/api/sensor/status` | HTTP REST | No | Every 30s |
| server_webrtc.py | websocket | WS | `/ws/audio/sensor/:id` | WebSocket | No | Continuous (Opus→PCM) |

## Backend → Postprocesamiento

| Backend Component | Target Section | Method | Path | Transport | Auth | Notes |
|---|---|---|---|---|---|---|
| reports.ts | core | POST | `http://python-analysis:8000/analyze_batch` | HTTP REST | No | Batch spectral analysis |

## Backend → External

| Backend Component | Target | Method | Path | Transport | Auth | Notes |
|---|---|---|---|---|---|---|
| reports.ts | Geolocation API | POST | `http://172.23.80.220:4155/localizar` | HTTP REST | No | Address geocoding |

## WebSocket Event Map

| Event | Direction | Section | Auth | Notes |
|---|---|---|---|---|
| `sensor_data` | backend → frontend | websocket | No | Real-time spectrum push |
| `sensor_gps` | backend → frontend | websocket | No | GPS coordinate push |
| `sensor_status` | backend → frontend | websocket | No | Sensor health push |
| `sensor_status_changed` | backend → frontend | websocket | No | Status transition notification |
| `subscribe_audio` | frontend → backend | websocket | No | Subscribe to sensor audio |
| `unsubscribe_audio` | frontend → backend | websocket | No | Unsubscribe from audio |
| `audio_data` | backend → frontend | websocket | No | Opus-encoded audio frames |

## Transport Summary

| Transport | Usage | Count |
|---|---|---|
| HTTP REST | Frontend↔Backend, Edge→Backend, Backend→Postprocesamiento | 40+ endpoints |
| WebSocket | Real-time data, audio streaming | 7 events |
| Internal HTTP | Backend→Python analysis | 1 endpoint |
| External HTTP | Backend→Geolocation | 1 endpoint |
