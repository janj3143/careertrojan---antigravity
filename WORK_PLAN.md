# CareerTrojan "Best of Breed" Master Work Plan

**Domain**: careertrojan.com  
**Objective**: Create the definitive runtime environment at `C:\careertrojan` by merging the highest quality code from `C:\AI_Platform`, `C:\AI_Platform2`, and `Q:\Antigravity Work`, linked to the `L:\VS ai_data final - version` data core. Cross-platform: Windows (primary) + Ubuntu (dedicated machine).

**Last Updated**: 2026-02-09 (Session 5 — Braintree payment gateway integration, 136 tests green)

---

## 1. Source Code Audit & Merge ("Best of Breed")
- [x] **Inventory Sources**: All legacy platforms audited.
- [x] **Runtime Consolidation (`C:\careertrojan`)**: Structure established with apps/, services/, shared/, infra/, scripts/.
- [x] **Backend**: FastAPI backend operational at `services/backend_api/`.
- [x] **Data Link**: Junctions created in `data-mounts/` → `L:\VS ai_data final - version`.

## 2. React Frontend Overhaul
- [x] **Logo Update**: CareerTrojan Horse logo applied.
- [x] **Admin Portal**: 31 pages (00–31) + 29 tools + 10 ops pages enacted.
- [x] **Admin Page 31**: `AdminPortalEntry.tsx` — system health dashboard, service grid, data architecture summary. Route: `/admin/portal-entry`.
- [x] **User Portal**: 15 pages + consolidation page enacted with React routing.
- [x] **User Consolidation Page**: `ConsolidationPage.tsx` — profile, sessions, resume, AI matches, coaching, mentorship. Route: `/consolidation`.
- [x] **Mentor Portal**: 12 pages enacted with protected React routes.
- [ ] **Visualisations Hub**: `/insights/visuals` — pinned multi-view workspace with crossfilter (Phase 05–12 components ready, to wire in).
- [ ] **Chart Integration**: D3 quadrant, D3-cloud word cloud, Cytoscape network, React Flow mind-map, radar, heatmap, Venn/UpSet, Sankey, timeline — components generated, to drop in.
- [ ] **Touch-Points Overlay Panel**: Linked selection store (Zustand) drives evidence + touch-nots panel on every chart click.

## 3. Data & Training Loop Verification
- [x] **Data Mounts**: `ai-data` junction → `L:\VS ai_data final - version`, `parser` junction → automated_parser.
- [x] **USER DATA Mount**: Junction verified at `data-mounts/user-data` → `L:\VS ai_data final - version\USER DATA`.
- [x] **Tandem Sync Trap**: `scripts/sync_user_data.py` — watchdog-based, 5-second mirror, 24-hour quarantine on delete, 15-minute full sync.
- [x] **Session History**: `services/backend_api/routers/sessions.py` — 234 lines, logging + sync-status + consolidated-user endpoints with `_write_with_mirror()`.
- [x] **AI Orchestrator Feedback**: `services/workers/ai_orchestrator_enrichment.py` — watches interactions/, routes by action type to ai_data_final enrichment.
- [ ] **Model Training**: Verify `scripts/train_models.py` uses L: dataset, saves to `trained_models/`.
- [ ] **FastAPI Middleware**: Add automatic user action logging middleware so every request creates an interaction record.

## 4. Endpoint & API Reconciliation
- [x] **17 Routers registered** in FastAPI backend (auth, user, admin, shared, mentorship, intelligence, coaching, ops, resume, blockers, credits, ai_data, jobs, taxonomy, sessions + payment/rewards/mentor optional).
- [x] **shared.router mounted**: Fixed — was imported but never `include_router()`'d.
- [x] **sessions.router created**: New router for session logging, sync status, consolidated user data.
- [x] **All prefixes standardised to `/api/{domain}/v1`**: coaching, resume, credits, ai_data, jobs, taxonomy, payment, mentor — all updated.
- [x] **rewards.router collision fixed**: Changed from `/user` (collision with user.router) to `/api/rewards/v1`.
- [ ] **Run endpoint pipeline**: `tools/fastapi_introspect_routes.py` → `tools/react_api_scan.py` → `tools/join_endpoint_graph.py` to generate visual endpoint map.
- [ ] **Update React API calls**: ~25 frontend callsites still reference old prefixes (/coaching, /resume, /jobs, /payment, etc.) — need updating to new `/api/.../v1` paths.
- [ ] **Portal Bridge**: Verify nginx config routes correctly to all portals + backend.
- [ ] **Mount unmounted routers**: 10 router files exist but are NOT mounted in main.py (admin_abuse, admin_parsing, admin_tokens, analytics, anti_gaming, insights, logs, mapping, telemetry).

## 5. Endpoint Introspection & Tracking (NEW — keeps endpoint map current)
- [x] **FastAPI Introspection Exporter**: `tools/fastapi_introspect_routes.py` — imports the app, walks `app.routes`, exports `endpoints_from_fastapi.json`.
- [x] **React API Scan Exporter**: `tools/react_api_scan.py` — regex scans React src for fetch/axios calls, exports `react_api_calls.json`.
- [x] **Joiner**: `tools/join_endpoint_graph.py` — merges FastAPI + React exports into `endpoints.json` + `connections.json` for the visual map.
- [ ] **Run the full pipeline** and verify counts (~160–300 endpoints estimated across all services).
- [ ] **Wire to Phase 13 visual HTML**: Drop joined JSON into visual HTML pack so the endpoint map + table are always current.
- [ ] **Automate**: Add introspection run to CI/CD so endpoint map regenerates on every deploy.

## 6. Visualisation Layer & Chart Catalogue (NEW)

### 6.1 Chart Types Available to Users
| Category | Charts | Library |
|----------|--------|---------|
| Peer Compare | Radar/Spider, Percentile bars, Box/Violin, Cohort scatter, Trajectory line | D3 / Recharts |
| Positioning | Magic Quadrant scatter, 2×2 quadrants, Bubble quadrant | D3 |
| Market Trends | Connected Word Cloud, Time-series trends, Chord diagram, Topic clusters | D3-cloud + D3 |
| Skill Gaps | Coverage heatmap, Gap waterfall, Skill treemap, Venn/UpSet | D3 / UpSetJS |
| Explainability | Touch-Point Network graph, Sankey flow, Timeline/swimlane | Cytoscape |
| User Directed | Mind-map editor, Career plan builder | React Flow |
| Admin Analytics | Parsing quality, Drift detection, Cohort segmentation, Calibration | Recharts |

### 6.2 Visual Registry
Registry at `src/lib/visual_registry.ts` — stable IDs, component names, required endpoints, selection types.

### 6.3 Linked Interaction Contract
Every visual emits: `{ source_visual_id, selection_type, ids[], touchpoint_ids[], filters }`.
Zustand store propagates selection to Touch-Points panel + other pinned visuals (crossfilter).

### 6.4 Backend Endpoints Required for Visuals
| Endpoint | Purpose | Status |
|----------|---------|--------|
| `POST /api/insights/v1/cohort/resolve` | Resolve peer cohort | To build |
| `GET /api/insights/v1/skills/radar` | Radar data | To build |
| `GET /api/insights/v1/quadrant` | Quadrant scatter data | To build |
| `GET /api/insights/v1/graph` | Network graph nodes/edges | To build |
| `GET /api/insights/v1/terms/cloud` | Word cloud terms + weights | To build |
| `GET /api/insights/v1/terms/cooccurrence` | Co-occurrence edges | To build |
| `GET /api/touchpoints/v1/evidence` | Evidence for touchpoint IDs | To build |
| `GET /api/touchpoints/v1/touchnots` | Missing/weak evidence | To build |
| `GET /api/mapping/v1/graph` | Live endpoint map (Phase 13) | To build |
| `GET /api/mapping/v1/endpoints` | Endpoint table data | To build |
| `GET /api/mapping/v1/registry` | Visual registry | To build |

## 7. AI Model Stack & Presentation (NEW)

### 7.1 Model Families in Use
| Layer | Models | Purpose |
|-------|--------|---------|
| Rules / Inference | Weighted scoring, constraint solvers, Lockstep checks | Reliability + explainability |
| Statistical | Regression, gradient boosting, PCA/UMAP, hypothesis tests | "Numbers you can defend" |
| Bayesian | Bayesian updating, hierarchical Bayes | Uncertainty bounds, sparse evidence |
| NLP / Embeddings | Sentence-transformers, keyword extraction, ESCO alignment | CV ↔ JD semantic matching |
| Neural / Transformers | RoBERTa/DeBERTa for ranking, sequence labelling for entity extraction | Task-specific NLP |
| Fuzzy Logic | Fuzzy inference (skill strength, recency, seniority), fuzzy clustering | Human-like scoring |
| vLLM (future) | High-throughput LLM serving | Self-hosted open-weight models |

### 7.2 Presentation Mechanisms
- **Visual overlays**: Green/amber/red inline highlights on resume + JD
- **Dashboard visuals**: Radar, heatmap, timeline, Sankey, confidence bars
- **Verbal methods**: One-line verdict, top 3 actions, evidence, confidence, trade-offs
- **Export**: PNG/SVG images, CSV/JSON data slices, "Insight Pack" PDF

### 7.3 Python Runtime Governance
- **Source of truth**: `C:\Python` (**3.11.9**) — cleaned 2026-02-08, all 3.14 / 3.11.7 remnants removed
- **Unified requirements**: `requirements.lock.txt` (pinned, all sections)
- **Venv**: `C:\Python\venvs\intellicv311\` or `.venv` in project root
- **Node**: v25.4.0 at `C:\nodej`, npm 11.7.0 — see Section 12 for full matrix
- **PATH**: `C:\Python\Scripts;C:\Python;C:\nodej;` — no ghost entries

## 8. Ubuntu Deployment (NEW)
- [x] **Cross-platform path resolver**: `services/shared/paths.py` — auto-detects win32 vs linux, reads from env vars.
- [x] **Bash launcher**: `scripts/start_and_map.sh` — Ubuntu equivalent of Start-And-Map.ps1.
- [x] **Ubuntu deployment guide**: `docs/UBUNTU_DEPLOYMENT_GUIDE.md` — mount points, symlinks, .env, systemd services, nginx, verification.
- [x] **Existing launcher pack**: `Q:\CareerTrojan_Ubuntu_LauncherPack_2026-01-15\` — bash scripts, GNOME .desktop files, careertrojan.env.
- [ ] **Test on Ubuntu**: Deploy to dedicated machine, verify all services start.

## 9. Cleanup & Script Hygiene
- [ ] **Audit scripts/**: Remove legacy scripts not part of the runtime.
- [ ] **Remove `.backup.*` files** across portal directories.
- [ ] **Remove duplicate docker-compose** files in app subdirectories.

## 10. Data Architecture
```
L:\VS ai_data final - version\       (SOURCE OF TRUTH)
├── ai_data_final/                    → C:\careertrojan\data-mounts\ai-data (junction) ✅
├── automated_parser/                 → C:\careertrojan\data-mounts\parser (junction) ✅
└── USER DATA/                        → C:\careertrojan\data-mounts\user-data (junction) ✅
    ├── sessions/         profiles/         interactions/
    ├── cv_uploads/       ai_matches/       session_logs/
    ├── admin_2fa/        test_accounts/    trap_profiles/
    ├── user_registry/    quarantine/       trap_reports/
    └── _sync_metadata.json

E:\CareerTrojan\USER_DATA_COPY\       (TANDEM MIRROR — watchdog sync)
└── [identical structure]

Ubuntu equivalent:
/mnt/careertrojan/ai_data_final/      → /opt/careertrojan/runtime/data-mounts/ai-data (symlink)
/mnt/careertrojan/user_data/          → /opt/careertrojan/runtime/data-mounts/user-data (symlink)
/mnt/careertrojan/backups/user_data/  (mirror)
```

## 11. Validation "Deep Dive"
- [ ] **Sales vs Python Trap**: Verify the contamination trap logic works.
- [ ] **Live Data Check**: Confirm no mock data is currently in use.
- [ ] **Sync Trap Test**: Write test file to L: USER DATA, verify mirror on E:.
- [x] **Page 31 & Consolidation Page**: Created and routed.
- [ ] **Endpoint Count**: Run `tools/fastapi_introspect_routes.py`, match against expected router count (~17 mounted + ~10 unmounted).
- [ ] **React API Call Audit**: Run `tools/react_api_scan.py`, verify all calls use new `/api/.../v1` prefixes.

---

## 12. Runtime Environment Matrix (NEW — 2026-02-08)

> **Principle**: Every runtime dependency has ONE authoritative install on C:, ONE mirror on E: for disaster recovery. No ghost versions, no duplicates.

| Component | Authoritative Path (C:) | Version | E: Mirror | Status |
|-----------|------------------------|---------|-----------|--------|
| Python | `C:\Python\python.exe` | **3.11.9** | `E:\Python\` (3.11.7 — needs update) | ✅ Cleaned |
| pip | `C:\Python\Scripts\pip.exe` | 24.0 | — | ✅ Bootstrapped |
| Node.js | `C:\nodej\node.exe` | v25.4.0 | `E:\nodej\` | ✅ |
| npm | `C:\nodej\npm` | 11.7.0 | — | ✅ |
| Docker Desktop | `C:\Program Files\Docker\` | 29.1.3 | `E:\Docker\` | ✅ Running |
| Docker Compose | (bundled) | v5.0.1 | — | ✅ |
| Git | `C:\Github Desktop\Git\` | 2.52.0 | — | ✅ |
| Redis | `C:\Redis\redis-cli.exe` | 3.0.504 | `E:\Redis\` | ✅ |
| PostgreSQL | `C:\Posgres\` | (psql not on PATH) | `E:\Posgres\` | ⚠️ Add `bin\` to PATH |
| Java | System | 1.8.0_481 | — | ✅ (Tesseract dep) |
| Tesseract-OCR | `C:\Tesseract-OCR\` | — | `E:\Tesseract-OCR\` | ✅ |

### 12.1 PATH Hygiene (Machine PATH — authoritative order)
```
C:\Python\Scripts\
C:\Python\
C:\nodej\
C:\Github Desktop\Git\cmd\
C:\Redis\
C:\Posgres\bin\                    ← TO ADD
C:\Program Files\Docker\Docker\resources\bin\
C:\Tesseract-OCR\
```

### 12.2 E: Drive Sync Checklist
- [ ] **Update E:\Python** to 3.11.9 (currently 3.11.7)
- [ ] **Verify E:\CareerTrojan** mirror is current with C:\careertrojan runtime code
- [ ] **Add Postgres bin to PATH**: `C:\Posgres\bin\` needs adding to Machine PATH
- [ ] **Scheduled robocopy**: Script to mirror C:\careertrojan → E:\CareerTrojan nightly

---

## 13. AI Data Enrichment Loop — "Robo-Learn" (NEW — 2026-02-08)

> **Core Philosophy**: Every user interaction is a training signal. When a user registers, uploads a CV, runs a coaching session, gets AI matches, or even browses — that data automatically enriches the AI models. This is a zero-admin, always-on feedback loop that makes the platform smarter with every user.

### 13.1 Data Capture Points
| User Action | Data Captured | Storage Path | AI Enrichment Target |
|-------------|---------------|--------------|---------------------|
| Register | Demographics, career stage, preferences | `user_data/user_registry/` | Cohort models, cold-start profiles |
| Upload CV | Raw PDF/DOCX + parsed entities | `user_data/cv_uploads/` + `ai_data_final/parsed/` | NLP embeddings, entity extraction training |
| Run AI Match | Match scores, job selections, rejections | `user_data/ai_matches/` | Ranking model feedback (implicit labels) |
| Coaching Session | Transcripts, goals, progress notes | `user_data/sessions/` | Coaching dialogue model fine-tuning |
| Mentor Interaction | Session logs, ratings, feedback | `user_data/session_logs/` | Mentor-quality scoring, recommendation |
| Browse/Click | Page views, dwell times, click paths | `user_data/interactions/` | UX optimisation, content ranking |
| Payment/Reward | Transaction history, credit usage | `user_data/transactions/` | Lifetime value prediction, churn risk |
| Admin Flags | Abuse reports, trap triggers | `user_data/trap_reports/` | Anti-gaming model training |

### 13.2 Enrichment Pipeline Architecture
```
[User Action] → [FastAPI Middleware Logger] → [interactions/ folder]
                                                      ↓
                              [ai_orchestrator_enrichment.py] (watchdog)
                                                      ↓
                          ┌───────────────────────────────────────┐
                          │  Route by action_type:                │
                          │  • cv_upload  → embedding pipeline    │
                          │  • match_feedback → ranking retrain   │
                          │  • session_log → coaching model FT    │
                          │  • browse_click → UX analytics        │
                          │  • payment → LTV model update         │
                          └───────────────────────────────────────┘
                                                      ↓
                              [ai_data_final/ enriched datasets]
                                                      ↓
                              [Scheduled model retrain (nightly)]
                                                      ↓
                              [trained_models/ updated weights]
                                                      ↓
                              [FastAPI hot-reload model endpoint]
```

### 13.3 Implementation TODO
- [x] **ai_orchestrator_enrichment.py**: Watchdog-based router exists at `services/workers/`
- [ ] **FastAPI Middleware Logger**: Add `InteractionLoggerMiddleware` to `main.py` — captures every request with user_id, endpoint, timestamp, response_time, payload_hash
- [ ] **Embedding Pipeline Worker**: `services/workers/embedding_pipeline.py` — on new CV upload, generate sentence-transformer embeddings, store in `ai_data_final/embeddings/`
- [ ] **Ranking Feedback Ingester**: `services/workers/ranking_feedback.py` — on match accept/reject, update implicit labels for gradient boosting ranker
- [ ] **Nightly Retrain Scheduler**: `scripts/nightly_retrain.py` — cron/task-scheduler job that reads enriched data, retrains models, saves to `trained_models/`
- [ ] **Model Hot-Reload**: FastAPI endpoint `/api/ai_data/v1/model/reload` — admin-only, reloads model weights without restart
- [ ] **Data Volume Monitoring**: Dashboard widget showing enrichment pipeline throughput, data growth rate, model freshness
- [ ] **Privacy Guardrails**: PII scrubbing before enrichment, GDPR-compliant data retention policy, user opt-out mechanism

### 13.4 Cost & Scale Considerations
- **Storage**: ~50MB per 1K users (CV uploads dominate). At 100K users → ~5GB active data
- **Compute**: Nightly retrain on commodity GPU — ~30 min for embedding + ranking refresh
- **Cloud Projection**: Azure ML or self-hosted vLLM for inference. Estimated ~£200/mo at 10K MAU, scaling to ~£2K/mo at 100K MAU
- **ROI**: Each enrichment cycle improves match accuracy → higher user retention → larger user base → more data → better AI (virtuous cycle)

---

## 14. Mobile-Friendly Strategy (NEW — 2026-02-08)

> **Priority**: Medium (not blocking current build, but must be in the architecture from day one so we don't retrofit later).

### 14.1 Approach: Responsive-First Web App (PWA)
| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Native Apps (iOS/Android) | Best UX, push notifications | 2× codebase, App Store approval | ❌ Not now |
| React Native | Shared codebase, native feel | New toolchain, can't reuse React web | ❌ Not now |
| **Progressive Web App (PWA)** | **Reuses existing React**, installable, offline, push | Limited hardware access | **✅ Phase 1** |
| Native Apps (later) | Best for power users | Build after PMF proven | ✅ Phase 2 (future) |

### 14.2 PWA Implementation Checklist
- [ ] **Responsive CSS**: All 3 portals (admin/user/mentor) use Tailwind — add breakpoint audit (`sm:`, `md:`, `lg:`)
- [ ] **Mobile Navigation**: Hamburger menu + bottom tab bar for user portal on `< 768px`
- [ ] **Service Worker**: `public/sw.js` — cache-first strategy for static assets, network-first for API calls
- [ ] **Web App Manifest**: `public/manifest.json` — name, icons, theme_color, start_url, display: standalone
- [ ] **Touch Interactions**: Swipe gestures for card-based views (job matches, coaching cards)
- [ ] **Viewport Meta**: Verify `<meta name="viewport" content="width=device-width, initial-scale=1">` in all portal index.html
- [ ] **CV Upload (Mobile)**: Camera capture option for uploading CVs via phone photo → OCR pipeline
- [ ] **Push Notifications**: Web Push API for match alerts, coaching reminders, mentor messages
- [ ] **Lighthouse Audit**: Target scores — Performance > 90, Accessibility > 90, PWA > 90

### 14.3 Mobile-Specific UI Components
| Component | Desktop | Mobile |
|-----------|---------|--------|
| Navigation | Sidebar | Bottom tab bar + hamburger |
| Dashboard cards | 3-column grid | Single column stack |
| Charts/Visuals | Full interactive | Simplified + tap-to-expand |
| CV Upload | Drag & drop | Camera capture + file picker |
| Coaching chat | Side panel | Full-screen modal |
| Data tables | Full table | Card list with expand-on-tap |

---

## 15. Backup & Disaster Recovery Strategy (NEW — 2026-02-08)

### 15.1 Backup Tiers
| Tier | What | Where | Frequency | Retention |
|------|------|-------|-----------|-----------|
| **Tier 1 — Live Mirror** | User data (L: → E:) | `E:\CareerTrojan\USER_DATA_COPY\` | Real-time (watchdog) | Continuous |
| **Tier 2 — Runtime Code** | `C:\careertrojan\` | `E:\CareerTrojan\` + GitHub | Nightly robocopy + git push | 30 days / all commits |
| **Tier 3 — Database** | PostgreSQL dumps | `E:\Backups\postgres\` | Nightly pg_dump | 7 daily, 4 weekly |
| **Tier 4 — Model Weights** | `trained_models/` | `E:\Backups\models\` | Post-retrain | Last 5 versions |
| **Tier 5 — Full Snapshot** | Entire C:\careertrojan + data | External / cloud blob | Weekly | 4 weekly |

### 15.2 Implementation TODO
- [ ] **Nightly robocopy script**: `scripts/backup_runtime.ps1` — mirrors C:\careertrojan → E:\CareerTrojan (exclude node_modules, __pycache__, .venv)
- [ ] **pg_dump script**: `scripts/backup_postgres.ps1` — dumps all databases, compresses, rotates
- [ ] **Model versioning**: Save `trained_models/` with timestamp + hash, keep last 5
- [ ] **Cloud backup (future)**: Azure Blob Storage or S3 for off-site Tier 5
- [ ] **Restore playbook**: `docs/DISASTER_RECOVERY.md` — step-by-step to rebuild from E: or cloud
- [ ] **Backup monitoring**: Admin dashboard widget — last backup time, size, success/fail status

---

## 16. SSL / TLS & Security (NEW — 2026-02-08)

### 16.1 Certificate Strategy
| Environment | Domain | Certificate | Provider |
|-------------|--------|-------------|----------|
| **Local Dev** | `localhost` / `careertrojan.local` | Self-signed (mkcert) | mkcert |
| **Staging** | `staging.careertrojan.com` | Let's Encrypt (auto-renew) | Certbot |
| **Production** | `careertrojan.com` + `*.careertrojan.com` | Let's Encrypt wildcard | Certbot + DNS-01 |
| **API Gateway** | `api.careertrojan.com` | Same wildcard cert | nginx / Caddy |

### 16.2 Security Checklist
- [ ] **mkcert**: Install locally, generate certs for `localhost`, `careertrojan.local`, `127.0.0.1`
- [ ] **nginx TLS config**: `infra/nginx/ssl.conf` — TLS 1.2+, HSTS, OCSP stapling
- [ ] **Certbot setup**: Document in `docs/SSL_SETUP.md` — DNS-01 challenge for wildcard
- [ ] **CORS policy**: Lock down allowed origins to `careertrojan.com`, `localhost:5173` (dev)
- [ ] **API Key rotation**: Admin endpoint to rotate API keys, secrets stored in `.env` (never committed)
- [ ] **Rate limiting**: FastAPI middleware — 100 req/min per user, 1000 req/min per IP
- [ ] **OWASP Top 10 audit**: XSS, CSRF, SQL injection, auth bypass — verify all mitigated
- [ ] **Docker secrets**: Move passwords out of compose.yaml into Docker secrets or `.env`
- [ ] **JWT token policy**: Access token 15 min, refresh token 7 days, rotate on use

---

## 17. GitHub & Version Control Strategy (NEW — 2026-02-08)

### 17.1 Repository Structure
| Repo | Contents | Visibility |
|------|----------|------------|
| `careertrojan/runtime` | `C:\careertrojan\` — all services, apps, config, scripts | Private |
| `careertrojan/infra` | Docker configs, nginx, deployment scripts, IaC | Private |
| `careertrojan/docs` | Documentation, API specs, architecture diagrams | Private (initially) |
| `careertrojan/ai-models` | Model definitions, training scripts (NOT weights) | Private |

### 17.2 Branching Strategy
```
main              ← production-ready, tagged releases
├── develop       ← integration branch, CI runs here
│   ├── feature/* ← new features (e.g., feature/mobile-pwa)
│   ├── fix/*     ← bug fixes
│   └── refactor/*← cleanup, restructuring
└── release/*     ← staging candidates
```

### 17.3 Git Workflow TODO
- [ ] **Create GitHub repo**: `careertrojan/runtime` (private)
- [ ] **Initial commit**: Push current `C:\careertrojan\` (excluding data-mounts, node_modules, __pycache__, trained_models, user_data)
- [ ] **.gitignore**: Comprehensive ignore file — data-mounts/, trained_models/, user_data/, node_modules/, __pycache__/, *.pyc, .env, *.log
- [ ] **Branch protection**: Require PR reviews on `main`, CI checks must pass
- [ ] **GitHub Actions CI**: Lint (ruff/eslint) → Type check (mypy/tsc) → Unit tests → Build check
- [ ] **Pre-commit hooks**: ruff format, eslint --fix, secret detection (gitleaks)
- [ ] **Tag first release**: `v0.1.0-alpha` — current state snapshot

---

## 18. API Strategy & Gateway (NEW — 2026-02-08)

### 18.1 API Design Principles
- **Versioned**: All endpoints use `/api/{domain}/v1/` prefix (already standardised)
- **RESTful**: Resources as nouns, HTTP verbs for actions, proper status codes
- **Documented**: Auto-generated OpenAPI spec at `/docs` (FastAPI built-in)
- **Rate-limited**: Per-user and per-IP limits (see Section 16)
- **Authenticated**: JWT bearer tokens on all non-public endpoints

### 18.2 API Gateway Architecture
```
[Client (Browser/Mobile/Third-party)]
              ↓
[nginx / Caddy — TLS termination, rate limiting]
              ↓
         ┌────────────────────────────────┐
         │  /api/auth/v1/*    → auth.router      │
         │  /api/user/v1/*    → user.router      │
         │  /api/admin/v1/*   → admin.router     │
         │  /api/coaching/v1/*→ coaching.router   │
         │  /api/resume/v1/*  → resume.router    │
         │  /api/jobs/v1/*    → jobs.router      │
         │  /api/insights/v1/*→ insights.router  │
         │  /api/ai_data/v1/* → ai_data.router   │
         │  /api/mapping/v1/* → mapping.router   │
         │  /api/mentor/v1/*  → mentor.router    │
         │  /api/analytics/v1/*→analytics.router │
         │  /api/telemetry/v1/*→telemetry.router │
         └────────────────────────────────┘
              ↓
[FastAPI — Python 3.11.9 — Uvicorn workers]
              ↓
[PostgreSQL / Redis / ai_data_final/]
```

### 18.3 API Lifecycle TODO
- [ ] **Mount all 10 unmounted routers** in `main.py` (admin_abuse, admin_parsing, admin_tokens, analytics, anti_gaming, insights, logs, mapping, telemetry)
- [ ] **OpenAPI spec export**: `scripts/export_openapi.py` — saves `docs/openapi.json` for client generation
- [ ] **API client SDK**: Auto-generate TypeScript client from OpenAPI spec for React frontends
- [ ] **API versioning strategy**: v1 is current; v2 only when breaking changes, old version deprecated with 6-month sunset
- [ ] **Webhook support (future)**: Allow external systems to subscribe to events (new match, coaching complete)
- [ ] **Third-party API access (future)**: OAuth2 client credentials for partner integrations
- [ ] **API analytics**: Track endpoint usage, latency, error rates — feed into admin dashboard

---

## 18.5 Payment Gateway — Braintree Integration (NEW — Session 5)

### Status: ✅ COMPLETE — Sandbox Configured, 27 Endpoint/Service Tests Passing

### Architecture
- **Gateway**: Braintree (PayPal) — sandbox environment
- **Service Layer**: `services/backend_api/services/braintree_service.py` (~300 lines)
  - Gateway singleton with lazy init from env vars
  - Customer management (find-or-create by email)
  - Payment method CRUD (card, PayPal, vault)
  - Transactions: sale / void / refund / find
  - Subscriptions: create / cancel / find
  - Plan mapping: `BRAINTREE_PLAN_MAP` — maps internal tiers (monthly/annual/enterprise) to Braintree plan IDs
- **Router Endpoints**: `services/backend_api/routers/payment.py` — 7 new endpoints on top of existing plan/subscription flow
  | Endpoint | Method | Description |
  |----------|--------|-------------|
  | `/api/payment/v1/client-token` | GET | Generates Braintree Drop-in UI client token |
  | `/api/payment/v1/methods` | POST | Vault a payment method (card/PayPal nonce) |
  | `/api/payment/v1/methods` | GET | List saved payment methods for user |
  | `/api/payment/v1/methods/{token}` | DELETE | Remove a vaulted payment method |
  | `/api/payment/v1/transactions/{id}` | GET | Look up transaction details |
  | `/api/payment/v1/refund/{id}` | POST | Refund (full or partial amount) |
  | `/api/payment/v1/gateway-info` | GET | Gateway config status (no secrets) |
- **Graceful Degradation**: All Braintree-specific endpoints return 503 when gateway not configured; `/process` falls back to stub

### Environment Variables (`.env`)
```
BRAINTREE_ENVIRONMENT=sandbox
BRAINTREE_MERCHANT_ID=xtwfsxyf55m7rgn3
BRAINTREE_PUBLIC_KEY=ch2crmy3fbgyg63p
BRAINTREE_PRIVATE_KEY=<in .env, not committed>
```

### Test Coverage
- **Unit Tests** (`tests/unit/test_braintree.py` — 27 tests): Config, endpoints, mocked service
- **E2E Sandbox Tests** (`tests/e2e/test_braintree_sandbox.py` — 20 tests): Real Braintree API calls
  - Client token generation (anonymous + customer)
  - Customer create / find
  - Sales: Visa, Mastercard, nonce → $1–$149.99
  - Declined nonce handling
  - Transaction find + void
  - Vault card → list → delete → pay with vaulted token
  - Full flow: nonce → sale → find → void
  - Vault flow: create customer → vault card → pay → find → void → cleanup
  - HTTP endpoint e2e: /client-token, /process, /process+promo, declined, /gateway-info
- Rate limiter auto-reset in root `conftest.py` (autouse fixture + .env auto-loaded via dotenv)

### Frontend Components (React)
- `apps/user/src/components/payment/BraintreeDropIn.tsx` — Drop-in UI v1.46.0 (CDN loaded)
  - Fetches client token from `/api/payment/v1/client-token`
  - Renders Braintree Drop-in (cards, PayPal, Apple Pay)
  - Returns payment method nonce on submission
- `apps/user/src/components/payment/SavedPaymentMethods.tsx` — Vaulted methods list/select/delete
- `apps/user/src/pages/PaymentPage.tsx` — Full checkout page
  - Plan cards with pricing and features
  - Sandbox mode indicator with test card info
  - Promo code input (LAUNCH20, CAREER10)
  - Saved method selection OR Drop-in for new payment
  - Submit → backend processes → success/error feedback

### Stripe Status
- **Fully removed** from careertrojan codebase — zero references to Stripe
- Braintree is the sole payment gateway (sandbox + production ready)
- Stripe API key still in `.env` as reference but unused by any code

### Braintree vs Stripe Comparison
| Feature | Braintree | Stripe |
|---------|-----------|--------|
| Transaction fee | 2.89% + $0.29 | 2.9% + $0.30 |
| Monthly fee | $0 | $0 |
| Go-live cost | **$0** (apply via PayPal) | $0 |
| PayPal built-in | ✅ Native | ❌ Separate integration |
| Venmo | ✅ 3.49% + $0.49 | ❌ |
| Apple Pay / Google Pay | ✅ Drop-in UI | ✅ Stripe Elements |
| Card vaulting | ✅ | ✅ |
| Recurring billing | ✅ | ✅ |
| PCI compliance | Drop-in handles all card data | Elements handles all card data |
| **Verdict** | **Optimal** — lower per-txn fee, PayPal+Venmo native | Good but no PayPal/Venmo |

### Go-Live Steps (Zero Upfront Cost)
1. [x] ~~Sandbox integration complete~~ ✅
2. [x] ~~E2E tested against real sandbox API~~ ✅ (20/20 passing)
3. [ ] **Apply for production account** → [braintreepayments.com/contact/sales](https://www.braintreepayments.com/contact/sales)
   - No monthly fee, no setup fee — only pay per-transaction (2.89% + $0.29)
4. [ ] **Create API user** in production control panel (dedicated user, not personal)
5. [ ] **Get production credentials** (merchant_id, public_key, private_key)
6. [ ] **Recreate plans** in production (monthly_pro, annual_pro, elite_pro) — sandbox plans don't transfer
7. [ ] **Update `.env.production`**:
   ```
   BRAINTREE_ENVIRONMENT=production
   BRAINTREE_MERCHANT_ID=<production_merchant_id>
   BRAINTREE_PUBLIC_KEY=<production_public_key>
   BRAINTREE_PRIVATE_KEY=<production_private_key>
   ```
8. [ ] **Test with real card** — run 2-3 low-value transactions ($0.50, $1.00), verify settlement in bank
9. [ ] **Configure production webhooks** for transaction events (optional but recommended)
10. [ ] **Add CSP headers** for `js.braintreegateway.com` in production nginx/reverse proxy
11. [ ] **PCI SAQ-A** — Braintree Drop-in UI handles all card data, so SAQ-A (simplest) applies

### Production Checklist
- [ ] Create Braintree production merchant account (free)
- [ ] Set up production plan IDs and update `BRAINTREE_PLAN_MAP`
- [ ] Configure production webhook URL for transaction events
- [ ] Switch `BRAINTREE_ENVIRONMENT=production` in deployment env
- [ ] Add Braintree CSP headers for Drop-in UI script
- [ ] ~~Wire Drop-in UI component into React payment page~~ ✅ (done)
- [ ] Add transaction receipt email via Resend/SendGrid
- [ ] PCI SAQ-A compliance review

---

## 19. Next Actions — Priority Queue (Updated 2026-02-08)

### Phase A — Immediate (This Session)
1. ~~Clean Python runtime to single 3.11.9~~ ✅
2. ~~Remove ghost PATH entries (Python314)~~ ✅
3. ~~Verify pip, Node, Docker, Git working~~ ✅
4. [ ] Update E:\Python mirror to 3.11.9
5. [ ] Add `C:\Posgres\bin\` to Machine PATH
6. [ ] Configure VS Code Python interpreter → `C:\Python\python.exe`

### Phase B — Next (Build Continuation)
7. [ ] Mount all 10 unmounted routers in `main.py`
8. [ ] Run endpoint introspection pipeline (`tools/`)
9. [ ] Update ~25 React API callsites to new `/api/.../v1` prefixes
10. [ ] Add `InteractionLoggerMiddleware` to FastAPI (Section 13.3)
11. [ ] Create `.gitignore` + push initial commit to GitHub

### Phase C — Near-Term
12. [ ] Wire visualisation components into `/insights/visuals`
13. [ ] Build insights/touchpoints endpoints (Section 6.4 table)
14. [ ] PWA manifest + service worker (Section 14.2)
15. [ ] Responsive breakpoint audit for mobile (Section 14.2)
16. [ ] nightly_retrain.py + backup scripts (Sections 13.3, 15.2)

### Phase D — Pre-Launch
17. [ ] SSL/TLS setup with mkcert (local) + Certbot (staging)
18. [ ] GitHub Actions CI pipeline
19. [ ] OWASP security audit
20. [ ] Lighthouse PWA audit (target > 90)
21. [ ] Ubuntu deployment test
22. [ ] Full validation deep-dive (Section 11)
