# IntelliCV Page 09 backend runner (PowerShell)
Set-Location -Path (Join-Path $PSScriptRoot "..\backend")

if (-not (Test-Path .venv)) {
  python -m venv .venv
}

. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

if (-not (Test-Path .env)) {
  Copy-Item .env.example .env
  Write-Host "Created .env from .env.example. Please set OPENAI_API_KEY / PERPLEXITY_API_KEY." -ForegroundColor Yellow
}

uvicorn app.main:app --reload --port 8000
