# API Schemas (Stable Contract)

This document defines the minimal, stable JSON contracts used by the frontend and integrations.

## Health Endpoints

### GET /api/health (Fast)
Used by frontend and scripts for quick status.

```json
{
  "status": "healthy|degraded",
  "hero_database_size": 0,
  "available_roles": ["fighter", "mage"],
  "version": "2.0.0",
  "timestamp": 1737000000.0
}
```

Notes:
- Always returns quickly. On exception, returns `{ status: "degraded" }` with `error` message.

### GET /api/health-isolated (Non-blocking)
Never depends on heavy subsystems and should always return immediately.

```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T20:30:00Z",
  "version": "2.0.0",
  "uptime": "running",
  "response_time_ms": 1
}
```

## Analysis Response (Backend → Frontend Proxy)

The dashboard’s proxy (`dashboard-ui-new/app/api/analyze/route.js`) normalizes several possible backend payloads. The backend should provide at least these fields:

- `statistical_feedback`: array (strings or `{ severity, feedback/message, category }`)
- `mental_feedback` or `mental_boost`: string
- `parsed_data`: object with keys used by the dashboard
  - `hero`: string
  - `kda`: string or structured
  - `damage`: number or string
  - `gpm`: number or string
  - `match_duration`: number or string
  - `rank`: string
- Confidence (any one of):
  - `confidence_scores.overall_confidence` (0–100)
  - `overall_confidence` (0–100 or 0–1)
  - `diagnostics.confidence_score` (0–1)

Optional diagnostics that enhance UI:
- `parsing_warnings`: array of strings
- `ultimate_analysis.processing_time`: number
- `ultimate_analysis.improvement_roadmap`: array of strings
- `diagnostics.data_completeness`: 0–1

The proxy will:
- Normalize confidence to 0–100
- Bound inflated confidence if data is incomplete
- Produce the final shape for dashboard widgets

