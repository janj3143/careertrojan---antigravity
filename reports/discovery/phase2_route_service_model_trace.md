# Phase 2 Route-Service-Model Trace

Generated: 2026-03-10
Base runtime checked: http://localhost:8600

## Scope Checked
- `ops` route family (`/api/ops/v1/*`)
- `intelligence` route family (`/api/intelligence/v1/*`)
- `lenses` route family (`/api/lenses/v1/*`)
- `mentor` route family (`/api/mentor/v1/*`)
- `payment` route family (`/api/payment/v1/*`)
- User visual/API bindings (`apps/user/src/lib/api.ts`, `apps/user/src/pages/VisualisationsHub.tsx`)

## Trace Findings

### 1. Operations path: Live and wired
- Route: `/api/ops/v1/processing/start`
- Router function adds background task: `_run_active_ingestion`
- Service call: `get_ingestion_service().ingest_parsed_directory(...)`
- Status: **Live and working**

### 2. Intelligence path: Live with mixed source quality
- Route: `/api/intelligence/v1/market`
- Service call: `web_intel.fetch_recent_trends(query)` with fallback hardcoded trend list
- Route: `/api/intelligence/v1/stats/regression`
- Service/model: uses `numpy.polyfit` and returns regression metrics
- Status: **Live but partially fallback-backed**

### 3. Lenses path: Live route, synthetic scoring behavior
- Route: `/api/lenses/v1/spider`
- Service/model references:
  - `StatisticalAnalysisEngine`
  - synthetic randomized baseline scores
- Output contract returns `SpiderProfile`
- Status: **Live but synthetic (not fully feature-driven from resume/JD)**

### 4. Mentor path: Core profile active, packages intentionally 404
- Active profile routes hit DB-backed mentor/user entities
- Package routes (`/packages`, `/packages/{package_id}`) return 404 by design
- Dashboard stats route returns static-zero payload
- Status: **Partially wired**

### 5. Payment path: Backend live, frontend contract mismatch found
- Backend routes available:
  - `/api/payment/v1/client-token` (auth required)
  - `/api/payment/v1/methods` (auth required)
- Frontend API file calls:
  - `/api/payment/v1/token`
  - `/api/payment/v1/vault`
- Runtime verification:
  - `/api/payment/v1/token` -> 404
  - `/api/payment/v1/vault` -> 404
  - `/api/payment/v1/client-token` -> 401 (expected without auth)
  - `/api/payment/v1/methods` -> 401 (expected without auth)
- Status: **Contract drift (frontend/backend mismatch)**

### 6. Visual binding path: Registry live, default port drift risk
- Visual hub fetches registry from `${API_BASE}/api/insights/v1/visuals`
- Default fallback base URL in `VisualisationsHub.tsx` is `http://localhost:8500`
- Current container runtime baseline is `http://localhost:8600`
- Status: **Live, but environment default can point to wrong runtime**

## Classification Snapshot
- Live and working:
  - ops processing start
  - intelligence market/regression endpoints
  - payment health and auth-protected endpoints
- Live but fragile/partial:
  - lenses spider scoring (synthetic/randomized baseline)
  - intelligence market fallback trends
  - visual hub default API base mismatch risk
- Partially wired:
  - mentor package and dashboard monetization path
- Critical contract mismatch:
  - frontend payment API paths (`token`, `vault`) vs backend (`client-token`, `methods`)

## Immediate Next Fixes
1. Align frontend payment routes in `apps/user/src/lib/api.ts`:
   - `token` -> `client-token`
   - `vault` -> `methods`
2. Align visual default base URL in `apps/user/src/pages/VisualisationsHub.tsx` to runtime 8600 or shared config.
3. Replace random spider baseline with deterministic feature bundle input path.
4. Implement mentor package DB-backed CRUD or feature-flag explicitly in UI.

## Evidence Files
- `services/backend_api/routers/ops.py`
- `services/backend_api/routers/intelligence.py`
- `services/backend_api/routers/lenses.py`
- `services/backend_api/routers/mentor.py`
- `services/backend_api/routers/payment.py`
- `apps/user/src/lib/api.ts`
- `apps/user/src/pages/VisualisationsHub.tsx`
