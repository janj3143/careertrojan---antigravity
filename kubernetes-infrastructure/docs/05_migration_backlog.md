# 05 — Migration backlog / priority list

## Priority 1
1. Add dedicated /health/live
2. Add dedicated /health/ready
3. Switch backend command to gunicorn + uvicorn workers
4. Add route snapshot generation
5. Add request-id middleware
6. Confirm backend import path (likely backend.app.main:app)

## Priority 2
1. Separate webhooks from heavy processing
2. Split worker deployment from API
3. Move file artifacts to object storage
4. Create real dev/staging/prod env sets
5. Add resource requests/limits everywhere
