# 03 — Suggested cluster shape

## Namespace
Use one namespace first: careertrojan

## Workloads
Deployments:
- backend-api
- web
- worker-zendesk-ai

Stateful/storage:
- postgres
- minio

Services:
- backend-api
- web
- redis
- postgres
- minio

## Public DNS
- careertrojan.com -> web
- api.careertrojan.com -> backend
