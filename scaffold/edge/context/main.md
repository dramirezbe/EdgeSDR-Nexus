# Context — Layer 3

> Parent: [../main.md](../main.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Architecture documentation and reference materials: detailed design docs for the RF engine and Python services, post-mortem analysis, and optimization roadmap.

## Tech stack & conventions
- Markdown documentation
- Doxygen/Sphinx for API docs (configured but optional)
- ReadTheDocs integration (`.readthedocs.yaml`)

## Structure
```
context/
├── RF_ENGINE.md              # C engine architecture (360 lines) — module inventory, main loop, DSP pipeline
├── PYTHON_SERVICES.md        # Python services architecture (518 lines) — orchestrator, campaigns, WebRTC
├── document/                 # Additional documentation files
├── issues/                   # Post-mortems and issue analysis
├── PROJECT_CONCEPTUAL_SUMMARY.md  # 470-line comprehensive architecture reference
└── OPTIMIZATION_ROADMAP.md   # Optimization plans and improvements
```

## Key documents

### RF_ENGINE.md
- Complete module inventory (15 header/source pairs)
- Main loop flow with request-driven state machine
- DSP pipeline (IQ -> compensation -> filtering -> PSD)
- Audio thread flow (demodulation -> Opus -> TCP)
- Calibration procedure (3-stage: sweep -> pilot -> fine symmetry)
- Error recovery and shutdown sequence
- Key design patterns table

### PYTHON_SERVICES.md
- Orchestrator main loop (realtime + campaign modes)
- Campaign scheduling via cron
- WebRTC audio bridge (GStreamer pipeline)
- Systemd initialization
- JSON contract schemas
- Data flow summaries

### PROJECT_CONCEPTUAL_SUMMARY.md
- 470-line comprehensive reference covering all modules
- Architecture diagrams (text-based)
- API contracts and data formats

## Key interactions
- **Reference for:** All other sections reference these docs
- **Used by:** AI agents, new developers, architecture reviews

## Common tasks & gotchas
- These are the authoritative architecture references for the Edge-Node
- `AGENTS.md` at Edge-Node root is the primary entry point for AI agents
- `context/` docs provide deeper dives into specific modules

## Open questions / TODO
- Some docs may be stale — last audit date not tracked
- No index or navigation between context docs
- `OPTIMIZATION_ROADMAP.md` may contain outdated priorities
