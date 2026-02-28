# Governance / Control Plane Execution Spec

Date: 2026-02-24

## Purpose
This document defines the reliability/control-plane implementation needed before the next full ingestion + retraining cycle is considered production-ready.

The target is to ensure:
- model behavior is measurable and controllable,
- role outcomes are validated for Admin / User / Mentor,
- regressions are blocked before release.

## Hard Release Gates
A release is blocked unless all gates pass:
1. Role route parity reviewed against page-order packs.
2. Automated parser re-ingestion completed and manifests healthy.
3. Control-plane policy/routing active in inference paths.
4. Always-on eval harness passing golden + adversarial sets.
5. Drift monitors green or explicitly waived with runbook.
6. Role acceptance dashboards show non-zero valid outcomes.

## Source-of-Truth Inputs
- Legacy page-order packs:
  - `Archive Scripts/pages order/Admin Pages Order`
  - `Archive Scripts/pages order/User Pages Order`
  - `Archive Scripts/pages order/Mentor Pages Order`
- Runtime role routes:
  - `apps/admin/src/App.tsx`
  - `apps/user/src/App.tsx`
  - `apps/mentor/src/App.tsx`
- Pipeline/orchestration:
  - `scripts/run_full_pipeline.py`
  - `scripts/run_parser_until_complete.py`
  - `services/workers/ai/ai-workers/orchestrator/ai_training_orchestrator.py`
  - `services/workers/ai/ai-workers/training/train_all_models.py`
- Parser + ingestion status:
  - `services/workers/ai/ai-workers/parser/automated_parser_engine.py`
  - `services/backend_api/routers/ai_data.py`

## Phase Plan

## Phase 0 — Baseline freeze (Pre-implementation)
Objective: lock baseline behavior before governance changes.

Deliverables:
- `reports/ROLE_ROUTE_PARITY_BASELINE.md`
- `reports/PARSER_INGESTION_BASELINE.md`
- `reports/MODEL_TRAINING_BASELINE.md`
- `reports/ENDPOINT_HEALTH_BASELINE.md`

Checks:
- Route inventory from all 3 App.tsx files.
- Current parser ingestion summary + trap flags.
- Existing harness status (`unit`, `integration`, `e2e`, smoke scripts).

## Phase 1 — Control plane foundation
Objective: define enforceable routing/policy logic independent of model weights.

New components (to add):
- `services/backend_api/services/governance/policy_engine.py`
- `services/backend_api/services/governance/confidence_engine.py`
- `services/backend_api/services/governance/routing_engine.py`
- `services/backend_api/services/governance/drift_monitor.py`
- `services/backend_api/services/governance/types.py`

Integration targets:
- `services/backend_api/services/ai/unified_ai_engine.py`
- `services/workers/ai/ai-workers/inference/unified_ai_engine.py`
- `services/backend_api/routers/telemetry.py`

Minimum behavior:
- task classification (`extract`, `rewrite`, `matching`, `compliance-risk`),
- policy action (`allow`, `fallback_deterministic`, `ask_clarifying`, `refuse`),
- confidence score + calibration band,
- decision trace emitted for auditability.

## Phase 2 — Ground-truth + feedback loops
Objective: convert behavior to measurable outcomes.

New artifacts (to add):
- `data/governance/outcome_labels.jsonl`
- `data/governance/feedback_events.jsonl`
- `services/backend_api/services/governance/labeling_service.py`

Signals to track:
- recruiter response rate,
- application progression / ATS pass proxy,
- user acceptance vs rewrite/edit rejection,
- mentor/admin workflow completion.

API additions (proposed):
- `POST /api/telemetry/v1/feedback`
- `GET /api/telemetry/v1/outcomes/summary`
- `GET /api/telemetry/v1/governance/decisions`

## Phase 3 — Always-on evaluation harness
Objective: make every release prove quality.

New test/eval structure (to add):
- `tests/eval/golden/test_skill_extraction.py`
- `tests/eval/golden/test_role_outcomes.py`
- `tests/eval/adversarial/test_prompt_safety.py`
- `tests/eval/adversarial/test_schema_breaks.py`
- `scripts/run_governance_eval.py`

Must-report metrics:
- extraction precision/recall/F1,
- consistency and schema-valid rate,
- latency p50/p95 and cost per request,
- safety/abuse violations,
- role outcome success rates.

## Phase 4 — Drift detection + release gating
Objective: detect degradation early and prevent silent quality decay.

New components (to add):
- `services/backend_api/services/governance/drift_rules.py`
- `services/backend_api/services/governance/release_gate.py`
- `scripts/check_release_gates.py`

Drift detectors:
- eval metric deltas,
- embedding distribution shift,
- rising edit/rejection and bounce patterns,
- parser error backlog increases.

Gate behavior:
- fail CI/release on critical threshold breach,
- allow waiver only with explicit runbook entry.

## Phase 5 — Role acceptance + factorial journeys
Objective: verify end-product value, not just model output.

Role acceptance suites (to add):
- `tests/e2e/role_journeys/test_admin_journeys.py`
- `tests/e2e/role_journeys/test_user_journeys.py`
- `tests/e2e/role_journeys/test_mentor_journeys.py`
- `tests/e2e/role_journeys/test_cross_role_factorial.py`

Coverage model:
- passive harness (existing automated tests),
- active factorial navigation and action permutations,
- endpoint + UI + data consistency assertions.

## Mapping to Existing Todo Program
- Reliability/control-plane track corresponds to todo items 22–41.
- Role-page and product-output gates correspond to items 10–12 and 20.
- Ingestion/retraining/bridge/contracts/graphics correspond to items 13–19.

## Immediate Execution Order (Next 3 Steps)
1. Create Phase 0 baselines and parity matrix documents.
2. Implement Phase 1 governance modules with no behavior change (shadow mode only).
3. Wire decision logging + telemetry endpoints and start collecting traces.

## Done Criteria
Control plane is considered operational when:
- governance decisions are logged for >= 95% AI requests,
- calibration score is published in telemetry,
- drift checks run automatically on each release,
- role acceptance dashboards show passing outcomes for Admin/User/Mentor,
- release gates block regressions by default.
