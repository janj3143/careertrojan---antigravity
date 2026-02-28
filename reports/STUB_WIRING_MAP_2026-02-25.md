# Stub & Wiring Map — 2026-02-25

## Scope
This map covers the currently active charting + support integration surfaces:
- Structural capability radar + template + clue wiring
- Connected word-cloud layered modes
- Coaching trigger integration
- Helpdesk provider wiring (including Zendesk)

## Fully Wired in This Pass

### 1) Structural Charting + Template
- Frontend template state now drives radar calibration and option suggestion.
- Peer percentile calibration panel is rendered.
- Intuitive clue engine is rendered from domain gaps and percentile signals.
- Gap clues are wired to coaching question generation via `/api/coaching/v1/questions/generate`.

### 2) Layered Word-Cloud Modes
- Word cloud supports mode switching: `all`, `dominant`, `growth`, `unknown`.
- Dominant/growth tagging is driven by shared template inputs.
- Layer legend and selective render behavior are enabled.

### 3) Zendesk Implementation Status
- Support APIs are no longer hardcoded to `mode=stub`.
- Provider-aware mode now resolves from config (`stub` or `zendesk`).
- Zendesk JWT token path is implemented using `HS256` when `HELPDESK_PROVIDER=zendesk` and `ZENDESK_SHARED_SECRET` are configured.
- New provider introspection endpoint: `GET /api/support/v1/providers`.

### 4) TensorFlow / ML Rewiring Status
- Replaced placeholder role-fit TODOs with model-first inference attempts (`predict_proba` / `decision_function` / `predict`) using compatible feature vectors.
- Added feature extraction path that combines profile structural features + keyword overlap signals.
- Replaced fixed clustering percentile placeholder (`50.0`) with computed peer percentile from same-cluster centroid distance where available.
- Replaced market-trend placeholder logic with extraction from `statistical_methods_analysis.json` payload and fallback keyword path.

## Remaining Stubs / Placeholders (Highlighted)

### A) Helpdesk (Partially Stubbed by Configuration)
- If `HELPDESK_PROVIDER` is left as `stub` (default), support remains non-production stub mode.
- Widget script URL and Zendesk base URL/subdomain are env-driven and require deployment config.
- No external Zendesk API validation call is performed yet; token generation and bootstrap are local.

### A1) TensorFlow Runtime Availability (Configuration Stub)
- TensorFlow model loading path is implemented, but runtime still depends on environment package availability.
- If TensorFlow is missing in the active environment, neural model predictions gracefully degrade and log debug failures.
- Final production step remains: install/verify TensorFlow package in deployment environment.

### B) Broader Platform Stubs (Outside this implementation slice)
- `services/backend_api/routers/ops.py` has processing sections marked stubbed.
- `services/backend_api/services/llm_service.py` is marked as a stub service.
- Multiple enrichment modules still have TODO placeholders for production analytics integration and TensorFlow feature/probability paths.

## Config Needed for Zendesk Production Mode
Set these environment variables:
- `HELPDESK_PROVIDER=zendesk`
- `ZENDESK_SHARED_SECRET=<secret>`
- `ZENDESK_SUBDOMAIN=<your_subdomain>` **or** `ZENDESK_BASE_URL=<https://...zendesk.com>`
- Optional:
  - `ZENDESK_WIDGET_SCRIPT_URL`
  - `ZENDESK_JWT_EMAIL_CLAIM`
  - `ZENDESK_JWT_NAME_CLAIM`
  - `ZENDESK_JWT_EXTERNAL_ID_CLAIM`

## Next Recommended Wiring
1. Add real Zendesk JWT verification smoke test in non-prod environment.
2. Add end-to-end coaching flow link from clue panel to Coaching Hub session context.
3. Complete TensorFlow rewiring in enrichment orchestrator (deferred step).
