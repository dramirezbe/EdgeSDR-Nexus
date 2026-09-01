# Reports — Layer 3

> Parent: [../main.md](../main.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Compliance report generation: collects campaign measurement data, resolves DANE geographic codes via external service, and calls Python microservice for spectral analysis and regulatory compliance evaluation.

## Tech stack & conventions
- Express routes at `/api/reports/*`
- axios for HTTP calls to Python microservice and geolocation service
- Parallel batch processing (4 sub-batches matching gunicorn workers)
- Report caching in `compliance_reports_cache` table

## Structure
```
reports/
└── reports.ts   # Report routes: compliance generation + batch processing
```

## Entry points
- `reports.ts`: mounted at `/api/reports` in app.ts

## Key interactions
- **Frontend -> Backend:** `POST /api/reports/compliance/:campaignId` (generate report)
- **Frontend -> Backend:** `POST /api/reports/compliance/batch/:campaignId` (get sensor list + report status)
- **Backend -> Python:** `POST http://python-analysis:8000/analyze_batch` (spectral analysis)
  - Sends: spectrum frames + DANE codes + tolerances + peaks
  - Returns: peak detection results with license compliance matching
- **Backend -> Geolocation:** `POST http://172.23.80.220:4155/localizar` (DANE code resolution)
  - Sends: `{lat, lon}`
  - Returns: DANE code for the location
- **No auth middleware** on report endpoints

## Common tasks & gotchas
- Report generation calls TWO external services sequentially: geolocation first, then Python analysis
- No retry/fallback logic — if either service is unreachable, report generation fails
- Python microservice is called with 4 parallel sub-batches (matching gunicorn's 4 workers)
- Report results are cached in `compliance_reports_cache` table (keyed by campaign_id)
- 1-hour server timeout (`server.setTimeout(3600000)`) specifically for long-running reports
- `GET /api/reports/ping` is a health check endpoint for the Python service

## Open questions / TODO
- No auth on report endpoints — anyone can generate reports
- No retry logic for external service calls
- Report generation is synchronous — no async job queue for very long reports
- Geolocation service IP `172.23.80.220` is hardcoded — no fallback
- Report caching invalidation strategy is unclear
