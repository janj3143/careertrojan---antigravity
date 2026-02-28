# Endpoint Topology Map

Generated from: `J:\Codec - runtime version\Antigravity\careertrojan`

## Summary
- Backend unique API paths: 206
- Admin: routes=76, api_call_paths=28, unmatched=0
- User: routes=20, api_call_paths=16, unmatched=0
- Mentor: routes=14, api_call_paths=5, unmatched=0

## Portal Route Surfaces
### Admin
- `/*`
- `/admin`
- `/admin/ai-content`
- `/admin/ai-enrich`
- `/admin/analytics`
- `/admin/api-integration`
- `/admin/batch`
- `/admin/blocker-test`
- `/admin/career-patterns`
- `/admin/coaching-insights`
- `/admin/competitive`
- `/admin/compliance`
- `/admin/connectivity`
- `/admin/contact`
- `/admin/email`
- `/admin/exa-web`
- `/admin/intel-hub`
- `/admin/job-cloud`
- `/admin/job-title-ai`
- `/admin/login`
- `/admin/logs`
- `/admin/market-intel`
- `/admin/mentor-review`
- `/admin/mentors`
- `/admin/model-training`
- `/admin/ops/about`
- `/admin/ops/admin-audit`
- `/admin/ops/api-explorer`
- `/admin/ops/backup`
- `/admin/ops/config`
- `/admin/ops/diagnostics`
- `/admin/ops/exports`
- `/admin/ops/logs`
- `/admin/ops/notifications`
- `/admin/ops/route-map`
- `/admin/parser`
- `/admin/pipeline-ops`
- `/admin/portal-entry`
- `/admin/requirements`
- `/admin/settings`
- `/admin/status`
- `/admin/support-ops`
- `/admin/tokens`
- `/admin/tokens-alt`
- `/admin/tools/about`
- `/admin/tools/admin-audit`
- `/admin/tools/api-explorer`
- `/admin/tools/backup`
- `/admin/tools/blob`
- `/admin/tools/config`
- `/admin/tools/data-health`
- `/admin/tools/datasets`
- `/admin/tools/diagnostics`
- `/admin/tools/email-analytics`
- `/admin/tools/email-capture`
- `/admin/tools/enrichment`
- `/admin/tools/evaluation`
- `/admin/tools/exports`
- `/admin/tools/fairness`
- `/admin/tools/job-index`
- `/admin/tools/keywords`
- `/admin/tools/logs-viewer`
- `/admin/tools/models`
- `/admin/tools/notifications`
- `/admin/tools/parser-runs`
- `/admin/tools/phrases`
- `/admin/tools/prompts`
- `/admin/tools/queue`
- `/admin/tools/resume-viewer`
- `/admin/tools/route-map`
- `/admin/tools/scoring`
- `/admin/tools/taxonomy`
- `/admin/tools/user-audit`
- `/admin/unified-analytics`
- `/admin/users`
- `/admin/web-intel`

### User
- `/`
- `/coaching`
- `/consolidation`
- `/dashboard`
- `/dual-career`
- `/glossary`
- `/jobs/swipe`
- `/login`
- `/mentor/apply`
- `/mentorship`
- `/mobile/cv`
- `/payment`
- `/profile`
- `/quick`
- `/register`
- `/resume`
- `/rewards`
- `/umarketu`
- `/verify`
- `/visuals`

### Mentor
- `/*`
- `/mentor`
- `/mentor/agreements`
- `/mentor/ai-assistant`
- `/mentor/calendar`
- `/mentor/communication`
- `/mentor/dashboard`
- `/mentor/financials`
- `/mentor/guardian-feedback`
- `/mentor/login`
- `/mentor/mentee-progress`
- `/mentor/my-agreements`
- `/mentor/packages`
- `/mentor/services`

## Frontend API Call Mismatches
### Admin
- None detected

### User
- None detected

### Mentor
- None detected

## Backend Router Inventory
### `services/backend_api/routers/admin.py`
- `GET /api/admin/v1/ai/content/jobs`
- `GET /api/admin/v1/ai/content/status`
- `GET /api/admin/v1/ai/enrichment/jobs`
- `GET /api/admin/v1/ai/enrichment/status`
- `GET /api/admin/v1/batch/jobs`
- `GET /api/admin/v1/batch/status`
- `GET /api/admin/v1/compliance/audit/events`
- `GET /api/admin/v1/compliance/summary`
- `GET /api/admin/v1/dashboard/snapshot`
- `GET /api/admin/v1/email/jobs`
- `GET /api/admin/v1/email/status`
- `GET /api/admin/v1/parsers/jobs`
- `GET /api/admin/v1/parsers/status`
- `GET /api/admin/v1/system/activity`
- `GET /api/admin/v1/system/health`
- `GET /api/admin/v1/tokens/users/{user_id}/ledger`
- `GET /api/admin/v1/user_subscriptions`
- `GET /api/admin/v1/users`
- `GET /api/admin/v1/users/metrics`
- `GET /api/admin/v1/users/security`
- `GET /api/admin/v1/users/{user_id}`
- `POST /api/admin/v1/ai/content/run`
- `POST /api/admin/v1/ai/enrichment/run`
- `POST /api/admin/v1/batch/run`
- `POST /api/admin/v1/email/sync`
- `POST /api/admin/v1/parsers/run`
- `PUT /api/admin/v1/users/{user_id}/disable`
- `PUT /api/admin/v1/users/{user_id}/plan`

### `services/backend_api/routers/admin_abuse.py`
- `GET /api/admin/v1/abuse/queue`

### `services/backend_api/routers/admin_parsing.py`
- `GET /api/admin/v1/parsing/parse`
- `GET /api/admin/v1/parsing/parse/{parse_id}`
- `POST /api/admin/v1/parsing/parse`

### `services/backend_api/routers/admin_tokens.py`
- `GET /api/admin/v1/tokens/config`
- `GET /api/admin/v1/tokens/usage`
- `PUT /api/admin/v1/tokens/config`

### `services/backend_api/routers/ai_data.py`
- `GET /api/ai-data/v1/automated/candidates`
- `GET /api/ai-data/v1/companies`
- `GET /api/ai-data/v1/email_extracted`
- `GET /api/ai-data/v1/emails`
- `GET /api/ai-data/v1/emails/diagnostics`
- `GET /api/ai-data/v1/emails/providers/{provider}`
- `GET /api/ai-data/v1/emails/summary`
- `GET /api/ai-data/v1/emails/tracking`
- `GET /api/ai-data/v1/emails/tracking/summary`
- `GET /api/ai-data/v1/job_descriptions`
- `GET /api/ai-data/v1/job_titles`
- `GET /api/ai-data/v1/locations`
- `GET /api/ai-data/v1/metadata`
- `GET /api/ai-data/v1/normalized`
- `GET /api/ai-data/v1/parsed_resumes`
- `GET /api/ai-data/v1/parsed_resumes/{doc_id}`
- `GET /api/ai-data/v1/parser/ingestion-status`
- `GET /api/ai-data/v1/status`
- `GET /api/ai-data/v1/user_data/files`
- `POST /api/ai-data/v1/emails/tracking`

### `services/backend_api/routers/analytics.py`
- `GET /api/analytics/v1/dashboard`
- `GET /api/analytics/v1/recent_jobs`
- `GET /api/analytics/v1/recent_resumes`
- `GET /api/analytics/v1/statistics`
- `GET /api/analytics/v1/system_health`

### `services/backend_api/routers/anti_gaming.py`
- `POST /api/admin/v1/anti-gaming/check`

### `services/backend_api/routers/auth.py`
- `POST /api/auth/v1/2fa/generate`
- `POST /api/auth/v1/2fa/verify`
- `POST /api/auth/v1/login`
- `POST /api/auth/v1/register`

### `services/backend_api/routers/blockers.py`
- `GET /api/blockers/v1/user/{user_id}`
- `POST /api/blockers/v1/detect`
- `POST /api/blockers/v1/improvement-plans/generate`

### `services/backend_api/routers/coaching.py`
- `GET /api/coaching/v1/health`
- `GET /api/coaching/v1/history`
- `GET /api/coaching/v1/learning/profile`
- `POST /api/coaching/v1/answers/review`
- `POST /api/coaching/v1/bundle`
- `POST /api/coaching/v1/learning/feedback`
- `POST /api/coaching/v1/plan/90day`
- `POST /api/coaching/v1/questions/generate`
- `POST /api/coaching/v1/role/detect`
- `POST /api/coaching/v1/stories/generate`

### `services/backend_api/routers/credits.py`
- `GET /api/credits/v1/actions`
- `GET /api/credits/v1/balance`
- `GET /api/credits/v1/can-perform/{action_id}`
- `GET /api/credits/v1/health`
- `GET /api/credits/v1/plans`
- `GET /api/credits/v1/usage`
- `POST /api/credits/v1/consume`
- `POST /api/credits/v1/teaser`
- `POST /api/credits/v1/upgrade/{plan_tier}`

### `services/backend_api/routers/gdpr.py`
- `DELETE /api/gdpr/v1/delete-account`
- `GET /api/gdpr/v1/audit-log`
- `GET /api/gdpr/v1/consent`
- `GET /api/gdpr/v1/export`
- `POST /api/gdpr/v1/consent`

### `services/backend_api/routers/insights.py`
- `GET /api/insights/v1/graph`
- `GET /api/insights/v1/quadrant`
- `GET /api/insights/v1/skills/radar`
- `GET /api/insights/v1/terms/cloud`
- `GET /api/insights/v1/terms/cooccurrence`
- `GET /api/insights/v1/visuals`
- `POST /api/insights/v1/cohort/resolve`

### `services/backend_api/routers/intelligence.py`
- `GET /api/intelligence/v1/company/registry`
- `GET /api/intelligence/v1/market`
- `GET /api/intelligence/v1/pipeline/ops-summary`
- `GET /api/intelligence/v1/support/status`
- `POST /api/intelligence/v1/company/briefing`
- `POST /api/intelligence/v1/company/extract`
- `POST /api/intelligence/v1/enrich`
- `POST /api/intelligence/v1/stats/descriptive`
- `POST /api/intelligence/v1/stats/regression`

### `services/backend_api/routers/jobs.py`
- `GET /api/jobs/v1/index`
- `GET /api/jobs/v1/search`

### `services/backend_api/routers/logs.py`
- `GET /api/admin/v1/logs/tail`

### `services/backend_api/routers/mapping.py`
- `GET /api/mapping/v1/endpoints`
- `GET /api/mapping/v1/graph`
- `GET /api/mapping/v1/registry`

### `services/backend_api/routers/mentor.py`
- `DELETE /api/mentor/v1/{mentor_profile_id}/packages/{package_id}`
- `GET /api/mentor/v1/health`
- `GET /api/mentor/v1/list`
- `GET /api/mentor/v1/profile-by-user/{user_id}`
- `GET /api/mentor/v1/{mentor_profile_id}/dashboard-stats`
- `GET /api/mentor/v1/{mentor_profile_id}/packages`
- `GET /api/mentor/v1/{mentor_profile_id}/packages/{package_id}`
- `GET /api/mentor/v1/{mentor_profile_id}/profile`
- `POST /api/mentor/v1/{mentor_profile_id}/packages`
- `PUT /api/mentor/v1/{mentor_profile_id}/availability`
- `PUT /api/mentor/v1/{mentor_profile_id}/packages/{package_id}`

### `services/backend_api/routers/mentorship.py`
- `GET /api/mentorship/v1/applications/pending`
- `GET /api/mentorship/v1/documents/{doc_id}`
- `GET /api/mentorship/v1/health`
- `GET /api/mentorship/v1/invoices/mentor/{mentor_id}`
- `GET /api/mentorship/v1/links/mentor/{mentor_id}`
- `GET /api/mentorship/v1/links/user/{user_id}`
- `GET /api/mentorship/v1/notes/{link_id}`
- `GET /api/mentorship/v1/summary`
- `PATCH /api/mentorship/v1/links/{link_id}/status`
- `PATCH /api/mentorship/v1/notes/{note_id}`
- `POST /api/mentorship/v1/applications`
- `POST /api/mentorship/v1/applications/{application_id}/approve`
- `POST /api/mentorship/v1/applications/{application_id}/reject`
- `POST /api/mentorship/v1/documents`
- `POST /api/mentorship/v1/documents/{doc_id}/reject`
- `POST /api/mentorship/v1/documents/{doc_id}/sign`
- `POST /api/mentorship/v1/invoices`
- `POST /api/mentorship/v1/invoices/{invoice_id}/confirm-completion`
- `POST /api/mentorship/v1/invoices/{invoice_id}/dispute`
- `POST /api/mentorship/v1/invoices/{invoice_id}/mark-paid`
- `POST /api/mentorship/v1/invoices/{invoice_id}/service-delivered`
- `POST /api/mentorship/v1/links`
- `POST /api/mentorship/v1/notes`

### `services/backend_api/routers/ontology.py`
- `GET /api/ontology/v1/phrases`
- `GET /api/ontology/v1/phrases/summary`

### `services/backend_api/routers/ops.py`
- `GET /api/ops/v1/processing/status`
- `GET /api/ops/v1/stats/public`
- `GET /api/ops/v1/tokens/config`
- `POST /api/ops/v1/anti-gaming/check`
- `POST /api/ops/v1/logs/lock`
- `POST /api/ops/v1/processing/start`

### `services/backend_api/routers/payment.py`
- `DELETE /api/payment/v1/methods/{token}`
- `GET /api/payment/v1/client-token`
- `GET /api/payment/v1/gateway-info`
- `GET /api/payment/v1/health`
- `GET /api/payment/v1/history`
- `GET /api/payment/v1/methods`
- `GET /api/payment/v1/plans`
- `GET /api/payment/v1/plans/{plan_id}`
- `GET /api/payment/v1/subscription`
- `GET /api/payment/v1/transactions/{transaction_id}`
- `POST /api/payment/v1/cancel`
- `POST /api/payment/v1/methods`
- `POST /api/payment/v1/process`
- `POST /api/payment/v1/refund/{transaction_id}`

### `services/backend_api/routers/resume.py`
- `GET /api/resume/v1/`
- `GET /api/resume/v1/{resume_id}`
- `POST /api/resume/v1/enrich`
- `POST /api/resume/v1/parse`
- `POST /api/resume/v1/upload`

### `services/backend_api/routers/rewards.py`
- `GET /api/rewards/v1/health`
- `GET /api/rewards/v1/leaderboard`
- `GET /api/rewards/v1/ownership-stats`
- `GET /api/rewards/v1/referral`
- `GET /api/rewards/v1/rewards`
- `GET /api/rewards/v1/rewards/available`
- `GET /api/rewards/v1/suggestions`
- `POST /api/rewards/v1/referral/claim`
- `POST /api/rewards/v1/rewards/redeem`
- `POST /api/rewards/v1/suggestions`

### `services/backend_api/routers/sessions.py`
- `GET /api/sessions/v1/consolidated/{user_id}`
- `GET /api/sessions/v1/summary/{user_id}`
- `GET /api/sessions/v1/sync-status`
- `POST /api/sessions/v1/log`

### `services/backend_api/routers/shared.py`
- `GET /api/shared/v1/health`
- `GET /api/shared/v1/health/deep`

### `services/backend_api/routers/support.py`
- `GET /api/support/v1/health`
- `GET /api/support/v1/status`
- `GET /api/support/v1/widget-config`
- `GET /api/support/v1/wiring-test`
- `POST /api/support/v1/token`

### `services/backend_api/routers/taxonomy.py`
- `GET /api/taxonomy/v1/industries`
- `GET /api/taxonomy/v1/industries/{high_level}/subindustries`
- `GET /api/taxonomy/v1/job-titles/infer-industries`
- `GET /api/taxonomy/v1/job-titles/metadata`
- `GET /api/taxonomy/v1/job-titles/naics-mapping`
- `GET /api/taxonomy/v1/job-titles/search`
- `GET /api/taxonomy/v1/naics/search`
- `GET /api/taxonomy/v1/naics/title`
- `GET /api/taxonomy/v1/summary`

### `services/backend_api/routers/telemetry.py`
- `GET /api/telemetry/v1/status`

### `services/backend_api/routers/touchpoints.py`
- `GET /api/touchpoints/v1/evidence`
- `GET /api/touchpoints/v1/touchnots`

### `services/backend_api/routers/user.py`
- `GET /api/user/v1/activity`
- `GET /api/user/v1/matches/summary`
- `GET /api/user/v1/me`
- `GET /api/user/v1/profile`
- `GET /api/user/v1/resume/latest`
- `GET /api/user/v1/sessions/summary`
- `GET /api/user/v1/stats`
- `PUT /api/user/v1/profile`
