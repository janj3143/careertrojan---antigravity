# CareerTrojan — Next Action Plan (Post Parser Completion)

**Updated**: 2026-02-22  
**Operator note**: Hetzner + SSL are now live at https://careertrojan.com

---

## Current Status Snapshot

### Completed
- ✅ Phase 1 foundation fixes completed (schema adapter, collocation engine, expert system baseline, routing sanity).
- ✅ Phase 2 ingestion execution completed (`ingest_deep_v3 --apply`, enhancement artefacts, source-of-truth audit).
- ✅ Phase 3 training execution completed (Bayesian + salary predictor generated from real dataset).
- ✅ Phase 4 core service wiring in progress and active:
  - interview coaching service facade
  - company intel service + auto-ingest on resume upload
  - registry and extraction endpoints
- ✅ Production infrastructure baseline complete:
  - Hetzner provisioned
  - SSL active
  - Live URL: https://careertrojan.com

### Open technical environment items
- ⚠️ `sentence-transformers` unavailable due to torch compatibility mismatch.
- ⚠️ `spacy` model `en_core_web_sm` not installed on runtime environment.

---

## Immediate Work Queue (Priority Order)

## P0 — Production Stability & Observability (Now)
1. ⬜ Add production health checks for all exposed services and verify `/health/deep` remotely.
2. ⬜ Add Sentry (or equivalent) backend exception tracking in production.
3. ⬜ Confirm daily backup policy for:
   - postgres dump
   - `ai_data_final/metadata`
   - company intel registry/log streams
4. ⬜ Add deploy smoke script against live domain (auth, resume upload, coaching, intelligence endpoints).

## P1 — Admin UI Additional Work (Requested)
1. ⬜ **Admin Company Intel Panel**
   - Registry table (company, seen_count, last_seen, sources)
   - Search/filter by company name
   - Quick action: trigger `/api/intelligence/v1/company/extract`
2. ⬜ **Admin Coaching Insights Panel**
   - Role detection test harness
   - 90-day plan generator controls
   - Learning profile viewer
3. ⬜ **Admin Support/Ticketing Entry**
   - Add Helpdesk status card (provider, widget state, SSO state)
   - Add link-outs to support queues and macros
4. ⬜ **Admin AI Pipeline Ops**
   - Last ingest run timestamp + counts
   - Last enhancement run timestamp + counts
   - Model artefact inventory (`trained_models/*`)

## P2 — API & Data Follow-through
1. ⬜ Add `.msg` extraction pipeline and feed to company/contact intelligence.
2. ⬜ Extend CSV ingestion for contact discussions and employer history fields.
3. ⬜ Add contamination trap test (`Sales` profile must not map to `Python Developer`).
4. ⬜ Add endpoint for recent company-intel events (`company_intel_events.jsonl`) with pagination.

## P3 — Runtime ML Gaps
1. ⬜ Fix torch/sentence-transformers package compatibility in runtime env.
2. ⬜ Install and verify spaCy model package in runtime/deploy env.
3. ⬜ Re-run full model pipeline and refresh report after package remediation.

---

## Live Endpoint Additions Already Available

- `POST /api/coaching/v1/role/detect`
- `POST /api/coaching/v1/plan/90day`
- `GET /api/intelligence/v1/company/registry`
- `POST /api/intelligence/v1/company/extract`

---

## Execution Sequence for Next Session

1. Production smoke + observability checks (P0)
2. Admin UI company/coaching panels (P1.1 + P1.2)
3. Admin AI pipeline ops panel (P1.4)
4. `.msg` and CSV ingestion expansions (P2.1 + P2.2)
5. ML dependency remediation and retrain (P3)

---

## Operator Confirmation

Hetzner + SSL completion has been recorded in this plan as **done**.  
Additional Admin UI work has been added as the top development priority after production stability checks.
