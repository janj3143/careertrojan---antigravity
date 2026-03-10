# Service Dependency Map

Generated: 2026-03-10T11:24:12Z

## Core Runtime Flow
- routers -> services/backend_api/services -> db/models
- routers -> services/ai_engine (selected routes)
- middleware stack in services/backend_api/main.py wraps all API calls

## Key Hubs
- services/backend_api/main.py (router composition)
- services/backend_api/routers/* (route layer)
- services/backend_api/services/* (business logic)
- services/ai_engine/* (training/analysis engines)

## Discovery Notes
- This report is structural; call-graph expansion should be added in phase-2 discovery.
