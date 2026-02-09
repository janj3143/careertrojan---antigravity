#!/usr/bin/env bash
# ===========================================================================
# CareerTrojan — Ubuntu 22.04 LTS Setup Script
# ===========================================================================
# Automates Track B steps B3-B6:
#   B3  Create mount points + fstab entries for data drives
#   B4  Install system dependencies (Docker, Python 3.11, Node 20)
#   B5  Clone / copy project to ext4 system disk
#   B6  Create Python venv and install all requirements
#
# Usage:
#   chmod +x scripts/setup_ubuntu.sh
#   sudo bash scripts/setup_ubuntu.sh          # runs system packages only
#   bash scripts/setup_ubuntu.sh --user-only   # venv + pip only (no sudo)
# ===========================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ── Defaults ──────────────────────────────────────────────────────────────
PROJECT_DIR="${CAREERTROJAN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
DATA_MOUNT="/mnt/ai-data"              # where L: drive data will live
VENV_DIR="${PROJECT_DIR}/.venv"
PYTHON_BIN="python3.11"
NODE_MAJOR=20
USER_ONLY=false

for arg in "$@"; do
  case "$arg" in
    --user-only) USER_ONLY=true ;;
  esac
done

# ── B3 — Mount Points ────────────────────────────────────────────────────
setup_mount_points() {
  info "Creating mount points..."
  sudo mkdir -p "$DATA_MOUNT"
  sudo mkdir -p /mnt/backup-data

  if ! grep -q "$DATA_MOUNT" /etc/fstab; then
    warn "Add your NTFS/ext4 drive to /etc/fstab. Example:"
    echo "  # L: drive (NTFS data — read-only for safety)"
    echo "  UUID=<YOUR-UUID>  $DATA_MOUNT  ntfs-3g  defaults,ro,uid=1000,gid=1000  0  0"
    echo ""
    echo "  # E: drive backup (ext4)"
    echo "  UUID=<YOUR-UUID>  /mnt/backup-data  ext4  defaults  0  2"
    echo ""
    echo "  Run: sudo blkid   to find your UUIDs"
  else
    info "fstab already contains $DATA_MOUNT entry."
  fi
}

# ── B4 — System Packages ────────────────────────────────────────────────
install_system_deps() {
  info "Updating apt..."
  sudo apt-get update -qq

  info "Installing base packages..."
  sudo apt-get install -y -qq \
    build-essential git curl wget unzip \
    software-properties-common apt-transport-https \
    ca-certificates gnupg lsb-release \
    ntfs-3g

  # Python 3.11
  if ! command -v "$PYTHON_BIN" &>/dev/null; then
    info "Installing Python 3.11..."
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3.11 python3.11-venv python3.11-dev python3.11-distutils
  else
    info "Python 3.11 already installed: $(${PYTHON_BIN} --version)"
  fi

  # pip bootstrap
  if ! command -v pip3.11 &>/dev/null; then
    curl -sS https://bootstrap.pypa.io/get-pip.py | sudo "$PYTHON_BIN"
  fi

  # Node.js (for React portals)
  if ! command -v node &>/dev/null; then
    info "Installing Node.js ${NODE_MAJOR}.x..."
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | \
      sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_MAJOR}.x nodistro main" | \
      sudo tee /etc/apt/sources.list.d/nodesource.list
    sudo apt-get update -qq && sudo apt-get install -y -qq nodejs
  else
    info "Node.js already installed: $(node --version)"
  fi

  # Docker
  if ! command -v docker &>/dev/null; then
    info "Installing Docker Engine..."
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
      sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
      https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker "$USER"
    info "Docker installed. Log out/in for group change to take effect."
  else
    info "Docker already installed: $(docker --version)"
  fi

  # Tesseract for OCR parsing
  if ! command -v tesseract &>/dev/null; then
    info "Installing Tesseract OCR..."
    sudo apt-get install -y -qq tesseract-ocr
  fi
}

# ── B5 — Project Directory ──────────────────────────────────────────────
setup_project() {
  if [ ! -d "$PROJECT_DIR/.git" ]; then
    info "Cloning project to $PROJECT_DIR..."
    git clone https://github.com/janj3143/careertrojan---antigravity.git "$PROJECT_DIR"
  else
    info "Project already exists at $PROJECT_DIR"
    cd "$PROJECT_DIR" && git pull --ff-only || warn "git pull failed — check branch state"
  fi
}

# ── B6 — Python Venv ────────────────────────────────────────────────────
setup_venv() {
  cd "$PROJECT_DIR"

  if [ ! -d "$VENV_DIR" ]; then
    info "Creating Python venv at $VENV_DIR..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi

  info "Activating venv and installing requirements..."
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"

  pip install --upgrade pip setuptools wheel

  # Install requirements in dependency order
  for req in requirements.txt requirements.parsers.txt requirements.ai.txt requirements.runtime.txt; do
    if [ -f "$req" ]; then
      info "Installing $req..."
      pip install -r "$req"
    fi
  done

  info "Venv ready.  Activate with:  source ${VENV_DIR}/bin/activate"
}

# ── .env Setup ───────────────────────────────────────────────────────────
setup_env() {
  cd "$PROJECT_DIR"
  if [ ! -f .env ] && [ -f .env.ubuntu ]; then
    info "Copying .env.ubuntu → .env  (edit paths + API keys)"
    cp .env.ubuntu .env
  elif [ -f .env ]; then
    info ".env already exists — skipping."
  else
    warn "No .env or .env.ubuntu found — create one before running."
  fi
}

# ── Data directory bootstrap ─────────────────────────────────────────────
bootstrap_data() {
  cd "$PROJECT_DIR"
  mkdir -p data/ai_data_final logs working
  info "Created local data stubs: data/, logs/, working/"

  if [ -d "$DATA_MOUNT/ai_data_final" ]; then
    info "Data drive detected at $DATA_MOUNT — linking..."
    # Symlink so CAREERTROJAN_DATA_ROOT can point to $DATA_MOUNT
    echo "  Set CAREERTROJAN_DATA_ROOT=$DATA_MOUNT in .env"
  else
    warn "No data at $DATA_MOUNT — using local data/ as placeholder"
  fi
}

# ── Run ──────────────────────────────────────────────────────────────────
main() {
  echo "=============================================="
  echo " CareerTrojan Ubuntu Setup"
  echo "=============================================="
  echo " PROJECT_DIR:  $PROJECT_DIR"
  echo " DATA_MOUNT:   $DATA_MOUNT"
  echo " PYTHON:       $PYTHON_BIN"
  echo " USER_ONLY:    $USER_ONLY"
  echo "=============================================="

  if [ "$USER_ONLY" = true ]; then
    setup_venv
    setup_env
    bootstrap_data
  else
    setup_mount_points
    install_system_deps
    setup_project
    setup_venv
    setup_env
    bootstrap_data
  fi

  echo ""
  info "Setup complete! Next steps:"
  echo "  1. Edit .env with your API keys and data paths"
  echo "  2. Mount your data drives (sudo mount -a)"
  echo "  3. source .venv/bin/activate"
  echo "  4. python -m pytest tests/ -v"
  echo "  5. docker compose up -d"
}

main "$@"
