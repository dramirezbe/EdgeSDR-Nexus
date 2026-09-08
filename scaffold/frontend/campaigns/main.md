# Campaigns — Layer 2

> Parent: [../main.md](../main.md)
> Last audited: 2026-09-08 @ commit 2bcb560

## Purpose
Campaign lifecycle management: create, list, view, start/stop campaigns, display campaign data, and generate compliance reports.

## Tech stack & conventions
- Recharts ^3.5.1 for campaign data visualization
- axios for API calls
- Complex modal forms for campaign creation/editing
- ComplianceReport component for regulatory report display

## Structure
```
components/                    # NOTE: flat in components/, NOT in campaigns/ subdirectory
├── CampaignsList.tsx         # Campaign list + status management (662 lines)
├── CampaignModal.tsx         # Campaign create/edit modal form (1257 lines)
├── CampaignDataViewer.tsx    # Campaign measurement data viewer (1759 lines, largest component)
└── ComplianceReport.tsx      # Compliance report display (~1400 lines)
```

## Entry points
- `CampaignsList.tsx`: rendered in App.tsx when `activeTab === 'campañas'`
- `CampaignDataViewer.tsx`: opened from CampaignsList to view campaign data
- `ComplianceReport.tsx`: opened from CampaignDataViewer to view compliance results

## Key interactions
- **Frontend -> Backend:** `GET /api/campaigns` (list all), `GET /api/campaigns/:id` (get one)
- **Frontend -> Backend:** `POST /api/campaigns` (create), `PUT /api/campaigns/:id` (update), `DELETE /api/campaigns/:id` (delete)
- **Frontend -> Backend:** `POST /api/campaigns/:id/start`, `POST /api/campaigns/:id/stop`
- **Frontend -> Backend:** `GET /api/campaigns/:id/data` (measurement data for campaign+sensor)
- **Frontend -> Backend:** `GET /api/campaigns/statistics/summary` (dashboard stats)
- **Frontend -> Backend:** `POST /api/reports/compliance/:campaignId` (generate compliance report)
- **Data flow:** CampaignsList -> CampaignModal (create/edit) -> CampaignDataViewer -> ComplianceReport

## Common tasks & gotchas
- CampaignDataViewer at 1759 lines is the largest component — handles data loading, visualization, and report generation
- Campaign creation supports pre-fill from monitoring configuration (`campaignPrefillData` prop from App.tsx)
- Campaign status lifecycle: `scheduled -> running -> completed` (managed by backend timer)
- NDJSON streaming available for large campaign data sets (`/api/campaigns/sensor/:mac/signals`)
- Compliance report calls Python microservice via backend — may take 10+ seconds

## File Criticality

| File | Lines | Status | Notes |
|------|-------|--------|-------|
| `CampaignsList.tsx` | 662 | Active | CRUD + start/stop campaigns |
| `CampaignModal.tsx` | 1257 | Active | Create/edit campaign form |
| `CampaignDataViewer.tsx` | 1759 | Active | NDJSON streaming data viewer |
| `ComplianceReport.tsx` | 1677 | Active | Report generation + display |

## Open questions / TODO
- CampaignDataViewer is monolithic — should be split into smaller components
- No real-time campaign progress updates (requires manual refresh)
- ComplianceReport has inline error handling but no retry logic for failed report generation
