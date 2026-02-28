# Priority Endpoint Probe — 2026-02-27

Generated: `2026-02-27T15:55:41.163274+00:00`

| Method | Path | Status | Classification |
|---|---|---:|---|
| GET | /api/admin/v1/integrations/status | 200 | ok |
| POST | /api/admin/v1/integrations/sendgrid/configure | 200 | ok |
| POST | /api/admin/v1/integrations/klaviyo/configure | 200 | ok |
| POST | /api/admin/v1/email/send_test | 200 | ok |
| POST | /api/admin/v1/email/send_bulk | 200 | ok |
| GET | /api/admin/v1/email/logs | 200 | ok |
| GET | /api/admin/v1/email/analytics | 200 | ok |
| GET | /api/admin/integrations/status | 404 | missing |
| POST | /api/admin/integrations/sendgrid/configure | 404 | missing |
| POST | /api/admin/integrations/klaviyo/configure | 404 | missing |
| POST | /api/admin/email/send_test | 404 | missing |
| POST | /api/admin/email/send_bulk | 404 | missing |
| GET | /api/ai-data/v1/emails/summary | 200 | ok |
| GET | /api/ai-data/v1/emails/providers/sendgrid | 200 | ok |
| GET | /api/ai-data/v1/emails/providers/klaviyo | 200 | ok |
| GET | /api/ai-data/v1/emails/providers/sendgrid/guarded-payload | 200 | ok |
| GET | /api/ai-data/v1/emails/tracking/summary | 200 | ok |
| GET | /api/admin/v1/ai/content/status | 501 | server_error |
| POST | /api/admin/v1/ai/content/run | 501 | server_error |
| GET | /api/admin/v1/ai/content/jobs | 501 | server_error |
| GET | /api/mentorship/v1/links/mentor/sample | 500 | server_error |
| GET | /api/mentorship/v1/links/user/sample | 500 | server_error |
| GET | /api/mentorship/v1/notes/sample | 500 | server_error |
| GET | /api/mentorship/v1/invoices/mentor/sample | 500 | server_error |
| GET | /api/mentorship/v1/applications/pending | 500 | server_error |

## Problem APIs

- GET /api/admin/integrations/status -> 404 (missing)
- POST /api/admin/integrations/sendgrid/configure -> 404 (missing)
- POST /api/admin/integrations/klaviyo/configure -> 404 (missing)
- POST /api/admin/email/send_test -> 404 (missing)
- POST /api/admin/email/send_bulk -> 404 (missing)
- GET /api/admin/v1/ai/content/status -> 501 (server_error)
- POST /api/admin/v1/ai/content/run -> 501 (server_error)
- GET /api/admin/v1/ai/content/jobs -> 501 (server_error)
- GET /api/mentorship/v1/links/mentor/sample -> 500 (server_error)
- GET /api/mentorship/v1/links/user/sample -> 500 (server_error)
- GET /api/mentorship/v1/notes/sample -> 500 (server_error)
- GET /api/mentorship/v1/invoices/mentor/sample -> 500 (server_error)
- GET /api/mentorship/v1/applications/pending -> 500 (server_error)

JSON: `J:/Codec - runtime version/Antigravity/careertrojan/reports/PRIORITY_ENDPOINT_PROBE_2026-02-27.json`