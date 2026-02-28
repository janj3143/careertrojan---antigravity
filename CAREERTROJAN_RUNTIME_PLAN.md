# CareerTrojan Runtime Build Plan

This document outlines the strategy for building the **CareerTrojan Runtime Version**, emerging from the **IntelliCV-AI** system. The goal is to create a high-performance, unified platform that links seamlessly with the `L:\Codec-Antigravity Data set` dataset.

## User Review Required

> [!IMPORTANT]
> **Global Renaming:** Every instance of "Intellicv-AI" will be rebranded to **CareerTrojan**. This includes headers, titles, logging, and metadata across all portals.
>
> **Python 3.11 Environment:** We will standardise on **Python 3.11** (located at `J:\Python311`) to ensure a self-contained runtime on the J: drive.
>
> **Consolidation:** We are moving from a "per-page" fragmented React structure to three unified portals: **Admin**, **User**, and **Mentor**.
>
> **Data & AI Linking:** The runtime will expect `ai_data_final` to be mounted at a canonical path: `L:\Codec-Antigravity Data set`. This folder will also host AI toolsets and scripts required for local model execution and parsing.
>
> **Configuration Phase 1 (Testing):** A Premium Test User (`janj3143`) will be auto-seeded.
>
> **Asset Location:** The Official Logo located at `L:\Codec-Antigravity Data set\FULL_REACT_PAGES\careertrojan-logo` MUST be used. No variations.
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

### 1. Code Structure (in `J:\Codec - runtime version\Antigravity\careertrojan`)

```
careertrojan/
├── apps/
│   ├── admin-portal/       # Unified React Admin app
│   ├── user-portal/        # Unified React User app
│   └── mentor-portal/      # Unified React Mentor app
├── services/
│   ├── backend-api/        # FastAPI Canonical API (v1)
│   ├── ai-workers/         # Resume parsing & enrichment workers
│   └── portal-bridge/      # Shared API client & auth logic
├── shared/
│   ├── contracts/          # OpenAPI & Data schemas
│   ├── registry/           # Dynamic capability registry (Flexibility Layer)
│   └── utils/              # Shared Python/JS utilities
├── infra/
│   ├── venv-py311/         # Python 3.11 Virtual Environment
│   ├── docker-compose.yml  # Local runtime orchestration
│   └── nginx/              # Reverse proxy & routing
└── scripts/                # Build and migration scripts
```

### 2. Implementation Phases

#### Phase 1: Foundation & Renaming
- [ ] Initialize `J:\Codec - runtime version\Antigravity\careertrojan` and create a **Python 3.11** virtual environment.
- [ ] Install mandatory packages from `d:\IntelliCV\requirements_lock_full.txt`.
- [ ] Run a global search-and-replace to change "Intellicv-AI" to "CareerTrojan".
- [ ] Set up the `portal-bridge` to handle unified authentication and API requests.

#### Phase 2: Flexible Mapping & Consolidation
- [ ] **Capability Registry:** Implement a dynamic registry in `shared/registry` to allow "flexing" capabilities (toggling AI models, parsers, or UI modules) without code changes.
- [ ] **Admin Portal:** Merge existing admin fragments from `ADMIN PAGES` into a single React application.
- [ ] **User Portal:** Merge `USER PAGES` and `user_portal_react` into a responsive unified portal.
- [ ] **Mentor Portal:** Consolodate `MENTOR pages` into the mentorship dashboard.

#### Phase 3: Backend & Data Linking
- [ ] Deploy the FastAPI `backend-api` with versioned routes (`/api/v1/*`).
- [ ] Wire the `L:\Codec-Antigravity Data set` path to the backend config.
- [ ] Implement the `ai-workers` to process files in the `automated_parser` directory.

#### Phase 4: Page-by-Page Testing & Validation
- [ ] map every route defined in `MAPPING.md` to a functioning React page.
- [ ] Verify API connectivity for every interaction (Resume Upload, Enrichment, etc.).

## Visual Diagram (Runtime Architecture)

```mermaid
graph TD
    subgraph "External Clients"
        Web[Browser / Mobile]
    end

    subgraph "Runtime: CareerTrojan (Drive 1)"
        Proxy[NGINX / API Gateway]
        
        subgraph "Frontend Apps"
            Admin[Admin Portal]
            User[User Portal]
            Mentor[Mentor Portal]
        end

        subgraph "Services"
            FastAPI[FastAPI Backend - Canonical v1]
            Workers[AI Workers - Parser/Enrichment]
            Bridge[Portal Bridge - Auth/Sessions]
        end
    end

    subgraph "Data Storage (Drive L)"
        Dataset[(ai_data_final)]
        ParserStore[(automated_parser)]
        Logs[(System Logs)]
    end

    subgraph "External APIs"
        Auth[Auth Provider]
        LLM[AI / LLM Services]
    end

    Web --> Proxy
    Proxy --> Admin
    Proxy --> User
    Proxy --> Mentor
    
    Admin -- "REST /api/v1" --> FastAPI
    User -- "REST /api/v1" --> FastAPI
    Mentor -- "REST /api/v1" --> FastAPI
    
    FastAPI --> Bridge
    Bridge --> Auth
    
    FastAPI -- "Jobs" --> Workers
    Workers -- "Read/Write" --> Dataset
    Workers -- "Processing" --> ParserStore
    Workers --> LLM
    
    FastAPI --> Logs
```

## Phase 5: React Page Reconciliation (Feb 2026)
> Canonical source: `E:\Archive Scripts\pages order\`

### Admin Portal — 31 Pages + Tools + Ops
All 30 original pages (00–30) from the archive are **enacted** in `apps/admin/src/pages/`.
- [x] Pages 00–30 verified present in React routes
- [ ] **Page 31: Admin Portal Entry Point** — NEW — Must be added
- [x] Tools pages (29 tools) wired under `/admin/tools/*`
- [x] Operations pages (10 ops) wired under `/admin/ops/*`

### User Portal — 15 Pages + Consolidation
Pages 01–15 (skipping 06) from the archive are enacted in `apps/user/src/pages/`.
- [x] Pages 01–15 verified present in React routes
- [x] Visualisations Hub added (beyond archive scope)
- [ ] **Consolidation Page** — NEW — Must be added (thread requirement)

### Mentor Portal — 12 Pages
All 12 pages from the archive are enacted in `apps/mentor/src/pages/` with React routes.
- [x] Pages 01–12 verified present and routed

## Phase 6: Data Architecture & Duplication Strategy (Feb 2026)

### Source of Truth
- **Primary Data Store**: `L:\Codec-Antigravity Data set\`
  - `ai_data_final/` — AI knowledge base (JSON, parsed CVs, job data)
  - `automated_parser/` — Raw document ingestion pipeline
  - `USER DATA/` — User sessions, audit logs, profiles, trap data
- **Runtime Data Mounts**: `J:\Codec - runtime version\Antigravity\careertrojan\data-mounts\`
  - `ai-data` → junction to `L:\Codec-Antigravity Data set`
  - `parser` → junction to `L:\Codec-Antigravity Data set\automated_parser`

### Tandem Duplication (L: ↔ E:)
- **Mirror Location**: `E:\CareerTrojan\USER_DATA_COPY\`
- **Sync Traps**: Every write to `L:\...\USER DATA\` must be automatically mirrored to `E:\CareerTrojan\USER_DATA_COPY\`
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
User Login/Action → USER DATA (L:)
       ↓                    ↓ (sync trap)
  AI Orchestrator      USER_DATA_COPY (E:)
       ↓
  ai_data_final enrichment
       ↓
  Knowledge base update
```
- User resume uploads, match results, coaching interactions, and enrichment outputs feed back into `ai_data_final` via the AI orchestrator.
- The orchestrator reads from `USER DATA/interactions/` and writes enriched entries to `ai_data_final/`.

## Phase 7: Endpoint & API Reconciliation (Feb 2026)
- 16 routers registered in FastAPI backend (+ `shared` router imported but **not mounted**)
- Endpoint mapping pipeline: Phase 14 (introspect) → Phase 15 (React scan) → Phase 16 (join) → Phase 13 (visual)
- **Known Issues**:
  - `shared.router` is imported but never `include_router()`'d — must be mounted
  - Mixed prefix conventions across routers — needs standardisation
  - `rewards.router` prefix overlaps with `user.router` at `/api/user/v1`
- **Portal Bridge** (`config/nginx/portal-bridge.conf`): Routes `/` → user, `/admin` → admin, `/mentor` → mentor, `/api` → backend

## Phase 8: Cleanup & Script Hygiene (Feb 2026)
Remove from `C:\careertrojan\`:
- Legacy migration scripts (e.g., `recut_migration.ps1`)
- One-off visual pack generators
- `.backup.*` files in portal directories
- Duplicate/orphaned docker-compose files in app subdirectories
- Utility scripts that have been superseded by the runtime

## Verification Plan

### Automated Tests
- **Backend Health:** Run `pytest` on `services/backend-api` to ensure all endpoints return 200 OK.
- **Contract Validation:** Use `schemathesis` to verify FastAPI matches the OpenAPI spec.
- **Renaming Integrity:** Scripted grep to ensure zero instances of "Intellicv-AI" remain in the `/apps` and `/services` directories.
- **Sync Trap Validation:** Write a test file to `L:\...\USER DATA\test\` and verify it appears in `E:\CareerTrojan\USER_DATA_COPY\test\` within 5 seconds.
- **Endpoint Coverage:** Run Phase 14 introspection and verify count matches expected routers.

### Manual Verification
1. **Login Flow:** Verify "CareerTrojan" branding on the login page and successful JWT acquisition.
2. **Resume Upload:** Upload a test resume to the User Portal and verify it appears in `L:\Codec-Antigravity Data set\automated_parser`.
3. **Admin Monitor:** Check the Admin Status Monitor to see live health checks of all services.
4. **Data Mapping:** Pick three random pages from `MAPPING.md` and verify they render correctly with live data.
5. **Page 31:** Verify Admin Portal entry point page loads and authenticates.
6. **Consolidation Page:** Verify User Consolidation page renders with combined user data.
7. **AI Feedback:** Verify a user interaction writes to both L: and E: user data, and triggers orchestrator enrichment.
