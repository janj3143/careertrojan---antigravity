# 01 — Kubernetes trajectory for CareerTrojan

## Phase A — Pre-Kubernetes hardening
- add /health/live
- add /health/ready
- move to gunicorn + uvicorn workers
- add request-id logging
- ensure webhook idempotency
- keep DB migrations separate
- keep API pods stateless

## Phase B — First cluster (recommended: k3s / k3d)
Run:
- backend deployment
- web deployment
- postgres
- redis
- minio
- worker deployment

## Phase C — Production shape
- managed secrets
- ingress + TLS automation
- HPA for backend and workers
- PDBs
- network policies
- central logs + metrics
- object storage first for large assets

## Phase D — Scale-out
Split workloads into:
- backend-api
- parser-worker
- enrichment-worker
- zendesk-ai-worker
- scheduled CronJobs
