# CODEC Masterplan — J + L Runtime Alignment (2026-02-11)

## Source of Truth
- Runtime code: J:\Codec - runtime version\Antigravity\careertrojan
- Data set root: L:\Codec-Antigravity Data set

## Objective
Make all runtime services resolve paths from a single, consistent contract so the J-drive runtime and L-drive data set operate together without hardcoded legacy locations.

## Current Mismatches (High Impact)
1. Multiple env var schemes remain (AI_DATA_PATH/AI_DATA_ROOT vs CAREERTROJAN_*), which can cause confusion and split configuration sources.
2. Documentation still references legacy C: paths and older L: dataset roots, which conflicts with the J/L contract.
3. If `CAREERTROJAN_DATA_ROOT` is not set, the resolver may pick `L:\VS ai_data final - version` when it exists, instead of the target dataset root.

## Code Violations and Issues (With Sources)
1. Legacy AI_* env keys remain in the master env file and can diverge from CAREERTROJAN_* values. See [careertrojan/.env](careertrojan/.env#L13-L26).
2. Docs still publish C:\careertrojan and legacy L: paths in operational instructions. See [careertrojan/WORK_PLAN.md](careertrojan/WORK_PLAN.md#L1-L40) and [careertrojan/docs/WORKFLOW_DATA_SYNC_AND_AI_LOOP.md](careertrojan/docs/WORKFLOW_DATA_SYNC_AND_AI_LOOP.md#L27-L60).

## Resolved This Pass
1. Updated runtime envs to use J-drive working/logs and L:\Codec-Antigravity Data set for data root. See [careertrojan/infra/env/runtime.env](careertrojan/infra/env/runtime.env#L3-L12) and [careertrojan/infra/docker/.env](careertrojan/infra/docker/.env#L1-L2).
2. Added L:\Codec-Antigravity Data set to path resolver defaults. See [careertrojan/services/shared/paths.py](careertrojan/services/shared/paths.py#L47-L54).
3. Removed hardcoded legacy L: fallbacks in worker/registry/runtime validation. See [careertrojan/services/workers/ai_orchestrator_enrichment.py](careertrojan/services/workers/ai_orchestrator_enrichment.py#L24-L40), [careertrojan/shared_backend/registry/capability_registry.py](careertrojan/shared_backend/registry/capability_registry.py#L10-L18), and [careertrojan/shared_backend/main.py](careertrojan/shared_backend/main.py#L7-L14).
4. Moved sqlite DB default under working root. See [careertrojan/services/backend_api/db/connection.py](careertrojan/services/backend_api/db/connection.py#L9-L18).
5. Aligned infra docker compose mounts to dataset root and CAREERTROJAN_DATA_ROOT contract. See [careertrojan/infra/docker/compose.yaml](careertrojan/infra/docker/compose.yaml#L18-L90).
6. Normalized router storage paths to shared path resolver for resumes, logs, and abuse queues. See [careertrojan/services/backend_api/routers/resume.py](careertrojan/services/backend_api/routers/resume.py#L15-L40), [careertrojan/services/backend_api/routers/logs.py](careertrojan/services/backend_api/routers/logs.py#L10-L34), and [careertrojan/services/backend_api/routers/admin_abuse.py](careertrojan/services/backend_api/routers/admin_abuse.py#L10-L22).
7. Wired collocation extraction into enrichment orchestrators with a profile corpus sample. See [careertrojan/services/backend_api/services/enrichment/ai_enrichment_orchestrator.py](careertrojan/services/backend_api/services/enrichment/ai_enrichment_orchestrator.py#L520-L590) and [careertrojan/apps/admin/services/enrichment/ai_enrichment_orchestrator.py](careertrojan/apps/admin/services/enrichment/ai_enrichment_orchestrator.py#L520-L590).
8. Normalized admin and shared routers to use the shared path resolver for interactions, ai_data, and logs. See [careertrojan/services/backend_api/routers/admin.py](careertrojan/services/backend_api/routers/admin.py#L14-L160) and [careertrojan/services/backend_api/routers/shared.py](careertrojan/services/backend_api/routers/shared.py#L1-L80).
9. Added ingestion smoke test to verify ai_data and interactions availability. See [careertrojan/scripts/ingestion_smoke_test.py](careertrojan/scripts/ingestion_smoke_test.py).
10. Added collocation glossary suite + ontology endpoint for phrase lookup. See [careertrojan/scripts/build_collocation_glossary.py](careertrojan/scripts/build_collocation_glossary.py) and [careertrojan/services/backend_api/routers/ontology.py](careertrojan/services/backend_api/routers/ontology.py).

## Target Contract (Canonical)
- CAREERTROJAN_DATA_ROOT = L:\Codec-Antigravity Data set
- CAREERTROJAN_AI_DATA = L:\Codec-Antigravity Data set\ai_data_final
- CAREERTROJAN_PARSER_ROOT = L:\Codec-Antigravity Data set\automated_parser
- CAREERTROJAN_USER_DATA = L:\Codec-Antigravity Data set\USER DATA
- CAREERTROJAN_WORKING_ROOT = J:\Codec - runtime version\Antigravity\careertrojan\working\working_copy
- CAREERTROJAN_APP_LOGS = J:\Codec - runtime version\Antigravity\careertrojan\logs
- CAREERTROJAN_MODELS = J:\Codec - runtime version\Antigravity\careertrojan\trained_models

## Recommended Changes
1. Normalize env files to the Target Contract (root .env, infra/env/runtime.env, infra/docker/.env).
2. Update path resolver defaults to include L:\Codec-Antigravity Data set before legacy L: candidates.
3. Refactor workers and registries that hardcode L: to use the path resolver or explicit env vars.
4. Ensure all runtime entrypoints treat CAREERTROJAN_DATA_ROOT as the dataset root, not ai_data_final.
5. Move sqlite DB (if used) to working/logs area, not inside the dataset folder.
6. Add collocation-aware phrase extraction (bigrams/trigrams + PMI) to improve NLP precision.

## Collocation Upgrade (Starter Implementation)
- Added n-gram and collocation extraction helpers to enrichment so the parser can surface multi-word concepts and near-phrase associations.
- Next step: feed `corpus_texts` from historical interactions or profile text batches to rank collocations by PMI.
- Optional: add a small domain gazette to lock critical industry phrases before statistical scoring.

## Verification Steps
1. Run unit path tests: tests/unit/test_paths_resolution.py
2. Run runtime review + full harness: scripts/full_harness.ps1
3. Run ingestion smoke test with `CAREERTROJAN_DATA_ROOT` set to `L:\Codec-Antigravity Data set`: scripts/ingestion_smoke_test.py
4. Run collocation suite: scripts/build_collocation_glossary.py
5. Check logs/test_results/full_harness_summary.md for path-related failures

## Notes
- Keep legacy aliases only if needed for older scripts; otherwise deprecate.
- Avoid hardcoded drive letters in code; prefer env + path resolver.

## Operational Delta (2026-02-20)

### Docker Port Standard (8600+)
- Root compose (`compose.yaml`):
  - `backend-api` → `8600:8000`
  - `admin-portal` → `8601:80`
  - `user-portal` → `8602:80`
  - `mentor-portal` → `8603:80`
  - `redis` → `8604:6379`
  - `postgres` → `8605:5432`
- Infra compose (`infra/docker/compose.yaml`):
  - `reverse-proxy` → `8600:80`, `8643:443`
  - `portal-bridge` → `8601:8001`
  - `shared-backend-api` → `8602:8000`
  - `redis` → `8604:6379`
  - `postgres` → `8605:5432`

### Full Testing Pyramid + Physical Local Checks
1. Tiered harness (preflight + unit + integration + e2e):
	- `powershell -ExecutionPolicy Bypass -File scripts/full_harness.ps1`
2. Coaching/local physical terminal checks (login + coaching endpoints):
  - `J:\Python311\python.exe scripts/coaching_endpoint_uptime_check.py --base-url http://127.0.0.1:8600`
3. Unified run (tiers + physical):
	- `powershell -ExecutionPolicy Bypass -File scripts/run_testing_pyramid_all_tiers.ps1`

### Missing Items (Current)
1. Frontend API callsite cleanup to eliminate remaining legacy non-`/api/.../v1` paths.
2. Router-mount decision for dormant admin/analytics/telemetry routes.
3. CI automation to regenerate endpoint introspection graph and publish artifact each run.

## Operational Delta (2026-02-27)

### Support Bridge (React → FastAPI → Zendesk)
- Implemented inside existing support router namespace: `/api/support/v1`.
- New bridge endpoints:
  - `POST /api/support/v1/tickets` (create Zendesk ticket + internal log)
  - `GET /api/support/v1/tickets/{ticket_id}` (internal ticket status + optional provider refresh)
  - `POST /api/support/v1/webhooks/zendesk` (webhook ingest + signature verification)
- Added persistence model: `support_tickets` in backend DB model layer.
- Added Zendesk bridge service for create/get ticket + webhook signature verification.

### Runtime `.env` (Sanitized — Do Not Hardcode)
```dotenv
HELPDESK_PROVIDER=zendesk
ZENDESK_BASE_URL=https://careertrojan.zendesk.com
ZENDESK_EMAIL=api@careertrojan.com
ZENDESK_API_TOKEN=***REDACTED***
ZENDESK_DEFAULT_GROUP_ID=
ZENDESK_DEFAULT_FORM_ID=
ZENDESK_WEBHOOK_SECRET=***REDACTED***
```

### Jobs To Do (Execution Backlog)
1. Wire React support modal to `POST /api/support/v1/tickets` with category + enrichment fields.
2. Add attachment pipeline (file limits, malware scan, content type validation).
3. Add user notification stream for webhook updates (`ticket.updated`, `ticket.solved`, comments).
4. Add retention policy enforcement + redaction policy for ticket metadata.
5. Move Zendesk secrets to Key Vault/K8s Secrets and rotate leaked token immediately.

### API Probe Snapshot (2026-02-27)
- Full endpoint inventory artifact: `reports/FULL_ENDPOINT_INVENTORY_2026-02-27.md` (275 endpoints).
- Priority probe artifact: `reports/PRIORITY_ENDPOINT_PROBE_2026-02-27.md`.

### #API Problems (Need Fix/Test)
- Legacy non-v1 admin routes missing (`404`):
  - `GET /api/admin/integrations/status`
  - `POST /api/admin/integrations/sendgrid/configure`
  - `POST /api/admin/integrations/klaviyo/configure`
  - `POST /api/admin/email/send_test`
  - `POST /api/admin/email/send_bulk`
- Admin AI content endpoints stubbed (`501`):
  - `GET /api/admin/v1/ai/content/status`
  - `POST /api/admin/v1/ai/content/run`
  - `GET /api/admin/v1/ai/content/jobs`
- Mentorship runtime failures (`500`):
  - `GET /api/mentorship/v1/links/mentor/sample` (SQL syntax issue)
  - `GET /api/mentorship/v1/links/user/sample` (SQL syntax issue)
  - `GET /api/mentorship/v1/notes/sample` (SQL syntax issue)
  - `GET /api/mentorship/v1/invoices/mentor/sample` (SQL syntax issue)
  - `GET /api/mentorship/v1/applications/pending` (missing table)

### TensorFlow + A/B Run Status
- TensorFlow runtime import check: **not importable** in current environment.
- A/B run smoke (`AdvancedAnalyticsService.run_ab_test`) failed with import error: `No module named 'analytics'`.
- Required follow-up:
  1. Install TensorFlow in runtime environment where neural workers execute.
  2. Fix Python module path/package wiring for analytics package resolution.
  3. Re-run A/B smoke and persist result artifact.
