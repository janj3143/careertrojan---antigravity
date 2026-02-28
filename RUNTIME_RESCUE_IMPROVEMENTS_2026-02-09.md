# Runtime Rescue Improvements (2026-02-09)

## Scope
Rescue and stabilize `J:\Codec - runtime version\Antigravity\careertrojan` for consistent runtime path behavior, especially for `ai_data_final` links on `L:`.

## Improvements Implemented
1. Hardened canonical path resolution in `services/shared/paths.py`.
2. Unified backend AI data routers to use one shared path source instead of conflicting local defaults.
3. Fixed taxonomy service default root logic to avoid duplicate `.../ai_data_final/ai_data_final` path construction.
4. Added unit tests for path normalization and environment-variable behavior.
5. Added logging improvements in AI data/analytics routers (replaced `print(...)` load errors with structured logger warnings).

## Files Changed
1. `services/shared/paths.py`
2. `services/backend_api/routers/ai_data.py`
3. `services/backend_api/routers/analytics.py`
4. `services/backend_api/services/industry_taxonomy_service.py`
5. `tests/unit/test_paths_resolution.py`

## L: Drive Linking Behavior Now
If `CAREERTROJAN_DATA_ROOT` is not explicitly set, Windows runtime now prefers these existing `L:` roots first:
1. `L:\VS ai_data final - version`
2. `L:\antigravity_version_ai_data_final`

Path normalization is now consistent when env vars point to either shape:
1. Data root shape: `...\<root>\` containing `ai_data_final\`
2. Direct AI shape: `...\<root>\ai_data_final\`

Both are normalized so backend consumers resolve:
1. `ai_data_final` correctly
2. `automated_parser` correctly
3. `USER DATA` correctly

## Validation Performed
1. New tests passed: `python -m pytest -q tests/unit/test_paths_resolution.py`
2. Syntax validation passed:
   `python -m compileall services/shared/paths.py services/backend_api/routers/ai_data.py services/backend_api/routers/analytics.py services/backend_api/services/industry_taxonomy_service.py`
3. App bootstrap import test passed:
   `J:\Python311\python.exe -m pytest -q tests/unit/test_app_bootstrap.py::TestAppBootstrap::test_app_imports_cleanly`
4. Runtime summary check confirms default Windows resolution currently points to:
   1. `Data Root: L:\VS ai_data final - version`
   2. `AI Data Final: L:\VS ai_data final - version\ai_data_final`
   3. `Parser Root: L:\VS ai_data final - version\automated_parser`
   4. `User Data: L:\VS ai_data final - version\USER DATA`
5. Runtime dependencies installed into J-drive Python:
   `J:\Python311\python.exe -m pip install -r requirements.runtime.txt`
   `J:\Python311\python.exe -m pip install -r requirements.txt`
