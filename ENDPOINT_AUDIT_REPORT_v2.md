# CareerTrojan Backend API — Comprehensive Endpoint Audit v2

**Generated:** 2025-06-17  
**Scope:** All 33 router files in `services/backend_api/routers/`  
**Entry point:** `services/backend_api/main.py` (port 8500)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Router Mounting (main.py)](#router-mounting)
3. [Complete Endpoint Table](#complete-endpoint-table)
4. [Critical Issues](#critical-issues)
5. [Severity Classification](#severity-classification)
6. [DB Model Coverage](#db-model-coverage)
7. [Recommendations](#recommendations)

---

## Executive Summary

| Metric | Count |
|--------|-------|
| Total router files | 33 |
| Total endpoints (approx) | **~190** |
| REAL (DB/service-backed) | ~65 |
| REAL (file-based) | ~30 |
| IN-MEMORY (no persistence) | ~25 |
| HARDCODED STUB | ~45 |
| 501 NOT IMPLEMENTED | ~15 |
| BROKEN (will crash) | ~5 |
| DB Models (SQLAlchemy) | 20+ |

**Overall health: ~50% of endpoints are production-viable.** The remaining half are stubs, hardcoded mocks, in-memory-only stores, or outright broken. Several routers silently fail to mount (try/except in main.py swallows import errors).

---

## Router Mounting

All 33 routers are imported in `main.py`. Most are mounted directly via `app.include_router()`. The following are wrapped in **try/except with silent pass** — if they fail to import, the app starts without them and no error is logged:

| Router | Risk |
|--------|------|
| `payment` | HIGH — payment endpoints vanish silently |
| `rewards` | MEDIUM |
| `mentor` | MEDIUM |
| `admin_abuse` | LOW |
| `admin_parsing` | LOW |
| `admin_tokens` | LOW |
| `anti_gaming` | LOW |
| `logs` | LOW |
| `telemetry` | LOW |

**Startup events:**
- Collocation engine bootstrap (non-blocking)
- Enrichment watchdog (5-minute interval background task)

**CORS origins:** localhost:3000-3002, 5173, 8500-8503, 8600

**Health probes:**
- `GET /healthz` — liveness (always 200)
- `GET /readyz` — deep health (DB, disk, Redis)

---

## Complete Endpoint Table

### Legend

| Status | Meaning |
|--------|---------|
| **REAL-DB** | Connected to SQLAlchemy/PostgreSQL |
| **REAL-FILE** | Reads/writes files on disk (ai_data_final, resume_store) |
| **REAL-SVC** | Delegates to a service class with real logic |
| **IN-MEM** | Works but stores data in Python dicts/lists — lost on restart |
| **STUB-HC** | Returns hardcoded/mock JSON |
| **STUB-501** | Returns HTTP 501 Not Implemented |
| **BROKEN** | Will crash at runtime (missing import, dead code path) |

---

### auth.py — Prefix: `/api/auth`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| POST | `/register` | **REAL-DB** | Creates user, hashes password, returns JWT |
| POST | `/login` | **REAL-DB** | Brute-force protection, JWT issuance |
| POST | `/2fa/generate` | **REAL-DB** | pyotp TOTP secret generation, QR code |
| POST | `/2fa/verify` | **REAL-DB** | TOTP verification |

---

### admin.py — Prefix: `/api/admin`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/users` | **REAL-DB** | Paginated user list |
| GET | `/users/{user_id}` | **REAL-DB** | Single user lookup |
| GET | `/compliance/summary` | **REAL-DB** | Privacy/GDPR compliance stats |
| GET | `/system/activity` | **REAL-DB** | Recent system-wide activity |
| GET | `/dashboard/snapshot` | **REAL-DB** | Aggregate dashboard metrics |
| GET | `/users/subscriptions` | **REAL-DB** | All subscriptions |
| GET | `/ai-loop/monitoring` | **REAL-DB** | AI loop health metrics |
| GET | `/audit/events` | **REAL-DB** | Paginated audit log |
| GET | `/enrichment/status` | **REAL-SVC** | Enrichment pipeline status |
| GET | `/enrichment/jobs` | **REAL-SVC** | Enrichment job list |
| GET | `/email/status` | **STUB-501** | Not implemented |
| GET | `/users/{user_id}/token-ledger` | **STUB-501** | Not implemented |
| GET | `/users/metrics` | **STUB-501** | Not implemented |
| GET | `/users/security` | **STUB-501** | Not implemented |
| PUT | `/users/{user_id}/plan` | **STUB-501** | Not implemented |
| PUT | `/users/{user_id}/disable` | **STUB-501** | Not implemented |
| GET | `/email/sync` | **STUB-501** | Not implemented |
| GET | `/email/jobs` | **STUB-501** | Not implemented |
| POST | `/parsers/run` | **STUB-501** | Not implemented |
| GET | `/parsers/jobs` | **STUB-501** | Not implemented |
| GET | `/parsers/status` | **STUB-HC** | Returns mock parser status |
| GET | `/batch/status` | **STUB-501** | Not implemented |
| POST | `/batch/run` | **STUB-501** | Not implemented |
| GET | `/batch/jobs` | **STUB-501** | Not implemented |
| GET | `/content/status` | **STUB-501** | Not implemented |
| POST | `/content/run` | **STUB-501** | Not implemented |
| GET | `/content/jobs` | **STUB-501** | Not implemented |

---

### admin_abuse.py — Prefix: `/api/admin/abuse`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/queue` | **REAL-FILE** | Scans resume_store directory for flagged items |

---

### admin_email_campaigns.py — Prefix: `/api/admin/email`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/integrations` | **REAL-SVC** | email_campaign_service |
| POST | `/integrations` | **REAL-SVC** | Create integration |
| GET | `/contacts` | **REAL-SVC** | List contacts |
| POST | `/contacts` | **REAL-SVC** | Create contact |
| GET | `/campaigns` | **REAL-SVC** | List campaigns |
| POST | `/campaigns` | **REAL-SVC** | Create campaign |
| POST | `/send` | **REAL-SVC** | Send single email |
| POST | `/bulk-send` | **REAL-SVC** | Bulk email send |
| GET | `/logs` | **REAL-SVC** | Email send logs |
| GET | `/analytics` | **REAL-SVC** | Campaign analytics |

---

### admin_parsing.py — Prefix: `/api/admin/parsing`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| POST | `/parse` | **REAL-SVC** | Proxies to parser service on port 8010 |
| GET | `/results/{parse_id}` | **IN-MEM** | Results stored in dict, lost on restart |
| GET | `/results` | **IN-MEM** | List all stored results |

---

### admin_tokens.py — Prefix: `/api/admin/tokens`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/config` | **BROKEN** | TokenStore.plans is empty → KeyError/500 |
| PUT | `/config` | **BROKEN** | Same — empty store |
| GET | `/usage` | **BROKEN** | Same — empty store. Comment: "MUST replace TokenStore with real DB" |

---

### admin_tools.py — Prefix: **NONE (mounts at root!)**

⚠️ **ALL ~27 endpoints return hardcoded mock JSON. No real logic whatsoever.**

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/fs/list` | **STUB-HC** | Fake directory listing |
| GET | `/fs/read` | **STUB-HC** | Fake file content |
| GET | `/ontology/keywords` | **STUB-HC** | Fake keyword list |
| GET | `/ontology/phrases` | **STUB-HC** | Fake phrase list |
| GET | `/models/registry` | **STUB-HC** | Fake model registry |
| GET | `/email/analytics` | **STUB-HC** | Fake email stats |
| GET | `/email/captured` | **STUB-HC** | Fake captured emails |
| GET | `/eval/runs` | **STUB-HC** | Fake eval results |
| GET | `/runs/parser` | **STUB-HC** | Fake parser runs |
| GET | `/runs/enrichment` | **STUB-HC** | Fake enrichment runs |
| GET | `/prompts/registry` | **STUB-HC** | Fake prompts |
| GET | `/audit/admin` | **STUB-HC** | Fake admin audit log |
| GET | `/audit/users` | **STUB-HC** | Fake user audit log |
| GET | `/analytics/fairness` | **STUB-HC** | Fake fairness metrics |
| GET | `/analytics/scoring` | **STUB-HC** | Fake scoring analytics |
| GET | `/admin/about` | **STUB-HC** | Fake about info |
| POST | `/admin/backup` | **STUB-HC** | Fake backup trigger |
| GET | `/admin/data-health` | **STUB-HC** | Fake data health |
| GET | `/admin/diagnostics` | **STUB-HC** | Fake diagnostics |
| GET | `/admin/api-explorer` | **STUB-HC** | Fake API explorer |
| GET | `/admin/exports` | **STUB-HC** | Fake exports list |
| GET | `/admin/logs-viewer` | **STUB-HC** | Fake log viewer |
| GET | `/admin/notifications` | **STUB-HC** | Fake notifications |
| GET | `/admin/resume-viewer` | **STUB-HC** | Fake resume viewer |
| GET | `/admin/route-map` | **STUB-HC** | Fake route map |
| GET | `/admin/config` | **STUB-HC** | Fake config |

**Risk:** No prefix means these paths can collide with other routers. The `/email/analytics` path conflicts with admin_email_campaigns.py's analytics endpoint.

---

### ai_data.py — Prefix: `/api/ai-data`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/parsed-resumes` | **REAL-FILE** | Reads from ai_data_final |
| GET | `/parsed-resumes/{resume_id}` | **REAL-FILE** | Single resume lookup |
| GET | `/job-descriptions` | **REAL-FILE** | JD listing |
| GET | `/job-descriptions/{jd_id}` | **REAL-FILE** | Single JD |
| GET | `/companies` | **REAL-FILE** | Company list |
| GET | `/companies/{company_id}` | **REAL-FILE** | Single company |
| GET | `/job-titles` | **REAL-FILE** | Job title list |
| GET | `/locations` | **REAL-FILE** | Location list |
| GET | `/metadata` | **REAL-FILE** | Dataset metadata |
| GET | `/normalized` | **REAL-FILE** | Normalized data |
| GET | `/email-extracted` | **REAL-FILE** | Extracted emails |
| GET | `/automated/candidates` | **REAL-FILE** | Candidate data |
| GET | `/user-data/files` | **REAL-FILE** | User data listing |
| POST | `/model/reload` | **REAL-SVC** | Reloads model config |
| POST | `/model/switch` | **REAL-SVC** | Switches active model |
| GET | `/model/status` | **REAL-SVC** | Current model info |

---

### analytics.py — Prefix: `/api/analytics`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/statistics` | **REAL-FILE** | Counts files in ai_data_final |
| GET | `/dashboard` | **REAL-FILE** | Aggregate dashboard from file counts |
| GET | `/recent-resumes` | **REAL-FILE** | Recently modified resume files |
| GET | `/recent-jobs` | **REAL-FILE** | Recently modified JD files |
| GET | `/system-health` | **REAL-FILE** | Directory existence + file counts |
| GET | `/enrichment/status` | **REAL-FILE** | Enrichment output status |
| GET | `/email/extraction-status` | **REAL-FILE** | Email extraction stats |

---

### anti_gaming.py — Prefix: `/api/anti-gaming`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| POST | `/check` | **REAL-SVC** | AbusePolicyService + ResumeStore fingerprint check |

---

### api_health.py — Prefix: `/api/health`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/endpoints` | **REAL-SVC** | Dynamic route extraction from FastAPI app |
| GET | `/probe-all` | **REAL-SVC** | TestClient probes all GET endpoints |
| GET | `/summary` | **REAL-SVC** | Cached health summary |

---

### blockers.py — Prefix: `/api/blockers/v1`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| POST | `/detect` | **REAL-SVC** | blocker_connector detection |
| GET | `/user/{user_id}` | **REAL-DB** | BlockerService with DB session |
| POST | `/improvement-plans/generate` | **BROKEN** | Uses `status.HTTP_501_NOT_IMPLEMENTED` but `status` is never imported → NameError crash |

---

### coaching.py — Prefix: `/api/coaching`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| POST | `/bundle` | **REAL-SVC** | career_coach + taxonomy service |
| GET | `/health` | **REAL-SVC** | Service health check |
| POST | `/questions/generate` | **STUB-HC** | Hardcoded question pools (not AI-generated) |
| POST | `/answers/review` | **STUB-HC** | Rule-based keyword scoring, not real review |
| POST | `/stories/generate` | **STUB-HC** | Template-based STAR story, not AI |
| POST | `/detect-role` | **REAL-SVC** | InterviewCoachingService (501 if unavailable) |
| POST | `/smart-questions` | **REAL-SVC** | InterviewCoachingService (501 if unavailable) |
| POST | `/90-day-plan` | **REAL-SVC** | InterviewCoachingService (501 if unavailable) |
| GET | `/company-intel/{company}` | **REAL-SVC** | company_intel_service (503 if unavailable) |
| GET | `/company-intel/{company}/culture` | **REAL-SVC** | Same |
| GET | `/company-intel/{company}/interview-style` | **REAL-SVC** | Same |
| GET | `/company-intel/{company}/red-flags` | **REAL-SVC** | Same |
| GET | `/company-intel/{company}/prep-kit` | **REAL-SVC** | Same |

---

### credits.py — Prefix: `/api/credits`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/balance` | **BROKEN** | `_get_user_id()` always raises HTTP 401 |
| POST | `/purchase` | **BROKEN** | Same — auth dependency dead |
| POST | `/consume` | **BROKEN** | Same |
| GET | `/transactions` | **BROKEN** | Same |
| GET | `/plans` | **BROKEN** | Same |
| POST | `/upgrade` | **BROKEN** | Same. Comment: "TODO: Wire to real JWT / session dependency" |
| GET | `/health` | **REAL-SVC** | Only endpoint that works |

---

### gdpr.py — Prefix: `/api/gdpr`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| POST | `/consent` | **REAL-DB** | Records consent with audit log |
| GET | `/consent/{user_id}` | **REAL-DB** | Retrieves consent records |
| PUT | `/consent/{user_id}` | **REAL-DB** | Updates consent |
| POST | `/data-export/{user_id}` | **REAL-DB** | Creates export request |
| GET | `/data-export/{user_id}` | **REAL-DB** | Gets export request status |
| DELETE | `/account/{user_id}` | **REAL-DB** | Full cascade deletion with audit |
| GET | `/audit/{user_id}` | **REAL-DB** | User's GDPR audit trail |

---

### insights.py — Prefix: `/api/insights`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/skills-radar/{profile_id}` | **STUB-HC** | Uses `random.uniform()` for "AI confidence" — not real |
| GET | `/quadrant/{profile_id}` | **REAL-SVC** | DataLoader-based |
| GET | `/term-cloud/{profile_id}` | **REAL-SVC** | DataLoader-based |
| GET | `/co-occurrence/{profile_id}` | **REAL-SVC** | DataLoader-based |
| GET | `/graph/{profile_id}` | **REAL-SVC** | DataLoader-based |
| GET | `/cohort-resolve/{profile_id}` | **REAL-SVC** | DataLoader-based |

---

### intelligence.py — Prefix: `/api/intelligence`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| POST | `/stats/descriptive` | **REAL-SVC** | StatisticalAnalysisEngine |
| POST | `/stats/regression` | **REAL-SVC** | StatisticalAnalysisEngine |
| GET | `/market` | **STUB-HC** | Hardcoded salary benchmarks |
| POST | `/enrich` | **STUB-501** | Returns empty arrays, TODO comment |

---

### jobs.py — Prefix: `/api/jobs`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/index` | **STUB-HC** | In-memory `_jobs_db` with 3 fake jobs |
| GET | `/search` | **STUB-HC** | Same in-memory list, keyword filter only |

**Note:** DB has a `jobs` table (Job model) but this router ignores it entirely.

---

### logs.py — Prefix: `/api/logs`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/tail` | **REAL-FILE** | File-based log tail with regex error matching |

---

### mapping.py — Prefix: `/api/mapping`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/endpoints` | **REAL-SVC** | Dynamic route extraction |
| GET | `/visual` | **REAL-FILE** | Reads visual registry JSON |
| GET | `/graph` | **REAL-SVC** | Cytoscape format graph generation |

---

### mentor.py — Prefix: `/api/mentor`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/profiles` | **IN-MEM** | Python dict, no DB |
| POST | `/profiles` | **IN-MEM** | Creates in dict, no persistence |
| GET | `/profiles/{mentor_id}` | **IN-MEM** | Lookup in dict |
| PUT | `/profiles/{mentor_id}` | **IN-MEM** | Update in dict |
| DELETE | `/profiles/{mentor_id}` | **IN-MEM** | Remove from dict |
| GET | `/packages` | **IN-MEM** | Service packages dict |
| POST | `/packages` | **IN-MEM** | Create in dict |
| GET | `/packages/{package_id}` | **IN-MEM** | Lookup in dict |
| GET | `/availability/{mentor_id}` | **IN-MEM** | Availability dict |
| PUT | `/availability/{mentor_id}` | **IN-MEM** | Update in dict |
| GET | `/dashboard-stats` | **IN-MEM** | Counts from dicts |
| GET | `/health` | **REAL-SVC** | Always returns ok |

**Note:** DB has `mentors` table (Mentor model) but this router ignores it entirely.

---

### mentorship.py — Prefix: `/api/mentorship`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| POST | `/links` | **REAL-DB** | MentorshipService (raw DBAPI cursor) |
| GET | `/links` | **REAL-DB** | List mentorship links |
| GET | `/links/{link_id}` | **REAL-DB** | Single link detail |
| PUT | `/links/{link_id}/status` | **REAL-DB** | Update link status |
| POST | `/notes` | **REAL-DB** | Create session note |
| GET | `/notes/{link_id}` | **REAL-DB** | Get notes for link |
| POST | `/documents` | **REAL-DB** | Create requirements doc |
| GET | `/documents/{link_id}` | **REAL-DB** | Get docs for link |
| PUT | `/documents/{doc_id}/sign` | **REAL-DB** | Sign document |
| POST | `/invoices` | **REAL-DB** | Create invoice |
| GET | `/invoices/{link_id}` | **REAL-DB** | Get invoices for link |
| PUT | `/invoices/{invoice_id}/status` | **REAL-DB** | Update invoice status |
| POST | `/disputes` | **REAL-DB** | File dispute |
| GET | `/disputes` | **REAL-DB** | List disputes |
| PUT | `/disputes/{dispute_id}` | **REAL-DB** | Resolve dispute |
| POST | `/applications` | **REAL-DB** | Mentor application |
| GET | `/applications` | **REAL-DB** | List applications |
| GET | `/dashboard/{user_id}` | **REAL-DB** | User mentorship dashboard |

---

### ops.py — Prefix: `/api/ops`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/stats/public` | **STUB-HC** | Hardcoded counts |
| POST | `/processing/start` | **STUB-HC** | Fake background task ID |
| POST | `/logs/lock` | **STUB-HC** | Lock simulation |
| GET | `/tokens/config` | **STUB-HC** | Hardcoded plan structure |
| POST | `/anti-gaming/check` | **STUB-HC** | Simplified mock check |
| GET | `/admin/logs` | **STUB-HC** | Hardcoded log entries |
| POST | `/admin/backup` | **STUB-HC** | Fake backup |
| GET | `/admin/diagnostics` | **STUB-HC** | Fake diagnostics |
| GET | `/admin/route-map` | **STUB-HC** | Fake route map |
| GET | `/admin/notifications` | **STUB-HC** | Fake notifications |
| GET | `/admin/config` | **STUB-HC** | Fake config |
| GET | `/admin/exports` | **STUB-HC** | Fake exports |
| GET | `/admin/api-explorer` | **STUB-HC** | Fake API explorer |
| GET | `/admin/about` | **STUB-HC** | Fake about |
| POST | `/admin/blob` | **STUB-HC** | Fake blob storage |
| POST | `/admin/queue` | **STUB-HC** | Fake queue push |

**Note:** Multiple paths here overlap with admin_tools.py (both define `/admin/backup`, `/admin/diagnostics`, etc.). FastAPI will use whichever was mounted first.

---

### payment.py — Prefix: `/api/payment`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/plans` | **REAL-SVC** | Hardcoded plan constants (not DB) but real structure |
| GET | `/client-token` | **REAL-SVC** | Braintree client token generation |
| POST | `/subscribe` | **REAL-SVC** | Braintree subscription creation with real gateway |
| GET | `/subscription/{user_id}` | **IN-MEM** | Stored in Python dict, not DB |
| POST | `/cancel` | **IN-MEM** | Cancels from dict + Braintree |
| GET | `/methods/{user_id}` | **REAL-SVC** | Braintree payment methods |
| POST | `/methods` | **REAL-SVC** | Create payment method in Braintree |
| DELETE | `/methods/{token}` | **REAL-SVC** | Delete from Braintree |
| GET | `/transactions/{user_id}` | **REAL-SVC** | Braintree transaction search |
| POST | `/refund/{transaction_id}` | **REAL-SVC** | Braintree refund |
| GET | `/health` | **REAL-SVC** | Gateway ping |

**Critical:** Subscription state stored in-memory dict — Braintree has the real data but local state is lost on restart. No DB persistence for subscriptions.

---

### resume.py — Prefix: `/api/resume`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| POST | `/upload` | **REAL-FILE** | Saves file + text extraction |
| GET | `/list` | **REAL-FILE** | Lists from JSON DB file |
| GET | `/{resume_id}` | **REAL-FILE** | Single resume lookup |
| GET | `/latest` | **REAL-FILE** | Most recent resume |
| POST | `/parse` | **STUB-HC** | Returns PLACEHOLDER skills/email/phone. Marked DEPRECATED |
| POST | `/enrich` | **STUB-501** | Not implemented |

---

### rewards.py — Prefix: `/api/rewards`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/available` | **IN-MEM** | Python dict of rewards |
| GET | `/{reward_id}` | **IN-MEM** | Single reward lookup |
| POST | `/redeem` | **IN-MEM** | Redemption recorded in dict |
| GET | `/history` | **IN-MEM** | Redemption history from dict |
| GET | `/suggestions` | **IN-MEM** | Suggestion list from dict |
| POST | `/referral` | **IN-MEM** | Referral tracking in dict |
| GET | `/referral/status` | **IN-MEM** | Referral status from dict |
| GET | `/leaderboard` | **IN-MEM** | Leaderboard from dict |
| GET | `/ownership-stats` | **IN-MEM** | Stats from dict |
| GET | `/health` | **REAL-SVC** | Always ok |

---

### sessions.py — Prefix: `/api/sessions`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| POST | `/log` | **REAL-FILE** | Writes session log to L: drive + mirror |
| GET | `/summary/{user_id}` | **REAL-FILE** | Reads session files |
| GET | `/sync-status` | **REAL-FILE** | Checks mirror sync |
| GET | `/user/{user_id}` | **REAL-FILE** | Consolidated user session view |

---

### shared.py — Prefix: `/api/shared`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/health` | **REAL-SVC** | Lightweight ping |
| GET | `/health/deep` | **REAL-SVC** | DB + disk + Redis checks |

---

### taxonomy.py — Prefix: `/api/taxonomy`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/industries` | **REAL-SVC** | industry_taxonomy_service |
| GET | `/industries/{industry_id}/sub-industries` | **REAL-SVC** | Same |
| GET | `/job-titles/search` | **REAL-SVC** | Same |
| GET | `/job-titles/{title_id}` | **REAL-SVC** | Same |
| GET | `/naics/search` | **REAL-SVC** | Same |
| GET | `/naics/{code}/mapping` | **REAL-SVC** | Same |

---

### telemetry.py — Prefix: `/api/telemetry`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/status` | **STUB-HC** | Returns `{"status": "ok"}` only |

---

### touchpoints.py — Prefix: `/api/touchpoints`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/evidence/{profile_id}` | **REAL-SVC** | DataLoader-based evidence lookup |
| GET | `/touch-not/{profile_id}` | **REAL-SVC** | DataLoader-based negative signals |

---

### user.py — Prefix: `/api/user`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| GET | `/me` | **REAL-DB** | Current user from JWT |
| GET | `/profile` | **REAL-DB** | User profile |
| PUT | `/profile` | **REAL-DB** | Update profile |
| GET | `/stats` | **STUB-HC** | Hardcoded demo statistics |
| GET | `/activity` | **STUB-HC** | Hardcoded demo activity feed |

---

### webhooks.py — Prefix: `/api/webhooks`

| Method | Path | Status | Notes |
|--------|------|--------|-------|
| POST | `/braintree` | **REAL-SVC** | Signature-verified webhook handler. Event dispatch implemented but handler bodies have TODOs for DB persistence |

---

## Critical Issues

### P0 — Will Crash at Runtime

| # | Issue | File | Impact |
|---|-------|------|--------|
| 1 | **`status` not imported** — `status.HTTP_501_NOT_IMPLEMENTED` causes `NameError` | `blockers.py:48` | POST `/api/blockers/v1/improvement-plans/generate` crashes with 500 |
| 2 | **`_get_user_id()` always raises 401** — hardcoded `raise HTTPException(401)` | `credits.py` | ALL 6 credit endpoints are dead (balance, purchase, consume, transactions, plans, upgrade) |
| 3 | **TokenStore is empty dataclass** — `.plans` attribute is an empty dict | `admin_tokens.py` | All 3 token admin endpoints throw 500 |
| 4 | **Silent router import failures** — `payment`, `rewards`, `mentor` wrapped in try/except pass | `main.py` | If any dependency fails, these routers vanish with zero logging |

### P1 — Data Loss / Integrity

| # | Issue | File | Impact |
|---|-------|------|--------|
| 5 | **Payment subscriptions in-memory only** — dict lost on restart | `payment.py` | Braintree has data, but app loses local subscription state |
| 6 | **Mentor profiles/packages in-memory** — full CRUD but no persistence | `mentor.py` | All mentor data lost on every restart. DB model exists but unused |
| 7 | **Rewards system in-memory** — redemptions, referrals, leaderboard | `rewards.py` | All reward state lost on restart |
| 8 | **Admin parse results in-memory** | `admin_parsing.py` | Parse results lost on restart |
| 9 | **Jobs router ignores DB** — uses hardcoded list instead of Job model | `jobs.py` | Jobs table exists in DB but is never queried |

### P2 — Functionality Gaps

| # | Issue | File | Impact |
|---|-------|------|--------|
| 10 | **~27 admin_tools endpoints are ALL stubs** — hardcoded JSON | `admin_tools.py` | Entire admin panel shows fake data |
| 11 | **~16 ops endpoints are ALL stubs** — hardcoded JSON | `ops.py` | Ops dashboard shows fake data |
| 12 | **~15 admin.py endpoints return 501** | `admin.py` | Large portions of admin functionality missing |
| 13 | **Resume parse returns placeholder data** | `resume.py` | Upload works but parsing returns fake skills/contact |
| 14 | **No prefix on admin_tools.py router** | `admin_tools.py` | Routes mount at root, potential conflicts with ops.py |
| 15 | **Path conflicts** — ops.py `/admin/backup` vs admin_tools.py `/admin/backup` | Both files | FastAPI serves first-mounted, second is shadowed |
| 16 | **insights skills-radar uses `random.uniform()`** for "AI confidence" | `insights.py` | Non-deterministic, non-meaningful data returned to users |
| 17 | **Coaching question generation uses hardcoded pools** | `coaching.py` | Not AI-generated despite endpoint name |
| 18 | **Telemetry is a single-line stub** | `telemetry.py` | No actual telemetry collection |

---

## Severity Classification

### Fully Production-Viable Routers (8)
- `auth.py` — DB-backed auth with 2FA
- `gdpr.py` — Full GDPR compliance
- `mentorship.py` — Full DB-backed mentorship system
- `admin_email_campaigns.py` — Full email campaign management
- `taxonomy.py` — Industry/job taxonomy service
- `sessions.py` — File-based session logging
- `shared.py` — Health checks
- `anti_gaming.py` — Abuse detection

### Mostly Working, Minor Gaps (8)
- `ai_data.py` — All file-based reads work
- `analytics.py` — File-based analytics work
- `api_health.py` — Dynamic health probing works
- `coaching.py` — Core bundle works; question/answer stubs
- `mapping.py` — Route mapping works
- `touchpoints.py` — DataLoader-dependent
- `webhooks.py` — Braintree handler works, TODOs in DB persistence
- `logs.py` — File tail works

### Partially Working (5)
- `payment.py` — Braintree real, subscriptions not persisted
- `user.py` — Profile real, stats/activity stubbed
- `resume.py` — Upload real, parse stubbed
- `blockers.py` — 2/3 endpoints work, 1 crashes
- `intelligence.py` — 2/4 endpoints work

### Completely Stub/Broken (12)
- `admin_tools.py` — 100% hardcoded stubs (~27 endpoints)
- `ops.py` — 100% hardcoded stubs (~16 endpoints)
- `admin_tokens.py` — 100% broken (always 500)
- `credits.py` — Auth dead, 0% functional (6 endpoints)
- `mentor.py` — In-memory only, ignores DB model
- `rewards.py` — In-memory only
- `jobs.py` — In-memory stubs, ignores DB model
- `telemetry.py` — Single stub line
- `admin.py` — 10 real / 17 stubbed (mixed)
- `insights.py` — skills-radar uses random()
- `admin_parsing.py` — Works but no persistence
- `admin_abuse.py` — Works but minimal

---

## DB Model Coverage

Models defined in `db/models.py` (20+ models):

| Model | Used By Router? | Notes |
|-------|----------------|-------|
| `User` | YES | auth, user, gdpr |
| `UserProfile` | YES | user.py profile CRUD |
| `ConsentRecord` | YES | gdpr.py consent |
| `AuditLog` | YES | gdpr.py, admin.py audit trail |
| `DataExportRequest` | YES | gdpr.py exports |
| `Interaction` | YES | middleware interaction logging |
| `Subscription` | PARTIAL | admin.py reads; payment.py ignores it (uses in-memory dict) |
| `PaymentTransaction` | NO | Defined but no router writes to it |
| `Resume` | PARTIAL | resume.py upload saves file, but model not used for parsed content |
| `Job` | NO | jobs.py uses hardcoded list instead |
| `Mentor` | NO | mentor.py uses in-memory dict instead |
| `Mentorship` | YES | mentorship.py full CRUD |
| `MentorNote` | YES | mentorship.py session notes |
| `RequirementDocument` | YES | mentorship.py documents |
| `Invoice` | YES | mentorship.py invoicing |
| `MentorApplication` | YES | mentorship.py applications |
| `ApplicationBlocker` | YES | blockers.py detection |
| `BlockerImprovementPlan` | PARTIAL | Model exists, but endpoint crashes (missing import) |
| `RoleFunctionDefinition` | YES | coaching.py interview coaching |
| `InterviewQuestionBank` | YES | coaching.py question bank |
| `NinetyDayPlanTemplate` | YES | coaching.py 90-day plans |
| `UserInterviewSession` | YES | coaching.py session tracking |
| `UserNinetyDayPlan` | YES | coaching.py custom plans |

**4 models are defined in the DB but completely ignored by their corresponding routers** (Job, Mentor, PaymentTransaction, Subscription-for-writes).

---

## Recommendations

### Immediate Fixes (< 1 day each)

1. **Fix `blockers.py`** — Add `from starlette import status` at top of file
2. **Fix `credits.py`** — Replace `_get_user_id()` with proper `Depends(get_current_user)` from auth
3. **Fix `admin_tokens.py`** — Connect to DB or remove; current state always 500s
4. **Add logging to try/except blocks in `main.py`** — Replace `pass` with `logger.error()`
5. **Add prefix to `admin_tools.py`** — Set `prefix="/api/admin-tools"` to prevent path collisions

### Short-Term (1-2 weeks)

6. **Wire `mentor.py` to DB** — Mentor model exists, just needs SQLAlchemy session
7. **Wire `jobs.py` to DB** — Job model exists, just needs queries
8. **Wire `payment.py` subscriptions to DB** — Subscription model exists
9. **Replace hardcoded resume parse** — Connect to parser service (already working in admin_parsing.py)
10. **Implement rewards persistence** — Create Reward/Redemption models or use existing

### Medium-Term (1-2 months)

11. **Replace admin_tools.py stubs** with real implementations
12. **Replace ops.py stubs** with real implementations
13. **Implement the 15+ admin.py 501 endpoints**
14. **Add real telemetry collection**
15. **Replace `random()` in insights skills-radar** with actual AI confidence scoring

---

*End of audit report.*
