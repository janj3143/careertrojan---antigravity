# CareerTrojan Full Wiring Map

Repository root: `J:\Codec - runtime version\Antigravity\careertrojan`

## Discovery summary

- Frontend API calls discovered: **34**
- Backend FastAPI routes discovered: **333**
- Frontend calls matched to backend routes: **23**
- Matched flows with backend AI signals: **7**

## 1. Frontend -> backend matched flows

| Portal | Frontend File | Line | Method | Frontend Path | Backend Match | AI Signals | Likely Services |
|---|---|---:|---|---|---|---|---|
| admin | `apps\admin\src\lib\api.ts` | 13 | GET | `/admin/system/health` | `/health`<br>`/health` | - | - |
| admin | `apps\admin\src\pages\AIEnrichment.tsx` | 36 | GET | `/api/admin/v1/ai/enrichment/jobs` | `/api/admin/v1/ai/enrichment/jobs` | - | router.get |
| admin | `apps\admin\src\pages\AIEnrichment.tsx` | 37 | GET | `/api/admin/v1/ai/enrichment/status` | `/api/admin/v1/ai/enrichment/status` | ai | router.get |
| admin | `apps\admin\src\pages\AIEnrichment.tsx` | 58 | POST | `/api/admin/v1/ai/enrichment/run` | `/api/admin/v1/ai/enrichment/run` | - | router.post |
| admin | `apps\admin\src\pages\APIIntegration.tsx` | 34 | GET | `/api/admin/v1/integrations/status` | `/api/admin/v1/integrations/status` | - | router.get |
| admin | `apps\admin\src\pages\APIIntegration.tsx` | 76 | POST | `/api/admin/v1/integrations/reminders/non-live` | `/api/admin/v1/integrations/reminders/non-live` | ai | router.post |
| admin | `apps\admin\src\pages\AdminHome.tsx` | 26 | GET | `/api/admin/v1/dashboard/snapshot` | `/api/admin/v1/dashboard/snapshot` | ai, model | router.get |
| admin | `apps\admin\src\pages\AdminLogin.tsx` | 24 | POST | `/api/auth/v1/login` | `/api/auth/v1/login` | - | router.post |
| admin | `apps\admin\src\pages\AdminPipelineOps.tsx` | 25 | GET | `/api/intelligence/v1/pipeline/ops-summary` | `/api/intelligence/v1/pipeline/ops-summary` | - | router.get |
| admin | `apps\admin\src\pages\DataParser.tsx` | 28 | POST | `/api/admin/v1/parsing/parse` | `/api/admin/v1/parsing/parse` | - | client.post, httpx.AsyncClient, router.post |
| admin | `apps\admin\src\pages\EmailIntegration.tsx` | 30 | GET | `/api/ai-data/v1/emails/summary` | `/api/ai-data/v1/emails/summary` | ai | router.get |
| admin | `apps\admin\src\pages\EmailIntegration.tsx` | 63 | GET | `/api/ai-data/v1/emails/tracking/summary` | `/api/ai-data/v1/emails/tracking/summary` | ai | router.get |
| admin | `apps\admin\src\pages\EmailIntegration.tsx` | 91 | POST | `/api/ai-data/v1/emails/tracking` | `/api/ai-data/v1/emails/tracking` | ai | router.post |
| admin | `apps\admin\src\pages\MarketIntelligence.tsx` | 23 | GET | `/api/intelligence/v1/market` | `/api/intelligence/v1/market` | - | router.get |
| admin | `apps\admin\src\pages\MentorManagement.tsx` | 27 | GET | `/api/mentorship/v1/applications/pending` | `/api/mentorship/v1/applications/pending` | - | router.get, service.get_pending_applications |
| admin | `apps\admin\src\pages\ServiceStatus.tsx` | 35 | GET | `/api/admin/v1/system/health` | `/health`<br>`/api/admin/v1/system/health`<br>`/health` | - | router.get |
| admin | `apps\admin\src\pages\ServiceStatus.tsx` | 36 | GET | `/api/admin/v1/system/activity` | `/api/admin/v1/system/activity` | - | router.get |
| admin | `apps\admin\src\pages\TokenManagement.tsx` | 34 | GET | `/api/admin/v1/tokens/config` | `/api/admin/v1/tokens/config` | - | router.get |
| admin | `apps\admin\src\pages\TokenManagement.tsx` | 35 | GET | `/api/admin/v1/tokens/usage` | `/api/admin/v1/tokens/usage` | - | router.get |
| admin | `apps\admin\src\pages\UserManagement.tsx` | 27 | GET | `/api/admin/v1/users` | `/api/admin/v1/users` | - | router.get |
| mentor | `apps\mentor\src\pages\Create Agreement\Create Agreement\src\services\chatService.ts` | 164 | GET | `/health` | `/health`<br>`/api/admin/v1/system/health`<br>`/api/coaching/v1/health`<br>`/api/credits/v1/health` | ai | braintree_service.is_configured, get_ai_data_index_service, router.get, service.get_state |
| mentor | `apps\mentor\src\pages\MentorLogin.tsx` | 20 | POST | `/api/auth/v1/login` | `/api/auth/v1/login` | - | router.post |
| mentor | `apps\mentor\src\pages\Set up Sessions\Setup Sessions\supabase\functions\server\index.tsx` | 32 | GET | `/make-server-f4611869/health` | `/health`<br>`/health` | - | - |

## 2. Unmatched frontend API calls

| Portal | File | Line | Method | Path | Source | Component |
|---|---|---:|---|---|---|---|
| mentor | `apps\mentor\src\pages\Create Agreement\Create Agreement\src\services\chatService.ts` | 105 | POST | `/https:/api.openai.com/v1/chat/completions` | fetch | - |
| mentor | `apps\mentor\src\pages\Financial Dashboard\Financial Dashboard\src\app\App.tsx` | 45 | GET | `/api/mentorship/v1/invoices` | fetch | - |
| mentor | `apps\mentor\src\pages\Set up Sessions\Setup Sessions\supabase\functions\server\index.tsx` | 39 | POST | `/make-server-f4611869/auth/signup` | app | - |
| mentor | `apps\mentor\src\pages\Set up Sessions\Setup Sessions\supabase\functions\server\index.tsx` | 109 | POST | `/make-server-f4611869/auth/verify-2fa` | app | - |
| mentor | `apps\mentor\src\pages\Set up Sessions\Setup Sessions\supabase\functions\server\index.tsx` | 151 | POST | `/make-server-f4611869/auth/check-2fa` | app | - |
| mentor | `apps\mentor\src\pages\Set up Sessions\Setup Sessions\supabase\functions\server\index.tsx` | 180 | POST | `/make-server-f4611869/auth/validate-2fa` | app | - |
| mentor | `apps\mentor\src\pages\Set up Sessions\Setup Sessions\supabase\functions\server\index.tsx` | 227 | GET | `/make-server-f4611869/sessions` | app | - |
| mentor | `apps\mentor\src\pages\Set up Sessions\Setup Sessions\supabase\functions\server\index.tsx` | 261 | POST | `/make-server-f4611869/sessions` | app | - |
| mentor | `apps\mentor\src\pages\Set up Sessions\Setup Sessions\supabase\functions\server\index.tsx` | 312 | PATCH | `/make-server-f4611869/sessions/:id` | app | - |
| mentor | `apps\mentor\src\pages\Set up Sessions\Setup Sessions\supabase\functions\server\index.tsx` | 358 | DELETE | `/make-server-f4611869/sessions/:id` | app | - |
| mentor | `apps\mentor\src\pages\Set up Sessions\Setup Sessions\supabase\functions\server\index.tsx` | 396 | GET | `/make-server-f4611869/activities` | app | - |

## 3. Backend routes with AI signals

### `GET /api/admin/v1/ai/enrichment/status`
- File: `services\backend_api\routers\admin.py`
- Function: `enrichment_status`
- AI signals: ai
- Likely services: router.get
- Attribute calls: ai_data_root.is_dir, datetime.fromtimestamp, datetime.fromtimestamp.isoformat, datetime.utcnow, datetime.utcnow.isoformat, entry.glob, entry.is_dir, interactions_dir.is_dir, interactions_dir.iterdir, os.path.getmtime, os.path.join, os.walk, router.get

### `GET /api/admin/v1/compliance/audit/events`
- File: `services\backend_api\routers\admin.py`
- Function: `audit_events`
- AI signals: model
- Likely services: router.get
- Attribute calls: db.query, db.query.order_by, e.created_at.isoformat, models.AuditLog.created_at.desc, q.filter, q.limit, q.limit.all, router.get

### `GET /api/admin/v1/dashboard/snapshot`
- File: `services\backend_api\routers\admin.py`
- Function: `dashboard_snapshot`
- AI signals: ai, model
- Likely services: router.get
- Attribute calls: a.created_at.isoformat, ai_data_root.is_dir, datetime.utcnow, datetime.utcnow.isoformat, db.query, db.query.filter, db.query.filter.scalar, db.query.order_by, db.query.order_by.limit, db.query.order_by.limit.all, db.query.scalar, func.count, models.AuditLog.created_at.desc, router.get

### `POST /api/admin/v1/email/send_bulk`
- File: `services\backend_api\routers\admin.py`
- Function: `send_bulk_email`
- AI signals: ai
- Likely services: router.post
- Attribute calls: _email_dispatch_log.append, datetime.utcnow, datetime.utcnow.isoformat, payload.get, router.post, str.strip

### `POST /api/admin/v1/email/send_test`
- File: `services\backend_api\routers\admin.py`
- Function: `send_test_email`
- AI signals: ai
- Likely services: router.post
- Attribute calls: _email_dispatch_log.append, datetime.utcnow, datetime.utcnow.isoformat, payload.get, router.post, str.strip

### `POST /api/admin/v1/integrations/reminders/non-live`
- File: `services\backend_api\routers\admin.py`
- Function: `send_non_live_api_reminder`
- AI signals: ai
- Likely services: router.post
- Attribute calls: _email_dispatch_log.append, datetime.utcnow, datetime.utcnow.isoformat, modes.get, os.getenv, payload.get, provider.title, provider_status.get, router.post, str.strip, str.strip.lower

### `GET /api/admin/v1/payments/disputes`
- File: `services\backend_api\routers\admin.py`
- Function: `payment_disputes`
- AI signals: model
- Likely services: router.get
- Attribute calls: amount_by_type.items, datetime.utcnow, db.query, db.query.filter, models.PaymentTransaction.created_at.desc, models.PaymentTransaction.transaction_type.in_, query.filter, query.order_by, query.order_by.limit, query.order_by.limit.all, records.append, router.get, row.created_at.isoformat

### `POST /api/admin/email/send_bulk`
- File: `services\backend_api\routers\admin_legacy.py`
- Function: `send_bulk_email_legacy`
- AI signals: ai
- Likely services: router.post
- Attribute calls: admin_v1.send_bulk_email, router.post

### `POST /api/admin/email/send_test`
- File: `services\backend_api\routers\admin_legacy.py`
- Function: `send_test_email_legacy`
- AI signals: ai
- Likely services: router.post
- Attribute calls: admin_v1.send_test_email, router.post

### `GET /api/ai-data/v1/email_extracted`
- File: `services\backend_api\routers\ai_data.py`
- Function: `get_email_extracted`
- AI signals: ai
- Likely services: router.get
- Attribute calls: router.get

### `GET /api/ai-data/v1/emails`
- File: `services\backend_api\routers\ai_data.py`
- Function: `get_emails`
- AI signals: ai
- Likely services: router.get
- Attribute calls: router.get

### `GET /api/ai-data/v1/emails/diagnostics`
- File: `services\backend_api\routers\ai_data.py`
- Function: `get_emails_diagnostics`
- AI signals: ai
- Likely services: router.get
- Attribute calls: router.get

### `GET /api/ai-data/v1/emails/summary`
- File: `services\backend_api\routers\ai_data.py`
- Function: `get_emails_summary`
- AI signals: ai
- Likely services: router.get
- Attribute calls: router.get

### `POST /api/ai-data/v1/emails/tracking`
- File: `services\backend_api\routers\ai_data.py`
- Function: `create_emails_tracking_record`
- AI signals: ai
- Likely services: router.post
- Attribute calls: router.post

### `GET /api/ai-data/v1/emails/tracking`
- File: `services\backend_api\routers\ai_data.py`
- Function: `get_emails_tracking`
- AI signals: ai
- Likely services: router.get
- Attribute calls: router.get

### `GET /api/ai-data/v1/emails/tracking/reroute-targets`
- File: `services\backend_api\routers\ai_data.py`
- Function: `get_emails_tracking_reroute_targets`
- AI signals: ai
- Likely services: router.get
- Attribute calls: router.get

### `GET /api/ai-data/v1/emails/tracking/summary`
- File: `services\backend_api\routers\ai_data.py`
- Function: `get_emails_tracking_summary`
- AI signals: ai
- Likely services: router.get
- Attribute calls: router.get

### `GET /api/ai-data/v1/status`
- File: `services\backend_api\routers\ai_data.py`
- Function: `get_ai_data_status`
- AI signals: ai
- Likely services: router.get
- Attribute calls: AI_DATA_PATH.absolute, dir_path.exists, dir_path.iterdir, router.get

### `GET /api/analytics/v1/dashboard`
- File: `services\backend_api\routers\analytics.py`
- Function: `get_dashboard_data`
- AI signals: model
- Likely services: router.get
- Attribute calls: d.is_dir, datetime.fromtimestamp, datetime.fromtimestamp.isoformat, datetime.utcnow, datetime.utcnow.isoformat, json.load, json_file.stat, logger.warning, models_path.exists, models_path.iterdir, recent_resumes.append, resume_path.exists, resume_path.glob, router.get

### `GET /api/analytics/v1/system_health`
- File: `services\backend_api\routers\analytics.py`
- Function: `get_system_health`
- AI signals: ai, model
- Likely services: router.get
- Attribute calls: AI_DATA_PATH.exists, d.is_dir, datetime.utcnow, datetime.utcnow.isoformat, dir_path.exists, dir_path.glob, models_path.exists, models_path.iterdir, router.get

### `POST /api/auth/v1/register`
- File: `services\backend_api\routers\auth.py`
- Function: `register`
- AI signals: model
- Likely services: router.post
- Attribute calls: db.add, db.commit, db.query, db.query.filter, db.query.filter.first, db.refresh, models.User, router.post, security.get_password_hash

### `GET /career-compass/routes`
- File: `services\backend_api\routers\career_compass.py`
- Function: `career_compass_routes`
- AI signals: vector
- Likely services: router.get
- Attribute calls: natural_next_steps.append, router.get, strategic_stretch.append, too_far_for_now.append, user_vector.get

### `POST /career-compass/spider-overlay`
- File: `services\backend_api\routers\career_compass.py`
- Function: `career_compass_spider_overlay`
- AI signals: vector
- Likely services: router.post
- Attribute calls: payload.role_text.strip, router.post

### `GET /api/coaching/v1/history`
- File: `services\backend_api\routers\coaching.py`
- Function: `get_coaching_history`
- AI signals: model
- Likely services: router.get
- Attribute calls: db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.limit, db.query.filter.order_by.limit.all, entry.created_at.isoformat, history.append, json.loads, models.Interaction.action_type.in_, models.Interaction.created_at.desc, router.get

### `POST /api/coaching/v1/profile/reflect`
- File: `services\backend_api\routers\coaching.py`
- Function: `profile_coach_reflect`
- AI signals: ai
- Likely services: router.post
- Attribute calls: payload.user_message.strip, router.post

### `GET /api/data-index/v1/ai-data/categories`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_ai_data_categories`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.get, service.get_ai_data_summary
- Attribute calls: router.get, service.get_ai_data_summary

### `GET /api/data-index/v1/ai-data/industries`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_top_industries`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.get, service.get_ai_data_summary
- Attribute calls: router.get, service.get_ai_data_summary, summary.top_industries.items

### `GET /api/data-index/v1/ai-data/industries/search`
- File: `services\backend_api\routers\data_index.py`
- Function: `search_industries`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.get, service.search_industries
- Attribute calls: router.get, service.search_industries

### `GET /api/data-index/v1/ai-data/locations`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_top_locations`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.get, service.get_ai_data_summary
- Attribute calls: router.get, service.get_ai_data_summary, summary.top_locations.items

### `GET /api/data-index/v1/ai-data/locations/search`
- File: `services\backend_api\routers\data_index.py`
- Function: `search_locations`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.get, service.search_locations
- Attribute calls: router.get, service.search_locations

### `GET /api/data-index/v1/ai-data/skills`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_top_skills`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.get, service.get_ai_data_summary
- Attribute calls: router.get, service.get_ai_data_summary, summary.top_skills.items

### `GET /api/data-index/v1/ai-data/skills/search`
- File: `services\backend_api\routers\data_index.py`
- Function: `search_skills`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.get, service.search_skills
- Attribute calls: router.get, service.search_skills

### `GET /api/data-index/v1/ai-data/summary`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_ai_data_summary`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.get, service.get_ai_data_summary
- Attribute calls: router.get, service.get_ai_data_summary

### `GET /api/data-index/v1/dependencies`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_optional_dependencies`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.get, service._detect_optional_dependencies
- Attribute calls: deps.get, router.get, service._detect_optional_dependencies

### `GET /api/data-index/v1/files/by-category/{category}`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_files_by_category`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.get, service._state.file_manifest.values
- Attribute calls: files.append, files.sort, router.get, service._state.file_manifest.values, x.get

### `GET /api/data-index/v1/files/manifest-stats`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_file_manifest_stats`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.get, service.get_file_manifest_stats
- Attribute calls: router.get, service.get_file_manifest_stats

### `GET /api/data-index/v1/files/new-data-summary`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_new_data_summary`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.get, service.get_new_data_summary
- Attribute calls: router.get, service.get_new_data_summary

### `GET /api/data-index/v1/files/since`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_files_since_timestamp`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.get, service.get_files_since
- Attribute calls: router.get, service.get_files_since

### `GET /api/data-index/v1/health`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_index_health`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.get, service.get_state
- Attribute calls: issues.append, router.get, service.get_state, warnings.append

### `POST /api/data-index/v1/index/ai-data`
- File: `services\backend_api\routers\data_index.py`
- Function: `trigger_ai_data_index`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.post, service.index_ai_data
- Attribute calls: router.post, service.index_ai_data

### `POST /api/data-index/v1/index/full`
- File: `services\backend_api\routers\data_index.py`
- Function: `trigger_full_index`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.post, service.full_index
- Attribute calls: router.post, service.full_index

### `POST /api/data-index/v1/index/incremental`
- File: `services\backend_api\routers\data_index.py`
- Function: `trigger_incremental_index`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.post, service.incremental_index
- Attribute calls: router.post, service.incremental_index

### `POST /api/data-index/v1/index/parser`
- File: `services\backend_api\routers\data_index.py`
- Function: `trigger_parser_index`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.post, service.index_parser_sources
- Attribute calls: router.post, service.index_parser_sources

### `GET /api/data-index/v1/parser/file-types`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_parser_file_types`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.get, service.get_parser_summary
- Attribute calls: router.get, service.get_parser_summary

### `GET /api/data-index/v1/parser/runs`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_parser_runs`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.get, service.get_parser_run_history
- Attribute calls: router.get, service.get_parser_run_history

### `POST /api/data-index/v1/parser/runs`
- File: `services\backend_api\routers\data_index.py`
- Function: `record_parser_run`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.post, service.record_parser_run
- Attribute calls: router.post, service.record_parser_run

### `GET /api/data-index/v1/parser/status`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_parser_status`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.get, service.get_parser_summary
- Attribute calls: router.get, service.get_parser_summary

### `GET /api/data-index/v1/parser/summary`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_parser_summary`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.get, service.get_parser_summary
- Attribute calls: router.get, service.get_parser_summary

### `GET /api/data-index/v1/status`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_index_status`
- AI signals: ai
- Likely services: get_ai_data_index_service, router.get, service.get_state
- Attribute calls: router.get, service.get_state

### `GET /api/gdpr/v1/audit-log`
- File: `services\backend_api\routers\gdpr.py`
- Function: `my_audit_log`
- AI signals: model
- Likely services: router.get
- Attribute calls: db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.limit, db.query.filter.order_by.limit.all, e.created_at.isoformat, models.AuditLog.created_at.desc, router.get

### `GET /api/gdpr/v1/consent`
- File: `services\backend_api\routers\gdpr.py`
- Function: `get_consent`
- AI signals: model
- Likely services: router.get
- Attribute calls: db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.all, models.ConsentRecord.created_at.desc, r.created_at.isoformat, r.revoked_at.isoformat, router.get

### `POST /api/gdpr/v1/consent`
- File: `services\backend_api\routers\gdpr.py`
- Function: `grant_consent`
- AI signals: model
- Likely services: router.post
- Attribute calls: db.add, db.commit, models.ConsentRecord, request.headers.get, router.post

### `DELETE /api/gdpr/v1/delete-account`
- File: `services\backend_api\routers\gdpr.py`
- Function: `delete_my_account`
- AI signals: model
- Likely services: router.delete
- Attribute calls: db.commit, db.query, db.query.filter, db.query.filter.delete, logger.info, models.MentorNote.link_id.in_, os.getcwd, os.path.isdir, os.path.join, router.delete

### `GET /api/gdpr/v1/export`
- File: `services\backend_api\routers\gdpr.py`
- Function: `export_my_data`
- AI signals: model
- Likely services: router.get
- Attribute calls: c.created_at.isoformat, c.revoked_at.isoformat, current_user.created_at.isoformat, datetime.utcnow, datetime.utcnow.isoformat, db.add, db.commit, db.query, db.query.filter, db.query.filter.all, db.query.filter.order_by, db.query.filter.order_by.limit, db.query.filter.order_by.limit.all, i.created_at.isoformat

### `POST /api/intelligence/v1/enrich`
- File: `services\backend_api\routers\intelligence.py`
- Function: `enrich_resume`
- AI signals: model
- Likely services: router.post
- Attribute calls: models.split, router.post

### `POST /api/intelligence/v1/stats/descriptive`
- File: `services\backend_api\routers\intelligence.py`
- Function: `get_stats`
- AI signals: engine
- Likely services: engine.descriptive_stats, router.post
- Attribute calls: engine.descriptive_stats, router.post

### `POST /api/intelligence/v1/stats/regression`
- File: `services\backend_api\routers\intelligence.py`
- Function: `regression`
- AI signals: engine, regression
- Likely services: engine.linear_regression, router.post
- Attribute calls: engine.linear_regression, np.corrcoef, np.polyfit, router.post

### `GET /api/jobs/v1/index`
- File: `services\backend_api\routers\jobs.py`
- Function: `get_job_index`
- AI signals: ai
- Likely services: router.get
- Attribute calls: router.get

### `GET /api/jobs/v1/search`
- File: `services\backend_api\routers\jobs.py`
- Function: `search_jobs`
- AI signals: ai
- Likely services: router.get
- Attribute calls: router.get

### `POST /api/lenses/v1/spider`
- File: `services\backend_api\routers\lenses.py`
- Function: `build_spider`
- AI signals: bayes, bayesian, engine, score
- Likely services: StatisticalAnalysisEngine, engine.bayesian_probability, router.post
- Attribute calls: axes.append, base_scores.items, base_scores.values, engine.bayesian_probability, key.replace, key.replace.title, random.randint, req.cohort.get, router.post

### `GET /api/admin/v1/logs/tail`
- File: `services\backend_api\routers\logs.py`
- Function: `tail_log`
- AI signals: ai
- Likely services: router.get
- Attribute calls: f.readlines, fp.exists, ln.rstrip, pat.search, re.compile, router.get

### `POST /api/mentorship/v1/invoices/{invoice_id}/dispute`
- File: `services\backend_api\routers\mentorship.py`
- Function: `raise_dispute`
- AI signals: ai
- Likely services: router.post, service.raise_dispute
- Attribute calls: logger.error, router.post, service.raise_dispute

### `POST /api/mentorship/v1/invoices/{invoice_id}/mark-paid`
- File: `services\backend_api\routers\mentorship.py`
- Function: `mark_invoice_paid`
- AI signals: ai
- Likely services: router.post, service.mark_invoice_paid
- Attribute calls: logger.error, router.post, service.mark_invoice_paid

### `POST /api/payment/v1/cancel`
- File: `services\backend_api\routers\payment.py`
- Function: `cancel_subscription`
- AI signals: ai, model
- Likely services: braintree_service.cancel_subscription, braintree_service.is_configured, router.post
- Attribute calls: braintree_service.cancel_subscription, braintree_service.is_configured, datetime.now, db.commit, db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.first, logger.warning, models.Subscription.created_at.desc, models.Subscription.status.in_, router.post, sub.current_period_end.isoformat

### `GET /api/payment/v1/client-token`
- File: `services\backend_api\routers\payment.py`
- Function: `get_client_token`
- AI signals: ai
- Likely services: braintree_service.generate_client_token, braintree_service.is_configured, router.get
- Attribute calls: braintree_service.generate_client_token, braintree_service.is_configured, logger.error, router.get

### `GET /api/payment/v1/gateway-info`
- File: `services\backend_api\routers\payment.py`
- Function: `gateway_info`
- AI signals: ai
- Likely services: braintree_service.is_configured, router.get
- Attribute calls: braintree_service.is_configured, os.getenv, router.get

### `GET /api/payment/v1/health`
- File: `services\backend_api\routers\payment.py`
- Function: `health_check`
- AI signals: ai
- Likely services: braintree_service.is_configured, router.get
- Attribute calls: braintree_service.is_configured, os.getenv, router.get

### `GET /api/payment/v1/history`
- File: `services\backend_api\routers\payment.py`
- Function: `get_payment_history`
- AI signals: model
- Likely services: router.get
- Attribute calls: db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.all, models.PaymentTransaction.created_at.desc, r.created_at.isoformat, router.get

### `POST /api/payment/v1/methods`
- File: `services\backend_api\routers\payment.py`
- Function: `add_payment_method`
- AI signals: ai
- Likely services: braintree_service.create_payment_method, braintree_service.find_or_create_customer, braintree_service.is_configured, router.post
- Attribute calls: braintree_service.create_payment_method, braintree_service.find_or_create_customer, braintree_service.is_configured, logger.error, router.post

### `GET /api/payment/v1/methods`
- File: `services\backend_api\routers\payment.py`
- Function: `list_payment_methods`
- AI signals: ai
- Likely services: braintree_service.is_configured, braintree_service.list_payment_methods, router.get
- Attribute calls: braintree_service.is_configured, braintree_service.list_payment_methods, router.get

### `DELETE /api/payment/v1/methods/{token}`
- File: `services\backend_api\routers\payment.py`
- Function: `remove_payment_method`
- AI signals: ai
- Likely services: braintree_service.delete_payment_method, braintree_service.is_configured, router.delete
- Attribute calls: braintree_service.delete_payment_method, braintree_service.is_configured, router.delete

### `POST /api/payment/v1/process`
- File: `services\backend_api\routers\payment.py`
- Function: `process_payment`
- AI signals: ai, model
- Likely services: router.post
- Attribute calls: datetime.now, db.add, db.commit, db.flush, logger.info, models.PaymentTransaction, models.Subscription, next_billing.isoformat, payment_result.get, router.post, uuid.uuid4

### `POST /api/payment/v1/refund/{transaction_id}`
- File: `services\backend_api\routers\payment.py`
- Function: `refund_transaction`
- AI signals: ai
- Likely services: braintree_service.is_configured, braintree_service.refund_transaction, router.post
- Attribute calls: braintree_service.is_configured, braintree_service.refund_transaction, result.get, router.post

### `GET /api/payment/v1/subscription`
- File: `services\backend_api\routers\payment.py`
- Function: `get_current_subscription`
- AI signals: model
- Likely services: router.get
- Attribute calls: PLANS.get, db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.first, models.Subscription.created_at.desc, models.Subscription.status.in_, router.get, sub.current_period_end.isoformat, sub.started_at.isoformat

### `GET /api/payment/v1/transactions/{transaction_id}`
- File: `services\backend_api\routers\payment.py`
- Function: `get_transaction`
- AI signals: ai
- Likely services: braintree_service.find_transaction, braintree_service.is_configured, router.get
- Attribute calls: braintree_service.find_transaction, braintree_service.is_configured, router.get

### `POST /api/v1/profile-coach/respond`
- File: `services\backend_api\routers\profile_coach_v1.py`
- Function: `respond_profile_coach`
- AI signals: ai
- Likely services: router.post
- Attribute calls: coaching._contains_stop_phrase, coaching._finish_summary, coaching._mirror_points, coaching._next_question, payload.answer.strip, router.post, session.follow_up_questions.append, session.mirrored_points.append, session.user_messages.append

### `POST /api/v1/profile/signals`
- File: `services\backend_api\routers\profile_v1.py`
- Function: `build_profile_signals`
- AI signals: vector
- Likely services: router.post
- Attribute calls: router.post, value.strip

### `GET /api/rewards/v1/leaderboard`
- File: `services\backend_api\routers\rewards.py`
- Function: `get_leaderboard`
- AI signals: ai
- Likely services: router.get
- Attribute calls: UserReward.user_id.distinct, db.query, db.query.filter, db.query.filter.first, db.query.filter.scalar, db.query.group_by, db.query.group_by.order_by, db.query.group_by.order_by.limit, db.query.group_by.order_by.limit.all, db.query.scalar, func.count, func.sum, func.sum.label, leaderboard.append

### `GET /api/rewards/v1/rewards/available`
- File: `services\backend_api\routers\rewards.py`
- Function: `get_available_rewards`
- AI signals: ai
- Likely services: router.get
- Attribute calls: REWARD_ACTIONS.items, available.append, db.query, db.query.filter, db.query.filter.all, router.get

### `GET /api/support/v1/ai/jobs`
- File: `services\backend_api\routers\support.py`
- Function: `list_ai_jobs`
- AI signals: ai
- Likely services: router.get
- Attribute calls: router.get

### `GET /api/support/v1/ai/jobs/{job_id}`
- File: `services\backend_api\routers\support.py`
- Function: `get_ai_job`
- AI signals: ai
- Likely services: router.get
- Attribute calls: router.get

### `GET /api/support/v1/ai/queue-stats`
- File: `services\backend_api\routers\support.py`
- Function: `get_ai_queue_stats`
- AI signals: ai
- Likely services: router.get
- Attribute calls: router.get

### `POST /api/support/v1/tickets`
- File: `services\backend_api\routers\support.py`
- Function: `create_support_ticket`
- AI signals: ai, model
- Likely services: router.post
- Attribute calls: _os.getenv, _os.getenv.lower, cfg.get, db.add, db.commit, db.refresh, models.SupportTicket, request.headers.get, router.post, ticket.created_at.isoformat, ticket.updated_at.isoformat, zendesk_result.get

### `GET /api/support/v1/tickets`
- File: `services\backend_api\routers\support.py`
- Function: `list_support_tickets`
- AI signals: model
- Likely services: router.get
- Attribute calls: db.query, models.SupportTicket.updated_at.desc, q.count, q.filter, q.order_by, q.order_by.offset, q.order_by.offset.limit, q.order_by.offset.limit.all, router.get

### `GET /api/support/v1/tickets/{ticket_id}/ai-draft`
- File: `services\backend_api\routers\support.py`
- Function: `get_ai_draft_for_ticket`
- AI signals: ai
- Likely services: router.get
- Attribute calls: db.query, db.query.filter, db.query.filter.first, full.get, job_ticket.get, router.get

### `POST /api/support/v1/tickets/{ticket_id}/approve-ai-draft`
- File: `services\backend_api\routers\support.py`
- Function: `approve_ai_draft`
- AI signals: ai
- Likely services: router.post
- Attribute calls: body.strip, datetime.utcnow, db.commit, db.query, db.query.filter, db.query.filter.first, db.refresh, job.get, result.get, router.post

### `POST /api/support/v1/webhooks/zendesk`
- File: `services\backend_api\routers\support.py`
- Function: `zendesk_webhook`
- AI signals: model
- Likely services: router.post
- Attribute calls: datetime.fromisoformat, datetime.utcnow, db.commit, db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.first, db.refresh, models.SupportTicket.id.desc, payload.get, request.body, request.json, router.post, str.replace

### `GET /api/taxonomy/v1/job-titles/naics-mapping`
- File: `services\backend_api\routers\taxonomy.py`
- Function: `job_title_to_naics`
- AI signals: ai
- Likely services: router.get
- Attribute calls: router.get, tax.map_job_title_to_naics

### `GET /api/taxonomy/v1/naics/search`
- File: `services\backend_api\routers\taxonomy.py`
- Function: `search_naics`
- AI signals: ai
- Likely services: router.get
- Attribute calls: router.get, tax.search_naics_by_phrase

### `GET /api/taxonomy/v1/naics/title`
- File: `services\backend_api\routers\taxonomy.py`
- Function: `naics_title`
- AI signals: ai
- Likely services: router.get
- Attribute calls: router.get, tax.get_naics_title

### `GET /api/user/v1/activity`
- File: `services\backend_api\routers\user.py`
- Function: `get_user_activity`
- AI signals: model
- Likely services: router.get
- Attribute calls: activity.append, db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.limit, db.query.filter.order_by.limit.all, entry.created_at.isoformat, json.loads, models.Interaction.created_at.desc, router.get

### `PUT /api/user/v1/profile`
- File: `services\backend_api\routers\user.py`
- Function: `update_profile`
- AI signals: model
- Likely services: router.put
- Attribute calls: db.add, db.commit, db.refresh, models.UserProfile, router.put

### `GET /api/user/v1/resume/latest`
- File: `services\backend_api\routers\user.py`
- Function: `get_latest_resume`
- AI signals: model
- Likely services: router.get
- Attribute calls: db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.first, latest.created_at.isoformat, models.Resume.created_at.desc, router.get

### `GET /api/user/v1/sessions/summary`
- File: `services\backend_api\routers\user.py`
- Function: `get_user_session_summary`
- AI signals: model
- Likely services: router.get
- Attribute calls: created_at.isoformat, db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.all, models.Interaction.created_at.desc, router.get

### `GET /api/v1/user-vector/current`
- File: `services\backend_api\routers\user_vector_v1.py`
- Function: `get_current_user_vector`
- AI signals: vector
- Likely services: router.get
- Attribute calls: Resume.created_at.desc, db.query, db.query.filter, query.filter, query.order_by, query.order_by.first, router.get, vector.keys

### `POST /api/webhooks/v1/braintree`
- File: `services\backend_api\routers\webhooks.py`
- Function: `braintree_webhook`
- AI signals: ai, model
- Likely services: braintree_service.gateway, router.post
- Attribute calls: braintree_service.gateway, datetime.now, db.add, db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.first, event_type.replace, event_type.replace.title, form.get, gw.webhook_notification.parse, logger.error, logger.exception, logger.info

### `GET /api/webhooks/v1/health`
- File: `services\backend_api\routers\webhooks.py`
- Function: `webhook_health`
- AI signals: ai
- Likely services: braintree_service.is_configured, router.get
- Attribute calls: braintree_service.is_configured, os.getenv, router.get

### `POST /api/webhooks/v1/stripe`
- File: `services\backend_api\routers\webhooks.py`
- Function: `stripe_webhook`
- AI signals: ai
- Likely services: router.post
- Attribute calls: datetime.now, event.get, logger.error, logger.exception, logger.info, obj.get, os.getenv, payload_dict.get, request.body, router.post, status_map.get, stripe.Webhook.construct_event

### `POST /api/webhooks/v1/zendesk`
- File: `services\backend_api\routers\webhooks.py`
- Function: `zendesk_webhook`
- AI signals: ai, model
- Likely services: router.post
- Attribute calls: datetime.fromisoformat, datetime.utcnow, db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.first, json.loads, logger.exception, logger.info, logger.warning, models.SupportTicket.id.desc, os.getenv, os.getenv.lower, payload.get

## 4. Service / orchestration hotspots

### `db_session` - `conftest.py`
- AI signals: engine
- Attribute calls: Base.metadata.create_all, engine.dispose, pytest.fixture, session.close
- Direct calls: Session, create_engine, sessionmaker

### `normalize_parsed_resume` - `scripts\aggregate_training_corpus.py`
- AI signals: ai
- Attribute calls: resume.get
- Direct calls: extract_email, extract_phone

### `normalize_profile` - `scripts\aggregate_training_corpus.py`
- AI signals: ai
- Attribute calls: education.append, profile.get, work_experience.append
- Direct calls: extract_email, extract_phone, join

### `main` - `scripts\build_collocation_glossary.py`
- AI signals: ai
- Attribute calls: argparse.ArgumentParser, bigram.items, bigram_entries.append, bigram_entries.sort, bigram_index.values, collocation_txt.exists, datetime.utcnow, datetime.utcnow.isoformat, glossary_path.exists, json.dump, near_pairs.most_common, negated_terms.most_common, output_path.open, output_path.parent.mkdir, p.exists
- Direct calls: CareerTrojanPaths, Counter, Path, compute_pmi, iter_json_files, len, list, load_gazetteer_phrases, load_glossary_terms, print, round, scan_json_file, scan_text_file, str, sum

### `build_company_domain_hints` - `scripts\extract_emails_deep.py`
- AI signals: ai
- Attribute calls: company_domains.items, company_domains.setdefault, counter.most_common, row.get, work_email.split
- Direct calls: Counter, clean_email, is_valid_email, normalize_company

### `build_company_domain_hints_from_company_store` - `scripts\extract_emails_deep.py`
- AI signals: ai
- Attribute calls: counter.most_common, directory.exists, directory.rglob, domain_candidates.append, hints.items, hints.setdefault, item.get, json.loads, json_file.read_text, row.values
- Direct calls: Counter, clean_name, extract_domain_from_value, find_field, isinstance, normalize_company, parse_csv_rows, str

### `collect_contact_rows` - `scripts\extract_emails_deep.py`
- AI signals: ai
- Attribute calls: rows.append
- Direct calls: any, clean_email, find_field, parse_csv_rows, str

### `extract_domain_from_value` - `scripts\extract_emails_deep.py`
- AI signals: ai
- Attribute calls: candidate.split, host.rsplit, host.split, host.startswith, lower.strip, raw.count, re.match, strip.strip
- Direct calls: clean_email, is_valid_email, len, lower, strip, urlparse

### `extract_from_text` - `scripts\extract_emails_deep.py`
- AI signals: ai
- Attribute calls: EMAIL_PATTERN.findall, emails.add
- Direct calls: clean_email, is_valid_email, set

### `infer_email_candidates` - `scripts\extract_emails_deep.py`
- AI signals: ai
- Attribute calls: company_domains.get, datetime.now, datetime.now.isoformat, inferred.values, row.get
- Direct calls: append, clean_email, clean_name, company_slug, is_valid_email, len, lower, normalize_company, sanitize_local_part, sorted, split_first_last

### `is_valid_email` - `scripts\extract_emails_deep.py`
- AI signals: ai
- Attribute calls: domain.endswith, domain.rsplit, domain.startswith, value.rsplit
- Direct calls: len, lower

### `load_tld_hints` - `scripts\extract_emails_deep.py`
- AI signals: ai
- Attribute calls: domain_file.exists, domain_file.read_text, raw.lower, re.findall, tlds.add
- Direct calls: set

### `scan_sources` - `scripts\extract_emails_deep.py`
- AI signals: ai
- Attribute calls: alert_flags.append, company_domains.setdefault, company_store_hints.items, datetime.now, datetime.now.isoformat, domain_counts.most_common, email.split, email_sources.items, email_sources.setdefault, email_sources.setdefault.add, file_path.is_file, file_path.suffix.lower, json.dumps, output_dir.mkdir, r.get
- Direct calls: Counter, build_company_domain_hints, build_company_domain_hints_from_company_store, collect_contact_rows, dict, extract_from_text, infer_email_candidates, iter_zip_texts, len, merge_legacy_records, read_msg_file, read_text_file, set, sorted, str

### `check_ai_structure` - `scripts\ingestion_smoke_test.py`
- AI signals: ai
- Direct calls: is_dir, join, print, print_fail, print_pass, print_warn

### `check_paths` - `scripts\ingestion_smoke_test.py`
- AI signals: ai
- Attribute calls: paths.ai_data_final.exists, paths.data_root.exists, paths.interactions.exists
- Direct calls: print, print_fail, print_pass, print_warn

### `main` - `scripts\ingestion_smoke_test.py`
- AI signals: ai
- Direct calls: CareerTrojanPaths, check_ai_structure, check_ingestion_outputs, check_paths, print

### `main` - `scripts\run_full_pipeline.py`
- AI signals: ai, training
- Attribute calls: argparse.ArgumentParser, datetime.now, datetime.now.isoformat, json.dump, log.error, log.info, log.warning, parser.add_argument, parser.parse_args, pipeline_results.items, result.get, sys.exit, time.time, traceback.print_exc
- Direct calls: CareerTrojanPaths, banner, int, isinstance, len, open, run_collocations, run_parser, run_smoke_test, run_training, str

### `run_collocations` - `scripts\run_full_pipeline.py`
- AI signals: ai, score
- Attribute calls: all_tokens.extend, bigram.split, bigram_counts.most_common, datetime.now, datetime.now.isoformat, gaz_dir.exists, gaz_dir.rglob, json.dump, log.info, log.warning, math.log2, near_pairs.most_common, negated_terms.most_common, pmi_scores.items, scan_dir.exists
- Direct calls: Counter, banner, enumerate, len, min, open, range, round, scan_json_file, scan_text_file, sorted, str

### `run_parser` - `scripts\run_full_pipeline.py`
- AI signals: engine
- Attribute calls: engine.run, log.info, log.warning, output_root.mkdir, sys.path.insert
- Direct calls: AutomatedParserEngine, banner, len, str

### `run_smoke_test` - `scripts\run_full_pipeline.py`
- AI signals: ai
- Attribute calls: log.error, log.info, log.warning, merged.exists, merged.stat, p.exists, p.mkdir, paths.ai_data_final.rglob
- Direct calls: append, banner

### `run_training` - `scripts\run_full_pipeline.py`
- AI signals: ai, bayes, bayesian, classifier, embedding, model, trained
- Attribute calls: datetime.now, datetime.now.isoformat, json.dump, log.error, log.info, log.warning, paths.trained_models.mkdir, sys.path.insert, traceback.print_exc, trainer.load_cv_data, trainer.models_dir.mkdir, trainer.setup_sentence_embeddings, trainer.setup_spacy_model, trainer.train_bayesian_classifier, trainer.train_statistical_models
- Direct calls: IntelliCVModelTrainer, Path, append, banner, get, len, open, str

### `main` - `scripts\run_parser_until_complete.py`
- AI signals: engine
- Attribute calls: datetime.utcnow, datetime.utcnow.isoformat, engine.run, results.get, time.sleep, time.time
- Direct calls: AutomatedParserEngine, CareerTrojanPaths, append_progress, int, len, print, round, str

### `_ensure_mentor_profile` - `scripts\run_super_experience_harness.py`
- AI signals: model
- Attribute calls: db.add, db.close, db.commit, db.query, db.query.filter, db.query.filter.first, db.refresh, models.Mentor
- Direct calls: SessionLocal

### `run` - `scripts\run_super_experience_harness.py`
- AI signals: ai
- Attribute calls: datetime.now, datetime.now.isoformat, json.dumps, self._ensure_mentor_profile, self._register_and_login, self._upsert_role, self.admin_journey, self.ai_learning_signals, self.mentor_journey, self.output_path.parent.mkdir, self.output_path.write_text, self.resume_probe, self.run_tiered_tests, self.user_journey
- Direct calls: HarnessReport, RuntimeError, asdict, set, sorted

### `check_environment_paths` - `scripts\smoke_test.py`
- AI signals: ai
- Attribute calls: os.path.exists
- Direct calls: print, print_fail, print_pass, print_warn

### `check_frontend_components` - `scripts\smoke_test.py`
- AI signals: ai
- Attribute calls: os.path.basename, os.path.exists, os.path.join
- Direct calls: print, print_fail, print_pass

### `verify_test_user_seeding` - `scripts\smoke_test.py`
- AI signals: ai
- Attribute calls: json.load, os.path.exists, os.path.join, user.get
- Direct calls: CareerTrojanPaths, isinstance, open, print, print_fail, print_pass, print_warn, str

### `_find_webhook_id` - `scripts\upsert_zendesk_webhook_triggers.py`
- AI signals: ai
- Attribute calls: available.append, chosen.get, client.get, client.get.get, preferred_url.strip, preferred_url.strip.rstrip, str.rstrip, webhook.get
- Direct calls: RuntimeError, get, isinstance, print, str

### `get` - `scripts\upsert_zendesk_webhook_triggers.py`
- AI signals: ai
- Attribute calls: requests.get, response.json, response.raise_for_status

### `post` - `scripts\upsert_zendesk_webhook_triggers.py`
- AI signals: ai
- Attribute calls: requests.post, response.json, response.raise_for_status

### `put` - `scripts\upsert_zendesk_webhook_triggers.py`
- AI signals: ai
- Attribute calls: requests.put, response.json, response.raise_for_status

### `main` - `scripts\validate_runtime_env.py`
- AI signals: ai
- Attribute calls: Path.resolve, argparse.ArgumentParser, env_map.get, env_path.exists, missing.extend, offenders.append, parser.add_argument, parser.parse_args, strip.lower, unsafe_identity_keys.append
- Direct calls: Path, _is_google_managed_service_agent, _is_personal_email, _missing, _warn_placeholder, parse_env_file, print, set, sorted, strip

### `__init__` - `services\ai_engine\ai_training_orchestrator.py`
- AI signals: model
- Attribute calls: logger.info, self.models_path.mkdir
- Direct calls: Path

### `calculate_similarity_matrix` - `services\ai_engine\ai_training_orchestrator.py`
- AI signals: similarity
- Attribute calls: logger.error, logger.info, np.array, np.save, similarity_matrix.max, similarity_matrix.mean
- Direct calls: cosine_similarity, len

### `main` - `services\ai_engine\ai_training_orchestrator.py`
- AI signals: ai, orchestrator, training
- Attribute calls: orchestrator.run_full_training_pipeline
- Direct calls: AITrainingOrchestrator, Path, str

### `run_full_training_pipeline` - `services\ai_engine\ai_training_orchestrator.py`
- AI signals: ai, classifier, clustering, embedding, similarity
- Attribute calls: datetime.now, datetime.now.isoformat, json.dump, logger.error, logger.info, self.calculate_similarity_matrix, self.load_data, self.prepare_text_data, self.train_clustering, self.train_embeddings, self.train_job_classifier, self.train_tfidf
- Direct calls: len, min, open, total_seconds

### `train_clustering` - `services\ai_engine\ai_training_orchestrator.py`
- AI signals: model, predict
- Attribute calls: Counter.items, dbscan_labels.tolist, json.dump, kmeans_labels.tolist, list.count, logger.error, logger.info, pickle.dump, self.dbscan_model.fit_predict, self.kmeans_model.fit_predict
- Direct calls: Counter, DBSCAN, KMeans, dict, float, int, len, list, open, set, str

### `train_embeddings` - `services\ai_engine\ai_training_orchestrator.py`
- AI signals: model
- Attribute calls: logger.error, logger.info, np.array, np.save, self.sentence_model.encode
- Direct calls: SentenceTransformer, len

### `train_job_classifier` - `services\ai_engine\ai_training_orchestrator.py`
- AI signals: ai, classifier, predict, score, vector
- Attribute calls: categories.append, logger.error, logger.info, pickle.dump, self.job_classifier.fit, self.job_classifier.predict, title.lower, vectorizer.fit_transform
- Direct calls: Counter, RandomForestClassifier, TfidfVectorizer, accuracy_score, any, dict, len, open, set, train_test_split

### `train_tfidf` - `services\ai_engine\ai_training_orchestrator.py`
- AI signals: vector
- Attribute calls: json.dump, logger.error, logger.info, np.array, pickle.dump, self.tfidf_vectorizer.fit_transform, self.tfidf_vectorizer.get_feature_names_out, tfidf_matrix.toarray
- Direct calls: TfidfVectorizer, len, list, open

### `find_near_pairs` - `services\ai_engine\collocation_engine.py`
- AI signals: ai
- Attribute calls: hit_details.append, pair_hits.items, ranked.sort, self._all_tokens
- Direct calls: Counter, enumerate, int, len, max, min, range, sorted, tuple

### `load_sample_profiles` - `services\ai_engine\data_loader.py`
- AI signals: score
- Attribute calls: PROFILES_DIR.exists, PROFILES_DIR.glob, data.get, json.load, loaded.append, logger.debug, logger.info, logger.warning, random.shuffle
- Direct calls: _derive_match_score, len, list, open

### `get_expert_system` - `services\ai_engine\expert_system.py`
- AI signals: engine
- Direct calls: ExpertSystemEngine

### `__init__` - `services\ai_engine\llm_service.py`
- AI signals: ai
- Attribute calls: os.getenv
- Direct calls: OpenAI, print

### `generate` - `services\ai_engine\llm_service.py`
- AI signals: model
- Attribute calls: kwargs.get, response.usage.model_dump, self.client.chat.completions.create
- Direct calls: LLMResponse, str

### `generate` - `services\ai_engine\llm_service.py`
- AI signals: model
- Attribute calls: kwargs.get, response.usage.model_dump, self.client.messages.create
- Direct calls: LLMResponse, str

### `generate` - `services\ai_engine\llm_service.py`
- AI signals: ai
- Attribute calls: data.get, kwargs.get, requests.post, response.json, response.raise_for_status
- Direct calls: LLMResponse, str

### `initialize` - `services\ai_engine\llm_service.py`
- AI signals: ai
- Attribute calls: backend.lower
- Direct calls: AnthropicService, LLMBackendType, OpenAIService, VLLMService

### `__init__` - `services\ai_engine\model_registry.py`
- AI signals: model
- Attribute calls: self._load_registry, self._resolve_registry_file, self.models_dir.mkdir, self.registry_dir.mkdir
- Direct calls: CareerTrojanPaths, Path

### `get_model` - `services\ai_engine\model_registry.py`
- AI signals: model
- Attribute calls: model_file.exists, pickle.load
- Direct calls: Path, open, print

### `get_vectorizer` - `services\ai_engine\model_registry.py`
- AI signals: model
- Attribute calls: self.get_model

### `rollback_deployment` - `services\ai_engine\model_registry.py`
- AI signals: model
- Attribute calls: self.deploy_model
- Direct calls: keys, len, list, print, reversed

### `verify_integrity` - `services\ai_engine\model_registry.py`
- AI signals: model
- Attribute calls: self._calculate_file_hash, self.get_model_info

### `__init__` - `services\ai_engine\train_all_models.py`
- AI signals: model
- Attribute calls: datetime.now, datetime.now.isoformat, self.models_dir.mkdir
- Direct calls: CareerTrojanPaths, Path, print

### `main` - `services\ai_engine\train_all_models.py`
- AI signals: ai, model, training
- Attribute calls: trainer.run_full_training
- Direct calls: IntelliCVModelTrainer

### `run_full_training` - `services\ai_engine\train_all_models.py`
- AI signals: ai, bayes, bayesian, classifier, embedding, model
- Attribute calls: self.generate_report, self.load_cv_data, self.setup_sentence_embeddings, self.setup_spacy_model, self.train_bayesian_classifier, self.train_statistical_models, traceback.print_exc
- Direct calls: print

### `setup_sentence_embeddings` - `services\ai_engine\train_all_models.py`
- AI signals: model
- Attribute calls: json.dump, model.encode
- Direct calls: SentenceTransformer, append, int, len, open, print, str

### `train_bayesian_classifier` - `services\ai_engine\train_all_models.py`
- AI signals: ai, model, predict, score, vector
- Attribute calls: df.apply, model.fit, model.predict, pickle.dump, self._infer_job_category, vectorizer.fit_transform
- Direct calls: MultinomialNB, TfidfVectorizer, accuracy_score, extend, float, int, isin, len, list, open, print, str, train_test_split, value_counts

### `train_statistical_models` - `services\ai_engine\train_all_models.py`
- AI signals: ai, model, predict, score
- Attribute calls: education_map.get, isna.sum, missing_exp_mask.any, model.fit, model.predict, pickle.dump, str.len
- Direct calls: RandomForestRegressor, append, apply, copy, float, int, isinstance, isna, len, map, notna, open, print, r2_score, str

### `__init__` - `services\ai_engine\train_bayesian_models.py`
- AI signals: model
- Attribute calls: logger.info, self.models_path.mkdir
- Direct calls: Path

### `train_all_bayesian` - `services\ai_engine\train_bayesian_models.py`
- AI signals: ai, bayes, bayesian, training
- Attribute calls: logger.error, logger.info, name.upper, results.items, self.load_training_data, self.prepare_features, self.train_bayesian_network, self.train_hierarchical_bayesian, self.train_mcmc_sampler, self.train_naive_bayes

### `train_bayesian_network` - `services\ai_engine\train_bayesian_models.py`
- AI signals: model
- Attribute calls: joblib.dump, json.dump, logger.error, logger.info, model.fit, network.add_edges_from, np.unique, nx.DiGraph, nx.node_link_data
- Direct calls: GaussianNB, len, open

### `train_hierarchical_bayesian` - `services\ai_engine\train_bayesian_models.py`
- AI signals: model, score
- Attribute calls: joblib.dump, logger.error, logger.info, model.fit, scores.mean, scores.std
- Direct calls: GaussianNB, cross_val_score

### `train_naive_bayes` - `services\ai_engine\train_bayesian_models.py`
- AI signals: ai, predict, score
- Attribute calls: bnb.fit, bnb.predict, gnb.fit, gnb.predict, joblib.dump, logger.error, logger.info, mnb.fit, mnb.predict, np.abs
- Direct calls: BernoulliNB, GaussianNB, MultinomialNB, accuracy_score, train_test_split

### `__init__` - `services\ai_engine\train_fuzzy_logic.py`
- AI signals: model
- Attribute calls: logger.info, self.models_path.mkdir
- Direct calls: Path

### `build_all_fuzzy_systems` - `services\ai_engine\train_fuzzy_logic.py`
- AI signals: ai
- Attribute calls: logger.info, name.upper, results.items, self.build_fuzzy_decision_tree, self.build_mamdani_fis, self.build_membership_functions, self.build_sugeno_fis, self.train_fcm_clusterer

### `__init__` - `services\ai_engine\train_neural_networks.py`
- AI signals: model
- Attribute calls: logger.info, self.models_path.mkdir
- Direct calls: Path

### `train_all_architectures` - `services\ai_engine\train_neural_networks.py`
- AI signals: ai, classifier, training
- Attribute calls: logger.error, logger.info, name.upper, results.items, self.load_training_data, self.prepare_features, self.train_autoencoder, self.train_cnn_embedder, self.train_dnn_classifier, self.train_lstm_sequence, self.train_transformer_encoder

### `train_cnn_embedder` - `services\ai_engine\train_neural_networks.py`
- AI signals: model
- Attribute calls: X.reshape, keras.Sequential, keras.layers.Conv1D, keras.layers.Dense, keras.layers.GlobalAveragePooling1D, keras.layers.MaxPooling1D, logger.error, logger.info, model.compile, model.fit, model.save

### `train_dnn_classifier` - `services\ai_engine\train_neural_networks.py`
- AI signals: ai, model
- Attribute calls: joblib.dump, keras.Sequential, keras.layers.Dense, keras.layers.Dropout, logger.error, logger.info, model.compile, model.evaluate, model.fit, model.save, scaler.fit_transform, scaler.transform
- Direct calls: StandardScaler, train_test_split

### `train_lstm_sequence` - `services\ai_engine\train_neural_networks.py`
- AI signals: model
- Attribute calls: X.reshape, keras.Sequential, keras.layers.Dense, keras.layers.Dropout, keras.layers.LSTM, logger.error, logger.info, model.compile, model.fit, model.save

### `train_transformer_encoder` - `services\ai_engine\train_neural_networks.py`
- AI signals: model
- Attribute calls: keras.Sequential, keras.layers.Dense, keras.layers.LayerNormalization, logger.error, logger.info, model.compile, model.fit, model.save

### `__init__` - `services\ai_engine\train_nlp_llm_models.py`
- AI signals: model
- Attribute calls: logger.info, self.models_path.mkdir
- Direct calls: Path

### `setup_bert_embeddings` - `services\ai_engine\train_nlp_llm_models.py`
- AI signals: model
- Attribute calls: bert_dir.mkdir, logger.error, logger.info, model.save
- Direct calls: SentenceTransformer, str

### `train_all_nlp_models` - `services\ai_engine\train_nlp_llm_models.py`
- AI signals: ai, classifier, embedding, model
- Attribute calls: logger.error, logger.info, name.upper, results.items, self.load_text_data, self.setup_bert_embeddings, self.setup_gpt_config, self.train_ner_model, self.train_sentiment_analyzer, self.train_text_classifier, self.train_tokenizer, self.train_topic_model, self.train_word2vec

### `train_sentiment_analyzer` - `services\ai_engine\train_nlp_llm_models.py`
- AI signals: classifier, vector
- Attribute calls: classifier.fit, joblib.dump, logger.error, logger.info, np.random.choice, vectorizer.fit_transform
- Direct calls: MultinomialNB, TfidfVectorizer, len

### `train_text_classifier` - `services\ai_engine\train_nlp_llm_models.py`
- AI signals: classifier, vector
- Attribute calls: classifier.fit, joblib.dump, logger.error, logger.info, np.random.choice, vectorizer.fit_transform
- Direct calls: CountVectorizer, MultinomialNB, len

### `train_topic_model` - `services\ai_engine\train_nlp_llm_models.py`
- AI signals: vector
- Attribute calls: joblib.dump, lda.fit, logger.error, logger.info, vectorizer.fit_transform
- Direct calls: CountVectorizer, LatentDirichletAllocation

### `train_word2vec` - `services\ai_engine\train_nlp_llm_models.py`
- AI signals: model
- Attribute calls: logger.error, logger.info, model.save, text.lower
- Direct calls: Word2Vec, len, str, word_tokenize

### `run_all` - `services\ai_engine\train_statistical_methods.py`
- AI signals: ai, bayes, bayesian, regression, training
- Attribute calls: json.dump, logger.info, self.load_training_data, self.run_anova, self.run_bayesian_analysis, self.run_chi_square, self.run_correlation, self.run_dbscan_summary, self.run_effect_size_power, self.run_factor_analysis, self.run_hierarchical_summary, self.run_kmeans_summary, self.run_linear_regression, self.run_logistic_regression, self.run_pca
- Direct calls: enumerate, len, open

### `run_linear_regression` - `services\ai_engine\train_statistical_methods.py`
- AI signals: model, regression, score
- Attribute calls: logger.error, logger.info, model.fit, model.score
- Direct calls: LinearRegression, append, float, len

### `run_logistic_regression` - `services\ai_engine\train_statistical_methods.py`
- AI signals: model, regression, score
- Attribute calls: logger.error, logger.info, model.fit, model.score
- Direct calls: LogisticRegression, append, float, len, tolist

### `run_pca` - `services\ai_engine\train_statistical_methods.py`
- AI signals: ai
- Attribute calls: df.select_dtypes, logger.error, logger.info, pca.explained_variance_ratio_.sum, pca.fit_transform, scaler.fit_transform
- Direct calls: PCA, StandardScaler, append, float, len

### `run_time_series` - `services\ai_engine\train_statistical_methods.py`
- AI signals: model, regression
- Attribute calls: df.sort_values, logger.error, logger.info, model.fit, rolling.mean
- Direct calls: LinearRegression, append, dropna, float, len, rolling

### `__init__` - `services\ai_engine\training_orchestrator.py`
- AI signals: ai, model, training
- Direct calls: IntelliCVModelTrainer, ModelRegistry, TrainingCheckpoint, print

### `_train_bayesian_model` - `services\ai_engine\training_orchestrator.py`
- AI signals: ai, bayes, bayesian, classifier, model, vector
- Attribute calls: self.registry.deploy_model, self.registry.register_model, self.registry.register_vectorizer, self.trainer.train_bayesian_classifier
- Direct calls: get, print, str

### `_train_sentence_embeddings` - `services\ai_engine\training_orchestrator.py`
- AI signals: ai, embedding, model
- Attribute calls: self.registry.deploy_model, self.registry.register_model, self.trainer.setup_sentence_embeddings
- Direct calls: get, print, str

### `_train_spacy_model` - `services\ai_engine\training_orchestrator.py`
- AI signals: ai, model
- Attribute calls: self.registry.deploy_model, self.registry.register_model, self.trainer.setup_spacy_model
- Direct calls: get, print, str

### `_train_statistical_models` - `services\ai_engine\training_orchestrator.py`
- AI signals: ai, model
- Attribute calls: self.registry.deploy_model, self.registry.register_model, self.trainer.train_statistical_models
- Direct calls: get, print, str

### `check_prerequisites` - `services\ai_engine\training_orchestrator.py`
- AI signals: model
- Attribute calls: core_db_dir.exists, data_path.exists, merged_db.exists, models_path.mkdir
- Direct calls: Path, print

### `generate_report` - `services\ai_engine\training_orchestrator.py`
- AI signals: model
- Attribute calls: datetime.now, datetime.now.isoformat, json.dump, self.registry.list_models
- Direct calls: Path, len, open, print

### `main` - `services\ai_engine\training_orchestrator.py`
- AI signals: ai, orchestrator, training
- Attribute calls: orchestrator.run_full_training
- Direct calls: TrainingOrchestrator

### `run_full_training` - `services\ai_engine\training_orchestrator.py`
- AI signals: ai, model
- Attribute calls: self.check_prerequisites, self.generate_report, self.print_summary, self.train_all_models, traceback.print_exc
- Direct calls: print

### `train_all_models` - `services\ai_engine\training_orchestrator.py`
- AI signals: ai
- Attribute calls: datetime.fromisoformat, datetime.now, datetime.now.isoformat, self.checkpoint.clear_checkpoint, self.checkpoint.load_checkpoint, self.checkpoint.save_checkpoint, self.trainer.load_cv_data, traceback.print_exc
- Direct calls: append, len, print, total_seconds, train_func

### `__init__` - `services\ai_engine\unified_ai_engine.py`
- AI signals: model
- Direct calls: CareerTrojanPaths, ModelRegistry, Path, print, str

### `_get_vectorizer` - `services\ai_engine\unified_ai_engine.py`
- AI signals: vector
- Attribute calls: datetime.now, datetime.now.isoformat, self.registry.get_vectorizer

### `ensemble_infer` - `services\ai_engine\unified_ai_engine.py`
- AI signals: predict
- Attribute calls: confidences.append, datetime.now, datetime.now.isoformat, self._generate_reasoning, self.infer_job_category, self.infer_salary_prediction
- Direct calls: EnsembleResult, len, print, sum

### `infer_job_category` - `services\ai_engine\unified_ai_engine.py`
- AI signals: inference, model, predict, vector
- Attribute calls: datetime.now, datetime.now.isoformat, model.predict, model.predict_proba, self._get_vectorizer, vectorizer.transform
- Direct calls: InferenceResult, dict, float, len, max, print, zip

### `infer_salary_prediction` - `services\ai_engine\unified_ai_engine.py`
- AI signals: inference, model, predict
- Attribute calls: datetime.now, datetime.now.isoformat, model.predict
- Direct calls: InferenceResult, float, min, print

### `load_all_models` - `services\ai_engine\unified_ai_engine.py`
- AI signals: model
- Attribute calls: models.keys, self.load_model, self.registry.list_models
- Direct calls: print

### `load_model` - `services\ai_engine\unified_ai_engine.py`
- AI signals: model
- Attribute calls: datetime.now, datetime.now.isoformat, self.registry.get_model
- Direct calls: print

### `main` - `services\ai_engine\unified_ai_engine.py`
- AI signals: ai, engine, model
- Attribute calls: engine.load_all_models, engine.print_status, engine.test_all_models
- Direct calls: UnifiedAIEngine, print

### `print_status` - `services\ai_engine\unified_ai_engine.py`
- AI signals: model
- Attribute calls: self.loaded_models.items, self.registry.list_models, self.registry.list_models.items
- Direct calls: len, print

### `to_dict` - `services\ai_engine\unified_ai_engine.py`
- AI signals: predict
- Attribute calls: self.all_predictions.items, v.to_dict

### `_build_timeseries` - `services\backend_api\routers\admin_tokens.py`
- AI signals: ai
- Attribute calls: _utcnow.date, d.isoformat, daily.keys, daily.setdefault, datetime.fromisoformat, datetime.fromisoformat.date, row.get, rows.append, store.get, ts.replace
- Direct calls: _utcnow, add, int, isinstance, len, set, sorted, str, timedelta

### `_ensure_user_from_google` - `services\backend_api\routers\auth.py`
- AI signals: model
- Attribute calls: db.add, db.commit, db.query, db.query.filter, db.query.filter.first, db.refresh, models.User, secrets.token_urlsafe, security.get_password_hash

### `_vector_from_text` - `services\backend_api\routers\career_compass.py`
- AI signals: score
- Attribute calls: text.lower
- Direct calls: _norm_score, sum

### `build_taxonomy_context_from_resume` - `services\backend_api\routers\coaching.py`
- AI signals: ai
- Attribute calls: _tax.infer_industries_from_titles, _tax.map_job_title_to_naics, r.get, resume_data.get, titles.append
- Direct calls: isinstance, strip

### `_audit` - `services\backend_api\routers\gdpr.py`
- AI signals: model
- Attribute calls: db.add, db.commit, models.AuditLog

### `_domain_series_from_text` - `services\backend_api\routers\insights.py`
- AI signals: score
- Attribute calls: STRUCTURAL_AXES.items
- Direct calls: _axis_score, round

### `_structural_response` - `services\backend_api\routers\insights.py`
- AI signals: ai, score
- Attribute calls: STRUCTURAL_AXES.items, cohort_domain_scores.items, domain_series.items, options_payload.keys, p.get, profile.get, statistics.median, str.strip, str.strip.lower, strip.lower, target_domain_scores.items, user_domains.items, user_profile.get
- Direct calls: _domain_series_from_text, _percentile, _profile_text_blob, _shape_label, abs, append, len, list, max, next, round, str, strip, sum

### `_pipeline_summary` - `services\backend_api\routers\intelligence.py`
- AI signals: ai, model
- Attribute calls: file_path.is_file, file_path.relative_to, file_path.stat, model_root.exists, model_root.rglob, model_rows.append, model_rows.sort, str.replace
- Direct calls: CareerTrojanPaths, _safe_read_json, _tail_jsonl, int, len, sorted, str

### `_process_braintree_payment` - `services\backend_api\routers\payment.py`
- AI signals: ai
- Attribute calls: braintree_service.create_sale, braintree_service.find_or_create_customer, braintree_service.is_configured
- Direct calls: HTTPException

### `_ensure_support_table` - `services\backend_api\routers\support.py`
- AI signals: model
- Attribute calls: models.SupportTicket.__table__.create

### `_handle_stripe_checkout` - `services\backend_api\routers\webhooks.py`
- AI signals: model
- Attribute calls: db.add, db.commit, db.query, db.query.filter, db.query.filter.first, models.PaymentTransaction, obj.get
- Direct calls: upper

### `_handle_stripe_invoice_paid` - `services\backend_api\routers\webhooks.py`
- AI signals: model
- Attribute calls: db.add, db.commit, db.query, db.query.filter, db.query.filter.first, models.PaymentTransaction, obj.get
- Direct calls: _update_subscription_from_gateway, upper

### `_log_event` - `services\backend_api\routers\webhooks.py`
- AI signals: model
- Attribute calls: db.add, db.flush, db.query, db.query.filter, db.query.filter.first, logger.info, models.WebhookEvent
- Direct calls: HTTPException

### `get` - `services\backend_api\services\admin_api_client.py`
- AI signals: ai
- Attribute calls: r.json, requests.get, self._headers, self._raise, self._url

### `post` - `services\backend_api\services\admin_api_client.py`
- AI signals: ai
- Attribute calls: r.json, requests.post, self._headers, self._raise, self._url

### `__init__` - `services\backend_api\services\advanced_analytics_service.py`
- AI signals: engine
- Attribute calls: logger.info
- Direct calls: CareerTrojanPaths, Path, get_feature_builder, get_stats_engine

### `analyze_candidate_pool` - `services\backend_api\services\advanced_analytics_service.py`
- AI signals: engine
- Attribute calls: datetime.now, datetime.now.isoformat, datetime.now.strftime, dropna.tolist, filters.items, logger.info, logger.warning, self._generate_candidate_insights, self.feature_builder.build_candidate_features, self.stats_engine.analyze_application_trends, self.stats_engine.describe_candidate_pool, self.stats_engine.fit_salary_distribution, self.stats_engine.load_candidates, self.stats_engine.save_analysis
- Direct calls: dropna, len, str

### `analyze_job_market` - `services\backend_api\services\advanced_analytics_service.py`
- AI signals: engine
- Attribute calls: datetime.now, datetime.now.isoformat, datetime.now.strftime, dropna.tolist, logger.info, logger.warning, self._generate_job_insights, self.feature_builder.build_job_features, self.stats_engine.describe_candidate_pool, self.stats_engine.fit_salary_distribution, self.stats_engine.load_jobs, self.stats_engine.save_analysis
- Direct calls: dropna, len, str

### `calculate_candidate_job_matches` - `services\backend_api\services\advanced_analytics_service.py`
- AI signals: engine
- Attribute calls: candidates_df.head, datetime.now, datetime.now.isoformat, datetime.now.strftime, jobs_df.head, logger.info, matches_df.nlargest, matches_df.nlargest.to_dict, self._generate_matching_insights, self.feature_builder.batch_calculate_matches, self.feature_builder.build_candidate_features, self.feature_builder.build_job_features, self.stats_engine.load_candidates, self.stats_engine.load_jobs, self.stats_engine.save_analysis
- Direct calls: float, len, max, mean, median

### `list_recent_analyses` - `services\backend_api\services\advanced_analytics_service.py`
- AI signals: engine
- Attribute calls: self.stats_engine.list_saved_analyses

### `load_saved_analysis` - `services\backend_api\services\advanced_analytics_service.py`
- AI signals: engine
- Attribute calls: self.stats_engine.load_analysis

### `predict_callback_probability` - `services\backend_api\services\advanced_analytics_service.py`
- AI signals: engine, predict
- Attribute calls: datetime.now, datetime.now.isoformat, datetime.now.strftime, insights.append, logger.info, self.stats_engine.predict_callback_rate, self.stats_engine.save_analysis
- Direct calls: items

### `run_ab_test` - `services\backend_api\services\advanced_analytics_service.py`
- AI signals: engine
- Attribute calls: datetime.now, datetime.now.isoformat, datetime.now.strftime, logger.info, self.stats_engine.compare_resume_quality, self.stats_engine.save_analysis, test_name.replace
- Direct calls: abs, len

### `get_ai_chat_service` - `services\backend_api\services\ai\ai_chat_service.py`
- AI signals: ai
- Direct calls: AIChatService

### `get_career_advice` - `services\backend_api\services\ai\ai_chat_service.py`
- AI signals: ai
- Attribute calls: datetime.now, datetime.now.isoformat, logger.error, self._build_career_advice_prompt, self._query_gemini, self._query_perplexity, self._unavailable_response

### `__init__` - `services\backend_api\services\ai\ai_feedback_loop.py`
- AI signals: ai, engine
- Attribute calls: logging.basicConfig, logging.getLogger, self.logger.info
- Direct calls: AIChatResearchEngine, WebResearchEngine, defaultdict

### `_research_openai` - `services\backend_api\services\ai\ai_feedback_loop.py`
- AI signals: ai
- Attribute calls: message.content.strip, self._build_ai_prompt, self._calculate_ai_confidence, self.logger.error, self.openai_client.ChatCompletion.create
- Direct calls: ResearchResult

### `get_system_status` - `services\backend_api\services\ai\ai_feedback_loop.py`
- AI signals: ai
- Attribute calls: self.completed_research.values, self.failed_research.values
- Direct calls: Counter, dict, len, max, min, sum

### `research_term_comprehensive` - `services\backend_api\services\ai\ai_feedback_loop.py`
- AI signals: ai, engine
- Attribute calls: all_results.extend, self._consolidate_research_results, self.ai_engine.research_with_ai, self.logger.debug, self.logger.error, self.logger.info, self.logger.warning, self.web_engine.research_term
- Direct calls: len

### `research_with_ai` - `services\backend_api\services\ai\ai_feedback_loop.py`
- AI signals: ai
- Attribute calls: results.append, self._research_openai, self.logger.error, self.logger.warning

### `get_learning_tracker` - `services\backend_api\services\ai\ai_learning_tracker.py`
- AI signals: ai
- Direct calls: AILearningPatternTracker

### `get_model` - `services\backend_api\services\ai\ai_model_loader.py`
- AI signals: model
- Attribute calls: self.load_all_models, self.models.get

### `get_model` - `services\backend_api\services\ai\ai_model_loader.py`
- AI signals: model
- Attribute calls: _loader.get_model

### `get_trained_models` - `services\backend_api\services\ai\ai_model_loader.py`
- AI signals: model
- Attribute calls: _loader.load_all_models

### `load_all_models` - `services\backend_api\services\ai\ai_model_loader.py`
- AI signals: bayes, bayesian, vector
- Attribute calls: bayesian_file.exists, logger.info, logger.warning, pickle.load, salary_file.exists, spacy.load, vectorizer_file.exists
- Direct calls: SentenceTransformer, len, open

### `__init__` - `services\backend_api\services\ai\ai_router.py`
- AI signals: engine
- Attribute calls: self._detect_engines

### `_detect_engines` - `services\backend_api\services\ai\ai_router.py`
- AI signals: ai
- Attribute calls: self.ai_chat.get_service_status, subprocess.run
- Direct calls: RealAIConnector, get_ai_chat_service

### `get_ai_router` - `services\backend_api\services\ai\ai_router.py`
- AI signals: ai
- Direct calls: AIRouter

### `route_career_advice` - `services\backend_api\services\ai\ai_router.py`
- AI signals: ai, engine
- Attribute calls: self.ai_chat.get_career_advice, self.engines_available.get, self.internal_ai.get_ai_generated_insights, user_profile.get

### `route_cv_analysis` - `services\backend_api\services\ai\ai_router.py`
- AI signals: ai, engine
- Attribute calls: self._analyze_with_internal, self._analyze_with_ollama, self.engines_available.get

### `route_market_intelligence` - `services\backend_api\services\ai\ai_router.py`
- AI signals: ai, engine
- Attribute calls: self.ai_chat.get_career_advice, self.ai_chat.get_job_market_insights, self.engines_available.get

### `__init__` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: bayes, bayesian, vector
- Attribute calls: bayesian_file.exists, logging.info, logging.warning, pickle.load, vectorizer_file.exists
- Direct calls: Path, open

### `__init__` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: model
- Attribute calls: self._initialize_model

### `__init__` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: ai, bayes, bayesian, engine, inference
- Attribute calls: logging.basicConfig, logging.getLogger, self.config.get, self.logger.info
- Direct calls: AILearningTable, AdvancedNLPEngine, BayesianInferenceEngine, FuzzyLogicEngine, LLMIntegrationEngine, NeuralNetworkEngine

### `_calculate_overall_scores` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: ai, bayes, bayesian, score
- Attribute calls: ai_analysis.keys, bayesian_results.get, confidence_scores.append, fuzzy_results.get, fuzzy_results.get.get
- Direct calls: append, get, len, min, sum

### `_openai_enhance_description` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: ai
- Attribute calls: logging.error, message.content.strip, self.openai_client.ChatCompletion.create

### `_openai_generate_summary` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: ai
- Attribute calls: logging.error, message.content.strip, self.openai_client.ChatCompletion.create
- Direct calls: isinstance, join, str

### `_run_bayesian_analysis` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: bayes, bayesian, engine, predict
- Attribute calls: nlp_results.get, self.bayesian_engine.calculate_skill_match_probability, self.bayesian_engine.predict_job_category
- Direct calls: append, list, set

### `_run_fuzzy_analysis` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: engine
- Attribute calls: e.get, entity.get, learned_terms.keys, nlp_results.items, nlp_results.values, self._map_nlp_to_learning_category, self.fuzzy_engine.assess_data_quality, self.fuzzy_engine.handle_ambiguous_data, self.learning_table.get_learned_terms, term.split
- Direct calls: append, len, lower, max, min, set, sum

### `_run_llm_enhancement` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: engine
- Attribute calls: nlp_results.get, self.llm_engine.enhance_job_description, self.llm_engine.generate_professional_summary
- Direct calls: append

### `_run_neural_analysis` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: embedding, engine, similarity
- Attribute calls: doc_embedding.tolist, self.neural_engine.calculate_similarity, self.neural_engine.get_embedding
- Direct calls: append, float, len, sort

### `_train_job_classifier` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: model, vector
- Attribute calls: label_encoder.fit_transform, model.fit, vectorizer.fit_transform
- Direct calls: LabelEncoder, MultinomialNB, TfidfVectorizer

### `calculate_similarity` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: model
- Attribute calls: logging.error, np.dot, np.linalg.norm, self.model.encode

### `enhance_job_description` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: ai
- Attribute calls: self._openai_enhance_description
- Direct calls: RuntimeError

### `generate_cover_letter` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: ai
- Attribute calls: candidate_data.get, job_data.get, logging.error, message.content.strip, self.openai_client.ChatCompletion.create
- Direct calls: RuntimeError

### `generate_professional_summary` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: ai
- Attribute calls: profile_data.get, self._openai_generate_summary
- Direct calls: RuntimeError

### `generate_star_bullets` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: ai
- Attribute calls: logging.error, message.content.strip, self.openai_client.ChatCompletion.create
- Direct calls: RuntimeError

### `get_embedding` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: model
- Attribute calls: logging.error, np.zeros, self.model.encode

### `optimize_ats` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: ai
- Attribute calls: logging.error, message.content.strip, self.openai_client.ChatCompletion.create
- Direct calls: RuntimeError, join

### `predict_job_category` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: predict
- Attribute calls: logging.error
- Direct calls: inverse_transform, max, predict, predict_proba, transform

### `process_document_intelligent` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: bayes, bayesian, engine, score
- Attribute calls: datetime.now, datetime.now.isoformat, self._calculate_overall_scores, self._empty_result, self._load_document, self._run_bayesian_analysis, self._run_fuzzy_analysis, self._run_llm_enhancement, self._run_neural_analysis, self._update_learning_table, self._update_stats, self.logger.error, self.logger.info, self.nlp_engine.analyze_sentiment, self.nlp_engine.extract_entities
- Direct calls: len, str

### `train_models` - `services\backend_api\services\ai\unified_ai_engine.py`
- AI signals: ai, classifier, predict
- Attribute calls: logging.info, self._train_industry_matcher, self._train_job_classifier, self._train_skill_predictor
- Direct calls: RuntimeError

### `__init__` - `services\backend_api\services\ai_data_index_service.py`
- AI signals: ai
- Attribute calls: self._load_file_manifest, self._load_persisted_state
- Direct calls: CareerTrojanPaths, Counter, DataIndexState

### `_append_run_record` - `services\backend_api\services\ai_data_index_service.py`
- AI signals: ai
- Attribute calls: f.write, json.dumps, logger.warning, self._state.parser_run_history.append, self.ai_data_final.mkdir
- Direct calls: asdict, open

### `_load_persisted_state` - `services\backend_api\services\ai_data_index_service.py`
- AI signals: ai
- Attribute calls: json.loads, line.strip, logger.warning, raw.get, self._index_file.exists, self._index_file.read_text, self._parser_runs_file.exists, self._parser_runs_file.read_text, self._parser_runs_file.read_text.strip, self._parser_runs_file.read_text.strip.split, self._state.parser_run_history.append
- Direct calls: AIDataIndexSummary, CategoryStats, ParserIndexSummary, ParserRunRecord, get

### `_persist_file_manifest` - `services\backend_api\services\ai_data_index_service.py`
- AI signals: ai
- Attribute calls: json.dump, logger.warning, self._state.file_manifest.items, self.ai_data_final.mkdir
- Direct calls: asdict, open

### `_persist_state` - `services\backend_api\services\ai_data_index_service.py`
- AI signals: ai
- Attribute calls: json.dump, logger.warning, self.ai_data_final.mkdir
- Direct calls: asdict, open

### `_write_parser_manifest` - `services\backend_api\services\ai_data_index_service.py`
- AI signals: ai
- Attribute calls: json.dump, logger.warning, self._detect_optional_dependencies, self.ai_data_final.mkdir
- Direct calls: asdict, open

### `full_index` - `services\backend_api\services\ai_data_index_service.py`
- AI signals: ai
- Attribute calls: self.index_ai_data, self.index_parser_sources

### `get_ai_data_index_service` - `services\backend_api\services\ai_data_index_service.py`
- AI signals: ai
- Direct calls: AIDataIndexService

### `index_ai_data` - `services\backend_api\services\ai_data_index_service.py`
- AI signals: ai
- Attribute calls: cat_path.exists, cat_path.rglob, categories.append, datetime.fromtimestamp, datetime.fromtimestamp.isoformat, datetime.utcnow, datetime.utcnow.isoformat, fp.relative_to, fp.stat, self.CATEGORY_MAP.items, self._industries.clear, self._industries.most_common, self._industries.update, self._locations.clear, self._locations.most_common
- Direct calls: AIDataIndexSummary, CategoryStats, FileIngestionRecord, _extract_industries, _extract_locations, _extract_skills, _file_hash, _safe_read_json, any, dict, isinstance, len, list, str

### `index_parser_sources` - `services\backend_api\services\ai_data_index_service.py`
- AI signals: ai
- Attribute calls: datetime.utcnow, datetime.utcnow.isoformat, entries.append, failed_index_file.exists, failed_index_file.read_text, failed_sources.get, failure_info.get, file_path.is_file, file_path.name.startswith, file_path.relative_to, file_path.stat, file_path.suffix.lower, file_types.get, json.loads, line.strip
- Direct calls: ParserIndexEntry, ParserIndexSummary, _file_hash, any, len, set, str

### `_request` - `services\backend_api\services\api_client.py`
- AI signals: ai
- Attribute calls: response.json, response.raise_for_status, self._client.request, self.logger.warning

### `__init__` - `services\backend_api\services\auto_screen_system.py`
- AI signals: ai
- Attribute calls: self._initialize_ai_services, self._load_screening_history
- Direct calls: Path

### `_calculate_data_quality_score` - `services\backend_api\services\auto_screen_system.py`
- AI signals: engine, score
- Attribute calls: engine_result.get, result.get, scores.append
- Direct calls: float, isinstance, len, sum

### `_find_user_files` - `services\backend_api\services\auto_screen_system.py`
- AI signals: ai
- Attribute calls: directory_path.exists, directory_path.rglob, file_path.is_file, file_path.suffix.lower, self._file_contains_user_data, self.data_directories.items, user_files.append, user_files.extend, user_id.lower, user_id.upper
- Direct calls: list, set

### `_initialize_ai_services` - `services\backend_api\services\auto_screen_system.py`
- AI signals: ai, engine, unified_ai_engine
- Direct calls: get_ai_data_manager, get_azure_integration, get_feedback_loop_system, get_sqlite_manager, get_unified_ai_engine, print

### `_process_file_with_ai` - `services\backend_api\services\auto_screen_system.py`
- AI signals: ai, engine
- Attribute calls: datetime.fromtimestamp, datetime.fromtimestamp.isoformat, datetime.now, file_path.read_text, file_path.stat, file_path.suffix.lower, self.ai_engine.process_document_intelligent
- Direct calls: print, str, total_seconds

### `screen_user_on_login` - `services\backend_api\services\auto_screen_system.py`
- AI signals: ai, score
- Attribute calls: analysis_result.get, datetime.now, datetime.now.isoformat, datetime.now.strftime, json.dumps, self._calculate_data_quality_score, self._find_user_files, self._generate_recommendations, self._process_file_with_ai, self._save_screening_history, self._save_screening_results, self.sqlite_manager.save_ai_learning_result
- Direct calls: append, len, print, str

## 5. Priority manual review targets

Review these first:

1. Matched frontend flows where backend AI signals appear
2. Unmatched frontend calls, because they often reveal stale endpoints, proxy-only paths, or incomplete migrations
3. Backend routes that call `service`, `router`, `engine`, `predict`, `score`, or `orchestrator`
4. Files named like `unified_ai_engine.py`, `orchestrator.py`, `router.py`, `feature_registry.py`, `context_assembler.py`

## 6. Limits of this pass

- Static analysis only; it does not execute the runtime
- Client wrappers and environment-based base URLs may hide some matches
- Dynamic route generation and dependency injection may require manual confirmation
