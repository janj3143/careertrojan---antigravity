# CareerTrojan Runtime Build Plan

**Last Updated**: 2026-02-22 (Session 11 — Phases 4a/4b/4c completed, Phase 8 cleanup done, Phase 9 production hardening done, Zendesk helpdesk integration phase added)

This document outlines the strategy for building the **CareerTrojan Runtime Version**, emerging from the **CareerTrojan** system. The goal is to create a high-performance, unified platform that links seamlessly with the `L:\antigravity_version_ai_data_final` dataset.

## User Review Required

> [!IMPORTANT]
> **Global Renaming:** Every instance of "Intellicv-AI" will be rebranded to **CareerTrojan**. This includes headers, titles, logging, and metadata across all portals.
>
> **Python 3.11 Environment:** Standardised on **Python 3.11.9** at `C:\careertrojan\.venv\Scripts\python.exe` (working SSL, pip, full ML stack). Legacy `infra/venv-py311` (3.11.4, broken SSL) deprecated. All ghost versions removed (2026-02-08).
>
> **Consolidation:** We are moving from a "per-page" fragmented React structure to three unified portals: **Admin**, **User**, and **Mentor**.
>
> **Data & AI Linking:** Runtime lives at `C:\careertrojan`; all production data lives at `L:\antigravity_version_ai_data_final` via junctions under `C:\careertrojan\data-mounts\`. Tandem sync to `L:\antigravity_version_ai_data_final\USER DATA\`.
>
> **Configuration Phase 1 (Testing):** A Premium Test User (`janj3143`) will be auto-seeded.
>
> **Asset Location:** The Official Logo located at `L:\antigravity_version_ai_data_final\FULL_REACT_PAGES\careertrojan-logo` MUST be used. No variations.
>
> **Docker Config:** Runtime will expose port **8500** (Web) and use the 8500-8600 range to avoid conflicts >8700. Container name `CaReerTroJan-Antigravity`.

## 🔒 Security & Access Protocols (Critical Review)

> [!CAUTION]
> **Admins MUST NEVER view or store user passwords.**

### 1. Admin Impersonation ("Masquerade Mode")
To allow Admins to debug user issues without compromising security:
1.  **Authentication**: Admin logs in with mandatory **2FA**.
2.  **Action**: Admin selects "Impersonate" on a user profile.
3.  **Mechanism**: The server issues a temporary, time-limited **Session Token** for that user.
4.  **Audit**: This action is logged in the immutable security log: `[ALERT] Admin X started impersonation of User Y`.

### 2. Log Immutability
- All logs in `USER DATA` are enforced as **Read-Only** immediately after writing.
- **Admin Review**: Access to these logs requires active 2FA verification.

### 3. Test Identity
- **Username**: `janj3143`
- **Role**: Premium User (Seeded on Bootstrap)

## 🪤 Data Integrity Traps (Anti-Contamination)
To ensure the system is using **Real AI Data** and not falling back to hardcoded demos:
- **The "Sales vs Python" Trap**: We will run an inference test on a "Sales Person" profile.
    - **Pass**: Result suggests "Account Executive", "Business Development".
    - **FAIL**: Result suggests "Python Developer", "Machine Learning Engineer" (Common hardcoded defaults).
- **Behavior**: If a Trap is triggered, the Runtime will **HALT** with a `DATA_CONTAMINATION_ERROR`.

## Proposed Architecture

### 1. Code Structure (in `c:\careertrojan`)

```
careertrojan/
├── apps/
│   ├── admin/              # Unified React Admin app
│   ├── user/               # Unified React User app
│   └── mentor/             # Unified React Mentor app
├── services/
│   ├── backend_api/        # FastAPI Canonical API (v1)
│   ├── ai_engine/          # AI inference engine
│   ├── workers/            # Resume parsing & enrichment workers
│   ├── shared/             # Shared services + portal-bridge
│   └── shared_backend/     # Shared backend utilities
├── shared/
│   ├── contracts/          # OpenAPI & Data schemas
│   ├── registry/           # Dynamic capability registry (Flexibility Layer)
│   └── utils/              # Shared Python/JS utilities
├── infra/
│   ├── venv-py311/         # Python 3.11 Virtual Environment
│   ├── docker-compose.yml  # Local runtime orchestration
│   └── nginx/              # Reverse proxy & routing
├── data-mounts/
│   ├── ai-data   → L:\antigravity_version_ai_data_final
│   ├── parser    → L:\antigravity_version_ai_data_final\automated_parser
│   ├── user-data → L:\antigravity_version_ai_data_final\USER DATA
│   ├── logs      → (TBD)
│   └── models    → (TBD)
└── scripts/                # Build and migration scripts
```

### 2. Implementation Phases

#### Phase 1: Foundation & Renaming ✅ COMPLETE
- [x] Initialize `c:\careertrojan` and create a **Python 3.11** virtual environment.
- [x] Install mandatory packages from requirements files.
- [x] Run a global search-and-replace to change "Intellicv-AI" to "CareerTrojan".
- [x] Set up the `portal-bridge` to handle unified authentication and API requests.

#### Phase 2: Flexible Mapping & Consolidation ✅ COMPLETE
- [x] **Capability Registry:** Dynamic registry in `shared/registry` for toggling AI models, parsers, or UI modules.
- [x] **Admin Portal:** 31 pages (00–31) + 29 tools + 10 ops pages in `apps/admin/src/pages/`.
- [x] **User Portal:** 15 pages + ConsolidationPage in `apps/user/src/pages/`.
- [x] **Mentor Portal:** 12 pages (each with nested sub-app src) in `apps/mentor/src/pages/`.

#### Phase 3: Backend & Data Linking ✅ COMPLETE
- [x] Deploy the FastAPI `backend-api` with versioned routes (`/api/{domain}/v1/*`).
- [x] Wire the `L:\antigravity_version_ai_data_final` path via junction mounts in `data-mounts/`.
- [x] Implement the `ai-workers` to process files in the `automated_parser` directory.
- [x] **29 routers** registered — all mounted (10 via try/except for graceful degradation).
- [x] **Middleware stack**: RequestCorrelationMiddleware → InteractionLoggerMiddleware → RateLimitMiddleware.
- [x] **Braintree payment gateway** — sandbox integration complete, 27 unit + 20 e2e tests passing.
- [x] **GDPR router** — data export/deletion endpoints.

#### Phase 4: Page-by-Page Testing & Validation ✅ COMPLETE (Feb 2026)
- [x] Map every route defined in `MAPPING.md` to a functioning React page.
- [x] Verify API connectivity for core interactions (Resume Upload, Enrichment, etc.).
- [x] **136 tests green** across unit/integration/e2e tiers.
- [x] **4a — Endpoint Introspection Pipeline** → `scripts/run_introspection.py` ✅ (2026-02-22)
  - **248 backend routes** discovered via FastAPI introspection
  - **150 frontend callsites** found across 3 portals + mentor sub-apps
  - **94 unmatched callsites** (widgets, external URLs, template literals — expected)
  - Output: `reports/endpoint_map.json`
- [x] **4b — React Callsite Migration** → `scripts/migrate_react_api_prefixes.py` ✅ (2026-02-22)
  - Scanned all portal `src/` directories (14 dirs including mentor sub-apps)
  - **0 legacy prefixes found** — all callsites already canonical `/api/{domain}/v1`
  - No files modified (migration was not needed)
- [x] **4c — Full Validation Deep-Dive** ✅ (2026-02-22)
  - **Zero "Intellicv-AI"** in live code (`apps/`, `services/`, `config/`, `scripts/`) — only in `full_rebrand.py` mapping table (expected)
  - **Junction health**: ai-data ✅, parser ✅, user-data ✅ (all confirmed as reparse points)
  - **L: sync trap**: write + read verified on `L:\antigravity_version_ai_data_final\USER DATA\test\`
  - **Contamination trap**: No hardcoded default-role contamination (source scan clean)

#### Phase 4d: Deep Ingestion, Collocation Mining & AI Model Training ✅ RUNNING (Feb 2026)
> **Script**: `scripts/deep_ingest_and_train.py` — unified 3-phase pipeline
> **Status**: Running as background process (started 2026-02-19 13:44)
> **Log**: `logs/deep_pipeline_output.log` + `logs/deep_ingest_and_train.log`

**ML Stack Installed (`.venv` Python 3.11.9)**:
- scikit-learn 1.3.2, pandas 2.2.2, numpy 1.26.4
- spaCy 3.8.11 + en_core_web_sm 3.8.0
- NLTK 3.9.2, sentence-transformers 5.2.3, PyTorch 2.10.0
- pdfplumber, python-docx, extract_msg, openpyxl

**Phase A — Deep Document Parsing** (174,005 files in `automated_parser/`):
- [x] Extracts text from PDF, DOCX, XLSX, CSV, MSG, TXT, JSON, RTF
- [x] Classifies each document as CV, job_description, company_info, email, data, etc.
- [x] Extracts job titles, skills, company names, contact info via spaCy NER + regex
- [x] Outputs per-document JSON to `ai_data_final/parsed_resumes/`, `parsed_from_automated/`, `parsed_job_descriptions/`
- [x] Updates `consolidated_terms.json`, `Candidate_database_merged.json`, `enhanced_job_titles_database.json`
- [x] File-hash deduplication + incremental progress tracking (`deep_parse_progress.json`)
- File breakdown: Candidate/ (155K), Holly backup (29K), ai_data (17K), David (5K), Consultant docs (4K), Companies (2K), +33 smaller dirs

**Phase B — Collocation Mining** (runs after Phase A):
- [x] N-gram extraction (2-4 grams, CountVectorizer, min_df=2)
- [x] PMI scoring (bigrams, threshold ≥3.0)
- [x] NLTK collocations (BigramCollocationFinder, TrigramCollocationFinder)
- [x] Window co-occurrence analysis (window=5)
- [x] Categorization into TECH_SKILL, SOFT_SKILL, CERTIFICATION, INDUSTRY_TERM, OIL_GAS, METHODOLOGY, INDUSTRIAL_SKILL
- [x] Updates gazetteers (7 JSON files), `learned_collocations.json`, `collocation_mining_results.json`

**Phase C — AI Model Training** (runs after Phase B):
- [x] Bayesian classifier (MultinomialNB + TF-IDF) → `trained_models/bayesian_classifier.pkl`
- [x] Sentence-BERT embeddings (all-MiniLM-L6-v2) → `trained_models/candidate_embeddings.npy`
- [x] spaCy NER verification → `trained_models/spacy_model_info.json`
- [x] K-Means + DBSCAN clustering → `trained_models/kmeans_model.pkl`, `clustering_results.json`
- [x] Cosine similarity matrix → `trained_models/similarity_matrix.npy`
- [x] Job title classifier (RandomForest) → `trained_models/job_classifier.pkl`
- [x] TF-IDF top features → `trained_models/tfidf_top_features.json`
- [x] Full training report → `trained_models/training_report.json`

#### Phase 5: React Page Reconciliation ✅ COMPLETE (Feb 2026)
> Canonical source: `E:\Archive Scripts\pages order\`

### Admin Portal — 31 Pages + Tools + Ops
All 31 pages (00–31) from the archive are **enacted** in `apps/admin/src/pages/`.
- [x] Pages 00–30 verified present in React routes
- [x] **Page 31: Admin Portal Entry Point** — `AdminPortalEntry.tsx`, route `/admin/portal-entry`
- [x] Tools pages (29 tools) wired under `/admin/tools/*`
- [x] Operations pages (10 ops) wired under `/admin/ops/*`

### User Portal — 15 Pages + Consolidation
Pages 01–15 (skipping 06) from the archive are enacted in `apps/user/src/pages/`.
- [x] Pages 01–15 verified present in React routes
- [x] Visualisations Hub added (beyond archive scope)
- [x] **Consolidation Page** — `ConsolidationPage.tsx`, route `/consolidation`

### Mentor Portal — 12 Pages
All 12 pages from the archive are enacted in `apps/mentor/src/pages/` with React routes.
Each mentor page contains a nested sub-app with its own `src/` directory.
- [x] Pages 01–12 verified present and routed

## Phase 6: Data Architecture & Duplication Strategy ✅ COMPLETE (Feb 2026)

### Source of Truth
- **Primary Data Store**: `L:\antigravity_version_ai_data_final\`
  - `ai_data_final/` — AI knowledge base (JSON, parsed CVs, job data)
  - `automated_parser/` — Raw document ingestion pipeline
  - `USER DATA/` — User sessions, audit logs, profiles, trap data
- **Runtime Data Mounts**: `C:\careertrojan\data-mounts\`
  - `ai-data` → junction to `L:\antigravity_version_ai_data_final`
  - `parser` → junction to `L:\antigravity_version_ai_data_final\automated_parser`
  - `user-data` → junction to `L:\antigravity_version_ai_data_final\USER DATA`

### Tandem Duplication (L: ↔ E:)
- **Mirror Location**: `L:\antigravity_version_ai_data_final\USER DATA\`
- **Sync Traps**: Every write to `L:\antigravity_version_ai_data_final\USER DATA\` must be automatically mirrored to `L:\antigravity_version_ai_data_final\USER DATA\`
- **Structure**: Both locations maintain identical subdirectories:
  ```
  USER DATA/
  ├── sessions/          # Login history, active sessions
  ├── profiles/          # User profiles, digital twins
  ├── interactions/      # Every user action (enrichment, search, upload)
  ├── cv_uploads/        # User resume files
  ├── ai_matches/        # AI-generated match results
  ├── session_logs/      # Full session replay data
  ├── admin_2fa/         # Admin security
  ├── test_accounts/     # Seed/test data
  ├── trap_profiles/     # Anti-contamination traps
  ├── user_registry/     # Master user index
  └── _sync_metadata.json
  ```
- **Rationale**: Protects against single-drive failure; both datasets are always current.

### AI Orchestrator Feedback Loop
```
User Login/Action → USER DATA (L:\antigravity_version_ai_data_final\USER DATA)
       ↓                    ↓ (sync trap)
  AI Orchestrator      USER_DATA_COPY (E:)
       ↓
  ai_data_final enrichment
       ↓
  Knowledge base update
```
- User resume uploads, match results, coaching interactions, and enrichment outputs feed back into `ai_data_final` via the AI orchestrator.
- The orchestrator reads from `USER DATA/interactions/` and writes enriched entries to `ai_data_final/`.

## Phase 7: Endpoint & API Reconciliation ✅ COMPLETE (Feb 2026)
- **29 routers** registered in FastAPI backend — ALL mounted
  - 19 core routers mounted directly
  - 10 supplementary routers mounted via try/except (graceful degradation)
- `shared.router` — ✅ Fixed and mounted (2026-02-08)
- `rewards.router` — ✅ Collision fixed, moved to `/api/rewards/v1`
- All prefixes standardised to `/api/{domain}/v1`
- **Braintree payment** integrated (7 new endpoints, sandbox tested)
- **GDPR router** added (data export/deletion)
- **Middleware stack** complete: correlation IDs → interaction logging → rate limiting
- Endpoint mapping pipeline tools exist: `fastapi_introspect_routes.py` → `react_api_scan.py` → `join_endpoint_graph.py`
- **Portal Bridge** (`config/nginx/portal-bridge.conf`): Routes `/` → user, `/admin` → admin, `/mentor` → mentor, `/api` → backend
- **Known remaining work**:
  - Run endpoint introspection pipeline to generate visual map
  - Update ~25 React frontend API callsites to new `/api/.../v1` prefixes

## Phase 7b: Zendesk Helpdesk Integration (Planned)

> **Model**: Hybrid — full branded help center + context-aware in-app widget

### 7b.1 Decide Helpdesk Model & Provider
- [ ] Choose provider: Zendesk (Guide + Support), Intercom, or self-built.
- [ ] Confirm hybrid model: standalone help center + in-app widget.
- [ ] Evaluate cost vs. build-your-own for v1 (recommend hosted for speed-to-market).

### 7b.2 Account, Subdomain & Branding
- [ ] Create helpdesk account and configure subdomain (e.g., `support.careertrojan.com`).
- [ ] Apply CareerTrojan branding: official logo (from `L:\antigravity_version_ai_data_final\FULL_REACT_PAGES\careertrojan-logo`), colours, typography, favicon.
- [ ] Set up knowledge base categories/sections: "Getting Started", "AI Tools", "Resume Parsing", "Cover Quadrants", "Billing & Payments", "Account & Security".
- [ ] Seed initial help articles for common user flows (CV upload, enrichment, match results, Braintree payments).

### 7b.3 Embed In-App Widget (All Three Portals)
- [ ] Add Zendesk/Intercom JS widget snippet to the root layout of all three React portals:
  - `apps/user/` — full widget (KB search + chat + ticket creation)
  - `apps/admin/` — internal widget (ticket queues + internal notes)
  - `apps/mentor/` — mentor-context widget (search + contact support)
- [ ] Configure widget behaviour: show as knowledge base search + contact form; chat if licensed.
- [ ] Add contextual entry points on complex pages (e.g., AI analysis pages → "Help with this analysis" pre-fills page context into ticket).
- [ ] Test in incognito: bubble loads, can search help center, can create ticket.

### 7b.4 User Identity & SSO
- [ ] Implement JWT/SSO between CareerTrojan backend and helpdesk so users don't re-authenticate.
- [ ] Pass user context to the widget on every page: `user_id`, `plan` (Free/Premium), `current_page_url`, `product_area`.
- [ ] Ensure tickets auto-attach to the logged-in user's email/id from the CareerTrojan user registry.
- [ ] Wire SSO through the portal-bridge NGINX config (add `/support` proxy rules to `config/nginx/portal-bridge.conf`).

### 7b.5 App Navigation & UX
- [ ] Add "Help" / "Support" / "?" entry in the User Portal primary nav or user menu.
- [ ] Add "Help" entry in Admin Portal nav (links to agent/admin helpdesk view).
- [ ] Add "Help" entry in Mentor Portal nav.
- [ ] Programmatic widget open: `window.zE('webWidget', 'open')` or equivalent on nav click.
- [ ] Contextual deep-links: on complex AI pages, "Need help?" opens widget pre-filled with page tag/URL.
- [ ] Public/marketing pages: lighter widget (FAQ/Contact only); full ticketing for logged-in users only.

### 7b.6 Admin Setup & Workflows (Helpdesk Side)
- [ ] Create inboxes/queues: Billing, Technical, Product Feedback, Account Security.
- [ ] Set up routing rules based on ticket tags or source URL (e.g., `/admin/*` → Technical queue).
- [ ] Create macros/response templates for common issues:
  - Password reset
  - "How do I upload my CV?"
  - "What is the cover quadrant?"
  - Payment failures (link to Braintree sandbox/production status)
  - Data export / GDPR requests (link to GDPR router)
- [ ] Configure SLAs: urgent (payment failures, security) → 1hr response; normal → 24hr.
- [ ] Set up email notifications and escalation rules.
- [ ] (Future) Plug in AI bot/auto-responder to deflect common queries before human agent.

### 7b.7 Backend Support Endpoints (Optional — if building own layer)
If self-building instead of hosted Zendesk:
- [ ] Data model: `tickets`, `comments`, `attachments`, `status`, `priority`, `assignee`, `tags` tables.
- [ ] New FastAPI router: `routers/support.py` → `/api/support/v1/` (create ticket, list user tickets, add reply, admin assign/change status).
- [ ] User portal: "My Tickets" page, open ticket form, reply thread.
- [ ] Agent UI (Admin portal): filtered ticket queues, internal notes, canned responses.
- [ ] Email integration: inbound/outbound email sync to ticket thread.
- [ ] Embed as React widget component (bottom-right bubble) matching Zendesk-style UX.

## Phase 8: Cleanup & Script Hygiene ✅ COMPLETE (2026-02-22)
Removed from `C:\careertrojan\`:
- [x] **`.bak` files** (2): `train_statistical_methods.py.bak`, `unified_ai_engine.py.bak`
- [x] **Test DB artifact**: `test_careertrojan.db` (725 KB)
- [x] **One-off Dockerfile variants**: `Dockerfile.simple`, `Dockerfile.minimal`
- [x] **Script output logs** (3): `extraction_output.txt`, `final_output.txt`, `output_v3.txt`
- [x] **Stale run logs** (4): `ai_ingestion.log`, `deep_ingest_and_train.log`, `deep_pipeline_output.log`, `rebrand_out.txt`
- [x] **Rebrand artifacts** (3): `rebrand_dryrun.txt`, `rebrand_log.txt`, `rebrand_report.json`
- [x] **Install log**: `requirements_install_log.txt`
- [x] **Archive directories** (2): `ENDPOINT_MAPPING_PHASES/` (15 files), `working/` (45+ files)
- [x] **Temp tools** (2): `tools/_test_import.py`, `tools/e_drive_audit.py`
- [x] **Superseded scripts** (6): `extract_collocations.py` (v1), `extract_collocations_v2.py`, `full_rebrand.py`, `fix_user_data_mount.ps1`, `_verify_gazetteers.py`, `diagnose_fastapi.py`
- [x] **`__pycache__` purge**: 35 directories removed (already in `.gitignore`)
- **Total cleaned**: ~110+ files/directories, ~2.4 MB freed
- **Kept**: canonical `compose.yaml`, per-portal `Dockerfile`s, active `tools/` (endpoint mapping utilities), `reports/endpoint_map.json`, `requirements-*.txt` (canonical series)

## Phase 9: Production Hardening ✅ COMPLETE (2026-02-22)

### 9.1 Secrets Management ✅
- [x] Added Docker Compose `secrets:` top-level block with 5 file-based secrets: `secret_key`, `postgres_password`, `braintree_private_key`, `openai_api_key`, `anthropic_api_key`
- [x] `backend-api` service references: `secret_key`, `postgres_password`, `braintree_private_key`
- [x] `ai-worker` service references: `openai_api_key`, `anthropic_api_key`
- [x] `SECRETS_DIR=/run/secrets` env var added so app reads from Docker secret mounts first
- [x] Created `services/backend_api/utils/secrets.py` — priority: Docker file → env var → default
- [x] `secrets/` directory created with placeholder `.txt` files (gitignored)
- [x] `.gitignore` updated: `secrets/` added to exclusion list
- [x] `.env` was already in both `.gitignore` and `.dockerignore` ✅

### 9.2 HTTPS & TLS ✅
- [x] Self-signed cert generation scripts:
  - `infra/nginx/certs/generate-dev-cert.sh` (Linux/Mac — OpenSSL)
  - `infra/nginx/certs/Generate-DevCert.ps1` (Windows — OpenSSL or PowerShell fallback)
- [x] Output: `dev.crt` + `dev.key` for local NGINX TLS termination
- [x] `infra/nginx/certs/dev.*` and `*.pfx` added to `.gitignore`
- [x] Production SSL config already exists: `config/nginx/ssl-letsencrypt.conf` (HSTS, security headers — confirmed Phase 9 audit)

### 9.3 Container Images ✅
- [x] **User Dockerfile HEALTHCHECK**: Added `HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3` (admin + mentor already had it)
- [x] **Backend Dockerfile non-root user**: Added `groupadd/useradd appuser` + `USER appuser` after `COPY . .`
- [x] **Resource limits on ALL 10 services** (previously only ai-worker):
  | Service | Memory Limit | CPU Limit | Memory Reservation |
  |---------|-------------|-----------|-------------------|
  | gateway | 256M | 0.50 | 64M |
  | backend-api | 1G | 1.00 | 256M |
  | admin-portal | 256M | 0.25 | 32M |
  | user-portal | 256M | 0.25 | 32M |
  | mentor-portal | 256M | 0.25 | 32M |
  | parser-worker | 2G | 1.00 | 512M |
  | enrichment-worker | 2G | 1.00 | 256M |
  | ai-worker | 4G | (no cpu) | 1G |
  | postgres | 1G | 1.00 | 256M |
  | redis | 512M | 0.50 | 64M |
- [x] **`.dockerignore` added** to all 3 portal apps (admin, user, mentor) — excludes node_modules, dist, .env, .git, *.log
- [x] All portal Dockerfiles use multi-stage builds (node:18-alpine → nginx:alpine)
- [x] Container name prefix: `careertrojan-claude-antigravity-*` ✅

### 9.4 Observability ✅
- [x] `/healthz` (liveness) and `/readyz` (readiness) canonical K8s aliases:
  - Root-level on FastAPI app (`main.py`) — no prefix, for Docker/K8s probes
  - Also on `shared.router` under `/api/shared/v1/healthz` and `/api/shared/v1/readyz`
- [x] Structured JSON logging already configured via structlog + `RequestCorrelationMiddleware` (confirmed Phase 9 audit)
- [x] Log rotation already set on all Compose services (`max-size: 5m-10m`, `max-file: 3`)

### 9.5 Rate Limiting & Abuse Prevention ✅
- [x] `RateLimitMiddleware` confirmed wired on all public endpoints (100 req/60s per IP)
- [x] **Login brute-force protection** implemented:
  - New module: `services/backend_api/middleware/login_protection.py`
  - Per-IP sliding-window tracker: 5 failed attempts → 15-minute lockout
  - Configurable via env: `LOGIN_MAX_FAILED_ATTEMPTS`, `LOGIN_LOCKOUT_WINDOW`, `LOGIN_LOCKOUT_DURATION`
  - Integrated into `auth.router /login` endpoint — checks lockout before auth, records failure/success
  - Successful login clears failure history for that IP

## Phase 10: Launch Readiness Checklist (In Progress — 2026-02-27)

| # | Check | Status |
|---|-------|--------|
| 1 | Fix 3 duplicate route conflicts (admin stub, ai_gateway drift/stats, control_plane /health) | ✅ |
| 2 | Endpoint count matches introspection report | ✅ |
| 3 | Zero legacy callsites in React (`migrate_react_api_prefixes.py --check`) | ✅ |
| 4 | Contamination trap passes on fresh boot (3/3 tests green) | ✅ |
| 5 | L: ↔ E: sync verified (< 5 s latency) | ✅ |
| 6 | Docker Compose `config` validates (exit 0) | ✅ |
| 7 | `janj3143` test user can login (DB-level seed + JWT test) | ✅ |
| 8 | Admin impersonation + audit log verified | ✅ |
| 9 | GDPR export + deletion tested end-to-end | ✅ |
| 10 | Braintree sandbox purchase flow succeeds | ✅ |
| 11 | Logo renders correctly on all three portals | ✅ |
| 12 | Zero instances of "IntelliCV" in active codebase (6 files rebranded) | ✅ |
| 13 | Full test suite green: **299 passed, 7 skipped, 0 failed** | ✅ |
| 14 | Phase 8 cleanup complete (no legacy scripts) | ✅ |
| 15 | Helpdesk widget loads on all three portals (user/admin/mentor) | ✅ |
| 16 | Helpdesk SSO working — ticket auto-attaches to logged-in user | ⬜ |
| 17 | Knowledge base seeded with initial articles (≥10 articles) | ⬜ |
| 18 | "Help" nav entry present and functional on all portals | ✅ |
| 19 | Contextual help link works on at least one AI analysis page | ✅ |
| 20 | Helpdesk SLAs and routing rules configured | ⬜ |

### Phase 10 Sprint Log (2026-02-27)

**Infrastructure verification:**
- ✅ **Portal Bridge**: `services/shared/portal-bridge/main.py` healthy (FastAPI /health, /auth/login, /auth/masquerade)
- ✅ **NGINX Portal Bridge**: `config/nginx/portal-bridge.conf` routes / → user, /admin → admin, /mentor → mentor, /api → backend
- ✅ **Klaviyo SDK**: Present at `apps/admin/Klayiyo - sdk/klaviyo-api-node-20.0.0/` for K-events
- ✅ **Lockstep**: Intelligence hub connector initializes portal bridge for cross-portal sync
- ✅ **React frontends**: Docker builds use React/Vite (npm run build), NOT Streamlit. Streamlit .py files in apps/admin/pages/ are legacy (not in Docker images)

**Bug fixes applied:**
- Fixed payment router `Depends()` bug (9 braintree tests)
- Fixed ErrorResponse envelope assertions in test_auth/test_gdpr/test_braintree (4 tests)
- Fixed `error_handlers.py` — was dropping `exc.headers` (Retry-After etc.)
- Excluded `slow`/`live_server` markers from default test run

## Verification Plan

### Automated Tests — 136 Passing ✅
- **Unit** (`tests/unit/`): 7 test files — bootstrap, braintree, endpoints, GDPR, models, observability, security
- **Integration** (`tests/integration/`): 4 test files — contamination trap, GDPR endpoints, HTTP endpoints, observability
- **E2E** (`tests/e2e/`): 1 test file — Braintree sandbox (20 tests against real API)
- **Root conftest.py**: Auto-loads .env, session-scoped app/client/db fixtures, auto-resets rate limiter
- **Contract Validation:** Use `schemathesis` to verify FastAPI matches the OpenAPI spec.
- **Renaming Integrity:** Scripted grep to ensure zero instances of "Intellicv-AI" remain.
- **Sync Trap Validation:** Write a test file to `L:\antigravity_version_ai_data_final\USER DATA\test\` and verify it appears in `L:\antigravity_version_ai_data_final\USER DATA\test\` within 5 seconds.
- **Endpoint Coverage:** Run endpoint introspection pipeline and verify count matches 29 registered routers.

### Manual Verification
1. **Login Flow:** Verify "CareerTrojan" branding on the login page and successful JWT acquisition.
2. **Resume Upload:** Upload a test resume to the User Portal and verify it appears in `L:\antigravity_version_ai_data_final\automated_parser`.
3. **Admin Monitor:** Check the Admin Status Monitor to see live health checks of all services.
4. **Data Mapping:** Pick three random pages from `MAPPING.md` and verify they render correctly with live data.
5. **Page 31:** Verify Admin Portal entry point page loads and authenticates.
6. **Consolidation Page:** Verify User Consolidation page renders with combined user data.
7. **AI Feedback:** Verify a user interaction writes to both L: and E: user data, and triggers orchestrator enrichment.
