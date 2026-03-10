#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${1:-http://localhost:8600}"
curl -fsS "${BASE_URL}/health/live" >/dev/null
curl -fsS "${BASE_URL}/health/ready" >/dev/null
curl -fsS "${BASE_URL}/openapi.json" >/dev/null
echo "smoke test passed"

