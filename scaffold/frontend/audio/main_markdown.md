# Audio — Layer 3

> Parent: [../main_markdown.md](../main_markdown.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Real-time audio streaming: WebRTC-based audio player for demodulated AM/FM signals from sensors, plus legacy audio players.

## Tech stack & conventions
- WebRTC for real-time audio (via backend signaling)
- Custom binary protocol for audio frame parsing
- Multiple player implementations (legacy + WebRTC)
- No external audio library — raw PCM handling

## Structure
```
audio/
├── WebRTCAudioPlayer.tsx      # WebRTC audio streaming player (389 lines)
├── AudioPlayerComponent.tsx   # Advanced audio player with controls (362 lines)
├── AudioPlayer.tsx            # Legacy/simple audio player (181 lines)
└── AudioPage.tsx              # Standalone audio page (route: /audio/:sensorId, 97 lines)
```

## Entry points
- `WebRTCAudioPlayer.tsx`: rendered in AnalysisPanel when demodulation is active
- `AudioPage.tsx`: standalone route `/audio/:sensorId`
- `AudioPlayer.tsx` / `AudioPlayerComponent.tsx`: used in monitoring views

## Key interactions
- **Frontend <- Backend:** WebSocket `/ws/audio/listen/{sensorId}` for PCM audio frames
- **Frontend -> Backend:** WebSocket message `subscribe_audio` / `unsubscribe_audio` for audio subscription
- **Audio flow:** Sensor -> rf_app (Opus) -> TCP :9000 -> server_webrtc.py -> GStreamer -> WebRTC -> backend audioServer.ts -> WebSocket -> frontend
- **Backend audioServer.ts:** Decodes Opus -> PCM, broadcasts to subscribed WebSocket clients

## Common tasks & gotchas
- WebRTC signaling happens through backend WebSocket at `/ws` (not a separate signaling server)
- Audio frames use custom binary header: magic (AUD0/OPU0), sequence number, sample rate, channels, payload length
- PCM sample rate: 48kHz mono, 20ms frames (960 samples)
- Three audio player implementations exist — WebRTC is the current one, others are legacy

## Open questions / TODO
- Legacy AudioPlayer and AudioPlayerComponent may be dead code — need to verify if they're still used
- No audio recording or playback from history
- No volume normalization across different sensors
- GStreamer is a system dependency not listed in requirements.txt
