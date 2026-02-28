#!/usr/bin/env bash
# ============================================================================
# CareerTrojan — Developer Environment Setup
# ============================================================================
# Sets up Entire.io CLI for code tracking + AI session capture.
# Run once per machine to install, then once per repo to enable.
#
# Usage:
#   chmod +x scripts/setup_entire.sh
#   ./scripts/setup_entire.sh
# ============================================================================

set -euo pipefail

echo "═══════════════════════════════════════════════════════════"
echo "  CareerTrojan — Entire.io Setup"
echo "═══════════════════════════════════════════════════════════"

# ── 1. Install Entire CLI ─────────────────────────────────────────────────
if command -v entire &>/dev/null; then
    echo "✓ Entire CLI already installed: $(entire --version 2>/dev/null || echo 'installed')"
else
    echo "→ Installing Entire CLI..."
    curl -fsSL https://entire.io/install.sh | bash
    echo "✓ Entire CLI installed"
fi

# ── 2. Enable in this repository ──────────────────────────────────────────
if [ -d .git ]; then
    echo "→ Enabling Entire in this repository..."
    entire enable
    echo "✓ Entire enabled — sessions will sync with commits"
else
    echo "✗ Not a git repository. Run from the project root."
    exit 1
fi

# ── 3. Verify ─────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Setup complete!"
echo ""
echo "  How it works:"
echo "    - Every commit gets a checkpoint (code + AI session)"
echo "    - Sessions are stored in git history (no external DB)"
echo "    - View history: entire log"
echo "    - Search context: entire search <query>"
echo ""
echo "  Supported agents: Claude Code, Gemini, GitHub Copilot (planned)"
echo "═══════════════════════════════════════════════════════════"
