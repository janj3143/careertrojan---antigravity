# CareerTrojan — Antigravity

AI-powered career development platform with multi-portal architecture.

## Quick Start

### Prerequisites

- Python 3.11+
- Docker
- PostgreSQL
- Redis

### Setup

```bash
# Clone the repository
git clone https://github.com/janj3143/careertrojan---antigravity.git
cd careertrojan---antigravity

# Set up Entire.io session tracking
./setup_entire.sh

# Install dependencies
pip install -r requirements.txt
pip install -r requirements.runtime.txt

# Configure environment
cp .env.example .env
# Edit .env with your local settings

# Start all services
docker compose -f infra/docker/compose.yaml up -d
```

### Access

| Service | URL |
|---|---|
| User portal | http://localhost:3000 |
| Admin portal | http://localhost:3001 |
| Mentor portal | http://localhost:3002 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

## AI Session Tracking with Entire.io

Every commit is linked to the AI-assisted development session that produced it,
providing full traceability from idea to deployed code.

**What Entire.io tracks**: AI editor sessions, prompts, and the commits they
generate — giving your team insight into how AI contributes to the codebase.

**CI setup**: Add `ENTIRE_TOKEN` to your repository's GitHub Actions secrets:
1. Generate a token at https://entire.io/dashboard
2. Go to **Settings → Secrets and variables → Actions** in your GitHub repo
3. Add a secret named `ENTIRE_TOKEN`

**Local setup**: Run `./setup_entire.sh` once per machine.

## Architecture

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11) |
| Frontend | Multiple portal apps |
| Gateway | Nginx reverse proxy |
| Workers | Background processing |
| Database | PostgreSQL |
| Cache | Redis |
| Containers | Docker + Docker Compose |

## Project Structure

```
apps/               # Portal frontend applications (user, admin, mentor)
shared_backend/     # Shared backend modules and utilities
services/           # Microservices (AI engine, backend API, workers, email)
infra/              # Infrastructure config (Docker, Nginx, Hetzner)
tests/              # Test suite
scripts/            # Utility and deployment scripts
```

## Testing

```bash
pytest tests/ --cov=shared_backend --cov=services --cov-report=xml --cov-report=term
```

## Documentation

- [Work Plan](WORK_PLAN.md)
- [Runtime Plan](CAREERTROJAN_RUNTIME_PLAN.md)
- [Endpoint Mapping Phases](docs/plans/)

## Contributing

1. Create a feature branch from `develop`
2. Make your changes with AI assistance (Entire.io will track the session)
3. Run the test suite
4. Open a pull request to `develop`


