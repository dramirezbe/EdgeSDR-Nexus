# WebSocket — Layer 2

> Parent: [../main.md](../main.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Real-time communication layer: main WebSocket for sensor data/status/GPS broadcasts, and audio WebSocket for Opus-to-PCM decoding and streaming.

## Tech stack & conventions
- `ws` ^8.18.3 (WebSocket library)
- `opusscript` ^0.1.1 (Opus audio decoding)
- Binary protocol for audio frames (custom header: magic, sequence, sample rate, channels, length)
- `noServer` mode for audio WebSocket (manual upgrade handling)

## Structure
```
websocket/
├── websocket.ts    # Main WebSocket (/ws) — sensor data + status + GPS + audio pub/sub
└── audioServer.ts  # Audio WebSocket (/ws/audio/*) — Opus decode -> PCM broadcast
```

## Entry points
- `websocket.ts`: `initWebSocket(server)` called from app.ts
- `audioServer.ts`: `setupAudioWebSocket(server)` called from app.ts

## Key interactions
- **Frontend <- Backend:** WebSocket `/ws` receives: `sensor_status`, `sensor_gps`, `sensor_data`, `sensor_status_changed`, `sensor_configure`, `sensor_stop`
- **Frontend -> Backend:** WebSocket `/ws` sends: `subscribe_audio`, `unsubscribe_audio`
- **Sensors -> Backend:** WebSocket `/ws/audio/sensor/{sensorId}` streams Opus audio frames
- **Frontend <- Backend:** WebSocket `/ws/audio/listen/{sensorId}` receives PCM audio frames
- **Audio pipeline:** Sensor Opus -> audioServer.ts (decode) -> PCM broadcast -> Frontend WebRTC

## Common tasks & gotchas
- Main WebSocket uses standard JSON messages
- Audio WebSocket uses binary frames with custom 16-byte header:
  - Sensor ingest: magic=OPU0, sequence(u32), sample_rate(u32), channels(u16), payload_length(u16)
  - Listener output: magic=AUD0, sequence(u32), sample_rate(u32), channels(u16), payload_length(u16)
- Audio decode: Opus -> PCM at 48kHz mono, 960 samples/frame (20ms)
- `broadcastToClients()` sends to all connected clients — no per-sensor filtering on main WS
- Audio subscribers are filtered by `demodType` (AM/FM)
- Per-sensor audio throughput logging every 1 second (frames/s, KiB/s)

## Open questions / TODO
- No WebSocket authentication — anyone can connect and receive sensor data
- No message rate limiting — could be overwhelmed by rapid sensor data
- Audio WebSocket uses `noServer` mode with manual upgrade — complex but flexible
- 30s ping interval for keepalive on listener connections
