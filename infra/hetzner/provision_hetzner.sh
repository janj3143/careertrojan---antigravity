#!/usr/bin/env bash
# ============================================================================
# CareerTrojan — Hetzner Cloud Server Provisioning
# ============================================================================
# Complete setup script for a Hetzner VPS running CareerTrojan.
# Run this ON the server after SSH'ing in for the first time.
#
# Hetzner setup (do in console.hetzner.cloud FIRST):
#   1. Create project: "careertrojan"
#   2. Add SSH key (from your local machine: cat ~/.ssh/id_rsa.pub)
#   3. Create server:
#        - Location: Falkenstein (FSN1) or Nuremberg (NBG1)
#        - Image: Ubuntu 24.04
#        - Type: CX22 (2 vCPU, 4GB RAM — ~€4.50/mo)
#                or CX32 (4 vCPU, 8GB RAM — ~€8/mo) for production
#        - Networking: Public IPv4 + IPv6
#        - SSH key: select yours
#        - Name: careertrojan-prod
#   4. Note the public IP from the server list
#   5. Update DNS A records for all domains → that IP
#   6. SSH in: ssh root@<IP>
#   7. Run this script: bash provision_hetzner.sh
#
# After this script: run setup_ssl.sh to get Let's Encrypt certs
# ============================================================================

set -euo pipefail

DOMAIN="careertrojan.com"
APP_USER="careertrojan"
SWAP_SIZE="2G"

echo "═══════════════════════════════════════════════════════════"
echo "  CareerTrojan — Hetzner Server Provisioning"
echo "═══════════════════════════════════════════════════════════"

# ── 1. System updates ────────────────────────────────────────────────────
echo "→ [1/8] System update..."
apt-get update -y && apt-get upgrade -y
apt-get install -y \
    curl wget git unzip htop ncdu \
    nginx certbot python3-certbot-nginx \
    ufw fail2ban \
    ca-certificates gnupg lsb-release

# ── 2. Create non-root user ──────────────────────────────────────────────
echo "→ [2/8] Creating app user: $APP_USER..."
if ! id "$APP_USER" &>/dev/null; then
    adduser --disabled-password --gecos "" "$APP_USER"
    usermod -aG sudo "$APP_USER"
    # Copy SSH keys
    mkdir -p /home/$APP_USER/.ssh
    cp /root/.ssh/authorized_keys /home/$APP_USER/.ssh/
    chown -R $APP_USER:$APP_USER /home/$APP_USER/.ssh
    echo "$APP_USER ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/$APP_USER
    echo "✓ User $APP_USER created with sudo"
else
    echo "✓ User $APP_USER already exists"
fi

# ── 3. Firewall (UFW) ───────────────────────────────────────────────────
echo "→ [3/8] Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
echo "✓ Firewall: SSH + HTTP + HTTPS allowed"

# ── 4. Fail2Ban (SSH brute force protection) ─────────────────────────────
echo "→ [4/8] Configuring fail2ban..."
cat > /etc/fail2ban/jail.local << 'EOF'
[sshd]
enabled = true
port = ssh
maxretry = 5
bantime = 3600
findtime = 600
EOF
systemctl enable fail2ban
systemctl restart fail2ban
echo "✓ Fail2ban active (5 retries → 1hr ban)"

# ── 5. Docker ────────────────────────────────────────────────────────────
echo "→ [5/8] Installing Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker $APP_USER
    systemctl enable docker
    echo "✓ Docker installed"
else
    echo "✓ Docker already installed"
fi

# ── 6. Swap (Hetzner CX22 only has 4GB RAM) ─────────────────────────────
echo "→ [6/8] Setting up ${SWAP_SIZE} swap..."
if [ ! -f /swapfile ]; then
    fallocate -l $SWAP_SIZE /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo "/swapfile none swap sw 0 0" >> /etc/fstab
    echo "vm.swappiness=10" >> /etc/sysctl.conf
    sysctl -p
    echo "✓ Swap configured"
else
    echo "✓ Swap already exists"
fi

# ── 7. NGINX base config ────────────────────────────────────────────────
echo "→ [7/8] Configuring NGINX..."
rm -f /etc/nginx/sites-enabled/default

cat > /etc/nginx/sites-available/careertrojan << 'NGINX'
server {
    listen 80;
    server_name careertrojan.com www.careertrojan.com
                careertrojan.co.uk www.careertrojan.co.uk
                careertrojan.org www.careertrojan.org;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 200 "CareerTrojan — server ready, SSL pending\n";
        add_header Content-Type text/plain;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/careertrojan /etc/nginx/sites-enabled/
nginx -t && systemctl enable nginx && systemctl reload nginx
echo "✓ NGINX configured (HTTP only — run SSL setup next)"

# ── 8. App directory ────────────────────────────────────────────────────
echo "→ [8/8] Creating app directory..."
mkdir -p /home/$APP_USER/careertrojan
chown -R $APP_USER:$APP_USER /home/$APP_USER/careertrojan

# ── Done ─────────────────────────────────────────────────────────────────
PUBLIC_IP=$(curl -s https://ipv4.icanhazip.com)

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Server provisioned!"
echo ""
echo "  Public IP: $PUBLIC_IP"
echo "  SSH:       ssh $APP_USER@$PUBLIC_IP"
echo ""
echo "  Next steps:"
echo "    1. Update DNS A records for all domains → $PUBLIC_IP"
echo "    2. Wait for DNS propagation (nslookup $DOMAIN)"
echo "    3. Run: bash setup_ssl.sh"
echo "    4. Deploy: scp compose.yaml $APP_USER@$PUBLIC_IP:~/careertrojan/"
echo "    5. On server: cd ~/careertrojan && docker compose up -d"
echo "═══════════════════════════════════════════════════════════"
