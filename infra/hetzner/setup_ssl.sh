#!/usr/bin/env bash
# ============================================================================
# CareerTrojan — SSL Certificate Setup (Let's Encrypt)
# ============================================================================
# Run this AFTER provision_hetzner.sh and AFTER DNS A records point here.
# Issues a single SAN certificate for all 3 domains + www variants.
#
# Usage: bash setup_ssl.sh
# ============================================================================

set -euo pipefail

echo "═══════════════════════════════════════════════════════════"
echo "  CareerTrojan — Let's Encrypt SSL Setup"
echo "═══════════════════════════════════════════════════════════"

# ── 1. Verify DNS ────────────────────────────────────────────────────────
echo "→ Checking DNS resolution..."
PUBLIC_IP=$(curl -s https://ipv4.icanhazip.com)
DOMAINS=("careertrojan.com" "www.careertrojan.com" "careertrojan.co.uk" "www.careertrojan.co.uk" "careertrojan.org" "www.careertrojan.org")
FAILED=()

for d in "${DOMAINS[@]}"; do
    RESOLVED=$(dig +short "$d" A 2>/dev/null | head -1)
    if [ "$RESOLVED" = "$PUBLIC_IP" ]; then
        echo "  ✓ $d → $RESOLVED"
    else
        echo "  ✗ $d → ${RESOLVED:-NXDOMAIN} (expected $PUBLIC_IP)"
        FAILED+=("$d")
    fi
done

if [ ${#FAILED[@]} -gt 0 ]; then
    echo ""
    echo "  ⚠ DNS not ready for: ${FAILED[*]}"
    echo "  Update A records and wait for propagation."
    echo "  Check: https://www.whatsmydns.net/#A/careertrojan.com"
    read -p "  Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# ── 2. Issue certificate ─────────────────────────────────────────────────
echo ""
echo "→ Requesting Let's Encrypt certificate..."
certbot --nginx \
    -d careertrojan.com -d www.careertrojan.com \
    -d careertrojan.co.uk -d www.careertrojan.co.uk \
    -d careertrojan.org -d www.careertrojan.org \
    --non-interactive --agree-tos \
    --email admin@careertrojan.com \
    --redirect

# ── 3. Deploy production NGINX config ─────────────────────────────────────
echo "→ Deploying production NGINX config..."
# If ssl-letsencrypt.conf was uploaded to the server:
if [ -f /home/careertrojan/ssl-letsencrypt.conf ]; then
    cp /home/careertrojan/ssl-letsencrypt.conf /etc/nginx/sites-available/careertrojan
    nginx -t && systemctl reload nginx
    echo "✓ Production NGINX config deployed"
else
    echo "  ℹ Using certbot-generated config (fine for now)"
    echo "  For production: scp config/nginx/ssl-letsencrypt.conf to the server"
fi

# ── 4. Enable auto-renewal ──────────────────────────────────────────────
echo "→ Enabling certificate auto-renewal..."
systemctl enable certbot.timer
systemctl start certbot.timer

# Test renewal
certbot renew --dry-run
echo "✓ Auto-renewal verified"

# ── 5. Verify ────────────────────────────────────────────────────────────
echo ""
echo "→ Verifying SSL..."
for d in careertrojan.com careertrojan.co.uk careertrojan.org; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$d" 2>/dev/null || echo "ERR")
    echo "  https://$d → $HTTP_CODE"
done

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  SSL setup complete!"
echo ""
echo "  Certificate location:"
echo "    /etc/letsencrypt/live/careertrojan.com/fullchain.pem"
echo "    /etc/letsencrypt/live/careertrojan.com/privkey.pem"
echo ""
echo "  Auto-renewal: active (certbot.timer)"
echo "  Expiry: ~90 days, renews automatically at 60 days"
echo "═══════════════════════════════════════════════════════════"
