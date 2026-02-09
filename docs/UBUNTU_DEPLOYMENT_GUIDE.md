# CareerTrojan — Ubuntu Deployment Guide

**Created**: 2026-02-08  
**Target OS**: Ubuntu 22.04 LTS or 24.04 LTS (x86_64)  
**Source**: Windows runtime at `C:\careertrojan`

---

## TL;DR — Can We Just Copy and Run?

**Yes, with minimal changes.** The CareerTrojan stack is:

| Component | Portable? | Changes Needed |
|-----------|-----------|----------------|
| FastAPI backend (Python) | ✅ Zero changes | Install Python 3.11, pip install requirements |
| React portals (Vite/TS) | ✅ Zero changes | `npm install && npm run build` produces static files |
| Docker Compose | ✅ Better on Linux | Change volume paths only |
| PostgreSQL, Redis | ✅ Native Linux | Already containerised |
| Nginx | ✅ Native Linux | Config already written |
| PowerShell scripts | ❌ Windows-only | Bash equivalents provided (see below) |
| Drive paths (L:\, E:\, C:\) | ❌ Windows-only | All paths read from `.env` — just change the values |
| NTFS junctions | ❌ Windows-only | Replace with `ln -s` (symlinks) — same concept |

**You do NOT need to cross-compile anything.** Python is interpreted, React builds to
static JS/CSS, and Docker containers are Linux-native.

---

## 1. Prerequisites

### 1.1 System Requirements
```
- Ubuntu 22.04 or 24.04 LTS (fresh install recommended)
- 8 GB RAM minimum (16 GB recommended for AI workers)
- 50 GB disk for application + 100 GB+ for ai_data_final
- SSD recommended for data mounts
```

### 1.2 Install System Packages
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    python3.11 python3.11-venv python3.11-dev \
    python3-pip \
    build-essential \
    curl wget git \
    nginx \
    nodejs npm \
    docker.io docker-compose-v2 \
    tesseract-ocr \
    postgresql-client

# Add user to docker group (logout/login after)
sudo usermod -aG docker $USER
```

### 1.3 Install Node.js 20 LTS (if system version is older)
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

---

## 2. Directory Layout

### 2.1 Create Mount Points
```bash
sudo mkdir -p /mnt/careertrojan/{ai_data_final,user_data,postgres,logs,backups}
sudo mkdir -p /opt/careertrojan/runtime
sudo chown -R $USER:$USER /mnt/careertrojan /opt/careertrojan
```

### 2.2 Path Mapping (Windows → Ubuntu)

| Windows Path | Ubuntu Path | Purpose |
|-------------|-------------|---------|
| `C:\careertrojan\` | `/opt/careertrojan/runtime/` | Application code |
| `L:\VS ai_data final - version\ai_data_final\` | `/mnt/careertrojan/ai_data_final/` | AI knowledge base |
| `L:\VS ai_data final - version\automated_parser\` | `/mnt/careertrojan/ai_data_final/automated_parser/` | Parser input |
| `L:\VS ai_data final - version\USER DATA\` | `/mnt/careertrojan/user_data/` | User sessions & data |
| `E:\CareerTrojan\USER_DATA_COPY\` | `/mnt/careertrojan/backups/user_data/` | Mirror backup |
| `C:\careertrojan\logs\` | `/mnt/careertrojan/logs/` | Application logs |
| `C:\careertrojan\trained_models\` | `/opt/careertrojan/runtime/trained_models/` | ML models |

---

## 3. Copy the Runtime

### 3.1 From Windows to Ubuntu
```bash
# Option A: rsync from Windows share
rsync -avz --exclude 'node_modules' --exclude '__pycache__' --exclude '.venv' \
    //WINDOWS_HOST/careertrojan/ /opt/careertrojan/runtime/

# Option B: zip and transfer
# On Windows: tar -czf careertrojan.tar.gz -C C:\ careertrojan --exclude=node_modules
# On Ubuntu:
tar -xzf careertrojan.tar.gz -C /opt/careertrojan/runtime/

# Option C: git clone (if in a repo)
git clone <your-repo-url> /opt/careertrojan/runtime
```

### 3.2 Copy AI Data
```bash
# This is the large dataset — use rsync for resumability
rsync -avz --progress \
    //WINDOWS_HOST/VS_ai_data_final/ /mnt/careertrojan/ai_data_final/

# Copy user data
rsync -avz --progress \
    //WINDOWS_HOST/USER_DATA/ /mnt/careertrojan/user_data/
```

---

## 4. Create Symlinks (replaces Windows junctions)

```bash
cd /opt/careertrojan/runtime/data-mounts

# Remove old Windows junctions (they won't work on Linux)
rm -rf ai-data parser user-data

# Create Linux symlinks
ln -s /mnt/careertrojan                           ai-data
ln -s /mnt/careertrojan/ai_data_final/automated_parser  parser
ln -s /mnt/careertrojan/user_data                  user-data
```

---

## 5. Configure Environment

### 5.1 Create Ubuntu `.env`
```bash
cat > /opt/careertrojan/runtime/.env << 'EOF'
# ── CareerTrojan Runtime Environment (Ubuntu) ──────────────
CAREERTROJAN_DATA_ROOT=/mnt/careertrojan
CAREERTROJAN_AI_DATA=/mnt/careertrojan/ai_data_final
CAREERTROJAN_PARSER_ROOT=/mnt/careertrojan/ai_data_final/automated_parser
CAREERTROJAN_USER_DATA=/mnt/careertrojan/user_data
CAREERTROJAN_USER_DATA_MIRROR=/mnt/careertrojan/backups/user_data
CAREERTROJAN_WORKING_ROOT=/opt/careertrojan/runtime/working/working_copy
CAREERTROJAN_APP_ROOT=/opt/careertrojan/runtime
CAREERTROJAN_APP_LOGS=/mnt/careertrojan/logs
CAREERTROJAN_PYTHON=python3.11
CAREERTROJAN_PORT=8500
CAREERTROJAN_HOST=0.0.0.0
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/careertrojan
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=change-me-in-production
DEMO_MODE=0
EOF
```

### 5.2 Also update the launcher pack env
```bash
cp /opt/careertrojan/runtime/.env /opt/careertrojan/config/careertrojan.env
```

---

## 6. Set Up Python Environment

```bash
cd /opt/careertrojan/runtime

# Create virtual environment with Python 3.11
python3.11 -m venv .venv
source .venv/bin/activate

# Install all dependencies
pip install --upgrade pip
pip install -r requirements.lock.txt

# Install PyTorch (CPU — for GPU see pytorch.org)
pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cpu

# Download spaCy model
python -m spacy download en_core_web_sm
```

---

## 7. Build React Portals

```bash
# Admin Portal
cd /opt/careertrojan/runtime/apps/admin
npm install
npm run build   # Output in dist/

# User Portal
cd /opt/careertrojan/runtime/apps/user
npm install
npm run build

# Mentor Portal
cd /opt/careertrojan/runtime/apps/mentor
npm install
npm run build
```

---

## 8. Start the Runtime

### Option A: Direct (development)
```bash
cd /opt/careertrojan/runtime
source .venv/bin/activate
bash scripts/start_and_map.sh
```

### Option B: Docker Compose (production)
```bash
cd /opt/careertrojan/runtime
docker compose up -d
docker compose ps
```

### Option C: k3s + Helm (full production)
```bash
# Install k3s
curl -sfL https://get.k3s.io | sh -

# Deploy via Helm
helm upgrade --install careertrojan config/k8s/ \
    --namespace careertrojan --create-namespace
```

### Option D: Desktop Launchers (from Q:\CareerTrojan_Ubuntu_LauncherPack_2026-01-15)
```bash
# Copy launchers
sudo cp -r /opt/careertrojan/scripts/*.sh /opt/careertrojan/scripts/
cp ~/Desktop/CareerTrojan*.desktop ~/Desktop/
chmod +x ~/Desktop/CareerTrojan*.desktop
```

---

## 9. Create systemd Services (auto-start on boot)

### 9.1 Backend API
```bash
sudo tee /etc/systemd/system/careertrojan-backend.service << 'EOF'
[Unit]
Description=CareerTrojan FastAPI Backend
After=network.target postgresql.service redis.service
Requires=network.target

[Service]
Type=simple
User=careertrojan
WorkingDirectory=/opt/careertrojan/runtime
EnvironmentFile=/opt/careertrojan/runtime/.env
ExecStart=/opt/careertrojan/runtime/.venv/bin/python -m uvicorn services.backend_api.main:app --host 0.0.0.0 --port 8500
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

### 9.2 Sync Trap
```bash
sudo tee /etc/systemd/system/careertrojan-sync.service << 'EOF'
[Unit]
Description=CareerTrojan User Data Sync Trap
After=network.target

[Service]
Type=simple
User=careertrojan
WorkingDirectory=/opt/careertrojan/runtime
EnvironmentFile=/opt/careertrojan/runtime/.env
ExecStart=/opt/careertrojan/runtime/.venv/bin/python scripts/sync_user_data.py --daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 9.3 AI Orchestrator
```bash
sudo tee /etc/systemd/system/careertrojan-ai-orch.service << 'EOF'
[Unit]
Description=CareerTrojan AI Orchestrator Enrichment Worker
After=network.target careertrojan-backend.service

[Service]
Type=simple
User=careertrojan
WorkingDirectory=/opt/careertrojan/runtime
EnvironmentFile=/opt/careertrojan/runtime/.env
ExecStart=/opt/careertrojan/runtime/.venv/bin/python services/workers/ai_orchestrator_enrichment.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 9.4 Enable & Start
```bash
sudo systemctl daemon-reload
sudo systemctl enable careertrojan-backend careertrojan-sync careertrojan-ai-orch
sudo systemctl start careertrojan-backend careertrojan-sync careertrojan-ai-orch

# Check status
sudo systemctl status careertrojan-*
```

---

## 10. Nginx Configuration (already exists)

```bash
# Copy the portal-bridge config
sudo cp /opt/careertrojan/runtime/config/nginx/portal-bridge.conf /etc/nginx/sites-available/careertrojan
sudo ln -s /etc/nginx/sites-available/careertrojan /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 11. Verify

```bash
# Run smoke test
bash /opt/careertrojan/scripts/smoke_test.sh

# Check endpoints
curl -s http://localhost:8500/api/shared/v1/health | python3 -m json.tool

# Check sync status
curl -s http://localhost:8500/api/sessions/v1/sync-status | python3 -m json.tool

# Check data mounts
ls -la /opt/careertrojan/runtime/data-mounts/
ls -la /mnt/careertrojan/ai_data_final/ | head -20
ls -la /mnt/careertrojan/user_data/
```

---

## 12. Files That Are Windows-Only vs Cross-Platform

### Cross-Platform (work on both OS without changes)
- All Python code (`services/`, `scripts/*.py`, `shared_backend/`)
- All React code (`apps/*/src/`)
- Docker Compose files
- Kubernetes manifests
- Nginx config
- `requirements.lock.txt`

### Windows-Only (have Ubuntu equivalents)
| Windows Script | Ubuntu Equivalent |
|---------------|-------------------|
| `scripts/Start-And-Map.ps1` | `scripts/start_and_map.sh` |
| `scripts/bootstrap.ps1` | Install steps in this guide |
| `scripts/setup_mounts.ps1` | Section 4 (symlinks) |
| `scripts/validate_ai_integrity.ps1` | `scripts/smoke_test.sh` (from launcher pack) |
| `scripts/verify_endpoint_counts.ps1` | `curl` commands in Section 11 |

### Path Resolution
All Python code uses `services/shared/paths.py` which auto-detects the platform
and reads from environment variables. **No code changes needed.**

---

## 13. Quick Reference Card

```
┌──────────────────────────────────────────────────────────┐
│  CareerTrojan on Ubuntu — Quick Reference                │
├──────────────────────────────────────────────────────────┤
│  App code:     /opt/careertrojan/runtime/                │
│  AI data:      /mnt/careertrojan/ai_data_final/          │
│  User data:    /mnt/careertrojan/user_data/              │
│  Mirror:       /mnt/careertrojan/backups/user_data/      │
│  Logs:         /mnt/careertrojan/logs/                   │
│  Backend:      http://localhost:8500                     │
│  Admin UI:     http://localhost:8501 or /admin           │
│  User UI:      http://localhost:8502 or /                │
│  Mentor UI:    http://localhost:8503 or /mentor          │
│                                                          │
│  Start:   systemctl start careertrojan-backend           │
│  Stop:    systemctl stop careertrojan-backend            │
│  Logs:    journalctl -u careertrojan-backend -f          │
│  Sync:    journalctl -u careertrojan-sync -f             │
└──────────────────────────────────────────────────────────┘
```
