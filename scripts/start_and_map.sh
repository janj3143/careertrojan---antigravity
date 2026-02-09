#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# start_and_map.sh — CareerTrojan Runtime Launcher (Ubuntu)
# ═══════════════════════════════════════════════════════════════
# Bash equivalent of scripts/Start-And-Map.ps1
# 1. Validates mount points
# 2. Verifies symlinks
# 3. Ensures USER DATA directory structure
# 4. Starts sync trap
# 5. Starts FastAPI backend
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

APP_ROOT="${CAREERTROJAN_APP_ROOT:-/opt/careertrojan/runtime}"
ENV_FILE="${APP_ROOT}/.env"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   CareerTrojan — Runtime Start & Map         ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── 1. Load .env ──────────────────────────────────────────────
if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
    echo "[OK] Loaded .env"
else
    echo "[WARN] No .env at $ENV_FILE — using defaults"
fi

# ── 2. Validate Mount Points ─────────────────────────────────
declare -A mounts=(
    ["Data Root"]="${CAREERTROJAN_DATA_ROOT:-/mnt/careertrojan}"
    ["AI Data"]="${CAREERTROJAN_AI_DATA:-/mnt/careertrojan/ai_data_final}"
    ["User Data"]="${CAREERTROJAN_USER_DATA:-/mnt/careertrojan/user_data}"
    ["Mirror"]="${CAREERTROJAN_USER_DATA_MIRROR:-/mnt/careertrojan/backups/user_data}"
)

all_ok=true
for label in "${!mounts[@]}"; do
    path="${mounts[$label]}"
    if [[ -d "$path" ]]; then
        echo "[OK] $label → $path"
    else
        echo "[FAIL] $label → $path NOT FOUND"
        all_ok=false
    fi
done

if [[ "$all_ok" != "true" ]]; then
    echo ""
    echo "[WARN] Some mounts missing. Check /mnt/careertrojan/ setup."
fi

# ── 3. Verify Symlinks ───────────────────────────────────────
data_mounts="${APP_ROOT}/data-mounts"
for name in ai-data parser user-data; do
    link="${data_mounts}/${name}"
    if [[ -L "$link" ]]; then
        target=$(readlink -f "$link")
        echo "[OK] Symlink: $name → $target"
    elif [[ -d "$link" ]]; then
        echo "[OK] Directory: $name"
    else
        echo "[MISS] Mount: $name ($link)"
    fi
done

# ── 4. Ensure USER DATA Structure ────────────────────────────
subdirs=(sessions profiles interactions cv_uploads ai_matches session_logs admin_2fa test_accounts trap_profiles trap_reports user_registry quarantine)

for root in "${CAREERTROJAN_USER_DATA:-/mnt/careertrojan/user_data}" "${CAREERTROJAN_USER_DATA_MIRROR:-/mnt/careertrojan/backups/user_data}"; do
    if [[ -d "$(dirname "$root")" ]]; then
        for sub in "${subdirs[@]}"; do
            mkdir -p "${root}/${sub}"
        done
        echo "[OK] User data structure ensured: $root"
    fi
done

# ── 5. Start Sync Trap ───────────────────────────────────────
PYTHON="${CAREERTROJAN_PYTHON:-python3}"
sync_script="${APP_ROOT}/scripts/sync_user_data.py"

if command -v "$PYTHON" &>/dev/null && [[ -f "$sync_script" ]]; then
    echo "[START] Sync trap (primary ↔ mirror)..."
    nohup "$PYTHON" "$sync_script" --daemon > "${CAREERTROJAN_APP_LOGS:-/mnt/careertrojan/logs}/sync_trap_nohup.log" 2>&1 &
    echo "[OK] Sync trap PID: $!"
else
    echo "[SKIP] Sync trap — Python or script not found"
fi

# ── 6. Start AI Orchestrator ─────────────────────────────────
orch_script="${APP_ROOT}/services/workers/ai_orchestrator_enrichment.py"
if [[ -f "$orch_script" ]]; then
    echo "[START] AI orchestrator enrichment worker..."
    nohup "$PYTHON" "$orch_script" > "${CAREERTROJAN_APP_LOGS:-/mnt/careertrojan/logs}/ai_orchestrator_nohup.log" 2>&1 &
    echo "[OK] AI orchestrator PID: $!"
fi

# ── 7. Start FastAPI Backend ─────────────────────────────────
HOST="${CAREERTROJAN_HOST:-0.0.0.0}"
PORT="${CAREERTROJAN_PORT:-8500}"

echo ""
echo "[START] FastAPI backend on ${HOST}:${PORT}"
cd "$APP_ROOT"
exec "$PYTHON" -m uvicorn services.backend_api.main:app --host "$HOST" --port "$PORT" --reload
