#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../backend"

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Please set OPENAI_API_KEY / PERPLEXITY_API_KEY."
fi

uvicorn app.main:app --reload --port 8000
