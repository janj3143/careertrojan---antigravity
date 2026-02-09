# CareerTrojan — Workflow: Data Sync, Session Management & AI Feedback Loop

**Created**: 2026-02-08  
**Status**: Active  
**Owner**: Runtime Build Team

---

## 1. Overview

This document defines the data architecture, synchronisation strategy, session management, and AI feedback loop for the CareerTrojan runtime. It covers:

1. **Drive Connections** — How the runtime links to `ai_data_final`, the automated parser, and user data.
2. **Tandem Duplication** — The L: ↔ E: mirror strategy with automatic sync traps.
3. **Session & History Management** — What user data is captured and how.
4. **AI Orchestrator Feedback Loop** — How user interactions enrich the AI knowledge base.
5. **Operational Procedures** — Monitoring, recovery, and validation.

---

## 2. Drive Connections

### 2.1 Source of Truth

| Location | Purpose | Access Mode |
|----------|---------|-------------|
| `L:\VS ai_data final - version\ai_data_final\` | AI knowledge base (JSON, parsed CVs, jobs, skills) | Read/Write |
| `L:\VS ai_data final - version\automated_parser\` | Raw document ingestion pipeline (CVs, JDs, emails) | Read/Write |
| `L:\VS ai_data final - version\USER DATA\` | User sessions, profiles, interactions, uploads | Read/Write |

### 2.2 Runtime Mounts (`C:\careertrojan\data-mounts\`)

| Mount Name | Junction Target | Status |
|-----------|-----------------|--------|
| `ai-data` | `L:\VS ai_data final - version` | ✅ Active (junction) |
| `parser` | `L:\VS ai_data final - version\automated_parser` | ✅ Active (junction) |
| `user-data` | `L:\VS ai_data final - version\USER DATA` | 🔧 TO CREATE |
| `logs/` | Local directory | ✅ Active |
| `models/` | Local directory | ✅ Active |

### 2.3 Environment Variables (`.env`)

```env
CAREERTROJAN_DATA_ROOT=L:\VS ai_data final - version
CAREERTROJAN_AI_DATA=L:\VS ai_data final - version\ai_data_final
CAREERTROJAN_PARSER_ROOT=L:\VS ai_data final - version\automated_parser
CAREERTROJAN_USER_DATA=L:\VS ai_data final - version\USER DATA
CAREERTROJAN_USER_DATA_MIRROR=E:\CareerTrojan\USER_DATA_COPY
CAREERTROJAN_WORKING_ROOT=C:\careertrojan\working\working_copy
```

### 2.4 Backend Config Mapping

The FastAPI backend (`services/backend_api/main.py`) reads `CAREERTROJAN_DATA_ROOT` and mounts the data at:
- `/mnt/ai_data` (Docker) or direct path reference (local dev).
- The `shared_backend/main.py` validates that the data root exists and contains required subdirectories.

---

## 3. Tandem Duplication Strategy (L: ↔ E:)

### 3.1 Why Two Copies?

- **Disaster Recovery**: If either drive fails, the other has a complete copy.
- **Continuous Availability**: Both locations serve as hot mirrors — no cold backup delays.
- **AI Training Safety**: The AI orchestrator can read from either location if one is locked.

### 3.2 Mirror Locations

| Primary (L:) | Mirror (E:) |
|--------------|-------------|
| `L:\VS ai_data final - version\USER DATA\` | `E:\CareerTrojan\USER_DATA_COPY\` |

### 3.3 Directory Structure (Both Locations)

```
USER DATA / USER_DATA_COPY
├── sessions/              # Active and historical sessions
│   ├── active_sessions.json
│   └── {session_id}.json  # Per-session replay data
├── profiles/              # User profile snapshots
│   └── {user_id}.json
├── interactions/          # Every user action log
│   └── {date}_{user_id}_{action}.json
├── cv_uploads/            # User-submitted resumes
│   └── {user_id}/
├── ai_matches/            # AI-generated match results per user
│   └── {user_id}_matches.json
├── session_logs/          # Immutable audit logs
│   └── {date}_log.jsonl
├── admin_2fa/             # Admin 2FA enrollment data
├── test_accounts/         # Seeded test identities
├── trap_profiles/         # Anti-contamination trap data
├── trap_reports/          # Trap execution results
├── user_registry/         # Master user index
│   └── user_registry.json
├── quarantine/            # Flagged/suspicious data
└── _sync_metadata.json    # Last sync timestamp, file counts, hashes
```

### 3.4 Sync Trap Implementation

The sync trap is implemented as a **filesystem watcher** that runs as a background service:

```
┌──────────────────────┐       ┌──────────────────────┐
│  L:\...\USER DATA\   │       │  E:\...\USER_DATA_   │
│  (Primary Write)     │──────▶│  COPY\ (Mirror)      │
└──────────────────────┘  trap └──────────────────────┘
         │                              │
         ▼                              ▼
   AI Orchestrator              Backup Verification
```

**Trap Rules:**
1. **On File Create/Modify**: Mirror the file to E: within 5 seconds.
2. **On File Delete**: Mirror the deletion (with a 24-hour quarantine on E:).
3. **On Sync Failure**: Log to `C:\careertrojan\logs\sync_trap_errors.log` and raise an alert.
4. **Periodic Full Sync**: Every 15 minutes, run a full directory comparison.
5. **Metadata Update**: After every sync, update `_sync_metadata.json` with timestamp, file count, and checksums.

### 3.5 Sync Trap Script Location

- **Primary**: `C:\careertrojan\scripts\sync_user_data.py`
- **Service Entry**: `C:\careertrojan\services\workers\user_data_sync_worker.py`
- **Invoked by**: `scripts/Start-And-Map.ps1` at runtime startup

---

## 4. Session & History Management

### 4.1 What Gets Captured

| Event | Storage Location | Format |
|-------|-----------------|--------|
| User login | `sessions/active_sessions.json` | JSON (user_id, timestamp, IP, device) |
| Session activity | `sessions/{session_id}.json` | JSON (action log, page views, clicks) |
| Resume upload | `cv_uploads/{user_id}/` | Original file + parsed JSON |
| AI match result | `ai_matches/{user_id}_matches.json` | JSON (job matches, scores, reasoning) |
| Coaching interaction | `interactions/{date}_{user_id}_coaching.json` | JSON (questions, AI responses) |
| Enrichment output | `interactions/{date}_{user_id}_enrichment.json` | JSON (skills extracted, gaps identified) |
| Search queries | `interactions/{date}_{user_id}_search.json` | JSON (query, results, selections) |
| Mentorship activity | `interactions/{date}_{user_id}_mentor.json` | JSON (mentor, session notes, feedback) |
| Profile changes | `profiles/{user_id}.json` | JSON (versioned profile snapshots) |

### 4.2 Session Lifecycle

```
Login → Create Session → Log Every Action → On Logout/Timeout → Finalize Session
  │                                                                      │
  └─→ Write to sessions/active_sessions.json                             │
                                                                         ▼
                                                           Write final session to
                                                           session_logs/{date}_log.jsonl
                                                           (IMMUTABLE — read-only after write)
```

### 4.3 User-Created Data

Anything the user generates that could enrich the AI:
- **Resume versions** (original + each parsed iteration)
- **Skill self-assessments**
- **Job preferences and filters**
- **Mentor feedback and ratings**
- **Coaching conversation history**
- **Match acceptance/rejection decisions**

All of this is stored in `USER DATA/` and mirrored to `E:\CareerTrojan\USER_DATA_COPY\`.

---

## 5. AI Orchestrator Feedback Loop

### 5.1 Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ User Portal │────▶│ FastAPI Backend  │────▶│ USER DATA (L:)   │
└─────────────┘     └─────────────────┘     └──────────────────┘
                           │                         │
                           ▼                    Sync Trap
                    ┌──────────────┐                 │
                    │ AI Workers   │                 ▼
                    │ (enrichment, │         USER_DATA_COPY (E:)
                    │  parser,     │
                    │  inference)  │
                    └──────────────┘
                           │
                           ▼
                    ┌──────────────────┐
                    │ ai_data_final    │ ◀── Knowledge Base Updated
                    │ (L:\...\)        │
                    └──────────────────┘
```

### 5.2 Feedback Triggers

| Trigger | Worker | Action |
|---------|--------|--------|
| Resume uploaded | `parser-worker` | Parse CV → extract skills/experience → write to `ai_data_final/parsed_resumes/` |
| User logs in | `enrichment-worker` | Check profile freshness → re-score matches if stale |
| Match accepted/rejected | `ai-worker` | Update match model training data in `ai_data_final/job_matching/` |
| Coaching session completed | `enrichment-worker` | Extract new skills/interests → update user digital twin |
| Mentor feedback received | `enrichment-worker` | Incorporate feedback into mentorship matching model |
| Profile updated | `enrichment-worker` | Re-run skill extraction → update `ai_data_final/profiles/` |

### 5.3 Knowledge Base Enrichment

The AI orchestrator (`services/ai_engine/`) reads from `USER DATA/interactions/` and:
1. Aggregates anonymised user behaviour patterns.
2. Updates skill-to-job mappings in `ai_data_final/job_titles/`.
3. Refines match scoring weights in `ai_data_final/job_matching/`.
4. Generates new career pathway suggestions based on collective user journeys.
5. Updates `ai_data_final/learning_library/` with trending skill gaps.

---

## 6. Operational Procedures

### 6.1 Startup Sequence (`scripts/Start-And-Map.ps1`)

1. Validate drive connections (L:, E: accessible).
2. Verify junctions in `data-mounts/` point to correct targets.
3. Start sync trap watcher (background).
4. Run data integrity check (`shared_backend/main.py` zero-demo validation).
5. Start FastAPI backend.
6. Start workers (parser, enrichment, AI).
7. Start portals (admin, user, mentor).

### 6.2 Monitoring

- **Sync Health**: Check `_sync_metadata.json` timestamps — alert if >20 minutes stale.
- **Session Count**: Monitor `sessions/active_sessions.json` for anomalies.
- **Worker Health**: Redis queue depth — alert if backlog >100 items.
- **Data Integrity**: Run contamination trap ("Sales vs Python") every 6 hours.

### 6.3 Recovery

If E: mirror falls behind:
```powershell
# Full re-sync from L: to E:
robocopy "L:\VS ai_data final - version\USER DATA" "E:\CareerTrojan\USER_DATA_COPY" /MIR /MT:8 /LOG:C:\careertrojan\logs\resync.log
```

If L: is unavailable:
```powershell
# Emergency: promote E: mirror to primary (temporary)
$env:CAREERTROJAN_USER_DATA = "E:\CareerTrojan\USER_DATA_COPY"
```

---

## 7. Task Checklist

- [x] Create `data-mounts/user-data` junction → `L:\VS ai_data final - version\USER DATA`
- [x] Update `.env` with all data path variables
- [x] Implement `scripts/sync_user_data.py` (watchdog filesystem watcher + mirror)
- [x] Implement `services/workers/ai_orchestrator_enrichment.py` (interactions → ai_data_final)
- [x] Add sync trap startup to `scripts/Start-And-Map.ps1`
- [ ] Create `interactions/`, `profiles/` structure in USER DATA if missing
- [x] Wire enrichment worker to read from `interactions/` and write to `ai_data_final/`
- [x] Add session history capture: `services/backend_api/routers/sessions.py` (234 lines)
- [ ] Add user action logging middleware to FastAPI
- [x] Implement periodic full-sync (every 15 min) — in `sync_user_data.py`
- [x] Add sync health monitoring endpoint: `GET /api/sessions/v1/sync-status`
- [ ] Test: Write file to L: USER DATA → verify appears on E:
- [ ] Test: User login → session file created in both locations
- [ ] Test: Resume upload → parsed result in ai_data_final AND user's cv_uploads/

---

## 8. Endpoint Introspection & Tracking (keeps endpoint map current)

### 8.1 Why Track Endpoints Continuously?

As the platform evolves (new features, new visuals, new routers), the endpoint map drifts.
The introspection pipeline regenerates the map from live code — no manual maintenance.

### 8.2 Pipeline (Phase 14 → 15 → 16 → 13)

```
┌──────────────────────┐     ┌──────────────────────┐
│ FastAPI Introspection │     │ React API Scan        │
│ tools/fastapi_        │     │ tools/react_api_      │
│ introspect_routes.py  │     │ scan.py               │
└─────────┬────────────┘     └─────────┬────────────┘
          │                            │
          ▼                            ▼
    endpoints_from_          react_api_calls.json
    fastapi.json             (file, line, method, url)
          │                            │
          └──────────┬─────────────────┘
                     ▼
          ┌─────────────────────┐
          │ Joiner              │
          │ tools/join_endpoint │
          │ _graph.py           │
          └─────────┬───────────┘
                    ▼
          endpoints.json + connections.json
                    │
                    ▼
          Phase 13 Visual HTML
          (graph + table + search)
```

### 8.3 Running the Pipeline

```powershell
# Step 1: FastAPI introspection
C:\Python\python.exe tools\fastapi_introspect_routes.py ^
  --app-import "services.backend_api.main:app" --out exports

# Step 2: React API scan (run for each portal)
C:\Python\python.exe tools\react_api_scan.py ^
  --root "apps\user\src" --out exports
C:\Python\python.exe tools\react_api_scan.py ^
  --root "apps\admin\src" --out exports
C:\Python\python.exe tools\react_api_scan.py ^
  --root "apps\mentor\src" --out exports

# Step 3: Join into visual map data
C:\Python\python.exe tools\join_endpoint_graph.py ^
  --fastapi exports\endpoints_from_fastapi.json ^
  --react exports\react_api_calls.json ^
  --out exports\joined
```

### 8.4 Estimated Endpoint Counts

| Element | Approx Endpoints |
|---------|-----------------|
| Backend API (FastAPI core) | 90–160 |
| Admin Portal API surface | 45–90 |
| Mentor Portal API surface | 25–60 |
| Portal Bridge | 15–35 |
| Lockstep (orchestration) | 20–45 |
| **Total (platform-wide)** | **~160–300** |

### 8.5 Automation Target

Add introspection to CI/CD so endpoints.json + connections.json regenerate on every deploy,
keeping the visual map at `careertrojan.com/admin/mapping` always current.
