# J-Drive Runtime Setup (No C-Drive Dependency)

This runtime is intended to be operated from:

`J:\Codec - runtime version\Antigravity\careertrojan`

## Rules
1. Code changes happen only under this J-drive project root.
2. Python runtime should be `J:\Python311\python.exe` or project-local `.venv-j`.
3. Node runtime should be `J:\nodej\node.exe`.
4. Data roots should point to L:/E: mounts via env vars (not C: paths).

## One-Time Setup
Run from project root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_j_runtime.ps1 -FullDeps -InstallPytest
```

This will:
1. Create `.venv-j`
2. Install Python dependencies
3. Install Node.js to `J:\nodej` if missing
4. Generate `.env.j-drive.generated`

Optional: install Docker CLI binaries to `J:\docker-cli`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_j_runtime.ps1 -InstallDockerCli
```

## Daily Runtime Commands
1. Backend:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_backend.ps1
```

2. Start & map runtime:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Start-And-Map.ps1
```

3. Bootstrap (with optional Docker start):
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1 -StartDocker
```

Docker compose project name defaults to `codec-antigravity` (override with `CAREERTROJAN_COMPOSE_PROJECT_NAME`).

## Quick Validation
```powershell
J:\Python311\python.exe -m pytest -q tests\unit\test_app_bootstrap.py::TestAppBootstrap::test_app_imports_cleanly
J:\Python311\python.exe -m pytest -q tests\unit\test_paths_resolution.py
```

## Full Harness (J-Drive)
Run one command for runtime review + unit + integration + E2E, with summary artifacts:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\full_harness.ps1
```

Outputs:
1. `logs/test_results/full_harness_summary.json`
2. `logs/test_results/full_harness_summary.md`

## Run-All Launcher (J-Drive)
One-command launcher for bootstrap + full harness (and optional runtime window):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_all.ps1
```

Common variants:
```powershell
# include one-time setup + dependency install
powershell -ExecutionPolicy Bypass -File .\scripts\run_all.ps1 -WithSetup

# require 100% pass gate
powershell -ExecutionPolicy Bypass -File .\scripts\run_all.ps1 -Require100

# start runtime window after tests pass
powershell -ExecutionPolicy Bypass -File .\scripts\run_all.ps1 -StartRuntimeWindow
```

Outputs:
1. `logs/run_all/run_all_<timestamp>.log` (full transcript)
2. `logs/run_all/run_all_summary_<timestamp>.json`
3. `logs/test_results/full_harness_summary.md`

## Sharing Full Errors
If a run fails, share these files instead of only exit codes:
1. Latest `logs/run_all/run_all_summary_<timestamp>.json`
2. Latest `logs/run_all/run_all_<timestamp>.log`
3. `logs/test_results/full_harness_summary.md`
