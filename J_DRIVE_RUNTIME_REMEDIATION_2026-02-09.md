# J-Drive Runtime Remediation (2026-02-09)

## Objective
Enforce J-drive-first runtime behavior for:
`J:\Codec - runtime version\Antigravity\careertrojan`

No new code/runtime dependencies were placed in `C:\`.

## Changes Made
1. Removed hardcoded `C:\careertrojan` / `C:\Python` runtime assumptions from launch scripts.
2. Added J-drive setup automation script:
   - `scripts/setup_j_runtime.ps1`
   - Creates `.venv-j`, installs deps, installs Node to `J:\nodej`, generates `.env.j-drive.generated`.
3. Updated runtime scripts to resolve project root from script location (`$PSScriptRoot`) rather than fixed drive paths:
   - `scripts/run_backend.ps1`
   - `scripts/bootstrap.ps1`
   - `scripts/Start-And-Map.ps1`
   - `scripts/build_frontends.ps1`
   - `scripts/setup_mounts.ps1`
4. Removed remaining `C:\...` hardcoded paths from script utilities:
   - `scripts/smoke_test.py`
   - `scripts/verify_endpoint_count_live.py`
   - `scripts/sync_user_data.py`
5. Removed remaining `C:\...` hardcoded paths from runtime-support code:
   - `services/ai_engine/config.py`
   - `services/workers/ai_orchestrator_enrichment.py`
   - `services/shared/portal-bridge/run_bridge.ps1`
   - `services/shared/registry/test_registry.py`
   - `tools/e_drive_audit.py`
   - `apps/admin/generate_pages.ps1`
   - `apps/mentor/generate_pages.ps1`
6. Added J-drive operation guide:
   - `docs/J_DRIVE_RUNTIME_SETUP.md`
7. Updated `.env.example` to J/L canonical runtime variables (`CAREERTROJAN_*`).
8. Added real E2E smoke coverage so the test ladder no longer reports zero E2E tests:
   - `tests/e2e/test_runtime_smoke.py`
9. Added single-command full harness wrapper:
   - `scripts/full_harness.ps1`
   - Produces `logs/test_results/full_harness_summary.json` and `.md`.

## J-Drive Tooling Status
1. Python runtime: `J:\Python311\python.exe` (in use)
2. Node runtime: `J:\nodej\node.exe` installed (v25.4.0)
3. NPM runtime: `J:\nodej\npm.cmd` installed (11.7.0)
4. Docker CLI runtime: `J:\docker-cli\docker.exe` installed (v29.2.1)
5. Project venv: `J:\Codec - runtime version\Antigravity\careertrojan\.venv-j`

## Validation
1. J-drive setup script execution:
   - `scripts/setup_j_runtime.ps1` executed successfully
2. Python script compile checks:
   - `python -m py_compile services/ai_engine/config.py services/workers/ai_orchestrator_enrichment.py services/shared/registry/test_registry.py tools/e_drive_audit.py scripts/smoke_test.py scripts/verify_endpoint_count_live.py scripts/sync_user_data.py`
3. Tests (J-drive Python):
   - `J:\Python311\python.exe -m pytest -q tests/unit/test_paths_resolution.py`
   - `J:\Python311\python.exe -m pytest -q tests/unit/test_app_bootstrap.py::TestAppBootstrap::test_app_imports_cleanly`
4. Grep audit (`*.md`/`*.txt` excluded) shows no remaining hardcoded `C:\careertrojan` or `C:\Python` references in executable code/config files.
5. Full harness now includes non-zero E2E pass results:
   - `.\scripts\agent_manager.ps1 -Mode all`
   - Runtime review: `23/23 (100%)`
   - Unit: `100%`
   - Integration: `100%`
   - E2E: `100%`

## Notes
Docker engine on Windows remains system-level software, but Docker CLI binaries are now present on `J:\docker-cli` and can be called directly from J-drive paths.

## Post-Review Upgrade Pass (2026-02-10)
Additional code upgrades were applied after full harness review to remove residual hardcoded legacy paths and standardize env-driven runtime resolution:

1. Launchers updated to J-drive/runtime-aware path resolution:
   - `apps/admin/launch_admin_portal.ps1`
   - `apps/user/CLEAN_PORTAL_LAUNCHER.ps1`
2. Admin shared config updated to `CAREERTROJAN_*` defaults:
   - `apps/admin/shared/env.py`
3. Universal ingestors updated to env/project-root CLI defaults (no fixed legacy path):
   - `services/backend_api/services/universal_data_ingestor.py`
   - `apps/admin/services/universal_data_ingestor.py`
4. Admin core modules updated to project/env-driven defaults for base/sandbox/root paths:
   - `apps/admin/modules/core/sandbox_admin_portal_creator.py`
   - `apps/admin/modules/core/json_chunking_manager.py`
   - `apps/admin/modules/core/data_organization_manager.py`
   - `apps/admin/modules/core/comprehensive_data_analysis.py`
   - `apps/admin/modules/core/ai_data_integration.py`
5. Removed stale hardcoded example cwd path from admin service monitor comments:
   - `apps/admin/pages/01_Service_Status_Monitor.py`

Validation:
1. Compile check passed for all upgraded Python modules.
2. `rg "C:\\\\"` on executable code files (`*.py`, `*.ps1`, `*.ts`, `*.tsx`) returned no matches.
3. Full harness passed:
   - `.\scripts\full_harness.ps1`
   - Runtime review: `23/23 (100%)`
   - Unit: `100%`
   - Integration: `100%`
   - E2E: `100%`

## Script Cleanup Pass (2026-02-10)
Removed non-runtime and legacy scripts from the J-runtime `scripts/` directory to keep only setup/startup/sync/test harness operations:

Removed:
1. `scripts/embedding_pipeline.py`
2. `scripts/ingest_ai_data.py`
3. `scripts/ingest_data.ps1`
4. `scripts/nightly_retrain.py`
5. `scripts/ranking_feedback.py`
6. `scripts/run_incremental_ingestion.py`
7. `scripts/seed_db.py`
8. `scripts/setup_ubuntu.sh`
9. `scripts/smart_verify.py`
10. `scripts/smoke_test_platform.py`
11. `scripts/start_and_map.sh`
12. `scripts/test_admin_security.py`
13. `scripts/validate_ai_integrity.ps1`
14. `scripts/verify_data_access.py`

Post-cleanup validation:
1. Full harness executed successfully via `.\scripts\full_harness.ps1`.
2. Runtime review: `23/23 (100%)`.
3. Unit, integration, and E2E all at `100%`.

## Second-Pass Cleanup (2026-02-10)
Extended cleanup of non-runtime artifacts in J-runtime:

Removed generated/build artifacts:
1. `apps/admin/node_modules/`
2. `apps/mentor/node_modules/`
3. `apps/user/node_modules/`
4. `apps/user/dist/`
5. Source-tree `__pycache__/` folders (outside `.venv-j` and embedded infra Python envs)
6. `.pytest_cache/`
7. `test_careertrojan.db`
8. `apps/user/pages/full pages list.zip`

Removed duplicate non-runtime docs:
1. `docs/CAREERTROJAN_MASTER_ROADMAP - including mobile conversion - multiple AI utilisation.md`
2. `docs/CAREERTROJAN_MASTER_ROADMAP - including mobile conversion.md`

Post-second-pass validation:
1. `.\scripts\full_harness.ps1` passed.
2. Runtime review: `23/23 (100%)`.
3. Unit: `100%`, Integration: `100%`, E2E: `100%`.
