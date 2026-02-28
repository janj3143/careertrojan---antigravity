# CareerTrojan — Comprehensive Backend API Endpoint Audit

**Generated:** 2025-06-15  
**Scope:** All 33 router files in `services/backend_api/routers/`, `main.py` mount points, admin frontend API consumption  
**Backend:** FastAPI on port 8500 | **Admin Frontend:** React+Vite on port 3001 (proxies `/api` → `localhost:8500`)

---

## Table of Contents

1. [Router File Inventory](#1-router-file-inventory)
2. [Complete Endpoint Catalog](#2-complete-endpoint-catalog)
3. [Data Status Summary](#3-data-status-summary)
4. [Frontend ↔ Backend Gap Analysis](#4-frontend--backend-gap-analysis)
5. [Email-Specific Endpoints](#5-email-specific-endpoints)
6. [Broken / 500-Error Endpoints](#6-broken--500-error-endpoints)
7. [Recommendations](#7-recommendations)

---

## 1. Router File Inventory

33 router files in `services/backend_api/routers/`:

| # | File | Prefix Mounted in main.py | Tags |
|---|------|--------------------------|------|
| 1 | `auth.py` | `/api/auth/v1` | auth |
| 2 | `admin.py` | `/api/admin/v1` | admin |
| 3 | `user.py` | `/api/user/v1` | user |
| 4 | `shared.py` | `/api/shared/v1` | shared |
| 5 | `mentor.py` | `/api/mentor/v1` | mentor (try/except) |
| 6 | `mentorship.py` | `/api/mentorship/v1` | mentorship |
| 7 | `intelligence.py` | `/api/intelligence/v1` | intelligence |
| 8 | `coaching.py` | `/api/coaching/v1` | coaching |
| 9 | `ops.py` | `/api/ops/v1` | ops |
| 10 | `resume.py` | `/api/resume/v1` | resume |
| 11 | `blockers.py` | `/api/blockers/v1` | blockers |
| 12 | `payment.py` | `/api/payment/v1` | payment (try/except) |
| 13 | `rewards.py` | `/api/rewards/v1` | rewards (try/except) |
| 14 | `credits.py` | `/api/credits/v1` | credits |
| 15 | `ai_data.py` | `/api/ai-data/v1` | ai-data |
| 16 | `jobs.py` | `/api/jobs/v1` | jobs |
| 17 | `taxonomy.py` | `/api/taxonomy/v1` | taxonomy |
| 18 | `sessions.py` | `/api/sessions/v1` | sessions |
| 19 | `insights.py` | `/api/insights/v1` | insights |
| 20 | `touchpoints.py` | `/api/touchpoints/v1` | touchpoints |
| 21 | `mapping.py` | `/api/mapping/v1` | mapping |
| 22 | `analytics.py` | `/api/analytics/v1` | analytics |
| 23 | `gdpr.py` | `/api/gdpr/v1` | gdpr |
| 24 | `api_health.py` | `/api/admin/v1/api-health` | admin-health |
| 25 | `admin_abuse.py` | `/api/admin/v1/abuse` | admin-abuse (try/except) |
| 26 | `admin_parsing.py` | `/api/admin/v1/parsing` | admin-parsing (try/except) |
| 27 | `admin_tokens.py` | `/api/admin/v1/tokens` | admin-tokens (try/except) |
| 28 | `anti_gaming.py` | `/api/admin/v1/anti-gaming` | anti-gaming (try/except) |
| 29 | `logs.py` | `/api/admin/v1/logs` | logs (try/except) |
| 30 | `telemetry.py` | `/api/telemetry/v1` | telemetry (try/except) |
| 31 | `webhooks.py` | `/api/payment/v1` | webhooks (try/except) |
| 32 | `admin_tools.py` | **(no prefix)** | tools |
| 33 | `admin_email_campaigns.py` | `/api/admin/v1` | email-campaigns |

**Root-level probes** (defined in `main.py` directly):
- `GET /healthz` — liveness
- `GET /readyz` — readiness

---

## 2. Complete Endpoint Catalog

### Legend

| Status | Meaning |
|--------|---------|
| **REAL** | Reads/writes to PostgreSQL DB, files, or external service |
| **REAL-FS** | File-system based (reads JSON/log files from disk) |
| **REAL-SVC** | Delegates to a service class; works when service is available |
| **MOCK** | Returns hardcoded / in-memory demo data |
| **STUB-501** | Returns HTTP 501 "Not Implemented" |
| **BROKEN** | Throws HTTP 500 at runtime |
| **PARTIAL** | Mix of real logic with hardcoded fallback |

---

### 2.1 auth.py — `/api/auth/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| POST | `/register` | `register` | REAL | DB insert, password hashing |
| POST | `/login` | `login` | REAL | DB + brute-force protection |
| POST | `/2fa/generate` | `generate_2fa` | REAL | pyotp + QR code generation |
| POST | `/2fa/verify` | `verify_2fa` | REAL | pyotp verification |

Helper deps: `get_current_user`, `get_current_active_admin`

---

### 2.2 admin.py — `/api/admin/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/users` | `get_all_users` | REAL | DB with pagination |
| GET | `/users/{user_id}` | `get_user_detail` | REAL | DB lookup |
| GET | `/system/health` | `get_system_health` | PARTIAL | Returns static "connected" |
| GET | `/compliance/summary` | `get_compliance_summary` | REAL | DB counts |
| GET | `/email/status` | `get_email_status` | STUB-501 | Overridden by admin_email_campaigns |
| GET | `/parsers/status` | `get_parser_status` | MOCK | Hardcoded "idle" |
| GET | `/system/activity` | `get_system_activity` | REAL | DB + file counts |
| GET | `/dashboard/snapshot` | `get_dashboard_snapshot` | REAL | Users, resumes, jobs, AI stats |
| GET | `/tokens/users/{user_id}/ledger` | `get_token_ledger` | STUB-501 | |
| GET | `/user_subscriptions` | `get_user_subscriptions` | REAL | DB query |
| GET | `/ai/monitoring` | `get_ai_monitoring` | REAL | DB + Redis + file stats |
| GET | `/users/metrics` | `get_user_metrics` | STUB-501 | |
| GET | `/users/security` | `get_users_security` | STUB-501 | |
| PUT | `/users/{user_id}/plan` | `update_user_plan` | STUB-501 | |
| PUT | `/users/{user_id}/disable` | `disable_user` | STUB-501 | |
| GET | `/compliance/audit/events` | `get_audit_events` | REAL | DB audit log w/ filtering |
| POST | `/email/sync` | `sync_email` | STUB-501 | |
| GET | `/email/jobs` | `get_email_jobs` | STUB-501 | |
| POST | `/parsers/run` | `run_parser` | STUB-501 | |
| GET | `/parsers/jobs` | `get_parser_jobs` | STUB-501 | |
| GET | `/batch/status` | `get_batch_status` | STUB-501 | |
| POST | `/batch/run` | `run_batch` | STUB-501 | |
| GET | `/batch/jobs` | `get_batch_jobs` | STUB-501 | |
| GET | `/ai/enrichment/status` | `get_enrichment_status` | REAL-FS | File-based interaction scan |
| POST | `/ai/enrichment/run` | `run_enrichment` | PARTIAL | Returns "queued" placeholder |
| GET | `/ai/enrichment/jobs` | `get_enrichment_jobs` | REAL-FS | Scans date directories |
| GET | `/ai/content/status` | `get_content_status` | STUB-501 | |
| POST | `/ai/content/run` | `run_content` | STUB-501 | |
| GET | `/ai/content/jobs` | `get_content_jobs` | STUB-501 | |

---

### 2.3 user.py — `/api/user/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/me` | `get_me` | REAL | DB |
| GET | `/profile` | `get_profile` | REAL | DB |
| PUT | `/profile` | `update_profile` | REAL | DB |
| GET | `/stats` | `get_stats` | MOCK | Hardcoded demo stats |
| GET | `/activity` | `get_activity` | MOCK | Hardcoded activity feed |

---

### 2.4 shared.py — `/api/shared/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/health` | `health` | REAL | Lightweight liveness |
| GET | `/healthz` | `healthz` | REAL | Alias |
| GET | `/health/deep` | `deep_health` | REAL | Checks DB, disk, dirs, Redis |
| GET | `/readyz` | `readyz` | REAL | Alias for deep health |

---

### 2.5 mentor.py — `/api/mentor/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/profile-by-user/{user_id}` | `get_mentor_profile_by_user` | MOCK | In-memory, auto-creates demo |
| GET | `/{mentor_profile_id}/profile` | `get_mentor_profile` | MOCK | In-memory dict |
| PUT | `/{mentor_profile_id}/availability` | `update_availability` | MOCK | In-memory dict |
| GET | `/list` | `list_mentors` | MOCK | In-memory dict |
| GET | `/{mentor_profile_id}/packages` | `get_mentor_packages` | MOCK | In-memory dict |
| POST | `/{mentor_profile_id}/packages` | `create_package` | MOCK | In-memory dict |
| GET | `/{mentor_profile_id}/packages/{package_id}` | `get_package` | MOCK | In-memory dict |
| PUT | `/{mentor_profile_id}/packages/{package_id}` | `update_package` | MOCK | In-memory dict |
| DELETE | `/{mentor_profile_id}/packages/{package_id}` | `delete_package` | MOCK | In-memory dict |

---

### 2.6 mentorship.py — `/api/mentorship/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| POST | `/links` | `create_link` | REAL | DB (raw DBAPI cursor) |
| GET | `/links/mentor/{mentor_id}` | `get_mentor_links` | REAL | DB |
| GET | `/links/user/{user_id}` | `get_user_links` | REAL | DB |
| PATCH | `/links/{link_id}/status` | `update_link_status` | REAL | DB |
| POST | `/notes` | `create_note` | REAL | DB |
| GET | `/notes/{link_id}` | `get_notes` | REAL | DB |
| PATCH | `/notes/{note_id}` | `update_note` | REAL | DB |
| POST | `/documents` | `create_document` | REAL | DB |
| GET | `/documents/{doc_id}` | `get_document` | REAL | DB |
| POST | `/documents/{doc_id}/sign` | `sign_document` | REAL | DB |
| POST | `/documents/{doc_id}/reject` | `reject_document` | REAL | DB |
| POST | `/invoices` | `create_invoice` | REAL | DB |
| GET | `/invoices/mentor/{mentor_id}` | `get_mentor_invoices` | REAL | DB |
| POST | `/invoices/{invoice_id}/mark-paid` | `mark_invoice_paid` | REAL | DB |
| POST | `/invoices/{invoice_id}/service-delivered` | `mark_service_delivered` | REAL | DB |
| POST | `/invoices/{invoice_id}/confirm-completion` | `confirm_completion` | REAL | DB |
| POST | `/invoices/{invoice_id}/dispute` | `dispute_invoice` | REAL | DB |
| POST | `/applications` | `submit_application` | REAL | DB |
| GET | `/applications/pending` | `get_pending_applications` | REAL | DB |
| POST | `/applications/{application_id}/approve` | `approve_application` | REAL | DB |
| GET | `/health` | `mentorship_health` | REAL | Service health |

---

### 2.7 intelligence.py — `/api/intelligence/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| POST | `/stats/descriptive` | `descriptive_stats` | REAL-SVC | StatisticalAnalysisEngine |
| POST | `/stats/regression` | `regression_analysis` | REAL-SVC | StatisticalAnalysisEngine |
| GET | `/market` | `market_data` | MOCK | Hardcoded salary benchmarks |
| POST | `/enrich` | `enrich_profile` | STUB | Returns empty data, 0 score |

---

### 2.8 coaching.py — `/api/coaching/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| POST | `/bundle` | `career_bundle` | REAL-SVC | career_coach if available |
| GET | `/health` | `coaching_health` | REAL | |
| POST | `/questions/generate` | `generate_questions` | PARTIAL | Deterministic fallback, no LLM |
| GET | `/role-functions` | `get_role_functions` | REAL-SVC | interview_coaching_service |
| POST | `/detect-role` | `detect_role` | REAL-SVC | if service available |
| POST | `/smart-questions` | `smart_questions` | REAL-SVC | if service available |
| POST | `/90-day-plan` | `ninety_day_plan` | REAL-SVC | if service available |
| POST | `/answers/review` | `review_answers` | MOCK | Rule-based, no LLM |
| POST | `/stories/generate` | `generate_stories` | MOCK | Simulated STAR stories |
| GET | `/company-intel/health` | `company_intel_health` | REAL | |
| POST | `/company-intel/overview` | `company_overview` | REAL-SVC | company_intel_service |
| POST | `/company-intel/hiring` | `company_hiring` | REAL-SVC | company_intel_service |
| POST | `/company-intel/news` | `company_news` | REAL-SVC | company_intel_service |
| POST | `/company-intel/talking-points` | `talking_points` | REAL-SVC | company_intel_service |
| POST | `/company-intel/full` | `full_intel` | REAL-SVC | company_intel_service |

---

### 2.9 ops.py — `/api/ops/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/stats/public` | `public_stats` | MOCK | Hardcoded numbers |
| POST | `/processing/start` | `start_processing` | MOCK | Fake background task |
| GET | `/processing/status` | `processing_status` | MOCK | |
| POST | `/logs/lock` | `lock_logs` | PARTIAL | Simulation |
| GET | `/tokens/config` | `get_tokens_config` | MOCK | Legacy |
| POST | `/anti-gaming/check` | `anti_gaming_check` | PARTIAL | Text-length heuristic |
| GET | `/logs` | `get_logs` | MOCK | Demo log entries |
| GET | `/backup` | `get_backup` | MOCK | Demo data |
| POST | `/backup` | `create_backup` | MOCK | Fake job_id |
| GET | `/diagnostics` | `get_diagnostics` | MOCK | Hardcoded |
| GET | `/route-map` | `get_route_map` | MOCK | Hardcoded counts |
| GET | `/notifications` | `get_notifications` | MOCK | Hardcoded |
| GET | `/config` | `get_config` | PARTIAL | Reads env vars |
| PUT | `/config` | `update_config` | MOCK | Doesn't persist |
| GET | `/exports` | `get_exports` | MOCK | |
| POST | `/exports` | `create_export` | MOCK | |
| GET | `/api-explorer` | `get_api_explorer` | MOCK | |

---

### 2.10 resume.py — `/api/resume/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| POST | `/upload` | `upload_resume` | REAL | Disk + JSON DB |
| GET | `/{resume_id}` | `get_resume` | REAL | JSON DB |
| GET | `/` | `list_resumes` | REAL | JSON DB |
| GET | `/latest` | `get_latest_resume` | REAL | cv_score hardcoded 78 |
| POST | `/parse` | `parse_resume` | DEPRECATED | |
| POST | `/enrich` | `enrich_resume` | STUB-501 | |

---

### 2.11 blockers.py — `/api/blockers/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| POST | `/detect` | `detect_blockers` | REAL-SVC | BlockerConnector |
| GET | `/user/{user_id}` | `get_user_blockers` | REAL | DB via BlockerService |
| POST | `/improvement-plans/generate` | `generate_plan` | STUB-501 | |

---

### 2.12 payment.py — `/api/payment/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/plans` | `get_plans` | REAL | In-memory PLANS dict (static) |
| GET | `/plans/{plan_id}` | `get_plan` | REAL | |
| POST | `/process` | `process_payment` | REAL | Braintree (503 if unconfigured) |
| GET | `/history` | `get_history` | MOCK | In-memory, not persisted |
| GET | `/subscription` | `get_subscription` | MOCK | In-memory |
| POST | `/cancel` | `cancel_subscription` | MOCK | In-memory |
| GET | `/health` | `payment_health` | REAL | |
| GET | `/client-token` | `get_client_token` | REAL | Braintree |
| POST | `/methods` | `add_payment_method` | REAL | Braintree vault |
| GET | `/methods` | `list_payment_methods` | REAL | Braintree |
| DELETE | `/methods/{token}` | `delete_payment_method` | REAL | Braintree |
| GET | `/transactions/{transaction_id}` | `get_transaction` | REAL | Braintree |
| POST | `/refund/{transaction_id}` | `refund_transaction` | REAL | Braintree |
| GET | `/gateway-info` | `gateway_info` | REAL | |
| POST | `/webhooks` | `braintree_webhook` | REAL | Braintree webhook handler |

---

### 2.13 rewards.py — `/api/rewards/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/rewards` | `get_rewards` | MOCK | In-memory dict |
| POST | `/referral` | `create_referral` | MOCK | In-memory |
| GET | `/referral/status` | `get_referral_status` | MOCK | In-memory |
| POST | `/redeem` | `redeem_reward` | MOCK | In-memory |
| GET | `/suggestions` | `reward_suggestions` | MOCK | In-memory |
| GET | `/leaderboard` | `get_leaderboard` | MOCK | In-memory |
| GET | `/health` | `rewards_health` | REAL | |

---

### 2.14 credits.py — `/api/credits/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/plans` | `get_credit_plans` | REAL-SVC | credit_system (if available) |
| GET | `/actions` | `get_credit_actions` | REAL-SVC | credit_system (if available) |
| GET | `/balance` | `get_balance` | **BROKEN** | `_get_user_id()` always raises 401 |
| POST | `/purchase` | `purchase_credits` | **BROKEN** | Same auth issue |
| POST | `/spend` | `spend_credits` | **BROKEN** | Same auth issue |
| GET | `/history` | `get_credit_history` | **BROKEN** | Same auth issue |

> **Critical:** `_get_user_id()` is a placeholder that always raises `HTTPException(401)`, making all user-scoped credit endpoints non-functional.

---

### 2.15 ai_data.py — `/api/ai-data/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/parsed_resumes` | `get_parsed_resumes` | REAL-FS | Scans `L:\...\ai_data_final\` |
| GET | `/parsed_resumes/{doc_id}` | `get_parsed_resume` | REAL-FS | |
| GET | `/job_descriptions` | `get_job_descriptions` | REAL-FS | |
| GET | `/companies` | `get_companies` | REAL-FS | |
| GET | `/job_titles` | `get_job_titles` | REAL-FS | |
| GET | `/locations` | `get_locations` | REAL-FS | |
| GET | `/metadata` | `get_metadata` | REAL-FS | |
| GET | `/normalized` | `get_normalized` | REAL-FS | |

---

### 2.16 jobs.py — `/api/jobs/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/index` | `get_job_index` | MOCK | 3 hardcoded jobs |
| GET | `/search` | `search_jobs` | MOCK | Searches hardcoded list |

---

### 2.17 taxonomy.py — `/api/taxonomy/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/industries` | `get_industries` | REAL-SVC | industry_taxonomy_service |
| GET | `/industries/{high_level}/subindustries` | `get_subindustries` | REAL-SVC | |
| GET | `/job-titles/search` | `search_job_titles` | REAL-SVC | |
| GET | `/job-titles/metadata` | `get_job_title_metadata` | REAL-SVC | |
| GET | `/job-titles/infer-industries` | `infer_industries` | REAL-SVC | |
| GET | `/naics/search` | `search_naics` | REAL-SVC | |
| GET | `/naics/title` | `get_naics_title` | REAL-SVC | |
| GET | `/job-titles/naics-mapping` | `get_naics_mapping` | REAL-SVC | |

---

### 2.18 sessions.py — `/api/sessions/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| POST | `/log` | `log_session` | REAL-FS | Writes to L: and mirror |
| GET | `/summary/{user_id}` | `get_session_summary` | REAL-FS | File-based |
| GET | `/sync-status` | `get_sync_status` | REAL-FS | Compares L: and E: mirrors |
| GET | `/consolidated/{user_id}` | `get_consolidated` | REAL-FS | |

---

### 2.19 insights.py — `/api/insights/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/visuals` | `get_visuals` | REAL | Visual registry catalogue |
| GET | `/skills/radar` | `get_skills_radar` | PARTIAL | Heuristic with randomness |
| GET | `/quadrant` | `get_quadrant` | REAL | From profiles |
| GET | `/terms/cloud` | `get_term_cloud` | REAL | |
| GET | `/terms/cooccurrence` | `get_cooccurrence` | REAL | |
| GET | `/graph` | `get_graph` | REAL | Cytoscape elements |
| POST | `/cohort/resolve` | `resolve_cohort` | REAL | Filter-based |

---

### 2.20 touchpoints.py — `/api/touchpoints/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/evidence` | `get_evidence` | REAL | From DataLoader profiles |
| GET | `/touchnots` | `get_touchnots` | REAL | Gap analysis |

---

### 2.21 mapping.py — `/api/mapping/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/registry` | `get_registry` | REAL-FS | visual_registry.json |
| GET | `/endpoints` | `get_endpoints` | REAL | Dynamic FastAPI route listing |
| GET | `/graph` | `get_graph` | REAL | Cytoscape graph |

---

### 2.22 analytics.py — `/api/analytics/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/statistics` | `get_statistics` | REAL-FS | File counts from ai_data_final |
| GET | `/dashboard` | `get_dashboard` | REAL-FS | Aggregated stats + recent resumes |
| GET | `/recent_resumes` | `get_recent_resumes` | REAL-FS | |
| GET | `/recent_jobs` | `get_recent_jobs` | REAL-FS | |
| GET | `/system_health` | `get_system_health` | REAL | |

---

### 2.23 gdpr.py — `/api/gdpr/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/consent` | `get_consent` | REAL | DB |
| POST | `/consent` | `save_consent` | REAL | DB |
| GET | `/export` | `export_data` | REAL | Full personal data export |
| DELETE | `/delete-account` | `delete_account` | REAL | Art. 17 erasure |

---

### 2.24 api_health.py — `/api/admin/v1/api-health`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/endpoints` | `get_endpoints` | REAL | Dynamic route list |
| POST | `/run-all` | `run_all_checks` | REAL | Probes all GET endpoints |
| GET | `/summary` | `get_summary` | REAL | Cached results |

---

### 2.25 admin_abuse.py — `/api/admin/v1/abuse`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/queue` | `get_abuse_queue` | REAL-FS | Scans resume_store for pending |

---

### 2.26 admin_parsing.py — `/api/admin/v1/parsing`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| POST | `/parse` | `run_parse` | REAL | Proxies to parser on port 8010 |
| GET | `/parse/{parse_id}` | `get_parse_result` | MOCK | In-memory, not persisted |
| GET | `/parse` | `list_parses` | MOCK | In-memory |

---

### 2.27 admin_tokens.py — `/api/admin/v1/tokens`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/config` | `get_token_config` | **BROKEN** | Empty store → KeyError → 500 |
| PUT | `/config` | `update_token_config` | PARTIAL | Validates, but in-memory only |
| GET | `/usage` | `get_token_usage` | **BROKEN** | Empty store → KeyError → 500 |

---

### 2.28 anti_gaming.py — `/api/admin/v1/anti-gaming`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| POST | `/check` | `anti_gaming_check` | REAL-SVC | AbusePolicyService + ResumeStore |

---

### 2.29 logs.py — `/api/admin/v1/logs`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/tail` | `tail_logs` | REAL-FS | Reads actual log files |

---

### 2.30 telemetry.py — `/api/telemetry/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/status` | `telemetry_status` | REAL | Simple "ok" |

---

### 2.31 webhooks.py — `/api/payment/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| POST | `/webhooks` | `braintree_webhook` | REAL | Braintree verification + dispatch |

> Note: This overlaps with payment.py's `/webhooks` on the same prefix. The last-registered router wins.

---

### 2.32 admin_tools.py — **(no prefix)**

All endpoints are `GET` and return **MOCK** hardcoded data. The `PageTemplate` component on the frontend fetches `${API_BASE}${endpoint}`.

| Method | Path | Function | Status | FE Consumer |
|--------|------|----------|--------|-------------|
| GET | `/fs/list` | `fs_list` | MOCK | tools/DatasetsBrowser |
| GET | `/fs/read` | `fs_read` | MOCK | — |
| GET | `/ontology/keywords` | `ontology_keywords` | MOCK | tools/KeywordOntology |
| GET | `/ontology/phrases` | `ontology_phrases` | MOCK | tools/PhraseManager |
| GET | `/models/registry` | `model_registry` | MOCK | tools/ModelRegistry |
| GET | `/email/analytics` | `email_analytics_stub` | MOCK | tools/EmailAnalytics |
| GET | `/email/captured` | `email_captured` | MOCK | tools/EmailCapture |
| GET | `/eval/runs` | `eval_runs` | MOCK | tools/EvaluationHarness |
| GET | `/runs/parser` | `parser_runs` | MOCK | tools/ParserRuns |
| GET | `/runs/enrichment` | `enrichment_runs` | MOCK | tools/EnrichmentRuns |
| GET | `/prompts/registry` | `prompt_registry` | MOCK | tools/PromptRegistry |
| GET | `/audit/admin` | `admin_audit` | MOCK | tools/AdminAudit, ops/OpsAdminAudit |
| GET | `/audit/users` | `user_audit` | MOCK | tools/UserAudit |
| GET | `/analytics/fairness` | `bias_fairness` | MOCK | tools/BiasAndFairness |
| GET | `/analytics/scoring` | `scoring_analytics` | MOCK | tools/ScoringAnalytics |
| GET | `/admin/about` | `admin_about` | MOCK | tools/About |
| GET | `/admin/backup` | `admin_backup` | MOCK | tools/BackupRestore |
| GET | `/admin/data-health` | `data_health` | MOCK | tools/DataRootsHealth |
| GET | `/admin/diagnostics` | `admin_diagnostics` | MOCK | tools/Diagnostics |
| GET | `/admin/api-explorer` | `admin_api_explorer` | MOCK | tools/APIExplorer |
| GET | `/admin/exports` | `admin_exports` | MOCK | tools/Exports |
| GET | `/admin/logs-viewer` | `admin_logs_viewer` | MOCK | tools/LogsViewer |
| GET | `/admin/notifications` | `admin_notifications` | MOCK | tools/Notifications |
| GET | `/admin/resume-viewer` | `admin_resume_viewer` | MOCK | tools/ResumeJSONViewer |
| GET | `/admin/route-map` | `admin_route_map` | MOCK | tools/RouteMap |
| GET | `/admin/config` | `admin_config` | MOCK | tools/SystemConfig |

---

### 2.33 admin_email_campaigns.py — `/api/admin/v1`

| Method | Path | Function | Status | Notes |
|--------|------|----------|--------|-------|
| GET | `/integrations/status` | `get_integration_status` | REAL-SVC | email_campaign_service |
| POST | `/integrations/sendgrid/configure` | `configure_sendgrid` | REAL-SVC | |
| POST | `/integrations/klaviyo/configure` | `configure_klaviyo` | REAL-SVC | |
| POST | `/integrations/gmail/configure` | `configure_gmail` | PARTIAL | Runtime only |
| POST | `/integrations/{provider}/disconnect` | `disconnect_provider` | REAL-SVC | |
| GET | `/contacts` | `list_contacts` | REAL-SVC | In-memory via service |
| POST | `/contacts` | `create_contact` | REAL-SVC | |
| PATCH | `/contacts/{contact_id}` | `update_contact` | REAL-SVC | |
| DELETE | `/contacts/{contact_id}` | `delete_contact` | REAL-SVC | |
| POST | `/contacts/import` | `import_contacts` | REAL-SVC | CSV parsing |
| GET | `/contacts/export` | `export_contacts` | REAL-SVC | CSV export |
| GET | `/campaigns` | `list_campaigns` | REAL-SVC | |
| POST | `/campaigns` | `create_campaign` | REAL-SVC | |
| GET | `/campaigns/{campaign_id}` | `get_campaign` | REAL-SVC | |
| POST | `/campaigns/{campaign_id}/send` | `send_campaign` | REAL-SVC | |
| POST | `/email/send_test` | `send_test_email` | REAL-SVC | Via provider |
| POST | `/email/send_bulk` | `send_bulk_email` | REAL-SVC | |
| GET | `/email/logs` | `get_email_logs` | REAL-SVC | |
| GET | `/email/analytics` | `get_email_analytics` | REAL-SVC | |
| GET | `/email/status` | `get_email_status` | REAL-SVC | Overrides admin.py 501 |

---

## 3. Data Status Summary

### Totals by Status

| Status | Count | % |
|--------|-------|---|
| REAL (DB) | ~55 | 33% |
| REAL-FS (file-based) | ~20 | 12% |
| REAL-SVC (service-dependent) | ~35 | 21% |
| MOCK (hardcoded/in-memory) | ~38 | 23% |
| STUB-501 | ~17 | 10% |
| BROKEN (500 at runtime) | ~5 | 3% |
| PARTIAL | ~7 | 4% |

**Approximate total: ~170 endpoints across 33 routers + 2 root probes**

### Routers That Are Entirely Mock / In-Memory

| Router | Endpoint Count | Risk |
|--------|---------------|------|
| `mentor.py` | 9 | HIGH — data lost on restart |
| `rewards.py` | 7 | HIGH — data lost on restart |
| `ops.py` | 17 | MEDIUM — admin visibility only |
| `admin_tools.py` | 26 | MEDIUM — admin tools pages |
| `jobs.py` | 2 | LOW — placeholder search |

### Routers That Are Fully Real

| Router | Endpoint Count |
|--------|---------------|
| `auth.py` | 4 |
| `mentorship.py` | 21 |
| `gdpr.py` | 4 |
| `analytics.py` | 5 |
| `ai_data.py` | 8 |
| `sessions.py` | 4 |
| `taxonomy.py` | 8 |

---

## 4. Frontend ↔ Backend Gap Analysis

### 4.1 Frontend Calls With **NO** Matching Backend Endpoint

| Frontend Page | API Call | Status |
|---------------|----------|--------|
| `MentorManagement.tsx` | `POST /api/admin/mentor-applications/{id}/approve` | **NO BACKEND** — Backend has `POST /api/mentorship/v1/applications/{id}/approve` (different prefix) |
| `MentorManagement.tsx` | `POST /api/admin/mentor-applications/{id}/reject` | **NO BACKEND** — No reject endpoint exists anywhere |
| `Analytics.tsx` | `GET /api/admin/analytics` | **WRONG PATH** — Should be `/api/analytics/v1/dashboard` or `/api/analytics/v1/statistics` |
| `ops/OpsAbout.tsx` | `GET /api/ops/v1/about` | **NO BACKEND** — ops.py has no `/about` route |
| `tools/BlobStorage.tsx` | `GET /api/ops/v1/blob` | **NO BACKEND** — No blob storage endpoint |
| `tools/QueueMonitor.tsx` | `GET /api/ops/v1/queue` | **NO BACKEND** — No queue monitoring endpoint |
| `tools/RoleTaxonomy.tsx` | `GET /api/taxonomy/v1/summary` | **NO BACKEND** — taxonomy.py has no `/summary` route |

### 4.2 Frontend Calls That Hit **BROKEN** Endpoints

| Frontend Page | API Call | Issue |
|---------------|----------|-------|
| `TokenManagement.tsx` | `GET /api/admin/v1/tokens/config` | **500**: empty store, KeyError |
| `TokenManagement.tsx` | `GET /api/admin/v1/tokens/usage` | **500**: empty store, KeyError |

### 4.3 Frontend Calls That Hit **MOCK** Data

| Frontend Page | API Call | Backend Router |
|---------------|----------|---------------|
| All 26 `tools/*` pages | Various `/admin/*`, `/email/*`, `/audit/*`, etc. | `admin_tools.py` (all MOCK) |
| All 10 `ops/*` pages | `/api/ops/v1/*` | `ops.py` (all MOCK) |
| `MarketIntelligence.tsx` | `GET /api/intelligence/v1/market` | `intelligence.py` (MOCK) |

### 4.4 Backend Endpoints With No Known Frontend Consumer

These backend endpoints exist but no admin frontend page calls them:

| Router | Endpoint | Notes |
|--------|----------|-------|
| `user.py` | All `/api/user/v1/*` | Consumed by user portal (not admin) |
| `coaching.py` | All 15 endpoints | Consumed by user portal |
| `blockers.py` | All 3 endpoints | Consumed by user portal |
| `resume.py` | All 6 endpoints | Consumed by user portal |
| `insights.py` | All 7 endpoints | Consumed by user portal's data viz |
| `touchpoints.py` | Both endpoints | Consumed by user portal |
| `mapping.py` | All 3 endpoints | Internal/debug |
| `credits.py` | All 6 endpoints | BROKEN anyway |
| `gdpr.py` | All 4 endpoints | Consumed by user portal settings |
| `sessions.py` | All 4 endpoints | Internal logging |
| `admin.py` | Multiple 501 stubs | Admin pages exist but stubs return 501 |

---

## 5. Email-Specific Endpoints

### What Exists

| Source | Endpoint | Status |
|--------|----------|--------|
| `admin_email_campaigns.py` | `GET /api/admin/v1/email/status` | REAL-SVC |
| `admin_email_campaigns.py` | `GET /api/admin/v1/email/analytics` | REAL-SVC |
| `admin_email_campaigns.py` | `GET /api/admin/v1/email/logs` | REAL-SVC |
| `admin_email_campaigns.py` | `POST /api/admin/v1/email/send_test` | REAL-SVC |
| `admin_email_campaigns.py` | `POST /api/admin/v1/email/send_bulk` | REAL-SVC |
| `admin_email_campaigns.py` | `GET /api/admin/v1/integrations/status` | REAL-SVC |
| `admin_email_campaigns.py` | `POST /api/admin/v1/integrations/sendgrid/configure` | REAL-SVC |
| `admin_email_campaigns.py` | `POST /api/admin/v1/integrations/klaviyo/configure` | REAL-SVC |
| `admin_email_campaigns.py` | `POST /api/admin/v1/integrations/gmail/configure` | PARTIAL |
| `admin_email_campaigns.py` | `POST /api/admin/v1/integrations/{provider}/disconnect` | REAL-SVC |
| `admin_email_campaigns.py` | Full CRUD for contacts (6 endpoints) | REAL-SVC (in-memory) |
| `admin_email_campaigns.py` | Full CRUD for campaigns (4 endpoints) | REAL-SVC (in-memory) |
| `admin_tools.py` | `GET /email/analytics` | MOCK (hardcoded) |
| `admin_tools.py` | `GET /email/captured` | MOCK (hardcoded) |
| `admin.py` | `GET /api/admin/v1/email/status` | STUB-501 (overridden) |
| `admin.py` | `POST /api/admin/v1/email/sync` | STUB-501 |
| `admin.py` | `GET /api/admin/v1/email/jobs` | STUB-501 |

### Frontend Email Pages

| Page | API Call | Resolution |
|------|----------|------------|
| `EmailIntegration.tsx` | **None** (static UI) | No API calls — purely decorative |
| `tools/EmailAnalytics.tsx` | `GET /email/analytics` | Hits `admin_tools.py` MOCK (not the real campaign analytics) |
| `tools/EmailCapture.tsx` | `GET /email/captured` | Hits `admin_tools.py` MOCK |

### Email Gaps

1. **EmailIntegration.tsx** makes zero API calls — needs to wire up to `admin_email_campaigns.py` integration endpoints
2. **EmailAnalytics** tools page hits the MOCK stub at `/email/analytics` instead of the real `GET /api/admin/v1/email/analytics`
3. **EmailCapture** has no real backend — `/email/captured` is MOCK
4. **Email sync** (`POST /api/admin/v1/email/sync`) remains a 501 stub
5. **Email jobs** (`GET /api/admin/v1/email/jobs`) remains a 501 stub
6. Contact and campaign data in `admin_email_campaigns.py` is in-memory — lost on restart

---

## 6. Broken / 500-Error Endpoints

| Endpoint | Router | Issue | Fix |
|----------|--------|-------|-----|
| `GET /api/admin/v1/tokens/config` | `admin_tokens.py` | Empty `_store` dict → KeyError | Initialize with defaults |
| `GET /api/admin/v1/tokens/usage` | `admin_tokens.py` | Empty `_store` dict → KeyError | Initialize with defaults |
| `GET /api/credits/v1/balance` | `credits.py` | `_get_user_id()` always raises 401 | Implement real auth extraction |
| `POST /api/credits/v1/purchase` | `credits.py` | Same | Same |
| `POST /api/credits/v1/spend` | `credits.py` | Same | Same |
| `GET /api/credits/v1/history` | `credits.py` | Same | Same |

---

## 7. Recommendations

### Priority 1 — Fix Broken Endpoints
- **admin_tokens.py**: Initialize `_store` with sensible defaults so `/config` and `/usage` don't 500
- **credits.py**: Replace `_get_user_id()` placeholder with actual JWT/session extraction

### Priority 2 — Fix Frontend ↔ Backend Mismatches
- **MentorManagement.tsx**: Change `POST /api/admin/mentor-applications/{id}/approve` → `POST /api/mentorship/v1/applications/{id}/approve`
- **MentorManagement.tsx**: Create `POST /api/mentorship/v1/applications/{id}/reject` endpoint
- **Analytics.tsx**: Change to use `/api/analytics/v1/dashboard`
- **RoleTaxonomy.tsx**: Add `GET /api/taxonomy/v1/summary` or reroute to existing endpoint

### Priority 3 — Create Missing Backend Endpoints
- `GET /api/ops/v1/about` — system/build info
- `GET /api/ops/v1/blob` — blob storage listing
- `GET /api/ops/v1/queue` — background job queue monitor

### Priority 4 — Wire Email Frontend to Real Backend
- Connect `EmailIntegration.tsx` to `admin_email_campaigns.py` integration endpoints
- Route `tools/EmailAnalytics` to `/api/admin/v1/email/analytics` instead of MOCK `/email/analytics`
- Persist email campaign contacts/campaigns to DB

### Priority 5 — Graduate Mock Routers to DB
- `mentor.py` → PostgreSQL (highest priority — user-facing)
- `rewards.py` → PostgreSQL
- `payment.py` history/subscription → PostgreSQL
- `ops.py` → real implementations or remove unused

### Priority 6 — Implement 501 Stubs
17 endpoints currently return 501. Prioritize:
- `/users/{user_id}/plan` and `/users/{user_id}/disable` (admin user management)
- `/parsers/run` and `/parsers/jobs` (parser orchestration)
- `/batch/*` (batch processing)

---

*End of audit report.*
