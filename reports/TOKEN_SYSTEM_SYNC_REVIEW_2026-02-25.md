# Token System Sync Review — 2026-02-25

## Summary
The proposed token model is feasible, but the current runtime is **not yet in sync**. The codebase has multiple parallel token/credit implementations with mismatched plans, endpoints, and billing coupling.

## What exists today

### 1) Credits API (newer direction)
- File: `services/backend_api/routers/credits.py`
- Backed by: `services/backend_api/services/credit_system.py`
- Pattern: action-based costs (`ACTION_COSTS`) and plan allocations (`PLANS`)
- Current allocations are small (e.g., free `15`, monthly `150`, annual `350`, elite `500` credits), which differ from the newly proposed economics.

### 2) Payment/Braintree API
- File: `services/backend_api/routers/payment.py`
- Braintree helpers: `services/backend_api/services/braintree_service.py`
- Supports subscription creation and direct payments, but current payment plan metadata (`token_limit`, `ai_calls_per_month`) is not automatically synchronized into the credit manager ledger.

### 3) Admin token endpoints (scaffolded)
- File: `services/backend_api/routers/admin_tokens.py`
- Status: scaffold/stub storage (`TokenStore`) and partial endpoint contract (`/api/admin/v1/tokens/config`, `/usage`)
- Not aligned with admin page/client contract expecting `/admin/tokens/plans`, `/costs`, `/logs`, `/analytics`, `/ledger/{user_id}`.

### 4) Admin token page expects richer contract
- File: `apps/admin/pages/10_Token_Management.py`
- Expects endpoint family that is not fully implemented server-side.

### 5) User-side token integration drift
- File: `apps/user/token_integration.py`
- References legacy path `BACKEND-ADMIN-REORIENTATION` and helper functions not part of canonical backend runtime.

## Main sync gaps

1. **Currency fragmentation**
- At least three concepts coexist: tokens, credits, and plan token limits.
- Need one canonical currency (credits/tokens) across backend + admin + user + billing.

2. **Plan catalog mismatch**
- Proposed model: Freemium/Monthly/Premium/Elite with larger monthly pools.
- Current code uses `free/monthly/annual/elite(or elitepro)` with different limits and naming.

3. **Endpoint contract mismatch**
- Admin UI/client expects `/admin/tokens/*` contract.
- Backend currently exposes only partial `/api/admin/v1/tokens/*` scaffold.

4. **Ledger persistence gap**
- Credit manager currently uses in-memory state; no durable monthly ledger for production-grade accounting.

5. **Braintree coupling incomplete**
- Subscription events do not reliably propagate into token/credit allocation resets and ledger entries.
- Booster-pack purchasing path is not yet production-wired into token ledger increments.

6. **Simulation engine missing**
- No canonical backend simulation API for scenario modeling (e.g., 10/20/50/100 UmarketU send-outs, suite combinations, overage recommendations).

## Feasibility against requested model
Yes, fully feasible with current architecture by implementing:
- A canonical token economics service,
- A durable ledger + monthly allocation engine,
- Config-driven feature/suite costs,
- Scenario simulation endpoints,
- Braintree webhook/event integration for subscriptions and boosters.

## Recommended implementation sequence

1. Canonicalize plan/tier + currency model.
2. Implement persistent token ledger and monthly allocation reset.
3. Unify admin endpoint contract to match token management page.
4. Add suite composition + simulation engine (scenario calculator).
5. Integrate Braintree subscription/booster events into ledger updates.
6. Migrate user portal token integration to canonical backend APIs.

## Immediate conclusion
The current system is **partially wired but not synchronized** with the requested parametric token strategy. This should be treated as a structured migration rather than incremental tweaks in isolated modules.
