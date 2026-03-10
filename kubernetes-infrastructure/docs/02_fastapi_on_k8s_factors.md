# 02 — FastAPI-specific factors on Kubernetes

## Process model
Use gunicorn + uvicorn workers:
```bash
gunicorn backend.app.main:app   -k uvicorn.workers.UvicornWorker   --bind 0.0.0.0:8600   --workers 2   --timeout 60   --graceful-timeout 30   --keep-alive 5
```

## Probes
- /health/live
- /health/ready

## Webhooks
For Braintree / Zendesk:
- verify signatures
- deduplicate
- persist event
- enqueue heavy processing
- return fast

## Logging
Each request should emit:
- request_id
- path
- method
- status_code
- duration_ms

