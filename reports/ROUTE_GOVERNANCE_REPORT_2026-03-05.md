# Route Governance Report

Generated: `2026-03-05T17:03:28.323887+00:00`
Total routes: **298**
Baseline: `FULL_ENDPOINT_INVENTORY_2026-02-27.json`

## Drift Summary

- Added routes: **23**
- Removed routes: **0**

### Added

| Method | Path |
|---|---|
| GET | /api/admin/integrations/status |
| GET | /api/auth/v1/google/callback |
| GET | /api/auth/v1/google/login |
| GET | /api/support/v1/ai/jobs |
| GET | /api/support/v1/ai/jobs/{job_id} |
| GET | /api/support/v1/ai/queue-stats |
| GET | /api/support/v1/tickets |
| GET | /api/support/v1/tickets/{ticket_id}/ai-draft |
| GET | /api/support/v1/tickets/{ticket_id}/comments |
| GET | /api/webhooks/v1/health |
| POST | /api/admin/email/send_bulk |
| POST | /api/admin/email/send_test |
| POST | /api/admin/integrations/klaviyo/configure |
| POST | /api/admin/integrations/sendgrid/configure |
| POST | /api/admin/v1/integrations/reminders/non-live |
| POST | /api/lenses/v1/composite |
| POST | /api/lenses/v1/covey |
| POST | /api/lenses/v1/spider |
| POST | /api/support/v1/tickets/{ticket_id}/approve-ai-draft |
| POST | /api/support/v1/tickets/{ticket_id}/reply |
| POST | /api/webhooks/v1/braintree |
| POST | /api/webhooks/v1/stripe |
| POST | /api/webhooks/v1/zendesk |

## Prefix Churn

| Prefix | Current | Added | Removed | Churn % | High churn |
|---|---:|---:|---:|---:|---|
| /admin/subscriptions | 1 | 0 | 0 | 0.0 | no |
| /admin/tokens | 14 | 0 | 0 | 0.0 | no |
| /api/admin | 52 | 6 | 0 | 11.54 | no |
| /api/ai-data | 22 | 0 | 0 | 0.0 | no |
| /api/analytics | 5 | 0 | 0 | 0.0 | no |
| /api/auth | 6 | 2 | 0 | 33.33 | yes |
| /api/blockers | 3 | 0 | 0 | 0.0 | no |
| /api/coaching | 10 | 0 | 0 | 0.0 | no |
| /api/credits | 9 | 0 | 0 | 0.0 | no |
| /api/data-index | 24 | 0 | 0 | 0.0 | no |
| /api/gdpr | 5 | 0 | 0 | 0.0 | no |
| /api/insights | 7 | 0 | 0 | 0.0 | no |
| /api/intelligence | 11 | 0 | 0 | 0.0 | no |
| /api/jobs | 2 | 0 | 0 | 0.0 | no |
| /api/lenses | 3 | 3 | 0 | 100.0 | yes |
| /api/mapping | 3 | 0 | 0 | 0.0 | no |
| /api/mentor | 11 | 0 | 0 | 0.0 | no |
| /api/mentorship | 23 | 0 | 0 | 0.0 | no |
| /api/ontology | 2 | 0 | 0 | 0.0 | no |
| /api/ops | 6 | 0 | 0 | 0.0 | no |
| /api/payment | 14 | 0 | 0 | 0.0 | no |
| /api/resume | 5 | 0 | 0 | 0.0 | no |
| /api/rewards | 11 | 0 | 0 | 0.0 | no |
| /api/sessions | 4 | 0 | 0 | 0.0 | no |
| /api/shared | 2 | 0 | 0 | 0.0 | no |
| /api/support | 18 | 8 | 0 | 44.44 | yes |
| /api/taxonomy | 9 | 0 | 0 | 0.0 | no |
| /api/telemetry | 1 | 0 | 0 | 0.0 | no |
| /api/touchpoints | 2 | 0 | 0 | 0.0 | no |
| /api/user | 8 | 0 | 0 | 0.0 | no |
| /api/webhooks | 4 | 4 | 0 | 100.0 | yes |
| /health | 1 | 0 | 0 | 0.0 | no |

## Header Coverage

- authorization_required: **103**
- has_required_headers: **106**
- no_explicit_required_headers: **192**
- signature_header_required: **3**

## Duplicate Semantic Routes

- `GET /admin/integrations/status` appears in:
  - `/api/admin/integrations/status`
  - `/api/admin/v1/integrations/status`
- `GET /admin/tokens/config` appears in:
  - `/admin/tokens/config`
  - `/api/admin/v1/tokens/config`
- `GET /admin/tokens/usage` appears in:
  - `/admin/tokens/usage`
  - `/api/admin/v1/tokens/usage`
- `POST /admin/email/send_bulk` appears in:
  - `/api/admin/email/send_bulk`
  - `/api/admin/v1/email/send_bulk`
- `POST /admin/email/send_test` appears in:
  - `/api/admin/email/send_test`
  - `/api/admin/v1/email/send_test`
- `POST /admin/integrations/klaviyo/configure` appears in:
  - `/api/admin/integrations/klaviyo/configure`
  - `/api/admin/v1/integrations/klaviyo/configure`
- `POST /admin/integrations/sendgrid/configure` appears in:
  - `/api/admin/integrations/sendgrid/configure`
  - `/api/admin/v1/integrations/sendgrid/configure`
