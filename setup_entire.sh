#!/usr/bin/env bash
set -e

echo "Setting up Entire.io for CareerTrojan..."

if command -v entire &>/dev/null; then
  echo "✓ Entire CLI is already installed: $(entire --version 2>/dev/null || echo 'version unknown')"
else
  echo "Installing Entire CLI..."
  curl -fsSL https://entire.io/install.sh | bash
  echo "✓ Entire CLI installed"
fi

# Add Entire bin to PATH for this session
export PATH="$HOME/.entire/bin:$PATH"

echo "Enabling Entire.io in this repository..."
entire enable

echo "Installing git hooks..."
entire hooks install

echo ""
echo "✓ Entire.io setup complete!"
echo ""
echo "Next steps:"
echo "  1. Add your ENTIRE_TOKEN to GitHub Actions secrets:"
echo "     https://github.com/settings/tokens → then add as a repo secret named ENTIRE_TOKEN"
echo "  2. View your AI session dashboard at https://entire.io/dashboard"
echo "  3. Every commit will now be linked to the AI session that produced it"
