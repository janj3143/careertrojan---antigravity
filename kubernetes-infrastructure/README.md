# CareerTrojan — FastAPI Kubernetes Full Pack (2026-03-06)

This pack is tailored to the current CareerTrojan runtime shape:
- FastAPI backend
- React/Vite portals (admin/user/mentor)
- PostgreSQL
- Redis
- MinIO/object-storage direction
- Zendesk AI queue/worker pattern
- Braintree billing

Contents:
- docs/: trajectory, FastAPI factors, cluster shape, release checklist, migration backlog
- kustomize/: base, dev, prod overlays
- docker/: backend and web Dockerfile skeletons
- snippets/: FastAPI health/lifespan, request-id middleware, gunicorn config, openapi snapshot
- scripts/: secret creation, port-forwarding, route snapshots, smoke test
- .github/workflows/: CI/CD skeletons
