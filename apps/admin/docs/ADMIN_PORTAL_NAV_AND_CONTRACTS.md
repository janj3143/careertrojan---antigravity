# IntelliCV Admin Portal — Navigation Alignment & API Contracts

_Last updated: 2025-12-11 • Author: GitHub Copilot (GPT-5.1-Codex Preview)_

## 1. Scope & References
- Source of truth for page inventory: `pages/27_System_Connectivity_Audit.py` (Nov 14, 2025 update).
- User portal anchors (from `user_portal_final/pages`): Home, Dashboard, UMarketU Suite (10), Coaching Hub (11), Mentorship Marketplace (12), Dual Career Suite (13), Rewards (14), Resume Upload (09), Payments (05), Profile Completion (08).
- Admin mission: keep navigation parity, expose control surfaces for every consolidated user experience, and feed FastAPI/Backend services with strong contracts.

## 2. Navigation Alignment Snapshot
| Admin Page | Category | Mapped User Surface(s) | Ownership Decision |
|------------|----------|------------------------|--------------------|
| `00_Home.py` | Navigation / Ops | User `01_Home` (status banner), Dashboard quick stats | Acts as Global Ops Center. Pulls only live metrics (no psutil fallbacks) from new API contracts below.
| `03_User_Management.py` | User Ops | User `03_Registration`, `08_Profile_Complete`, `04_Dashboard` auth widgets | Split into `user_accounts.py` (auth + CRUD) and `user_activity.py` (metrics). This file becomes thin controller wiring to FastAPI.
| `05_Email_Integration.py` | Data Intake | User `09_Resume_Upload_Analysis`, `12_Mentorship_Marketplace`, `13_Dual_Career_Suite` | Remains ingestion control. Must publish feed readiness to UMarketU bridge.
| `06_Complete_Data_Parser.py` | Data Processing | User `09_Resume_Upload_Analysis` | Provides parser status + queue lengths. Expose API for resume pipeline state.
| `08_AI_Enrichment.py` | AI Services | User `09`, `10`, `14` | Supplies AI enrichment insights consumed by resume analysis and UMarketU.
| `10_Market_Intelligence_Center.py` | Intelligence | User `10` & `13` | Deliver curated market intel payloads for UMarketU + Dual Career.
| `11_Competitive_Intelligence.py` | Intelligence | User `10` & `11` | Feed competitive overlays into UMarketU + Coaching Hub.
| `20_Job_Title_AI_Integration.py` | Job Intelligence | User `10`, `11`, `13` | Owner of job-title embeddings powering UMarketU fit + Coaching persona.
| `21_Job_Title_Overlap_Cloud.py` | Analytics | User `10`, `13` | Provides overlap datasets to UMarketU & Dual Career. Hooks already sketched in `integration_hooks`.
| `24_Token_Management.py` | Commerce | User `05_Payment`, `06_Pricing`, `14_User_Rewards` | Sole authority for balances + burn. API must power payment + rewards widgets.
| `25_Intelligence_Hub.py` | Intelligence | User `04_Dashboard` summary tiles | Becomes intelligence aggregation microservice feeding dashboard.
| `27_System_Connectivity_Audit.py` | Ops Tooling | Admin only | Stays as audit/report. Inputs the alignment table above.

(Full listing attached in appendix A; only high-impact surfaces shown here.)

## 3. API / Interface Contracts (to be delivered by FastAPI backend)
_All endpoints live under `/api/admin/v1` and return JSON. Use `X-Admin-Portal` header for routing._

### 3.1 System Health & Ops (consumed by `00_Home.py`)
- `GET /api/admin/v1/system/health`
  - **Response**: `{ "uptime": float, "cpu_pct": float, "memory_pct": float, "services": {"backend_api": "up|down", "postgres": "up|degraded", ...}, "last_incident": ISO8601 }`
- `GET /api/admin/v1/system/activity`
  - Streams last 25 activities: `{ "events": [{"ts": ISO8601, "source": "parser|ai|sync", "status": "success|error", "details": str}] }`

### 3.2 User Metrics (consumed by `03_User_Management.py`, Coaching Ops)
- `GET /api/admin/v1/users/metrics`
  - `{ "total_candidates": int, "total_companies": int, "registered_users": int, "active_sessions": int, "candidate_directories": int, "last_sync": ISO8601 }`
- `GET /api/admin/v1/users/security`
  - `{ "weak_passwords": int, "duplicate_accounts": int, "suspicious_users": int, "failed_login_attempts": int, "mfa_enabled_pct": float }`
- `GET /api/admin/v1/users/subscriptions`
  - `{ "monthly_subscribers": int, "annual_subscribers": int, "free_users": int, "monthly_revenue": float, "annual_revenue": float, "conversion_rate": float }`
- `GET /api/admin/v1/users/data-sources`
  - `{ "sources": [{"name": "Candidate.csv", "status": "ready|missing", "records": int}], "last_scan": ISO8601 }`

### 3.3 Feature Bridges
- `POST /api/admin/v1/bridges/umarketu`
  - Payload: `{ "user_id": str, "job_discovery": {...}, "fit_analysis": {...}, "resume_tuning": {...}, "application_tracker": [...], "partner_mode": {...} }`
  - Tied to `integration_hooks.sync_umarketu_suite_data`.
- `POST /api/admin/v1/bridges/dual-career`
  - `{ "user_id": str, "partners": [{...}], "geographic_analysis": {...}, "market_visualization": {...} ] }`
- `POST /api/admin/v1/bridges/coaching`
  - `{ "user_id": str, "career_patterns": {...}, "recommendations": [...], "playbooks": [...] }`

### 3.4 Commerce / Tokens
- `GET /api/admin/v1/tokens/summary` (feeds payments + rewards)
  - `{ "available_tokens": int, "allocated_tokens": int, "pending_transfers": int, "burn_rate": float }`
- `POST /api/admin/v1/tokens/adjust`
  - `{ "user_id": str, "delta": int, "reason": str }`

## 4. Page Ownership Decisions
1. **Consolidate User Ops**: split `03_User_Management.py` into two thinner Streamlit pages after data layer refactor: `User_Control_Center` (CRUD, auth, alerts) vs `User_Intelligence` (metrics + charts). Both rely exclusively on FastAPI client functions.
2. **Surface Health Everywhere**: `00_Home.py` becomes the only place performing authentication gate + environment health; other pages trust the centralized session state.
3. **Bridge Stewardship**: `integration_hooks` remains the single orchestrator. Each admin AI/intelligence page publishes one canonical payload to backend endpoints listed in §3.3.
4. **Commerce Cohesion**: `24_Token_Management` manages all balances; payment & rewards pages only consume data—no more direct file/CSV touches.

## 5. Immediate Next Steps
1. Finalize endpoint signatures with backend owners; add them to FastAPI OpenAPI spec.
2. Implement shared `AdminFastAPIClient` (Action 2) and update `UserDataService` to consume `/users/*` endpoints before falling back to CSV legacy paths.
3. Update `00_Home.py` + `03_User_Management.py` to drop local psutil/CSV metrics once API is verified.

---
**Appendix A**: Full page alignment stored in `pages/27_System_Connectivity_Audit.py` (`SystemConnectivityAuditor.scan_admin_portal`).
