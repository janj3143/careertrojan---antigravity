#!/usr/bin/env bash
# ============================================================================
# Antigravity — CareerTrojan | Production Deploy (Hetzner)
# ============================================================================
# Run ON the Hetzner server as the careertrojan user.
#
# Prerequisites (already done by provision_hetzner.sh + setup_ssl.sh):
#   - Docker installed, careertrojan user in docker group
#   - NGINX installed with SSL certs for careertrojan.com
#   - UFW open on 80/443
#   - Code cloned/synced to /home/careertrojan/careertrojan
#
# Usage:
#   cd ~/careertrojan
#   bash infra/hetzner/deploy.sh          # first deploy or update
#   bash infra/hetzner/deploy.sh --build   # force rebuild all images
# ============================================================================

set -euo pipefail

APP_DIR="/home/careertrojan/careertrojan"
DATA_DIR="/opt/careertrojan/data"
LOG_DIR="/opt/careertrojan/logs"
COMPOSE_FILE="compose.production.yaml"
PROJECT="antigravity-careertrojan"
FORCE_BUILD=""

if [[ "${1:-}" == "--build" ]]; then
    FORCE_BUILD="--build"
fi

echo "═══════════════════════════════════════════════════════════"
echo "  Antigravity — CareerTrojan Deploy"
echo "  Project: $PROJECT"
echo "═══════════════════════════════════════════════════════════"

# ── 1. Verify we're in the right place ────────────────────────────────────
if [ ! -f "$APP_DIR/$COMPOSE_FILE" ]; then
    echo "✗ compose.production.yaml not found in $APP_DIR"
    echo "  Sync the repo first: git clone / rsync / scp"
    exit 1
fi
cd "$APP_DIR"

# ── 2. Create data directories ───────────────────────────────────────────
echo "→ [1/7] Creating data directories..."
sudo mkdir -p "$DATA_DIR/ai-data" \
              "$DATA_DIR/user-data" \
              "$DATA_DIR/parser" \
              "$LOG_DIR"
sudo chown -R careertrojan:careertrojan "$DATA_DIR" "$LOG_DIR"
echo "  ✓ $DATA_DIR/{ai-data,user-data,parser}"
echo "  ✓ $LOG_DIR"

# ── 3. Verify secrets ────────────────────────────────────────────────────
echo "→ [2/7] Checking secrets..."
SECRETS_DIR="$APP_DIR/secrets"
MISSING=()
for f in secret_key.txt postgres_password.txt braintree_private_key.txt openai_api_key.txt anthropic_api_key.txt; do
    if [ ! -f "$SECRETS_DIR/$f" ]; then
        MISSING+=("$f")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "  ⚠ Missing secret files in $SECRETS_DIR/:"
    for m in "${MISSING[@]}"; do
        echo "    - $m"
    done
    echo ""
    echo "  Create them:"
    echo "    mkdir -p $SECRETS_DIR"
    echo "    echo -n 'your-value' > $SECRETS_DIR/secret_key.txt"
    echo ""
    read -p "  Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "  ✓ All 5 secret files present"
fi

# ── 4. Verify .env.production ────────────────────────────────────────────
echo "→ [3/7] Checking .env.production..."
if [ ! -f "$APP_DIR/.env.production" ]; then
    echo "  ⚠ .env.production not found"
    if [ -f "$APP_DIR/.env.production.template" ]; then
        echo "  Copying template → .env.production (fill in real values!)"
        cp "$APP_DIR/.env.production.template" "$APP_DIR/.env.production"
    else
        echo "  ✗ No template found either. Create .env.production first."
        exit 1
    fi
fi
echo "  ✓ .env.production exists"

# ── 5. Deploy NGINX config ──────────────────────────────────────────────
echo "→ [4/7] Deploying NGINX config..."
NGINX_SRC="$APP_DIR/config/nginx/ssl-letsencrypt.conf"
NGINX_DST="/etc/nginx/sites-available/careertrojan"
if [ -f "$NGINX_SRC" ]; then
    sudo cp "$NGINX_SRC" "$NGINX_DST"
    sudo ln -sf "$NGINX_DST" /etc/nginx/sites-enabled/careertrojan
    sudo rm -f /etc/nginx/sites-enabled/default
    if sudo nginx -t 2>&1; then
        sudo systemctl reload nginx
        echo "  ✓ NGINX config deployed and reloaded"
    else
        echo "  ✗ NGINX config test failed — check syntax"
        exit 1
    fi
else
    echo "  ⚠ ssl-letsencrypt.conf not found, skipping NGINX update"
fi

# ── 6. Build and start containers ────────────────────────────────────────
echo "→ [5/7] Building and starting containers..."
docker compose -f "$COMPOSE_FILE" pull postgres redis 2>/dev/null || true
docker compose -f "$COMPOSE_FILE" build $FORCE_BUILD
docker compose -f "$COMPOSE_FILE" up -d

echo "→ [6/7] Waiting for services to become healthy..."
sleep 10

# ── 7. Health check ──────────────────────────────────────────────────────
echo "→ [7/7] Verifying services..."
echo ""
docker compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""

# Check backend health
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8700/health 2>/dev/null || echo "000")
if [ "$BACKEND_STATUS" = "200" ]; then
    echo "  ✓ Backend API: healthy (HTTP 200)"
else
    echo "  ⚠ Backend API: HTTP $BACKEND_STATUS (may still be starting)"
fi

# Check portals
for port_name in "8701:admin" "8702:user" "8703:mentor"; do
    PORT="${port_name%%:*}"
    NAME="${port_name##*:}"
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PORT/" 2>/dev/null || echo "000")
    if [ "$STATUS" = "200" ]; then
        echo "  ✓ $NAME-portal: healthy (HTTP 200)"
    else
        echo "  ⚠ $NAME-portal: HTTP $STATUS"
    fi
done

# Check SSL
echo ""
for d in careertrojan.com www.careertrojan.com; do
    HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$d" 2>/dev/null || echo "ERR")
    echo "  https://$d → $HTTPS_STATUS"
done

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Deploy complete!"
echo ""
echo "  Dashboard:  https://careertrojan.com"
echo "  Admin:      https://careertrojan.com/admin/"
echo "  Mentor:     https://careertrojan.com/mentor/"
echo "  API docs:   https://careertrojan.com/docs"
echo ""
echo "  Logs:       docker compose -f $COMPOSE_FILE logs -f"
echo "  Status:     docker compose -f $COMPOSE_FILE ps"
echo "  Stop:       docker compose -f $COMPOSE_FILE down"
echo "═══════════════════════════════════════════════════════════"
