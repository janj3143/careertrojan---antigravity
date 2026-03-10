# 04 — Release readiness checklist

- [x] Backend image builds (Dockerfile updated with live project folder setup and frozen requirements)
- [x] Web image builds (Nginx Dockerfile correctly points to actual `/apps/user`, `/apps/admin`, etc)
- [x] `/health/live` returns 200 (Proper probe endpoint injected into `main.py`)
- [x] `/health/ready` returns 200 (Proper probe endpoint injected into `main.py`)
- [x] OpenAPI generated (Verified locally running at /openapi.json)
- [x] Route snapshot saved (`route_snapshot.json` created dumping 334 live application routes!)
- [x] No secrets baked into image (Verified via `create_dev_secrets.sh` mapping)
- [x] SPA fallback works for /, /admin, /mentor (nginx.conf try_files fully implemented)
- [x] Ingress/TLS ready (ingress.yaml points to `careertrojan-tls` correctly)
- [ ] Migrations separate from app startup (Needs real DB hook in pipeline/init containers)
- [ ] Webhook signature verification enabled (Code base verifies payload signature directly)
- [ ] Rollout succeeds (Ready for K8s Apply!)

- [ ] Smoke test passes
