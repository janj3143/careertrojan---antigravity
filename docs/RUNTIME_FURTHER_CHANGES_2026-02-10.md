# Runtime Further Changes (2026-02-10)

This document tracks additional runtime-focused changes made in:

`J:\Codec - runtime version\Antigravity\careertrojan`

## Scope

- Stabilize J-drive runtime operations.
- Improve in-portal runtime validation controls.
- Harden test harness execution.
- Isolate Docker project naming for this runtime.

## Code Changes

1. `apps/admin/pages/13_API_Integration.py`
- Added a runtime validation panel on the API Integration page.
- Added "Run All Runtime Checks" button to execute `scripts/run_all.ps1`.
- Added J-drive guardrails for runtime actions.
- Added latest run summary loading from `logs/run_all/run_all_summary_*.json`.
- Added in-page display of step status, transcript path, harness summary path, and console output.

2. `scripts/agent_manager.ps1`
- Added explicit Python and Docker binary resolution (`Resolve-PythonBin`, `Resolve-DockerBin`) to reduce PATH ambiguity.
- Switched test execution calls to resolved Python binary.
- Fixed test infrastructure check to accept either root `conftest.py` or `tests/conftest.py`.
- Fixed incorrect `Join-Path` usage for `tests/conftest.py`.
- Fixed incorrect `Join-Path` usage for `logs/test_results`.
- Improved startup logging for resolved runtime binaries and watch label formatting.

3. `scripts/bootstrap.ps1`
- Refactored for J-drive runtime root resolution (`scripts` parent), not hardcoded C paths.
- Added optional `-StartDocker` launch behavior with clearer preflight checks.
- Added runtime env var `CAREERTROJAN_COMPOSE_PROJECT_NAME` (default: `codec-antigravity`).
- Updated Docker launch command to pass an explicit compose file and project name.
- Added explicit non-zero exit handling after docker compose launch attempt.

4. `compose.yaml`
- Added compose project name: `name: codec-antigravity`.
- Updated usage comments to include explicit `-p codec-antigravity`.

5. `infra/docker/compose.yaml`
- Added compose project name: `name: codec-antigravity`.

6. `infra/docker/Dockerfile.bridge`
- Fixed bridge source copy path from non-existent `services/portal_bridge` to `services/shared/portal-bridge`.
- Updated container command to run uvicorn with explicit app directory:
  - `main:app`
  - `--app-dir /app/services/shared/portal-bridge`

7. `scripts/full_harness.ps1`
- Hardened default `ProjectRoot` resolution to avoid null/empty `$PSScriptRoot` failures in some shell invocation paths.
- Added fallback to current working directory when `$PSScriptRoot` is unavailable.

## Operational Notes

- Compose naming is now standardized to `codec-antigravity` for this runtime.
- Current host Docker CLI still needs proper `docker compose` support validation; bootstrap now reports compose startup failures explicitly instead of reporting a false success.
