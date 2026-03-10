# CareerTrojan Runtime Wiring Map

Repository root: `J:\Codec - runtime version\Antigravity\careertrojan`

## Discovery summary

- Route handlers discovered: **333**
- Route handlers with AI-related call signals: **99**
- Service-like functions discovered: **437**
- Python files with AI/model/orchestration keywords: **288**

## 1. Route to service discovery

| Method | Full Path | Route Function | File | Likely Services / Calls | AI Signals |
|---|---|---|---|---|---|
| GET | `/health/live` | `health_live` | `kubernetes-infrastructure\snippets\fastapi\lifespan_health.py` | router.get | - |
| GET | `/health/ready` | `health_ready` | `kubernetes-infrastructure\snippets\fastapi\lifespan_health.py` | router.get | - |
| GET | `/health` | `health` | `services\backend_api\main.py` | - | - |
| GET | `/health/live` | `health_live` | `services\backend_api\main.py` | - | - |
| GET | `/health/ready` | `health_ready` | `services\backend_api\main.py` | - | - |
| GET | `/api/admin/v1/ai/content/jobs` | `content_jobs` | `services\backend_api\routers\admin.py` | router.get | - |
| POST | `/api/admin/v1/ai/content/run` | `content_run` | `services\backend_api\routers\admin.py` | router.post | - |
| GET | `/api/admin/v1/ai/content/status` | `content_status` | `services\backend_api\routers\admin.py` | router.get | - |
| GET | `/api/admin/v1/ai/enrichment/jobs` | `enrichment_jobs` | `services\backend_api\routers\admin.py` | router.get | - |
| POST | `/api/admin/v1/ai/enrichment/run` | `enrichment_run` | `services\backend_api\routers\admin.py` | router.post | - |
| GET | `/api/admin/v1/ai/enrichment/status` | `enrichment_status` | `services\backend_api\routers\admin.py` | router.get | ai |
| GET | `/api/admin/v1/batch/jobs` | `batch_jobs` | `services\backend_api\routers\admin.py` | router.get | - |
| POST | `/api/admin/v1/batch/run` | `batch_run` | `services\backend_api\routers\admin.py` | router.post | - |
| GET | `/api/admin/v1/batch/status` | `batch_status` | `services\backend_api\routers\admin.py` | router.get | - |
| GET | `/api/admin/v1/compliance/audit/events` | `audit_events` | `services\backend_api\routers\admin.py` | router.get | model |
| GET | `/api/admin/v1/compliance/summary` | `compliance_summary` | `services\backend_api\routers\admin.py` | router.get | - |
| GET | `/api/admin/v1/dashboard/snapshot` | `dashboard_snapshot` | `services\backend_api\routers\admin.py` | router.get | ai, model |
| GET | `/api/admin/v1/email/analytics` | `email_analytics` | `services\backend_api\routers\admin.py` | router.get | - |
| GET | `/api/admin/v1/email/jobs` | `email_jobs` | `services\backend_api\routers\admin.py` | router.get | - |
| GET | `/api/admin/v1/email/logs` | `email_logs` | `services\backend_api\routers\admin.py` | router.get | - |
| POST | `/api/admin/v1/email/send_bulk` | `send_bulk_email` | `services\backend_api\routers\admin.py` | router.post | ai |
| POST | `/api/admin/v1/email/send_test` | `send_test_email` | `services\backend_api\routers\admin.py` | router.post | ai |
| GET | `/api/admin/v1/email/status` | `email_status` | `services\backend_api\routers\admin.py` | router.get | - |
| POST | `/api/admin/v1/email/sync` | `email_sync` | `services\backend_api\routers\admin.py` | router.post | - |
| POST | `/api/admin/v1/integrations/gmail/configure` | `configure_gmail` | `services\backend_api\routers\admin.py` | router.post | - |
| POST | `/api/admin/v1/integrations/klaviyo/configure` | `configure_klaviyo` | `services\backend_api\routers\admin.py` | router.post | - |
| POST | `/api/admin/v1/integrations/reminders/non-live` | `send_non_live_api_reminder` | `services\backend_api\routers\admin.py` | router.post | ai |
| POST | `/api/admin/v1/integrations/sendgrid/configure` | `configure_sendgrid` | `services\backend_api\routers\admin.py` | router.post | - |
| GET | `/api/admin/v1/integrations/status` | `integrations_status` | `services\backend_api\routers\admin.py` | router.get | - |
| POST | `/api/admin/v1/integrations/{provider}/disconnect` | `disconnect_integration` | `services\backend_api\routers\admin.py` | router.post | - |
| GET | `/api/admin/v1/parsers/jobs` | `parsers_jobs` | `services\backend_api\routers\admin.py` | router.get | - |
| POST | `/api/admin/v1/parsers/run` | `parsers_run` | `services\backend_api\routers\admin.py` | router.post | - |
| GET | `/api/admin/v1/parsers/status` | `parsers_status` | `services\backend_api\routers\admin.py` | parser_root.exists, router.get | - |
| GET | `/api/admin/v1/payments/disputes` | `payment_disputes` | `services\backend_api\routers\admin.py` | router.get | model |
| GET | `/api/admin/v1/system/activity` | `system_activity` | `services\backend_api\routers\admin.py` | router.get | - |
| GET | `/api/admin/v1/system/health` | `system_health` | `services\backend_api\routers\admin.py` | router.get | - |
| GET | `/api/admin/v1/tokens/users/{user_id}/ledger` | `user_token_ledger` | `services\backend_api\routers\admin.py` | router.get | - |
| GET | `/api/admin/v1/user_subscriptions` | `user_subscriptions` | `services\backend_api\routers\admin.py` | router.get | - |
| GET | `/api/admin/v1/users` | `list_users` | `services\backend_api\routers\admin.py` | router.get | - |
| GET | `/api/admin/v1/users/metrics` | `user_metrics` | `services\backend_api\routers\admin.py` | router.get | - |
| GET | `/api/admin/v1/users/security` | `user_security` | `services\backend_api\routers\admin.py` | router.get | - |
| GET | `/api/admin/v1/users/{user_id}` | `get_user` | `services\backend_api\routers\admin.py` | router.get | - |
| PUT | `/api/admin/v1/users/{user_id}/disable` | `disable_user` | `services\backend_api\routers\admin.py` | router.put | - |
| PUT | `/api/admin/v1/users/{user_id}/plan` | `set_user_plan` | `services\backend_api\routers\admin.py` | router.put | - |
| GET | `/api/admin/v1/abuse/queue` | `queue` | `services\backend_api\routers\admin_abuse.py` | router.get | - |
| POST | `/api/admin/email/send_bulk` | `send_bulk_email_legacy` | `services\backend_api\routers\admin_legacy.py` | router.post | ai |
| POST | `/api/admin/email/send_test` | `send_test_email_legacy` | `services\backend_api\routers\admin_legacy.py` | router.post | ai |
| POST | `/api/admin/integrations/klaviyo/configure` | `configure_klaviyo_legacy` | `services\backend_api\routers\admin_legacy.py` | router.post | - |
| POST | `/api/admin/integrations/sendgrid/configure` | `configure_sendgrid_legacy` | `services\backend_api\routers\admin_legacy.py` | router.post | - |
| GET | `/api/admin/integrations/status` | `integrations_status_legacy` | `services\backend_api\routers\admin_legacy.py` | router.get | - |
| GET | `/api/admin/v1/parsing/parse` | `list_admin_parses` | `services\backend_api\routers\admin_parsing.py` | router.get | - |
| POST | `/api/admin/v1/parsing/parse` | `admin_parse_file` | `services\backend_api\routers\admin_parsing.py` | client.post, httpx.AsyncClient, router.post | - |
| GET | `/api/admin/v1/parsing/parse/{parse_id}` | `get_admin_parse` | `services\backend_api\routers\admin_parsing.py` | router.get | - |
| GET | `/admin/subscriptions` | `get_subscriptions` | `services\backend_api\routers\admin_tokens.py` | router.get | - |
| GET | `/admin/tokens/analytics` | `get_usage_analytics` | `services\backend_api\routers\admin_tokens.py` | router.get | - |
| GET | `/admin/tokens/config` | `get_token_config` | `services\backend_api\routers\admin_tokens.py` | router.get | - |
| GET | `/admin/tokens/costs` | `get_token_costs` | `services\backend_api\routers\admin_tokens.py` | router.get | - |
| POST | `/admin/tokens/costs/update` | `update_token_cost` | `services\backend_api\routers\admin_tokens.py` | router.post, router.put | - |
| PUT | `/admin/tokens/costs/{feature}` | `update_token_cost` | `services\backend_api\routers\admin_tokens.py` | router.post, router.put | - |
| POST | `/admin/tokens/ledger/emit` | `emit_ledger_event` | `services\backend_api\routers\admin_tokens.py` | router.post | - |
| GET | `/admin/tokens/ledger/{user_id}` | `get_user_token_ledger` | `services\backend_api\routers\admin_tokens.py` | router.get | - |
| GET | `/admin/tokens/logs` | `get_usage_logs` | `services\backend_api\routers\admin_tokens.py` | router.get | - |
| GET | `/admin/tokens/plans` | `get_token_config` | `services\backend_api\routers\admin_tokens.py` | router.get | - |
| POST | `/admin/tokens/plans` | `put_token_config` | `services\backend_api\routers\admin_tokens.py` | router.post, router.put | - |
| PUT | `/admin/tokens/plans` | `put_token_config` | `services\backend_api\routers\admin_tokens.py` | router.post, router.put | - |
| GET | `/admin/tokens/subscriptions` | `get_subscriptions` | `services\backend_api\routers\admin_tokens.py` | router.get | - |
| GET | `/admin/tokens/unit-economics` | `get_token_unit_economics` | `services\backend_api\routers\admin_tokens.py` | router.get | - |
| GET | `/admin/tokens/usage` | `get_token_usage` | `services\backend_api\routers\admin_tokens.py` | router.get | - |
| GET | `/api/admin/v1/tokens/config` | `get_token_config` | `services\backend_api\routers\admin_tokens.py` | router.get | - |
| PUT | `/api/admin/v1/tokens/config` | `put_token_config` | `services\backend_api\routers\admin_tokens.py` | router.post, router.put | - |
| GET | `/api/admin/v1/tokens/usage` | `get_token_usage` | `services\backend_api\routers\admin_tokens.py` | router.get | - |
| GET | `/api/ai-data/v1/automated/candidates` | `get_automated_candidates` | `services\backend_api\routers\ai_data.py` | router.get | - |
| GET | `/api/ai-data/v1/companies` | `get_companies` | `services\backend_api\routers\ai_data.py` | router.get | - |
| GET | `/api/ai-data/v1/email_extracted` | `get_email_extracted` | `services\backend_api\routers\ai_data.py` | router.get | ai |
| GET | `/api/ai-data/v1/emails` | `get_emails` | `services\backend_api\routers\ai_data.py` | router.get | ai |
| GET | `/api/ai-data/v1/emails/diagnostics` | `get_emails_diagnostics` | `services\backend_api\routers\ai_data.py` | router.get | ai |
| GET | `/api/ai-data/v1/emails/providers/{provider}` | `get_emails_provider_payload` | `services\backend_api\routers\ai_data.py` | router.get | - |
| GET | `/api/ai-data/v1/emails/providers/{provider}/guarded-payload` | `get_guarded_email_provider_payload` | `services\backend_api\routers\ai_data.py` | router.get | - |
| GET | `/api/ai-data/v1/emails/summary` | `get_emails_summary` | `services\backend_api\routers\ai_data.py` | router.get | ai |
| GET | `/api/ai-data/v1/emails/tracking` | `get_emails_tracking` | `services\backend_api\routers\ai_data.py` | router.get | ai |
| POST | `/api/ai-data/v1/emails/tracking` | `create_emails_tracking_record` | `services\backend_api\routers\ai_data.py` | router.post | ai |
| GET | `/api/ai-data/v1/emails/tracking/reroute-targets` | `get_emails_tracking_reroute_targets` | `services\backend_api\routers\ai_data.py` | router.get | ai |
| GET | `/api/ai-data/v1/emails/tracking/summary` | `get_emails_tracking_summary` | `services\backend_api\routers\ai_data.py` | router.get | ai |
| GET | `/api/ai-data/v1/job_descriptions` | `get_job_descriptions` | `services\backend_api\routers\ai_data.py` | router.get | - |
| GET | `/api/ai-data/v1/job_titles` | `get_job_titles` | `services\backend_api\routers\ai_data.py` | router.get | - |
| GET | `/api/ai-data/v1/locations` | `get_locations` | `services\backend_api\routers\ai_data.py` | router.get | - |
| GET | `/api/ai-data/v1/metadata` | `get_metadata` | `services\backend_api\routers\ai_data.py` | router.get | - |
| GET | `/api/ai-data/v1/normalized` | `get_normalized_data` | `services\backend_api\routers\ai_data.py` | router.get | - |
| GET | `/api/ai-data/v1/parsed_resumes` | `get_parsed_resumes` | `services\backend_api\routers\ai_data.py` | router.get | - |
| GET | `/api/ai-data/v1/parsed_resumes/{doc_id}` | `get_parsed_resume` | `services\backend_api\routers\ai_data.py` | router.get | - |
| GET | `/api/ai-data/v1/parser/ingestion-status` | `get_parser_ingestion_status` | `services\backend_api\routers\ai_data.py` | router.get | - |
| GET | `/api/ai-data/v1/status` | `get_ai_data_status` | `services\backend_api\routers\ai_data.py` | router.get | ai |
| GET | `/api/ai-data/v1/user_data/files` | `list_user_data_files` | `services\backend_api\routers\ai_data.py` | router.get | - |
| GET | `/api/analytics/v1/dashboard` | `get_dashboard_data` | `services\backend_api\routers\analytics.py` | router.get | model |
| GET | `/api/analytics/v1/recent_jobs` | `get_recent_jobs` | `services\backend_api\routers\analytics.py` | router.get | - |
| GET | `/api/analytics/v1/recent_resumes` | `get_recent_resumes` | `services\backend_api\routers\analytics.py` | router.get | - |
| GET | `/api/analytics/v1/statistics` | `get_statistics` | `services\backend_api\routers\analytics.py` | router.get | - |
| GET | `/api/analytics/v1/system_health` | `get_system_health` | `services\backend_api\routers\analytics.py` | router.get | ai, model |
| POST | `/api/admin/v1/anti-gaming/check` | `check` | `services\backend_api\routers\anti_gaming.py` | router.post | - |
| POST | `/api/auth/v1/2fa/generate` | `generate_2fa` | `services\backend_api\routers\auth.py` | router.post | - |
| POST | `/api/auth/v1/2fa/verify` | `verify_2fa` | `services\backend_api\routers\auth.py` | router.post | - |
| GET | `/api/auth/v1/google/callback` | `google_callback` | `services\backend_api\routers\auth.py` | router.get | - |
| GET | `/api/auth/v1/google/login` | `google_login` | `services\backend_api\routers\auth.py` | router.get | - |
| POST | `/api/auth/v1/login` | `login` | `services\backend_api\routers\auth.py` | router.post | - |
| POST | `/api/auth/v1/register` | `register` | `services\backend_api\routers\auth.py` | router.post | model |
| POST | `/api/blockers/v1/detect` | `detect_blockers` | `services\backend_api\routers\blockers.py` | connector.detect_blockers_for_user, get_blocker_connector, router.post | - |
| POST | `/api/blockers/v1/improvement-plans/generate` | `generate_plans` | `services\backend_api\routers\blockers.py` | BlockerService, router.post | - |
| GET | `/api/blockers/v1/user/{user_id}` | `get_user_blockers` | `services\backend_api\routers\blockers.py` | BlockerService, router.get, service.get_user_blockers | - |
| GET | `/career-compass/cluster/{cluster_id}` | `career_compass_cluster` | `services\backend_api\routers\career_compass.py` | router.get | - |
| POST | `/career-compass/culdesac-check` | `career_compass_culdesac_check` | `services\backend_api\routers\career_compass.py` | router.post | - |
| GET | `/career-compass/map` | `career_compass_map` | `services\backend_api\routers\career_compass.py` | router.get | - |
| GET | `/career-compass/market-signal` | `career_compass_market_signal` | `services\backend_api\routers\career_compass.py` | router.get | - |
| POST | `/career-compass/mentor-match` | `career_compass_mentor_match` | `services\backend_api\routers\career_compass.py` | router.post | - |
| GET | `/career-compass/routes` | `career_compass_routes` | `services\backend_api\routers\career_compass.py` | router.get | vector |
| POST | `/career-compass/runway` | `career_compass_runway` | `services\backend_api\routers\career_compass.py` | router.post | - |
| POST | `/career-compass/save-scenario` | `career_compass_save_scenario` | `services\backend_api\routers\career_compass.py` | router.post | - |
| POST | `/career-compass/spider-overlay` | `career_compass_spider_overlay` | `services\backend_api\routers\career_compass.py` | router.post | vector |
| POST | `/api/coaching/v1/answers/review` | `review_answer` | `services\backend_api\routers\coaching.py` | router.post | - |
| POST | `/api/coaching/v1/bundle` | `get_coaching_bundle` | `services\backend_api\routers\coaching.py` | router.post | - |
| GET | `/api/coaching/v1/health` | `coaching_health` | `services\backend_api\routers\coaching.py` | router.get | - |
| GET | `/api/coaching/v1/history` | `get_coaching_history` | `services\backend_api\routers\coaching.py` | router.get | model |
| POST | `/api/coaching/v1/learning/feedback` | `submit_interview_learning_feedback` | `services\backend_api\routers\coaching.py` | router.post | - |
| GET | `/api/coaching/v1/learning/profile` | `fetch_interview_learning_profile` | `services\backend_api\routers\coaching.py` | router.get | - |
| POST | `/api/coaching/v1/plan/90day` | `generate_90day_plan` | `services\backend_api\routers\coaching.py` | get_interview_coaching_service, router.post, service.get_90day_plan | - |
| POST | `/api/coaching/v1/profile/bridge-lockstep` | `build_profile_bridge_lockstep` | `services\backend_api\routers\coaching.py` | router.post | - |
| GET | `/api/coaching/v1/profile/config` | `get_profile_coach_config` | `services\backend_api\routers\coaching.py` | router.get | - |
| GET | `/api/coaching/v1/profile/cv-upload-step` | `get_profile_cv_upload_step_contract` | `services\backend_api\routers\coaching.py` | router.get | - |
| POST | `/api/coaching/v1/profile/reflect` | `profile_coach_reflect` | `services\backend_api\routers\coaching.py` | router.post | ai |
| GET | `/api/coaching/v1/profile/system-prompt` | `get_profile_coach_system_prompt` | `services\backend_api\routers\coaching.py` | router.get | - |
| POST | `/api/coaching/v1/questions/generate` | `generate_questions` | `services\backend_api\routers\coaching.py` | router.post | - |
| POST | `/api/coaching/v1/role/detect` | `detect_role` | `services\backend_api\routers\coaching.py` | get_interview_coaching_service, router.post, service.detect_role_function | - |
| POST | `/api/coaching/v1/stories/generate` | `generate_stories` | `services\backend_api\routers\coaching.py` | router.post | - |
| GET | `/api/credits/v1/actions` | `get_action_costs` | `services\backend_api\routers\credits.py` | router.get | - |
| GET | `/api/credits/v1/balance` | `get_balance` | `services\backend_api\routers\credits.py` | get_credit_manager, manager.get_usage_summary, router.get | - |
| GET | `/api/credits/v1/can-perform/{action_id}` | `can_perform_action` | `services\backend_api\routers\credits.py` | get_credit_manager, manager.can_perform_action, manager.get_user_credits, router.get | - |
| POST | `/api/credits/v1/consume` | `consume_credits` | `services\backend_api\routers\credits.py` | get_credit_manager, manager.consume_credits, router.post | - |
| GET | `/api/credits/v1/health` | `health_check` | `services\backend_api\routers\credits.py` | router.get | - |
| GET | `/api/credits/v1/plans` | `get_plans` | `services\backend_api\routers\credits.py` | get_credit_manager, manager.get_user_credits, router.get | - |
| POST | `/api/credits/v1/teaser` | `get_teaser` | `services\backend_api\routers\credits.py` | router.post | - |
| POST | `/api/credits/v1/upgrade/{plan_tier}` | `upgrade_plan` | `services\backend_api\routers\credits.py` | get_credit_manager, manager.set_user_plan, router.post | - |
| GET | `/api/credits/v1/usage` | `get_usage_details` | `services\backend_api\routers\credits.py` | get_credit_manager, manager.get_usage_summary, router.get | - |
| GET | `/api/data-index/v1/ai-data/categories` | `get_ai_data_categories` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.get, service.get_ai_data_summary | ai |
| GET | `/api/data-index/v1/ai-data/industries` | `get_top_industries` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.get, service.get_ai_data_summary | ai |
| GET | `/api/data-index/v1/ai-data/industries/search` | `search_industries` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.get, service.search_industries | ai |
| GET | `/api/data-index/v1/ai-data/locations` | `get_top_locations` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.get, service.get_ai_data_summary | ai |
| GET | `/api/data-index/v1/ai-data/locations/search` | `search_locations` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.get, service.search_locations | ai |
| GET | `/api/data-index/v1/ai-data/skills` | `get_top_skills` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.get, service.get_ai_data_summary | ai |
| GET | `/api/data-index/v1/ai-data/skills/search` | `search_skills` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.get, service.search_skills | ai |
| GET | `/api/data-index/v1/ai-data/summary` | `get_ai_data_summary` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.get, service.get_ai_data_summary | ai |
| GET | `/api/data-index/v1/dependencies` | `get_optional_dependencies` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.get, service._detect_optional_dependencies | ai |
| GET | `/api/data-index/v1/files/by-category/{category}` | `get_files_by_category` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.get, service._state.file_manifest.values | ai |
| GET | `/api/data-index/v1/files/manifest-stats` | `get_file_manifest_stats` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.get, service.get_file_manifest_stats | ai |
| GET | `/api/data-index/v1/files/new-data-summary` | `get_new_data_summary` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.get, service.get_new_data_summary | ai |
| GET | `/api/data-index/v1/files/since` | `get_files_since_timestamp` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.get, service.get_files_since | ai |
| GET | `/api/data-index/v1/health` | `get_index_health` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.get, service.get_state | ai |
| POST | `/api/data-index/v1/index/ai-data` | `trigger_ai_data_index` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.post, service.index_ai_data | ai |
| POST | `/api/data-index/v1/index/full` | `trigger_full_index` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.post, service.full_index | ai |
| POST | `/api/data-index/v1/index/incremental` | `trigger_incremental_index` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.post, service.incremental_index | ai |
| POST | `/api/data-index/v1/index/parser` | `trigger_parser_index` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.post, service.index_parser_sources | ai |
| GET | `/api/data-index/v1/parser/file-types` | `get_parser_file_types` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.get, service.get_parser_summary | ai |
| GET | `/api/data-index/v1/parser/runs` | `get_parser_runs` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.get, service.get_parser_run_history | ai |
| POST | `/api/data-index/v1/parser/runs` | `record_parser_run` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.post, service.record_parser_run | ai |
| GET | `/api/data-index/v1/parser/status` | `get_parser_status` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.get, service.get_parser_summary | ai |
| GET | `/api/data-index/v1/parser/summary` | `get_parser_summary` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.get, service.get_parser_summary | ai |
| GET | `/api/data-index/v1/status` | `get_index_status` | `services\backend_api\routers\data_index.py` | get_ai_data_index_service, router.get, service.get_state | ai |
| GET | `/api/gdpr/v1/audit-log` | `my_audit_log` | `services\backend_api\routers\gdpr.py` | router.get | model |
| GET | `/api/gdpr/v1/consent` | `get_consent` | `services\backend_api\routers\gdpr.py` | router.get | model |
| POST | `/api/gdpr/v1/consent` | `grant_consent` | `services\backend_api\routers\gdpr.py` | router.post | model |
| DELETE | `/api/gdpr/v1/delete-account` | `delete_my_account` | `services\backend_api\routers\gdpr.py` | router.delete | model |
| GET | `/api/gdpr/v1/export` | `export_my_data` | `services\backend_api\routers\gdpr.py` | router.get | model |
| POST | `/api/insights/v1/cohort/resolve` | `resolve_cohort` | `services\backend_api\routers\insights.py` | router.post | - |
| GET | `/api/insights/v1/graph` | `get_graph_data` | `services\backend_api\routers\insights.py` | router.get | - |
| GET | `/api/insights/v1/quadrant` | `get_quadrant_data` | `services\backend_api\routers\insights.py` | router.get | - |
| GET | `/api/insights/v1/skills/radar` | `get_skills_radar` | `services\backend_api\routers\insights.py` | router.get | - |
| GET | `/api/insights/v1/terms/cloud` | `get_term_cloud` | `services\backend_api\routers\insights.py` | router.get | - |
| GET | `/api/insights/v1/terms/cooccurrence` | `get_cooccurrence` | `services\backend_api\routers\insights.py` | router.get | - |
| GET | `/api/insights/v1/visuals` | `get_visual_catalogue` | `services\backend_api\routers\insights.py` | router.get | - |
| POST | `/api/intelligence/v1/company/briefing` | `company_briefing` | `services\backend_api\routers\intelligence.py` | router.post | - |
| POST | `/api/intelligence/v1/company/extract` | `company_extract` | `services\backend_api\routers\intelligence.py` | router.post | - |
| GET | `/api/intelligence/v1/company/registry` | `company_registry` | `services\backend_api\routers\intelligence.py` | router.get | - |
| GET | `/api/intelligence/v1/company/registry/analytics` | `company_registry_analytics` | `services\backend_api\routers\intelligence.py` | router.get | - |
| GET | `/api/intelligence/v1/company/registry/events` | `company_registry_events` | `services\backend_api\routers\intelligence.py` | router.get | - |
| POST | `/api/intelligence/v1/enrich` | `enrich_resume` | `services\backend_api\routers\intelligence.py` | router.post | model |
| GET | `/api/intelligence/v1/market` | `market_intel` | `services\backend_api\routers\intelligence.py` | router.get | - |
| GET | `/api/intelligence/v1/pipeline/ops-summary` | `pipeline_ops_summary` | `services\backend_api\routers\intelligence.py` | router.get | - |
| POST | `/api/intelligence/v1/stats/descriptive` | `get_stats` | `services\backend_api\routers\intelligence.py` | engine.descriptive_stats, router.post | engine |
| POST | `/api/intelligence/v1/stats/regression` | `regression` | `services\backend_api\routers\intelligence.py` | engine.linear_regression, router.post | engine, regression |
| GET | `/api/intelligence/v1/support/status` | `support_status` | `services\backend_api\routers\intelligence.py` | router.get | - |
| GET | `/api/jobs/v1/index` | `get_job_index` | `services\backend_api\routers\jobs.py` | router.get | ai |
| GET | `/api/jobs/v1/search` | `search_jobs` | `services\backend_api\routers\jobs.py` | router.get | ai |
| POST | `/api/lenses/v1/composite` | `build_composite` | `services\backend_api\routers\lenses.py` | router.post | - |
| POST | `/api/lenses/v1/covey` | `build_covey` | `services\backend_api\routers\lenses.py` | router.post | - |
| POST | `/api/lenses/v1/spider` | `build_spider` | `services\backend_api\routers\lenses.py` | StatisticalAnalysisEngine, engine.bayesian_probability, router.post | bayes, bayesian, engine, score |
| GET | `/api/admin/v1/logs/tail` | `tail_log` | `services\backend_api\routers\logs.py` | router.get | ai |
| GET | `/api/mapping/v1/endpoints` | `endpoints` | `services\backend_api\routers\mapping.py` | router.get | - |
| GET | `/api/mapping/v1/graph` | `graph` | `services\backend_api\routers\mapping.py` | router.get | - |
| GET | `/api/mapping/v1/registry` | `registry` | `services\backend_api\routers\mapping.py` | router.get | - |
| GET | `/api/mentor/v1/health` | `health_check` | `services\backend_api\routers\mentor.py` | router.get | - |
| GET | `/api/mentor/v1/list` | `list_mentors` | `services\backend_api\routers\mentor.py` | router.get | - |
| GET | `/api/mentor/v1/profile-by-user/{user_id}` | `get_mentor_profile_by_user` | `services\backend_api\routers\mentor.py` | router.get | - |
| PUT | `/api/mentor/v1/{mentor_profile_id}/availability` | `update_availability` | `services\backend_api\routers\mentor.py` | router.put | - |
| GET | `/api/mentor/v1/{mentor_profile_id}/dashboard-stats` | `get_dashboard_stats` | `services\backend_api\routers\mentor.py` | router.get | - |
| GET | `/api/mentor/v1/{mentor_profile_id}/packages` | `get_mentor_packages` | `services\backend_api\routers\mentor.py` | router.get | - |
| POST | `/api/mentor/v1/{mentor_profile_id}/packages` | `create_package` | `services\backend_api\routers\mentor.py` | router.post | - |
| DELETE | `/api/mentor/v1/{mentor_profile_id}/packages/{package_id}` | `delete_package` | `services\backend_api\routers\mentor.py` | router.delete | - |
| GET | `/api/mentor/v1/{mentor_profile_id}/packages/{package_id}` | `get_package` | `services\backend_api\routers\mentor.py` | router.get | - |
| PUT | `/api/mentor/v1/{mentor_profile_id}/packages/{package_id}` | `update_package` | `services\backend_api\routers\mentor.py` | router.put | - |
| GET | `/api/mentor/v1/{mentor_profile_id}/profile` | `get_mentor_profile` | `services\backend_api\routers\mentor.py` | router.get | - |
| POST | `/api/mentorship/v1/applications` | `submit_mentor_application` | `services\backend_api\routers\mentorship.py` | router.post, service.submit_mentor_application | - |
| GET | `/api/mentorship/v1/applications/pending` | `get_pending_applications` | `services\backend_api\routers\mentorship.py` | router.get, service.get_pending_applications | - |
| POST | `/api/mentorship/v1/applications/{application_id}/approve` | `approve_mentor_application` | `services\backend_api\routers\mentorship.py` | router.post, service.approve_mentor_application | - |
| POST | `/api/mentorship/v1/applications/{application_id}/reject` | `reject_mentor_application` | `services\backend_api\routers\mentorship.py` | router.post, service.reject_mentor_application | - |
| POST | `/api/mentorship/v1/documents` | `create_requirement_document` | `services\backend_api\routers\mentorship.py` | router.post, service.create_requirement_document | - |
| GET | `/api/mentorship/v1/documents/{doc_id}` | `get_requirement_document` | `services\backend_api\routers\mentorship.py` | router.get, service.get_requirement_document | - |
| POST | `/api/mentorship/v1/documents/{doc_id}/reject` | `reject_document` | `services\backend_api\routers\mentorship.py` | router.post, service.reject_document | - |
| POST | `/api/mentorship/v1/documents/{doc_id}/sign` | `sign_document` | `services\backend_api\routers\mentorship.py` | router.post, service.sign_document | - |
| GET | `/api/mentorship/v1/health` | `health_check` | `services\backend_api\routers\mentorship.py` | router.get | - |
| POST | `/api/mentorship/v1/invoices` | `create_invoice` | `services\backend_api\routers\mentorship.py` | router.post, service.create_invoice | - |
| GET | `/api/mentorship/v1/invoices/mentor/{mentor_id}` | `get_mentor_invoices` | `services\backend_api\routers\mentorship.py` | router.get, service.get_mentor_invoices | - |
| POST | `/api/mentorship/v1/invoices/{invoice_id}/confirm-completion` | `confirm_service_completion` | `services\backend_api\routers\mentorship.py` | router.post, service.confirm_service_completion | - |
| POST | `/api/mentorship/v1/invoices/{invoice_id}/dispute` | `raise_dispute` | `services\backend_api\routers\mentorship.py` | router.post, service.raise_dispute | ai |
| POST | `/api/mentorship/v1/invoices/{invoice_id}/mark-paid` | `mark_invoice_paid` | `services\backend_api\routers\mentorship.py` | router.post, service.mark_invoice_paid | ai |
| POST | `/api/mentorship/v1/invoices/{invoice_id}/service-delivered` | `mark_service_delivered` | `services\backend_api\routers\mentorship.py` | router.post, service.mark_service_delivered | - |
| POST | `/api/mentorship/v1/links` | `create_mentorship_link` | `services\backend_api\routers\mentorship.py` | router.post, service.create_mentorship_link | - |
| GET | `/api/mentorship/v1/links/mentor/{mentor_id}` | `get_mentor_connections` | `services\backend_api\routers\mentorship.py` | router.get, service.get_mentor_connections | - |
| GET | `/api/mentorship/v1/links/user/{user_id}` | `get_user_connections` | `services\backend_api\routers\mentorship.py` | router.get, service.get_user_connections | - |
| PATCH | `/api/mentorship/v1/links/{link_id}/status` | `update_link_status` | `services\backend_api\routers\mentorship.py` | router.patch, service.update_link_status | - |
| POST | `/api/mentorship/v1/notes` | `create_note` | `services\backend_api\routers\mentorship.py` | router.post, service.create_note | - |
| GET | `/api/mentorship/v1/notes/{link_id}` | `get_notes_for_link` | `services\backend_api\routers\mentorship.py` | router.get, service.get_notes_for_link | - |
| PATCH | `/api/mentorship/v1/notes/{note_id}` | `update_note` | `services\backend_api\routers\mentorship.py` | router.patch, service.update_note | - |
| GET | `/api/mentorship/v1/summary` | `get_mentorship_summary` | `services\backend_api\routers\mentorship.py` | router.get | - |
| GET | `/api/ontology/v1/phrases` | `list_phrases` | `services\backend_api\routers\ontology.py` | router.get | - |
| GET | `/api/ontology/v1/phrases/summary` | `phrases_summary` | `services\backend_api\routers\ontology.py` | router.get | - |
| POST | `/api/ops/v1/anti-gaming/check` | `check_abuse` | `services\backend_api\routers\ops.py` | router.post | - |
| POST | `/api/ops/v1/logs/lock` | `lock_audit_logs` | `services\backend_api\routers\ops.py` | router.post | - |
| POST | `/api/ops/v1/processing/start` | `start_processing` | `services\backend_api\routers\ops.py` | router.post | - |
| GET | `/api/ops/v1/processing/status` | `processing_status` | `services\backend_api\routers\ops.py` | router.get | - |
| GET | `/api/ops/v1/stats/public` | `get_public_stats` | `services\backend_api\routers\ops.py` | router.get | - |
| GET | `/api/ops/v1/tokens/config` | `get_token_config` | `services\backend_api\routers\ops.py` | router.get | - |
| POST | `/api/payment/v1/cancel` | `cancel_subscription` | `services\backend_api\routers\payment.py` | braintree_service.cancel_subscription, braintree_service.is_configured, router.post | ai, model |
| GET | `/api/payment/v1/client-token` | `get_client_token` | `services\backend_api\routers\payment.py` | braintree_service.generate_client_token, braintree_service.is_configured, router.get | ai |
| GET | `/api/payment/v1/gateway-info` | `gateway_info` | `services\backend_api\routers\payment.py` | braintree_service.is_configured, router.get | ai |
| GET | `/api/payment/v1/health` | `health_check` | `services\backend_api\routers\payment.py` | braintree_service.is_configured, router.get | ai |
| GET | `/api/payment/v1/history` | `get_payment_history` | `services\backend_api\routers\payment.py` | router.get | model |
| GET | `/api/payment/v1/methods` | `list_payment_methods` | `services\backend_api\routers\payment.py` | braintree_service.is_configured, braintree_service.list_payment_methods, router.get | ai |
| POST | `/api/payment/v1/methods` | `add_payment_method` | `services\backend_api\routers\payment.py` | braintree_service.create_payment_method, braintree_service.find_or_create_customer, braintree_service.is_configured, router.post | ai |
| DELETE | `/api/payment/v1/methods/{token}` | `remove_payment_method` | `services\backend_api\routers\payment.py` | braintree_service.delete_payment_method, braintree_service.is_configured, router.delete | ai |
| GET | `/api/payment/v1/plans` | `get_plans` | `services\backend_api\routers\payment.py` | router.get | - |
| GET | `/api/payment/v1/plans/{plan_id}` | `get_plan` | `services\backend_api\routers\payment.py` | router.get | - |
| POST | `/api/payment/v1/process` | `process_payment` | `services\backend_api\routers\payment.py` | router.post | ai, model |
| POST | `/api/payment/v1/refund/{transaction_id}` | `refund_transaction` | `services\backend_api\routers\payment.py` | braintree_service.is_configured, braintree_service.refund_transaction, router.post | ai |
| GET | `/api/payment/v1/subscription` | `get_current_subscription` | `services\backend_api\routers\payment.py` | router.get | model |
| GET | `/api/payment/v1/transactions/{transaction_id}` | `get_transaction` | `services\backend_api\routers\payment.py` | braintree_service.find_transaction, braintree_service.is_configured, router.get | ai |
| POST | `/api/v1/profile-coach/finish` | `finish_profile_coach` | `services\backend_api\routers\profile_coach_v1.py` | router.post | - |
| POST | `/api/v1/profile-coach/respond` | `respond_profile_coach` | `services\backend_api\routers\profile_coach_v1.py` | router.post | ai |
| POST | `/api/v1/profile-coach/start` | `start_profile_coach` | `services\backend_api\routers\profile_coach_v1.py` | router.post | - |
| POST | `/api/v1/profile/build` | `build_profile` | `services\backend_api\routers\profile_v1.py` | router.post | - |
| POST | `/api/v1/profile/signals` | `build_profile_signals` | `services\backend_api\routers\profile_v1.py` | router.post | vector |
| GET | `/api/resume/v1` | `list_resumes` | `services\backend_api\routers\resume.py` | router.get | - |
| POST | `/api/resume/v1/enrich` | `enrich` | `services\backend_api\routers\resume.py` | router.post | - |
| POST | `/api/resume/v1/parse` | `parse` | `services\backend_api\routers\resume.py` | router.post | - |
| POST | `/api/resume/v1/upload` | `upload_resume` | `services\backend_api\routers\resume.py` | get_company_intel_service, get_company_intel_service.ingest_resume_text, router.post | - |
| GET | `/api/resume/v1/{resume_id}` | `get_resume` | `services\backend_api\routers\resume.py` | router.get | - |
| GET | `/api/rewards/v1/health` | `health_check` | `services\backend_api\routers\rewards.py` | router.get | - |
| GET | `/api/rewards/v1/leaderboard` | `get_leaderboard` | `services\backend_api\routers\rewards.py` | router.get | ai |
| GET | `/api/rewards/v1/ownership-stats` | `get_ownership_stats` | `services\backend_api\routers\rewards.py` | router.get | - |
| GET | `/api/rewards/v1/referral` | `get_referral_code` | `services\backend_api\routers\rewards.py` | router.get | - |
| POST | `/api/rewards/v1/referral/claim` | `claim_referral` | `services\backend_api\routers\rewards.py` | router.post | - |
| GET | `/api/rewards/v1/rewards` | `get_rewards` | `services\backend_api\routers\rewards.py` | router.get | - |
| GET | `/api/rewards/v1/rewards/available` | `get_available_rewards` | `services\backend_api\routers\rewards.py` | router.get | ai |
| POST | `/api/rewards/v1/rewards/award/{action_key}` | `award_action` | `services\backend_api\routers\rewards.py` | router.post | - |
| POST | `/api/rewards/v1/rewards/redeem` | `redeem_rewards` | `services\backend_api\routers\rewards.py` | router.post | - |
| GET | `/api/rewards/v1/suggestions` | `get_my_suggestions` | `services\backend_api\routers\rewards.py` | router.get | - |
| POST | `/api/rewards/v1/suggestions` | `submit_suggestion` | `services\backend_api\routers\rewards.py` | router.post | - |
| GET | `/api/sessions/v1/consolidated/{user_id}` | `get_consolidated_user_data` | `services\backend_api\routers\sessions.py` | router.get | - |
| POST | `/api/sessions/v1/log` | `log_session_event` | `services\backend_api\routers\sessions.py` | router.post | - |
| GET | `/api/sessions/v1/summary/{user_id}` | `get_session_summary` | `services\backend_api\routers\sessions.py` | router.get | - |
| GET | `/api/sessions/v1/sync-status` | `get_sync_status` | `services\backend_api\routers\sessions.py` | router.get | - |
| GET | `/api/shared/v1/health` | `health_check` | `services\backend_api\routers\shared.py` | router.get | - |
| GET | `/api/shared/v1/health/deep` | `deep_health_check` | `services\backend_api\routers\shared.py` | router.get | - |
| GET | `/api/support/v1/ai/jobs` | `list_ai_jobs` | `services\backend_api\routers\support.py` | router.get | ai |
| GET | `/api/support/v1/ai/jobs/{job_id}` | `get_ai_job` | `services\backend_api\routers\support.py` | router.get | ai |
| GET | `/api/support/v1/ai/queue-stats` | `get_ai_queue_stats` | `services\backend_api\routers\support.py` | router.get | ai |
| GET | `/api/support/v1/health` | `support_health` | `services\backend_api\routers\support.py` | router.get | - |
| GET | `/api/support/v1/providers` | `support_providers` | `services\backend_api\routers\support.py` | router.get | - |
| GET | `/api/support/v1/readiness` | `support_readiness` | `services\backend_api\routers\support.py` | router.get | - |
| GET | `/api/support/v1/status` | `support_status` | `services\backend_api\routers\support.py` | router.get | - |
| GET | `/api/support/v1/tickets` | `list_support_tickets` | `services\backend_api\routers\support.py` | router.get | model |
| POST | `/api/support/v1/tickets` | `create_support_ticket` | `services\backend_api\routers\support.py` | router.post | ai, model |
| GET | `/api/support/v1/tickets/{ticket_id}` | `get_support_ticket` | `services\backend_api\routers\support.py` | router.get | - |
| GET | `/api/support/v1/tickets/{ticket_id}/ai-draft` | `get_ai_draft_for_ticket` | `services\backend_api\routers\support.py` | router.get | ai |
| POST | `/api/support/v1/tickets/{ticket_id}/approve-ai-draft` | `approve_ai_draft` | `services\backend_api\routers\support.py` | router.post | ai |
| GET | `/api/support/v1/tickets/{ticket_id}/comments` | `get_ticket_comments` | `services\backend_api\routers\support.py` | router.get | - |
| POST | `/api/support/v1/tickets/{ticket_id}/reply` | `reply_to_ticket` | `services\backend_api\routers\support.py` | router.post | - |
| POST | `/api/support/v1/token` | `issue_support_token` | `services\backend_api\routers\support.py` | router.post | - |
| POST | `/api/support/v1/webhooks/zendesk` | `zendesk_webhook` | `services\backend_api\routers\support.py` | router.post | model |
| GET | `/api/support/v1/widget-config` | `support_widget_config` | `services\backend_api\routers\support.py` | router.get | - |
| GET | `/api/support/v1/wiring-test` | `support_wiring_test` | `services\backend_api\routers\support.py` | router.get | - |
| GET | `/api/taxonomy/v1/industries` | `list_industries` | `services\backend_api\routers\taxonomy.py` | router.get | - |
| GET | `/api/taxonomy/v1/industries/{high_level}/subindustries` | `list_subindustries` | `services\backend_api\routers\taxonomy.py` | router.get | - |
| GET | `/api/taxonomy/v1/job-titles/infer-industries` | `infer_industries` | `services\backend_api\routers\taxonomy.py` | router.get | - |
| GET | `/api/taxonomy/v1/job-titles/metadata` | `job_title_metadata` | `services\backend_api\routers\taxonomy.py` | router.get | - |
| GET | `/api/taxonomy/v1/job-titles/naics-mapping` | `job_title_to_naics` | `services\backend_api\routers\taxonomy.py` | router.get | ai |
| GET | `/api/taxonomy/v1/job-titles/search` | `search_job_titles` | `services\backend_api\routers\taxonomy.py` | router.get | - |
| GET | `/api/taxonomy/v1/naics/search` | `search_naics` | `services\backend_api\routers\taxonomy.py` | router.get | ai |
| GET | `/api/taxonomy/v1/naics/title` | `naics_title` | `services\backend_api\routers\taxonomy.py` | router.get | ai |
| GET | `/api/taxonomy/v1/summary` | `taxonomy_summary` | `services\backend_api\routers\taxonomy.py` | router.get | - |
| GET | `/api/telemetry/v1/status` | `status` | `services\backend_api\routers\telemetry.py` | router.get | - |
| GET | `/api/touchpoints/v1/evidence` | `get_evidence` | `services\backend_api\routers\touchpoints.py` | router.get | - |
| GET | `/api/touchpoints/v1/touchnots` | `get_touchnots` | `services\backend_api\routers\touchpoints.py` | router.get | - |
| GET | `/api/user/v1/activity` | `get_user_activity` | `services\backend_api\routers\user.py` | router.get | model |
| GET | `/api/user/v1/matches/summary` | `get_match_summary` | `services\backend_api\routers\user.py` | router.get | - |
| GET | `/api/user/v1/me` | `read_users_me` | `services\backend_api\routers\user.py` | router.get | - |
| GET | `/api/user/v1/profile` | `get_profile` | `services\backend_api\routers\user.py` | router.get | - |
| PUT | `/api/user/v1/profile` | `update_profile` | `services\backend_api\routers\user.py` | router.put | model |
| GET | `/api/user/v1/resume/latest` | `get_latest_resume` | `services\backend_api\routers\user.py` | router.get | model |
| GET | `/api/user/v1/sessions/summary` | `get_user_session_summary` | `services\backend_api\routers\user.py` | router.get | model |
| GET | `/api/user/v1/stats` | `get_user_stats` | `services\backend_api\routers\user.py` | router.get | - |
| GET | `/api/v1/user-vector/current` | `get_current_user_vector` | `services\backend_api\routers\user_vector_v1.py` | router.get | vector |
| POST | `/api/webhooks/v1/braintree` | `braintree_webhook` | `services\backend_api\routers\webhooks.py` | braintree_service.gateway, router.post | ai, model |
| GET | `/api/webhooks/v1/health` | `webhook_health` | `services\backend_api\routers\webhooks.py` | braintree_service.is_configured, router.get | ai |
| POST | `/api/webhooks/v1/stripe` | `stripe_webhook` | `services\backend_api\routers\webhooks.py` | router.post | ai |
| POST | `/api/webhooks/v1/zendesk` | `zendesk_webhook` | `services\backend_api\routers\webhooks.py` | router.post | ai, model |
| GET | `/companies` | `get_companies` | `services\backend_api\services\company_intelligence_api.py` | - | - |
| GET | `/enrich` | `enrich_company` | `services\backend_api\services\company_intelligence_api.py` | - | - |
| GET | `/enrich_many` | `enrich_many` | `services\backend_api\services\company_intelligence_api.py` | - | - |
| POST | `/auth/login` | `login` | `services\shared\portal-bridge\main.py` | - | - |
| POST | `/auth/masquerade` | `masquerade` | `services\shared\portal-bridge\main.py` | - | - |
| GET | `/health` | `health_check` | `services\shared\portal-bridge\main.py` | - | - |
| GET | `/api/v1/health` | `health_check` | `services\shared_backend\main.py` | - | - |
| GET | `/api/v1/stats` | `get_stats` | `services\shared_backend\main.py` | - | - |
| GET | `/api/v1/users` | `get_users` | `services\shared_backend\main.py` | - | - |
| GET | `/api/v1/health` | `health_check` | `shared_backend\main.py` | - | - |

## 2. AI-bearing routes

### `GET /api/admin/v1/compliance/audit/events`
- File: `services\backend_api\routers\admin.py`
- Function: `audit_events`
- AI signals: model
- Likely services/calls: router.get
- Attribute calls: db.query, db.query.order_by, e.created_at.isoformat, models.AuditLog.created_at.desc, q.filter, q.limit, q.limit.all, router.get

### `GET /api/admin/v1/dashboard/snapshot`
- File: `services\backend_api\routers\admin.py`
- Function: `dashboard_snapshot`
- AI signals: ai, model
- Likely services/calls: router.get
- Attribute calls: a.created_at.isoformat, ai_data_root.is_dir, datetime.utcnow, datetime.utcnow.isoformat, db.query, db.query.filter, db.query.filter.scalar, db.query.order_by, db.query.order_by.limit, db.query.order_by.limit.all, db.query.scalar, func.count

### `GET /api/admin/v1/ai/enrichment/status`
- File: `services\backend_api\routers\admin.py`
- Function: `enrichment_status`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: ai_data_root.is_dir, datetime.fromtimestamp, datetime.fromtimestamp.isoformat, datetime.utcnow, datetime.utcnow.isoformat, entry.glob, entry.is_dir, interactions_dir.is_dir, interactions_dir.iterdir, os.path.getmtime, os.path.join, os.walk

### `GET /api/admin/v1/payments/disputes`
- File: `services\backend_api\routers\admin.py`
- Function: `payment_disputes`
- AI signals: model
- Likely services/calls: router.get
- Attribute calls: amount_by_type.items, datetime.utcnow, db.query, db.query.filter, models.PaymentTransaction.created_at.desc, models.PaymentTransaction.transaction_type.in_, query.filter, query.order_by, query.order_by.limit, query.order_by.limit.all, records.append, router.get

### `POST /api/admin/v1/email/send_bulk`
- File: `services\backend_api\routers\admin.py`
- Function: `send_bulk_email`
- AI signals: ai
- Likely services/calls: router.post
- Attribute calls: _email_dispatch_log.append, datetime.utcnow, datetime.utcnow.isoformat, payload.get, router.post, str.strip

### `POST /api/admin/v1/integrations/reminders/non-live`
- File: `services\backend_api\routers\admin.py`
- Function: `send_non_live_api_reminder`
- AI signals: ai
- Likely services/calls: router.post
- Attribute calls: _email_dispatch_log.append, datetime.utcnow, datetime.utcnow.isoformat, modes.get, os.getenv, payload.get, provider.title, provider_status.get, router.post, str.strip, str.strip.lower

### `POST /api/admin/v1/email/send_test`
- File: `services\backend_api\routers\admin.py`
- Function: `send_test_email`
- AI signals: ai
- Likely services/calls: router.post
- Attribute calls: _email_dispatch_log.append, datetime.utcnow, datetime.utcnow.isoformat, payload.get, router.post, str.strip

### `POST /api/admin/email/send_bulk`
- File: `services\backend_api\routers\admin_legacy.py`
- Function: `send_bulk_email_legacy`
- AI signals: ai
- Likely services/calls: router.post
- Attribute calls: admin_v1.send_bulk_email, router.post

### `POST /api/admin/email/send_test`
- File: `services\backend_api\routers\admin_legacy.py`
- Function: `send_test_email_legacy`
- AI signals: ai
- Likely services/calls: router.post
- Attribute calls: admin_v1.send_test_email, router.post

### `POST /api/ai-data/v1/emails/tracking`
- File: `services\backend_api\routers\ai_data.py`
- Function: `create_emails_tracking_record`
- AI signals: ai
- Likely services/calls: router.post
- Attribute calls: router.post

### `GET /api/ai-data/v1/status`
- File: `services\backend_api\routers\ai_data.py`
- Function: `get_ai_data_status`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: AI_DATA_PATH.absolute, dir_path.exists, dir_path.iterdir, router.get

### `GET /api/ai-data/v1/email_extracted`
- File: `services\backend_api\routers\ai_data.py`
- Function: `get_email_extracted`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: router.get

### `GET /api/ai-data/v1/emails`
- File: `services\backend_api\routers\ai_data.py`
- Function: `get_emails`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: router.get

### `GET /api/ai-data/v1/emails/diagnostics`
- File: `services\backend_api\routers\ai_data.py`
- Function: `get_emails_diagnostics`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: router.get

### `GET /api/ai-data/v1/emails/summary`
- File: `services\backend_api\routers\ai_data.py`
- Function: `get_emails_summary`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: router.get

### `GET /api/ai-data/v1/emails/tracking`
- File: `services\backend_api\routers\ai_data.py`
- Function: `get_emails_tracking`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: router.get

### `GET /api/ai-data/v1/emails/tracking/reroute-targets`
- File: `services\backend_api\routers\ai_data.py`
- Function: `get_emails_tracking_reroute_targets`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: router.get

### `GET /api/ai-data/v1/emails/tracking/summary`
- File: `services\backend_api\routers\ai_data.py`
- Function: `get_emails_tracking_summary`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: router.get

### `GET /api/analytics/v1/dashboard`
- File: `services\backend_api\routers\analytics.py`
- Function: `get_dashboard_data`
- AI signals: model
- Likely services/calls: router.get
- Attribute calls: d.is_dir, datetime.fromtimestamp, datetime.fromtimestamp.isoformat, datetime.utcnow, datetime.utcnow.isoformat, json.load, json_file.stat, logger.warning, models_path.exists, models_path.iterdir, recent_resumes.append, resume_path.exists

### `GET /api/analytics/v1/system_health`
- File: `services\backend_api\routers\analytics.py`
- Function: `get_system_health`
- AI signals: ai, model
- Likely services/calls: router.get
- Attribute calls: AI_DATA_PATH.exists, d.is_dir, datetime.utcnow, datetime.utcnow.isoformat, dir_path.exists, dir_path.glob, models_path.exists, models_path.iterdir, router.get

### `POST /api/auth/v1/register`
- File: `services\backend_api\routers\auth.py`
- Function: `register`
- AI signals: model
- Likely services/calls: router.post
- Attribute calls: db.add, db.commit, db.query, db.query.filter, db.query.filter.first, db.refresh, models.User, router.post, security.get_password_hash

### `GET /career-compass/routes`
- File: `services\backend_api\routers\career_compass.py`
- Function: `career_compass_routes`
- AI signals: vector
- Likely services/calls: router.get
- Attribute calls: natural_next_steps.append, router.get, strategic_stretch.append, too_far_for_now.append, user_vector.get

### `POST /career-compass/spider-overlay`
- File: `services\backend_api\routers\career_compass.py`
- Function: `career_compass_spider_overlay`
- AI signals: vector
- Likely services/calls: router.post
- Attribute calls: payload.role_text.strip, router.post

### `GET /api/coaching/v1/history`
- File: `services\backend_api\routers\coaching.py`
- Function: `get_coaching_history`
- AI signals: model
- Likely services/calls: router.get
- Attribute calls: db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.limit, db.query.filter.order_by.limit.all, entry.created_at.isoformat, history.append, json.loads, models.Interaction.action_type.in_, models.Interaction.created_at.desc, router.get

### `POST /api/coaching/v1/profile/reflect`
- File: `services\backend_api\routers\coaching.py`
- Function: `profile_coach_reflect`
- AI signals: ai
- Likely services/calls: router.post
- Attribute calls: payload.user_message.strip, router.post

### `GET /api/data-index/v1/ai-data/categories`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_ai_data_categories`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.get, service.get_ai_data_summary
- Attribute calls: router.get, service.get_ai_data_summary

### `GET /api/data-index/v1/ai-data/summary`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_ai_data_summary`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.get, service.get_ai_data_summary
- Attribute calls: router.get, service.get_ai_data_summary

### `GET /api/data-index/v1/files/manifest-stats`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_file_manifest_stats`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.get, service.get_file_manifest_stats
- Attribute calls: router.get, service.get_file_manifest_stats

### `GET /api/data-index/v1/files/by-category/{category}`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_files_by_category`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.get, service._state.file_manifest.values
- Attribute calls: files.append, files.sort, router.get, service._state.file_manifest.values, x.get

### `GET /api/data-index/v1/files/since`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_files_since_timestamp`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.get, service.get_files_since
- Attribute calls: router.get, service.get_files_since

### `GET /api/data-index/v1/health`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_index_health`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.get, service.get_state
- Attribute calls: issues.append, router.get, service.get_state, warnings.append

### `GET /api/data-index/v1/status`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_index_status`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.get, service.get_state
- Attribute calls: router.get, service.get_state

### `GET /api/data-index/v1/files/new-data-summary`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_new_data_summary`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.get, service.get_new_data_summary
- Attribute calls: router.get, service.get_new_data_summary

### `GET /api/data-index/v1/dependencies`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_optional_dependencies`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.get, service._detect_optional_dependencies
- Attribute calls: deps.get, router.get, service._detect_optional_dependencies

### `GET /api/data-index/v1/parser/file-types`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_parser_file_types`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.get, service.get_parser_summary
- Attribute calls: router.get, service.get_parser_summary

### `GET /api/data-index/v1/parser/runs`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_parser_runs`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.get, service.get_parser_run_history
- Attribute calls: router.get, service.get_parser_run_history

### `GET /api/data-index/v1/parser/status`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_parser_status`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.get, service.get_parser_summary
- Attribute calls: router.get, service.get_parser_summary

### `GET /api/data-index/v1/parser/summary`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_parser_summary`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.get, service.get_parser_summary
- Attribute calls: router.get, service.get_parser_summary

### `GET /api/data-index/v1/ai-data/industries`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_top_industries`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.get, service.get_ai_data_summary
- Attribute calls: router.get, service.get_ai_data_summary, summary.top_industries.items

### `GET /api/data-index/v1/ai-data/locations`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_top_locations`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.get, service.get_ai_data_summary
- Attribute calls: router.get, service.get_ai_data_summary, summary.top_locations.items

### `GET /api/data-index/v1/ai-data/skills`
- File: `services\backend_api\routers\data_index.py`
- Function: `get_top_skills`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.get, service.get_ai_data_summary
- Attribute calls: router.get, service.get_ai_data_summary, summary.top_skills.items

### `POST /api/data-index/v1/parser/runs`
- File: `services\backend_api\routers\data_index.py`
- Function: `record_parser_run`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.post, service.record_parser_run
- Attribute calls: router.post, service.record_parser_run

### `GET /api/data-index/v1/ai-data/industries/search`
- File: `services\backend_api\routers\data_index.py`
- Function: `search_industries`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.get, service.search_industries
- Attribute calls: router.get, service.search_industries

### `GET /api/data-index/v1/ai-data/locations/search`
- File: `services\backend_api\routers\data_index.py`
- Function: `search_locations`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.get, service.search_locations
- Attribute calls: router.get, service.search_locations

### `GET /api/data-index/v1/ai-data/skills/search`
- File: `services\backend_api\routers\data_index.py`
- Function: `search_skills`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.get, service.search_skills
- Attribute calls: router.get, service.search_skills

### `POST /api/data-index/v1/index/ai-data`
- File: `services\backend_api\routers\data_index.py`
- Function: `trigger_ai_data_index`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.post, service.index_ai_data
- Attribute calls: router.post, service.index_ai_data

### `POST /api/data-index/v1/index/full`
- File: `services\backend_api\routers\data_index.py`
- Function: `trigger_full_index`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.post, service.full_index
- Attribute calls: router.post, service.full_index

### `POST /api/data-index/v1/index/incremental`
- File: `services\backend_api\routers\data_index.py`
- Function: `trigger_incremental_index`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.post, service.incremental_index
- Attribute calls: router.post, service.incremental_index

### `POST /api/data-index/v1/index/parser`
- File: `services\backend_api\routers\data_index.py`
- Function: `trigger_parser_index`
- AI signals: ai
- Likely services/calls: get_ai_data_index_service, router.post, service.index_parser_sources
- Attribute calls: router.post, service.index_parser_sources

### `DELETE /api/gdpr/v1/delete-account`
- File: `services\backend_api\routers\gdpr.py`
- Function: `delete_my_account`
- AI signals: model
- Likely services/calls: router.delete
- Attribute calls: db.commit, db.query, db.query.filter, db.query.filter.delete, logger.info, models.MentorNote.link_id.in_, os.getcwd, os.path.isdir, os.path.join, router.delete

### `GET /api/gdpr/v1/export`
- File: `services\backend_api\routers\gdpr.py`
- Function: `export_my_data`
- AI signals: model
- Likely services/calls: router.get
- Attribute calls: c.created_at.isoformat, c.revoked_at.isoformat, current_user.created_at.isoformat, datetime.utcnow, datetime.utcnow.isoformat, db.add, db.commit, db.query, db.query.filter, db.query.filter.all, db.query.filter.order_by, db.query.filter.order_by.limit

### `GET /api/gdpr/v1/consent`
- File: `services\backend_api\routers\gdpr.py`
- Function: `get_consent`
- AI signals: model
- Likely services/calls: router.get
- Attribute calls: db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.all, models.ConsentRecord.created_at.desc, r.created_at.isoformat, r.revoked_at.isoformat, router.get

### `POST /api/gdpr/v1/consent`
- File: `services\backend_api\routers\gdpr.py`
- Function: `grant_consent`
- AI signals: model
- Likely services/calls: router.post
- Attribute calls: db.add, db.commit, models.ConsentRecord, request.headers.get, router.post

### `GET /api/gdpr/v1/audit-log`
- File: `services\backend_api\routers\gdpr.py`
- Function: `my_audit_log`
- AI signals: model
- Likely services/calls: router.get
- Attribute calls: db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.limit, db.query.filter.order_by.limit.all, e.created_at.isoformat, models.AuditLog.created_at.desc, router.get

### `POST /api/intelligence/v1/enrich`
- File: `services\backend_api\routers\intelligence.py`
- Function: `enrich_resume`
- AI signals: model
- Likely services/calls: router.post
- Attribute calls: models.split, router.post

### `POST /api/intelligence/v1/stats/descriptive`
- File: `services\backend_api\routers\intelligence.py`
- Function: `get_stats`
- AI signals: engine
- Likely services/calls: engine.descriptive_stats, router.post
- Attribute calls: engine.descriptive_stats, router.post

### `POST /api/intelligence/v1/stats/regression`
- File: `services\backend_api\routers\intelligence.py`
- Function: `regression`
- AI signals: engine, regression
- Likely services/calls: engine.linear_regression, router.post
- Attribute calls: engine.linear_regression, np.corrcoef, np.polyfit, router.post

### `GET /api/jobs/v1/index`
- File: `services\backend_api\routers\jobs.py`
- Function: `get_job_index`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: router.get

### `GET /api/jobs/v1/search`
- File: `services\backend_api\routers\jobs.py`
- Function: `search_jobs`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: router.get

### `POST /api/lenses/v1/spider`
- File: `services\backend_api\routers\lenses.py`
- Function: `build_spider`
- AI signals: bayes, bayesian, engine, score
- Likely services/calls: StatisticalAnalysisEngine, engine.bayesian_probability, router.post
- Attribute calls: axes.append, base_scores.items, base_scores.values, engine.bayesian_probability, key.replace, key.replace.title, random.randint, req.cohort.get, router.post

### `GET /api/admin/v1/logs/tail`
- File: `services\backend_api\routers\logs.py`
- Function: `tail_log`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: f.readlines, fp.exists, ln.rstrip, pat.search, re.compile, router.get

### `POST /api/mentorship/v1/invoices/{invoice_id}/mark-paid`
- File: `services\backend_api\routers\mentorship.py`
- Function: `mark_invoice_paid`
- AI signals: ai
- Likely services/calls: router.post, service.mark_invoice_paid
- Attribute calls: logger.error, router.post, service.mark_invoice_paid

### `POST /api/mentorship/v1/invoices/{invoice_id}/dispute`
- File: `services\backend_api\routers\mentorship.py`
- Function: `raise_dispute`
- AI signals: ai
- Likely services/calls: router.post, service.raise_dispute
- Attribute calls: logger.error, router.post, service.raise_dispute

### `POST /api/payment/v1/methods`
- File: `services\backend_api\routers\payment.py`
- Function: `add_payment_method`
- AI signals: ai
- Likely services/calls: braintree_service.create_payment_method, braintree_service.find_or_create_customer, braintree_service.is_configured, router.post
- Attribute calls: braintree_service.create_payment_method, braintree_service.find_or_create_customer, braintree_service.is_configured, logger.error, router.post

### `POST /api/payment/v1/cancel`
- File: `services\backend_api\routers\payment.py`
- Function: `cancel_subscription`
- AI signals: ai, model
- Likely services/calls: braintree_service.cancel_subscription, braintree_service.is_configured, router.post
- Attribute calls: braintree_service.cancel_subscription, braintree_service.is_configured, datetime.now, db.commit, db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.first, logger.warning, models.Subscription.created_at.desc, models.Subscription.status.in_, router.post

### `GET /api/payment/v1/gateway-info`
- File: `services\backend_api\routers\payment.py`
- Function: `gateway_info`
- AI signals: ai
- Likely services/calls: braintree_service.is_configured, router.get
- Attribute calls: braintree_service.is_configured, os.getenv, router.get

### `GET /api/payment/v1/client-token`
- File: `services\backend_api\routers\payment.py`
- Function: `get_client_token`
- AI signals: ai
- Likely services/calls: braintree_service.generate_client_token, braintree_service.is_configured, router.get
- Attribute calls: braintree_service.generate_client_token, braintree_service.is_configured, logger.error, router.get

### `GET /api/payment/v1/subscription`
- File: `services\backend_api\routers\payment.py`
- Function: `get_current_subscription`
- AI signals: model
- Likely services/calls: router.get
- Attribute calls: PLANS.get, db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.first, models.Subscription.created_at.desc, models.Subscription.status.in_, router.get, sub.current_period_end.isoformat, sub.started_at.isoformat

### `GET /api/payment/v1/history`
- File: `services\backend_api\routers\payment.py`
- Function: `get_payment_history`
- AI signals: model
- Likely services/calls: router.get
- Attribute calls: db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.all, models.PaymentTransaction.created_at.desc, r.created_at.isoformat, router.get

### `GET /api/payment/v1/transactions/{transaction_id}`
- File: `services\backend_api\routers\payment.py`
- Function: `get_transaction`
- AI signals: ai
- Likely services/calls: braintree_service.find_transaction, braintree_service.is_configured, router.get
- Attribute calls: braintree_service.find_transaction, braintree_service.is_configured, router.get

### `GET /api/payment/v1/health`
- File: `services\backend_api\routers\payment.py`
- Function: `health_check`
- AI signals: ai
- Likely services/calls: braintree_service.is_configured, router.get
- Attribute calls: braintree_service.is_configured, os.getenv, router.get

### `GET /api/payment/v1/methods`
- File: `services\backend_api\routers\payment.py`
- Function: `list_payment_methods`
- AI signals: ai
- Likely services/calls: braintree_service.is_configured, braintree_service.list_payment_methods, router.get
- Attribute calls: braintree_service.is_configured, braintree_service.list_payment_methods, router.get

### `POST /api/payment/v1/process`
- File: `services\backend_api\routers\payment.py`
- Function: `process_payment`
- AI signals: ai, model
- Likely services/calls: router.post
- Attribute calls: datetime.now, db.add, db.commit, db.flush, logger.info, models.PaymentTransaction, models.Subscription, next_billing.isoformat, payment_result.get, router.post, uuid.uuid4

### `POST /api/payment/v1/refund/{transaction_id}`
- File: `services\backend_api\routers\payment.py`
- Function: `refund_transaction`
- AI signals: ai
- Likely services/calls: braintree_service.is_configured, braintree_service.refund_transaction, router.post
- Attribute calls: braintree_service.is_configured, braintree_service.refund_transaction, result.get, router.post

### `DELETE /api/payment/v1/methods/{token}`
- File: `services\backend_api\routers\payment.py`
- Function: `remove_payment_method`
- AI signals: ai
- Likely services/calls: braintree_service.delete_payment_method, braintree_service.is_configured, router.delete
- Attribute calls: braintree_service.delete_payment_method, braintree_service.is_configured, router.delete

### `POST /api/v1/profile-coach/respond`
- File: `services\backend_api\routers\profile_coach_v1.py`
- Function: `respond_profile_coach`
- AI signals: ai
- Likely services/calls: router.post
- Attribute calls: coaching._contains_stop_phrase, coaching._finish_summary, coaching._mirror_points, coaching._next_question, payload.answer.strip, router.post, session.follow_up_questions.append, session.mirrored_points.append, session.user_messages.append

### `POST /api/v1/profile/signals`
- File: `services\backend_api\routers\profile_v1.py`
- Function: `build_profile_signals`
- AI signals: vector
- Likely services/calls: router.post
- Attribute calls: router.post, value.strip

### `GET /api/rewards/v1/rewards/available`
- File: `services\backend_api\routers\rewards.py`
- Function: `get_available_rewards`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: REWARD_ACTIONS.items, available.append, db.query, db.query.filter, db.query.filter.all, router.get

### `GET /api/rewards/v1/leaderboard`
- File: `services\backend_api\routers\rewards.py`
- Function: `get_leaderboard`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: UserReward.user_id.distinct, db.query, db.query.filter, db.query.filter.first, db.query.filter.scalar, db.query.group_by, db.query.group_by.order_by, db.query.group_by.order_by.limit, db.query.group_by.order_by.limit.all, db.query.scalar, func.count, func.sum

### `POST /api/support/v1/tickets/{ticket_id}/approve-ai-draft`
- File: `services\backend_api\routers\support.py`
- Function: `approve_ai_draft`
- AI signals: ai
- Likely services/calls: router.post
- Attribute calls: body.strip, datetime.utcnow, db.commit, db.query, db.query.filter, db.query.filter.first, db.refresh, job.get, result.get, router.post

### `POST /api/support/v1/tickets`
- File: `services\backend_api\routers\support.py`
- Function: `create_support_ticket`
- AI signals: ai, model
- Likely services/calls: router.post
- Attribute calls: _os.getenv, _os.getenv.lower, cfg.get, db.add, db.commit, db.refresh, models.SupportTicket, request.headers.get, router.post, ticket.created_at.isoformat, ticket.updated_at.isoformat, zendesk_result.get

### `GET /api/support/v1/tickets/{ticket_id}/ai-draft`
- File: `services\backend_api\routers\support.py`
- Function: `get_ai_draft_for_ticket`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: db.query, db.query.filter, db.query.filter.first, full.get, job_ticket.get, router.get

### `GET /api/support/v1/ai/jobs/{job_id}`
- File: `services\backend_api\routers\support.py`
- Function: `get_ai_job`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: router.get

### `GET /api/support/v1/ai/queue-stats`
- File: `services\backend_api\routers\support.py`
- Function: `get_ai_queue_stats`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: router.get

### `GET /api/support/v1/ai/jobs`
- File: `services\backend_api\routers\support.py`
- Function: `list_ai_jobs`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: router.get

### `GET /api/support/v1/tickets`
- File: `services\backend_api\routers\support.py`
- Function: `list_support_tickets`
- AI signals: model
- Likely services/calls: router.get
- Attribute calls: db.query, models.SupportTicket.updated_at.desc, q.count, q.filter, q.order_by, q.order_by.offset, q.order_by.offset.limit, q.order_by.offset.limit.all, router.get

### `POST /api/support/v1/webhooks/zendesk`
- File: `services\backend_api\routers\support.py`
- Function: `zendesk_webhook`
- AI signals: model
- Likely services/calls: router.post
- Attribute calls: datetime.fromisoformat, datetime.utcnow, db.commit, db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.first, db.refresh, models.SupportTicket.id.desc, payload.get, request.body, request.json

### `GET /api/taxonomy/v1/job-titles/naics-mapping`
- File: `services\backend_api\routers\taxonomy.py`
- Function: `job_title_to_naics`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: router.get, tax.map_job_title_to_naics

### `GET /api/taxonomy/v1/naics/title`
- File: `services\backend_api\routers\taxonomy.py`
- Function: `naics_title`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: router.get, tax.get_naics_title

### `GET /api/taxonomy/v1/naics/search`
- File: `services\backend_api\routers\taxonomy.py`
- Function: `search_naics`
- AI signals: ai
- Likely services/calls: router.get
- Attribute calls: router.get, tax.search_naics_by_phrase

### `GET /api/user/v1/resume/latest`
- File: `services\backend_api\routers\user.py`
- Function: `get_latest_resume`
- AI signals: model
- Likely services/calls: router.get
- Attribute calls: db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.first, latest.created_at.isoformat, models.Resume.created_at.desc, router.get

### `GET /api/user/v1/activity`
- File: `services\backend_api\routers\user.py`
- Function: `get_user_activity`
- AI signals: model
- Likely services/calls: router.get
- Attribute calls: activity.append, db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.limit, db.query.filter.order_by.limit.all, entry.created_at.isoformat, json.loads, models.Interaction.created_at.desc, router.get

### `GET /api/user/v1/sessions/summary`
- File: `services\backend_api\routers\user.py`
- Function: `get_user_session_summary`
- AI signals: model
- Likely services/calls: router.get
- Attribute calls: created_at.isoformat, db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.all, models.Interaction.created_at.desc, router.get

### `PUT /api/user/v1/profile`
- File: `services\backend_api\routers\user.py`
- Function: `update_profile`
- AI signals: model
- Likely services/calls: router.put
- Attribute calls: db.add, db.commit, db.refresh, models.UserProfile, router.put

### `GET /api/v1/user-vector/current`
- File: `services\backend_api\routers\user_vector_v1.py`
- Function: `get_current_user_vector`
- AI signals: vector
- Likely services/calls: router.get
- Attribute calls: Resume.created_at.desc, db.query, db.query.filter, query.filter, query.order_by, query.order_by.first, router.get, vector.keys

### `POST /api/webhooks/v1/braintree`
- File: `services\backend_api\routers\webhooks.py`
- Function: `braintree_webhook`
- AI signals: ai, model
- Likely services/calls: braintree_service.gateway, router.post
- Attribute calls: braintree_service.gateway, datetime.now, db.add, db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.first, event_type.replace, event_type.replace.title, form.get, gw.webhook_notification.parse, logger.error

### `POST /api/webhooks/v1/stripe`
- File: `services\backend_api\routers\webhooks.py`
- Function: `stripe_webhook`
- AI signals: ai
- Likely services/calls: router.post
- Attribute calls: datetime.now, event.get, logger.error, logger.exception, logger.info, obj.get, os.getenv, payload_dict.get, request.body, router.post, status_map.get, stripe.Webhook.construct_event

### `GET /api/webhooks/v1/health`
- File: `services\backend_api\routers\webhooks.py`
- Function: `webhook_health`
- AI signals: ai
- Likely services/calls: braintree_service.is_configured, router.get
- Attribute calls: braintree_service.is_configured, os.getenv, router.get

### `POST /api/webhooks/v1/zendesk`
- File: `services\backend_api\routers\webhooks.py`
- Function: `zendesk_webhook`
- AI signals: ai, model
- Likely services/calls: router.post
- Attribute calls: datetime.fromisoformat, datetime.utcnow, db.query, db.query.filter, db.query.filter.order_by, db.query.filter.order_by.first, json.loads, logger.exception, logger.info, logger.warning, models.SupportTicket.id.desc, os.getenv

## 3. Service and orchestration signals

### `db_session` — `conftest.py`
- AI signals: engine
- Attribute calls: Base.metadata.create_all, engine.dispose, pytest.fixture, session.close
- Direct calls: Session, create_engine, sessionmaker

### `test_client` — `conftest.py`
- AI signals: -
- Attribute calls: pytest.fixture
- Direct calls: TestClient

### `normalize_parsed_resume` — `scripts\aggregate_training_corpus.py`
- AI signals: ai
- Attribute calls: resume.get
- Direct calls: extract_email, extract_phone

### `normalize_profile` — `scripts\aggregate_training_corpus.py`
- AI signals: ai
- Attribute calls: education.append, profile.get, work_experience.append
- Direct calls: extract_email, extract_phone, join

### `main` — `scripts\build_collocation_glossary.py`
- AI signals: ai
- Attribute calls: argparse.ArgumentParser, bigram.items, bigram_entries.append, bigram_entries.sort, bigram_index.values, collocation_txt.exists, datetime.utcnow, datetime.utcnow.isoformat, glossary_path.exists, json.dump, near_pairs.most_common, negated_terms.most_common, output_path.open, output_path.parent.mkdir, p.exists
- Direct calls: CareerTrojanPaths, Counter, Path, compute_pmi, iter_json_files, len, list, load_gazetteer_phrases, load_glossary_terms, print, round, scan_json_file, scan_text_file, str, sum

### `build_company_domain_hints` — `scripts\extract_emails_deep.py`
- AI signals: ai
- Attribute calls: company_domains.items, company_domains.setdefault, counter.most_common, row.get, work_email.split
- Direct calls: Counter, clean_email, is_valid_email, normalize_company

### `build_company_domain_hints_from_company_store` — `scripts\extract_emails_deep.py`
- AI signals: ai
- Attribute calls: counter.most_common, directory.exists, directory.rglob, domain_candidates.append, hints.items, hints.setdefault, item.get, json.loads, json_file.read_text, row.values
- Direct calls: Counter, clean_name, extract_domain_from_value, find_field, isinstance, normalize_company, parse_csv_rows, str

### `collect_contact_rows` — `scripts\extract_emails_deep.py`
- AI signals: ai
- Attribute calls: rows.append
- Direct calls: any, clean_email, find_field, parse_csv_rows, str

### `extract_domain_from_value` — `scripts\extract_emails_deep.py`
- AI signals: ai
- Attribute calls: candidate.split, host.rsplit, host.split, host.startswith, lower.strip, raw.count, re.match, strip.strip
- Direct calls: clean_email, is_valid_email, len, lower, strip, urlparse

### `extract_from_text` — `scripts\extract_emails_deep.py`
- AI signals: ai
- Attribute calls: EMAIL_PATTERN.findall, emails.add
- Direct calls: clean_email, is_valid_email, set

### `infer_email_candidates` — `scripts\extract_emails_deep.py`
- AI signals: ai
- Attribute calls: company_domains.get, datetime.now, datetime.now.isoformat, inferred.values, row.get
- Direct calls: append, clean_email, clean_name, company_slug, is_valid_email, len, lower, normalize_company, sanitize_local_part, sorted, split_first_last

### `is_valid_email` — `scripts\extract_emails_deep.py`
- AI signals: ai
- Attribute calls: domain.endswith, domain.rsplit, domain.startswith, value.rsplit
- Direct calls: len, lower

### `load_tld_hints` — `scripts\extract_emails_deep.py`
- AI signals: ai
- Attribute calls: domain_file.exists, domain_file.read_text, raw.lower, re.findall, tlds.add
- Direct calls: set

### `scan_sources` — `scripts\extract_emails_deep.py`
- AI signals: ai
- Attribute calls: alert_flags.append, company_domains.setdefault, company_store_hints.items, datetime.now, datetime.now.isoformat, domain_counts.most_common, email.split, email_sources.items, email_sources.setdefault, email_sources.setdefault.add, file_path.is_file, file_path.suffix.lower, json.dumps, output_dir.mkdir, r.get
- Direct calls: Counter, build_company_domain_hints, build_company_domain_hints_from_company_store, collect_contact_rows, dict, extract_from_text, infer_email_candidates, iter_zip_texts, len, merge_legacy_records, read_msg_file, read_text_file, set, sorted, str

### `check_ai_structure` — `scripts\ingestion_smoke_test.py`
- AI signals: ai
- Direct calls: is_dir, join, print, print_fail, print_pass, print_warn

### `check_paths` — `scripts\ingestion_smoke_test.py`
- AI signals: ai
- Attribute calls: paths.ai_data_final.exists, paths.data_root.exists, paths.interactions.exists
- Direct calls: print, print_fail, print_pass, print_warn

### `main` — `scripts\ingestion_smoke_test.py`
- AI signals: ai
- Direct calls: CareerTrojanPaths, check_ai_structure, check_ingestion_outputs, check_paths, print

### `main` — `scripts\run_full_pipeline.py`
- AI signals: ai, training
- Attribute calls: argparse.ArgumentParser, datetime.now, datetime.now.isoformat, json.dump, log.error, log.info, log.warning, parser.add_argument, parser.parse_args, pipeline_results.items, result.get, sys.exit, time.time, traceback.print_exc
- Direct calls: CareerTrojanPaths, banner, int, isinstance, len, open, run_collocations, run_parser, run_smoke_test, run_training, str

### `run_collocations` — `scripts\run_full_pipeline.py`
- AI signals: ai, score
- Attribute calls: all_tokens.extend, bigram.split, bigram_counts.most_common, datetime.now, datetime.now.isoformat, gaz_dir.exists, gaz_dir.rglob, json.dump, log.info, log.warning, math.log2, near_pairs.most_common, negated_terms.most_common, pmi_scores.items, scan_dir.exists
- Direct calls: Counter, banner, enumerate, len, min, open, range, round, scan_json_file, scan_text_file, sorted, str

### `run_parser` — `scripts\run_full_pipeline.py`
- AI signals: engine
- Attribute calls: engine.run, log.info, log.warning, output_root.mkdir, sys.path.insert
- Direct calls: AutomatedParserEngine, banner, len, str

### `run_smoke_test` — `scripts\run_full_pipeline.py`
- AI signals: ai
- Attribute calls: log.error, log.info, log.warning, merged.exists, merged.stat, p.exists, p.mkdir, paths.ai_data_final.rglob
- Direct calls: append, banner

### `run_training` — `scripts\run_full_pipeline.py`
- AI signals: ai, bayes, bayesian, classifier, embedding, model, trained
- Attribute calls: datetime.now, datetime.now.isoformat, json.dump, log.error, log.info, log.warning, paths.trained_models.mkdir, sys.path.insert, traceback.print_exc, trainer.load_cv_data, trainer.models_dir.mkdir, trainer.setup_sentence_embeddings, trainer.setup_spacy_model, trainer.train_bayesian_classifier, trainer.train_statistical_models
- Direct calls: IntelliCVModelTrainer, Path, append, banner, get, len, open, str

### `count_router_decorators` — `scripts\run_orchestrator_discovery.py`
- AI signals: -
- Attribute calls: p.read_text, txt.count
- Direct calls: py_files

### `main` — `scripts\run_parser_until_complete.py`
- AI signals: engine
- Attribute calls: datetime.utcnow, datetime.utcnow.isoformat, engine.run, results.get, time.sleep, time.time
- Direct calls: AutomatedParserEngine, CareerTrojanPaths, append_progress, int, len, print, round, str

### `_ensure_mentor_profile` — `scripts\run_super_experience_harness.py`
- AI signals: model
- Attribute calls: db.add, db.close, db.commit, db.query, db.query.filter, db.query.filter.first, db.refresh, models.Mentor
- Direct calls: SessionLocal

### `run` — `scripts\run_super_experience_harness.py`
- AI signals: ai
- Attribute calls: datetime.now, datetime.now.isoformat, json.dumps, self._ensure_mentor_profile, self._register_and_login, self._upsert_role, self.admin_journey, self.ai_learning_signals, self.mentor_journey, self.output_path.parent.mkdir, self.output_path.write_text, self.resume_probe, self.run_tiered_tests, self.user_journey
- Direct calls: HarnessReport, RuntimeError, asdict, set, sorted

### `check_environment_paths` — `scripts\smoke_test.py`
- AI signals: ai
- Attribute calls: os.path.exists
- Direct calls: print, print_fail, print_pass, print_warn

### `check_frontend_components` — `scripts\smoke_test.py`
- AI signals: ai
- Attribute calls: os.path.basename, os.path.exists, os.path.join
- Direct calls: print, print_fail, print_pass

### `simulate_docker_services` — `scripts\smoke_test.py`
- AI signals: -
- Attribute calls: os.path.exists, os.path.join
- Direct calls: print, print_pass, print_warn

### `verify_test_user_seeding` — `scripts\smoke_test.py`
- AI signals: ai
- Attribute calls: json.load, os.path.exists, os.path.join, user.get
- Direct calls: CareerTrojanPaths, isinstance, open, print, print_fail, print_pass, print_warn, str

### `_find_webhook_id` — `scripts\upsert_zendesk_webhook_triggers.py`
- AI signals: ai
- Attribute calls: available.append, chosen.get, client.get, client.get.get, preferred_url.strip, preferred_url.strip.rstrip, str.rstrip, webhook.get
- Direct calls: RuntimeError, get, isinstance, print, str

### `get` — `scripts\upsert_zendesk_webhook_triggers.py`
- AI signals: ai
- Attribute calls: requests.get, response.json, response.raise_for_status

### `post` — `scripts\upsert_zendesk_webhook_triggers.py`
- AI signals: ai
- Attribute calls: requests.post, response.json, response.raise_for_status

### `put` — `scripts\upsert_zendesk_webhook_triggers.py`
- AI signals: ai
- Attribute calls: requests.put, response.json, response.raise_for_status

### `_is_google_managed_service_agent` — `scripts\validate_runtime_env.py`
- AI signals: -
- Attribute calls: re.match, value.strip, value.strip.lower
- Direct calls: bool

### `main` — `scripts\validate_runtime_env.py`
- AI signals: ai
- Attribute calls: Path.resolve, argparse.ArgumentParser, env_map.get, env_path.exists, missing.extend, offenders.append, parser.add_argument, parser.parse_args, strip.lower, unsafe_identity_keys.append
- Direct calls: Path, _is_google_managed_service_agent, _is_personal_email, _missing, _warn_placeholder, parse_env_file, print, set, sorted, strip

### `__init__` — `services\ai_engine\ai_training_orchestrator.py`
- AI signals: model
- Attribute calls: logger.info, self.models_path.mkdir
- Direct calls: Path

### `calculate_similarity_matrix` — `services\ai_engine\ai_training_orchestrator.py`
- AI signals: similarity
- Attribute calls: logger.error, logger.info, np.array, np.save, similarity_matrix.max, similarity_matrix.mean
- Direct calls: cosine_similarity, len

### `main` — `services\ai_engine\ai_training_orchestrator.py`
- AI signals: ai, orchestrator, training
- Attribute calls: orchestrator.run_full_training_pipeline
- Direct calls: AITrainingOrchestrator, Path, str

### `run_full_training_pipeline` — `services\ai_engine\ai_training_orchestrator.py`
- AI signals: ai, classifier, clustering, embedding, similarity
- Attribute calls: datetime.now, datetime.now.isoformat, json.dump, logger.error, logger.info, self.calculate_similarity_matrix, self.load_data, self.prepare_text_data, self.train_clustering, self.train_embeddings, self.train_job_classifier, self.train_tfidf
- Direct calls: len, min, open, total_seconds

### `train_clustering` — `services\ai_engine\ai_training_orchestrator.py`
- AI signals: model, predict
- Attribute calls: Counter.items, dbscan_labels.tolist, json.dump, kmeans_labels.tolist, list.count, logger.error, logger.info, pickle.dump, self.dbscan_model.fit_predict, self.kmeans_model.fit_predict
- Direct calls: Counter, DBSCAN, KMeans, dict, float, int, len, list, open, set, str

### `train_embeddings` — `services\ai_engine\ai_training_orchestrator.py`
- AI signals: model
- Attribute calls: logger.error, logger.info, np.array, np.save, self.sentence_model.encode
- Direct calls: SentenceTransformer, len

### `train_job_classifier` — `services\ai_engine\ai_training_orchestrator.py`
- AI signals: ai, classifier, predict, score, vector
- Attribute calls: categories.append, logger.error, logger.info, pickle.dump, self.job_classifier.fit, self.job_classifier.predict, title.lower, vectorizer.fit_transform
- Direct calls: Counter, RandomForestClassifier, TfidfVectorizer, accuracy_score, any, dict, len, open, set, train_test_split

### `train_tfidf` — `services\ai_engine\ai_training_orchestrator.py`
- AI signals: vector
- Attribute calls: json.dump, logger.error, logger.info, np.array, pickle.dump, self.tfidf_vectorizer.fit_transform, self.tfidf_vectorizer.get_feature_names_out, tfidf_matrix.toarray
- Direct calls: TfidfVectorizer, len, list, open

### `find_near_pairs` — `services\ai_engine\collocation_engine.py`
- AI signals: ai
- Attribute calls: hit_details.append, pair_hits.items, ranked.sort, self._all_tokens
- Direct calls: Counter, enumerate, int, len, max, min, range, sorted, tuple

### `load_sample_profiles` — `services\ai_engine\data_loader.py`
- AI signals: score
- Attribute calls: PROFILES_DIR.exists, PROFILES_DIR.glob, data.get, json.load, loaded.append, logger.debug, logger.info, logger.warning, random.shuffle
- Direct calls: _derive_match_score, len, list, open

### `get_expert_system` — `services\ai_engine\expert_system.py`
- AI signals: engine
- Direct calls: ExpertSystemEngine

### `__init__` — `services\ai_engine\llm_service.py`
- AI signals: ai
- Attribute calls: os.getenv
- Direct calls: OpenAI, print

### `generate` — `services\ai_engine\llm_service.py`
- AI signals: model
- Attribute calls: kwargs.get, response.usage.model_dump, self.client.chat.completions.create
- Direct calls: LLMResponse, str

### `generate` — `services\ai_engine\llm_service.py`
- AI signals: model
- Attribute calls: kwargs.get, response.usage.model_dump, self.client.messages.create
- Direct calls: LLMResponse, str

### `generate` — `services\ai_engine\llm_service.py`
- AI signals: ai
- Attribute calls: data.get, kwargs.get, requests.post, response.json, response.raise_for_status
- Direct calls: LLMResponse, str

### `get_service` — `services\ai_engine\llm_service.py`
- AI signals: -
- Attribute calls: cls.initialize

### `initialize` — `services\ai_engine\llm_service.py`
- AI signals: ai
- Attribute calls: backend.lower
- Direct calls: AnthropicService, LLMBackendType, OpenAIService, VLLMService

### `__init__` — `services\ai_engine\model_registry.py`
- AI signals: model
- Attribute calls: self._load_registry, self._resolve_registry_file, self.models_dir.mkdir, self.registry_dir.mkdir
- Direct calls: CareerTrojanPaths, Path

### `get_model` — `services\ai_engine\model_registry.py`
- AI signals: model
- Attribute calls: model_file.exists, pickle.load
- Direct calls: Path, open, print

### `get_vectorizer` — `services\ai_engine\model_registry.py`
- AI signals: model
- Attribute calls: self.get_model

### `rollback_deployment` — `services\ai_engine\model_registry.py`
- AI signals: model
- Attribute calls: self.deploy_model
- Direct calls: keys, len, list, print, reversed

### `verify_integrity` — `services\ai_engine\model_registry.py`
- AI signals: model
- Attribute calls: self._calculate_file_hash, self.get_model_info

### `__init__` — `services\ai_engine\train_all_models.py`
- AI signals: model
- Attribute calls: datetime.now, datetime.now.isoformat, self.models_dir.mkdir
- Direct calls: CareerTrojanPaths, Path, print

### `main` — `services\ai_engine\train_all_models.py`
- AI signals: ai, model, training
- Attribute calls: trainer.run_full_training
- Direct calls: IntelliCVModelTrainer

### `run_full_training` — `services\ai_engine\train_all_models.py`
- AI signals: ai, bayes, bayesian, classifier, embedding, model
- Attribute calls: self.generate_report, self.load_cv_data, self.setup_sentence_embeddings, self.setup_spacy_model, self.train_bayesian_classifier, self.train_statistical_models, traceback.print_exc
- Direct calls: print

### `setup_sentence_embeddings` — `services\ai_engine\train_all_models.py`
- AI signals: model
- Attribute calls: json.dump, model.encode
- Direct calls: SentenceTransformer, append, int, len, open, print, str

### `train_bayesian_classifier` — `services\ai_engine\train_all_models.py`
- AI signals: ai, model, predict, score, vector
- Attribute calls: df.apply, model.fit, model.predict, pickle.dump, self._infer_job_category, vectorizer.fit_transform
- Direct calls: MultinomialNB, TfidfVectorizer, accuracy_score, extend, float, int, isin, len, list, open, print, str, train_test_split, value_counts

### `train_statistical_models` — `services\ai_engine\train_all_models.py`
- AI signals: ai, model, predict, score
- Attribute calls: education_map.get, isna.sum, missing_exp_mask.any, model.fit, model.predict, pickle.dump, str.len
- Direct calls: RandomForestRegressor, append, apply, copy, float, int, isinstance, isna, len, map, notna, open, print, r2_score, str

### `__init__` — `services\ai_engine\train_bayesian_models.py`
- AI signals: model
- Attribute calls: logger.info, self.models_path.mkdir
- Direct calls: Path

### `train_all_bayesian` — `services\ai_engine\train_bayesian_models.py`
- AI signals: ai, bayes, bayesian, training
- Attribute calls: logger.error, logger.info, name.upper, results.items, self.load_training_data, self.prepare_features, self.train_bayesian_network, self.train_hierarchical_bayesian, self.train_mcmc_sampler, self.train_naive_bayes

### `train_bayesian_network` — `services\ai_engine\train_bayesian_models.py`
- AI signals: model
- Attribute calls: joblib.dump, json.dump, logger.error, logger.info, model.fit, network.add_edges_from, np.unique, nx.DiGraph, nx.node_link_data
- Direct calls: GaussianNB, len, open

### `train_hierarchical_bayesian` — `services\ai_engine\train_bayesian_models.py`
- AI signals: model, score
- Attribute calls: joblib.dump, logger.error, logger.info, model.fit, scores.mean, scores.std
- Direct calls: GaussianNB, cross_val_score

### `train_naive_bayes` — `services\ai_engine\train_bayesian_models.py`
- AI signals: ai, predict, score
- Attribute calls: bnb.fit, bnb.predict, gnb.fit, gnb.predict, joblib.dump, logger.error, logger.info, mnb.fit, mnb.predict, np.abs
- Direct calls: BernoulliNB, GaussianNB, MultinomialNB, accuracy_score, train_test_split

### `__init__` — `services\ai_engine\train_fuzzy_logic.py`
- AI signals: model
- Attribute calls: logger.info, self.models_path.mkdir
- Direct calls: Path

### `build_all_fuzzy_systems` — `services\ai_engine\train_fuzzy_logic.py`
- AI signals: ai
- Attribute calls: logger.info, name.upper, results.items, self.build_fuzzy_decision_tree, self.build_mamdani_fis, self.build_membership_functions, self.build_sugeno_fis, self.train_fcm_clusterer

### `__init__` — `services\ai_engine\train_neural_networks.py`
- AI signals: model
- Attribute calls: logger.info, self.models_path.mkdir
- Direct calls: Path

### `train_all_architectures` — `services\ai_engine\train_neural_networks.py`
- AI signals: ai, classifier, training
- Attribute calls: logger.error, logger.info, name.upper, results.items, self.load_training_data, self.prepare_features, self.train_autoencoder, self.train_cnn_embedder, self.train_dnn_classifier, self.train_lstm_sequence, self.train_transformer_encoder

### `train_cnn_embedder` — `services\ai_engine\train_neural_networks.py`
- AI signals: model
- Attribute calls: X.reshape, keras.Sequential, keras.layers.Conv1D, keras.layers.Dense, keras.layers.GlobalAveragePooling1D, keras.layers.MaxPooling1D, logger.error, logger.info, model.compile, model.fit, model.save

### `train_dnn_classifier` — `services\ai_engine\train_neural_networks.py`
- AI signals: ai, model
- Attribute calls: joblib.dump, keras.Sequential, keras.layers.Dense, keras.layers.Dropout, logger.error, logger.info, model.compile, model.evaluate, model.fit, model.save, scaler.fit_transform, scaler.transform
- Direct calls: StandardScaler, train_test_split

### `train_lstm_sequence` — `services\ai_engine\train_neural_networks.py`
- AI signals: model
- Attribute calls: X.reshape, keras.Sequential, keras.layers.Dense, keras.layers.Dropout, keras.layers.LSTM, logger.error, logger.info, model.compile, model.fit, model.save

### `train_transformer_encoder` — `services\ai_engine\train_neural_networks.py`
- AI signals: model
- Attribute calls: keras.Sequential, keras.layers.Dense, keras.layers.LayerNormalization, logger.error, logger.info, model.compile, model.fit, model.save

### `__init__` — `services\ai_engine\train_nlp_llm_models.py`
- AI signals: model
- Attribute calls: logger.info, self.models_path.mkdir
- Direct calls: Path

### `setup_bert_embeddings` — `services\ai_engine\train_nlp_llm_models.py`
- AI signals: model
- Attribute calls: bert_dir.mkdir, logger.error, logger.info, model.save
- Direct calls: SentenceTransformer, str

### `train_all_nlp_models` — `services\ai_engine\train_nlp_llm_models.py`
- AI signals: ai, classifier, embedding, model
- Attribute calls: logger.error, logger.info, name.upper, results.items, self.load_text_data, self.setup_bert_embeddings, self.setup_gpt_config, self.train_ner_model, self.train_sentiment_analyzer, self.train_text_classifier, self.train_tokenizer, self.train_topic_model, self.train_word2vec

### `train_sentiment_analyzer` — `services\ai_engine\train_nlp_llm_models.py`
- AI signals: classifier, vector
- Attribute calls: classifier.fit, joblib.dump, logger.error, logger.info, np.random.choice, vectorizer.fit_transform
- Direct calls: MultinomialNB, TfidfVectorizer, len

### `train_text_classifier` — `services\ai_engine\train_nlp_llm_models.py`
- AI signals: classifier, vector
- Attribute calls: classifier.fit, joblib.dump, logger.error, logger.info, np.random.choice, vectorizer.fit_transform
- Direct calls: CountVectorizer, MultinomialNB, len

### `train_topic_model` — `services\ai_engine\train_nlp_llm_models.py`
- AI signals: vector
- Attribute calls: joblib.dump, lda.fit, logger.error, logger.info, vectorizer.fit_transform
- Direct calls: CountVectorizer, LatentDirichletAllocation

### `train_word2vec` — `services\ai_engine\train_nlp_llm_models.py`
- AI signals: model
- Attribute calls: logger.error, logger.info, model.save, text.lower
- Direct calls: Word2Vec, len, str, word_tokenize

### `run_all` — `services\ai_engine\train_statistical_methods.py`
- AI signals: ai, bayes, bayesian, regression, training
- Attribute calls: json.dump, logger.info, self.load_training_data, self.run_anova, self.run_bayesian_analysis, self.run_chi_square, self.run_correlation, self.run_dbscan_summary, self.run_effect_size_power, self.run_factor_analysis, self.run_hierarchical_summary, self.run_kmeans_summary, self.run_linear_regression, self.run_logistic_regression, self.run_pca
- Direct calls: enumerate, len, open

### `run_linear_regression` — `services\ai_engine\train_statistical_methods.py`
- AI signals: model, regression, score
- Attribute calls: logger.error, logger.info, model.fit, model.score
- Direct calls: LinearRegression, append, float, len

### `run_logistic_regression` — `services\ai_engine\train_statistical_methods.py`
- AI signals: model, regression, score
- Attribute calls: logger.error, logger.info, model.fit, model.score
- Direct calls: LogisticRegression, append, float, len, tolist

### `run_pca` — `services\ai_engine\train_statistical_methods.py`
- AI signals: ai
- Attribute calls: df.select_dtypes, logger.error, logger.info, pca.explained_variance_ratio_.sum, pca.fit_transform, scaler.fit_transform
- Direct calls: PCA, StandardScaler, append, float, len

### `run_time_series` — `services\ai_engine\train_statistical_methods.py`
- AI signals: model, regression
- Attribute calls: df.sort_values, logger.error, logger.info, model.fit, rolling.mean
- Direct calls: LinearRegression, append, dropna, float, len, rolling

### `__init__` — `services\ai_engine\training_orchestrator.py`
- AI signals: ai, model, training
- Direct calls: IntelliCVModelTrainer, ModelRegistry, TrainingCheckpoint, print

### `_train_bayesian_model` — `services\ai_engine\training_orchestrator.py`
- AI signals: ai, bayes, bayesian, classifier, model, vector
- Attribute calls: self.registry.deploy_model, self.registry.register_model, self.registry.register_vectorizer, self.trainer.train_bayesian_classifier
- Direct calls: get, print, str

### `_train_sentence_embeddings` — `services\ai_engine\training_orchestrator.py`
- AI signals: ai, embedding, model
- Attribute calls: self.registry.deploy_model, self.registry.register_model, self.trainer.setup_sentence_embeddings
- Direct calls: get, print, str

### `_train_spacy_model` — `services\ai_engine\training_orchestrator.py`
- AI signals: ai, model
- Attribute calls: self.registry.deploy_model, self.registry.register_model, self.trainer.setup_spacy_model
- Direct calls: get, print, str

### `_train_statistical_models` — `services\ai_engine\training_orchestrator.py`
- AI signals: ai, model
- Attribute calls: self.registry.deploy_model, self.registry.register_model, self.trainer.train_statistical_models
- Direct calls: get, print, str

### `check_prerequisites` — `services\ai_engine\training_orchestrator.py`
- AI signals: model
- Attribute calls: core_db_dir.exists, data_path.exists, merged_db.exists, models_path.mkdir
- Direct calls: Path, print

### `generate_report` — `services\ai_engine\training_orchestrator.py`
- AI signals: model
- Attribute calls: datetime.now, datetime.now.isoformat, json.dump, self.registry.list_models
- Direct calls: Path, len, open, print

### `main` — `services\ai_engine\training_orchestrator.py`
- AI signals: ai, orchestrator, training
- Attribute calls: orchestrator.run_full_training
- Direct calls: TrainingOrchestrator

### `run_full_training` — `services\ai_engine\training_orchestrator.py`
- AI signals: ai, model
- Attribute calls: self.check_prerequisites, self.generate_report, self.print_summary, self.train_all_models, traceback.print_exc
- Direct calls: print

### `train_all_models` — `services\ai_engine\training_orchestrator.py`
- AI signals: ai
- Attribute calls: datetime.fromisoformat, datetime.now, datetime.now.isoformat, self.checkpoint.clear_checkpoint, self.checkpoint.load_checkpoint, self.checkpoint.save_checkpoint, self.trainer.load_cv_data, traceback.print_exc
- Direct calls: append, len, print, total_seconds, train_func

### `__init__` — `services\ai_engine\unified_ai_engine.py`
- AI signals: model
- Direct calls: CareerTrojanPaths, ModelRegistry, Path, print, str

### `_get_vectorizer` — `services\ai_engine\unified_ai_engine.py`
- AI signals: vector
- Attribute calls: datetime.now, datetime.now.isoformat, self.registry.get_vectorizer

### `ensemble_infer` — `services\ai_engine\unified_ai_engine.py`
- AI signals: predict
- Attribute calls: confidences.append, datetime.now, datetime.now.isoformat, self._generate_reasoning, self.infer_job_category, self.infer_salary_prediction
- Direct calls: EnsembleResult, len, print, sum

### `infer_job_category` — `services\ai_engine\unified_ai_engine.py`
- AI signals: inference, model, predict, vector
- Attribute calls: datetime.now, datetime.now.isoformat, model.predict, model.predict_proba, self._get_vectorizer, vectorizer.transform
- Direct calls: InferenceResult, dict, float, len, max, print, zip

### `infer_salary_prediction` — `services\ai_engine\unified_ai_engine.py`
- AI signals: inference, model, predict
- Attribute calls: datetime.now, datetime.now.isoformat, model.predict
- Direct calls: InferenceResult, float, min, print

### `load_all_models` — `services\ai_engine\unified_ai_engine.py`
- AI signals: model
- Attribute calls: models.keys, self.load_model, self.registry.list_models
- Direct calls: print

### `load_model` — `services\ai_engine\unified_ai_engine.py`
- AI signals: model
- Attribute calls: datetime.now, datetime.now.isoformat, self.registry.get_model
- Direct calls: print

### `main` — `services\ai_engine\unified_ai_engine.py`
- AI signals: ai, engine, model
- Attribute calls: engine.load_all_models, engine.print_status, engine.test_all_models
- Direct calls: UnifiedAIEngine, print

### `print_status` — `services\ai_engine\unified_ai_engine.py`
- AI signals: model
- Attribute calls: self.loaded_models.items, self.registry.list_models, self.registry.list_models.items
- Direct calls: len, print

### `to_dict` — `services\ai_engine\unified_ai_engine.py`
- AI signals: predict
- Attribute calls: self.all_predictions.items, v.to_dict

### `_include_optional_router` — `services\backend_api\main.py`
- AI signals: -
- Attribute calls: app.include_router, logger.exception

### `_client_ip` — `services\backend_api\middleware\rate_limiter.py`
- AI signals: -
- Attribute calls: forwarded.split, request.headers.get
- Direct calls: strip

### `_build_timeseries` — `services\backend_api\routers\admin_tokens.py`
- AI signals: ai
- Attribute calls: _utcnow.date, d.isoformat, daily.keys, daily.setdefault, datetime.fromisoformat, datetime.fromisoformat.date, row.get, rows.append, store.get, ts.replace
- Direct calls: _utcnow, add, int, isinstance, len, set, sorted, str, timedelta

### `_ensure_user_from_google` — `services\backend_api\routers\auth.py`
- AI signals: model
- Attribute calls: db.add, db.commit, db.query, db.query.filter, db.query.filter.first, db.refresh, models.User, secrets.token_urlsafe, security.get_password_hash

### `_vector_from_text` — `services\backend_api\routers\career_compass.py`
- AI signals: score
- Attribute calls: text.lower
- Direct calls: _norm_score, sum

### `_require_ai_service` — `services\backend_api\routers\coaching.py`
- AI signals: -
- Direct calls: HTTPException

### `build_taxonomy_context_from_resume` — `services\backend_api\routers\coaching.py`
- AI signals: ai
- Attribute calls: _tax.infer_industries_from_titles, _tax.map_job_title_to_naics, r.get, resume_data.get, titles.append
- Direct calls: isinstance, strip

### `_audit` — `services\backend_api\routers\gdpr.py`
- AI signals: model
- Attribute calls: db.add, db.commit, models.AuditLog

### `_domain_series_from_text` — `services\backend_api\routers\insights.py`
- AI signals: score
- Attribute calls: STRUCTURAL_AXES.items
- Direct calls: _axis_score, round

### `_structural_response` — `services\backend_api\routers\insights.py`
- AI signals: ai, score
- Attribute calls: STRUCTURAL_AXES.items, cohort_domain_scores.items, domain_series.items, options_payload.keys, p.get, profile.get, statistics.median, str.strip, str.strip.lower, strip.lower, target_domain_scores.items, user_domains.items, user_profile.get
- Direct calls: _domain_series_from_text, _percentile, _profile_text_blob, _shape_label, abs, append, len, list, max, next, round, str, strip, sum

### `_pipeline_summary` — `services\backend_api\routers\intelligence.py`
- AI signals: ai, model
- Attribute calls: file_path.is_file, file_path.relative_to, file_path.stat, model_root.exists, model_root.rglob, model_rows.append, model_rows.sort, str.replace
- Direct calls: CareerTrojanPaths, _safe_read_json, _tail_jsonl, int, len, sorted, str

### `get_mentorship_service` — `services\backend_api\routers\mentorship.py`
- AI signals: -
- Attribute calls: db.connection
- Direct calls: Depends, MentorshipService

### `_process_braintree_payment` — `services\backend_api\routers\payment.py`
- AI signals: ai
- Attribute calls: braintree_service.create_sale, braintree_service.find_or_create_customer, braintree_service.is_configured
- Direct calls: HTTPException

### `_ensure_support_table` — `services\backend_api\routers\support.py`
- AI signals: model
- Attribute calls: models.SupportTicket.__table__.create

### `_handle_stripe_checkout` — `services\backend_api\routers\webhooks.py`
- AI signals: model
- Attribute calls: db.add, db.commit, db.query, db.query.filter, db.query.filter.first, models.PaymentTransaction, obj.get
- Direct calls: upper

### `_handle_stripe_invoice_paid` — `services\backend_api\routers\webhooks.py`
- AI signals: model
- Attribute calls: db.add, db.commit, db.query, db.query.filter, db.query.filter.first, models.PaymentTransaction, obj.get
- Direct calls: _update_subscription_from_gateway, upper

### `_log_event` — `services\backend_api\routers\webhooks.py`
- AI signals: model
- Attribute calls: db.add, db.flush, db.query, db.query.filter, db.query.filter.first, logger.info, models.WebhookEvent
- Direct calls: HTTPException

### `get` — `services\backend_api\services\admin_api_client.py`
- AI signals: ai
- Attribute calls: r.json, requests.get, self._headers, self._raise, self._url

### `get_admin_api_client` — `services\backend_api\services\admin_api_client.py`
- AI signals: -
- Attribute calls: os.getenv
- Direct calls: AdminFastAPIClient, int

### `post` — `services\backend_api\services\admin_api_client.py`
- AI signals: ai
- Attribute calls: r.json, requests.post, self._headers, self._raise, self._url

### `__init__` — `services\backend_api\services\advanced_analytics_service.py`
- AI signals: engine
- Attribute calls: logger.info
- Direct calls: CareerTrojanPaths, Path, get_feature_builder, get_stats_engine

### `analyze_candidate_pool` — `services\backend_api\services\advanced_analytics_service.py`
- AI signals: engine
- Attribute calls: datetime.now, datetime.now.isoformat, datetime.now.strftime, dropna.tolist, filters.items, logger.info, logger.warning, self._generate_candidate_insights, self.feature_builder.build_candidate_features, self.stats_engine.analyze_application_trends, self.stats_engine.describe_candidate_pool, self.stats_engine.fit_salary_distribution, self.stats_engine.load_candidates, self.stats_engine.save_analysis
- Direct calls: dropna, len, str

### `analyze_job_market` — `services\backend_api\services\advanced_analytics_service.py`
- AI signals: engine
- Attribute calls: datetime.now, datetime.now.isoformat, datetime.now.strftime, dropna.tolist, logger.info, logger.warning, self._generate_job_insights, self.feature_builder.build_job_features, self.stats_engine.describe_candidate_pool, self.stats_engine.fit_salary_distribution, self.stats_engine.load_jobs, self.stats_engine.save_analysis
- Direct calls: dropna, len, str

### `calculate_candidate_job_matches` — `services\backend_api\services\advanced_analytics_service.py`
- AI signals: engine
- Attribute calls: candidates_df.head, datetime.now, datetime.now.isoformat, datetime.now.strftime, jobs_df.head, logger.info, matches_df.nlargest, matches_df.nlargest.to_dict, self._generate_matching_insights, self.feature_builder.batch_calculate_matches, self.feature_builder.build_candidate_features, self.feature_builder.build_job_features, self.stats_engine.load_candidates, self.stats_engine.load_jobs, self.stats_engine.save_analysis
- Direct calls: float, len, max, mean, median

### `get_advanced_analytics_service` — `services\backend_api\services\advanced_analytics_service.py`
- AI signals: -
- Direct calls: AdvancedAnalyticsService

### `list_recent_analyses` — `services\backend_api\services\advanced_analytics_service.py`
- AI signals: engine
- Attribute calls: self.stats_engine.list_saved_analyses

### `load_saved_analysis` — `services\backend_api\services\advanced_analytics_service.py`
- AI signals: engine
- Attribute calls: self.stats_engine.load_analysis

### `predict_callback_probability` — `services\backend_api\services\advanced_analytics_service.py`
- AI signals: engine, predict
- Attribute calls: datetime.now, datetime.now.isoformat, datetime.now.strftime, insights.append, logger.info, self.stats_engine.predict_callback_rate, self.stats_engine.save_analysis
- Direct calls: items

### `run_ab_test` — `services\backend_api\services\advanced_analytics_service.py`
- AI signals: engine
- Attribute calls: datetime.now, datetime.now.isoformat, datetime.now.strftime, logger.info, self.stats_engine.compare_resume_quality, self.stats_engine.save_analysis, test_name.replace
- Direct calls: abs, len

### `get_ai_chat_service` — `services\backend_api\services\ai\ai_chat_service.py`
- AI signals: ai
- Direct calls: AIChatService

### `get_career_advice` — `services\backend_api\services\ai\ai_chat_service.py`
- AI signals: ai
- Attribute calls: datetime.now, datetime.now.isoformat, logger.error, self._build_career_advice_prompt, self._query_gemini, self._query_perplexity, self._unavailable_response

### `get_service_status` — `services\backend_api\services\ai\ai_chat_service.py`
- AI signals: -
- Direct calls: bool

### `__init__` — `services\backend_api\services\ai\ai_feedback_loop.py`
- AI signals: ai, engine
- Attribute calls: logging.basicConfig, logging.getLogger, self.logger.info
- Direct calls: AIChatResearchEngine, WebResearchEngine, defaultdict

### `_research_openai` — `services\backend_api\services\ai\ai_feedback_loop.py`
- AI signals: ai
- Attribute calls: message.content.strip, self._build_ai_prompt, self._calculate_ai_confidence, self.logger.error, self.openai_client.ChatCompletion.create
- Direct calls: ResearchResult

### `get_system_status` — `services\backend_api\services\ai\ai_feedback_loop.py`
- AI signals: ai
- Attribute calls: self.completed_research.values, self.failed_research.values
- Direct calls: Counter, dict, len, max, min, sum

### `research_term_comprehensive` — `services\backend_api\services\ai\ai_feedback_loop.py`
- AI signals: ai, engine
- Attribute calls: all_results.extend, self._consolidate_research_results, self.ai_engine.research_with_ai, self.logger.debug, self.logger.error, self.logger.info, self.logger.warning, self.web_engine.research_term
- Direct calls: len

### `research_with_ai` — `services\backend_api\services\ai\ai_feedback_loop.py`
- AI signals: ai
- Attribute calls: results.append, self._research_openai, self.logger.error, self.logger.warning

### `get_learning_tracker` — `services\backend_api\services\ai\ai_learning_tracker.py`
- AI signals: ai
- Direct calls: AILearningPatternTracker

### `get_model` — `services\backend_api\services\ai\ai_model_loader.py`
- AI signals: model
- Attribute calls: self.load_all_models, self.models.get

### `get_model` — `services\backend_api\services\ai\ai_model_loader.py`
- AI signals: model
- Attribute calls: _loader.get_model

### `get_trained_models` — `services\backend_api\services\ai\ai_model_loader.py`
- AI signals: model
- Attribute calls: _loader.load_all_models

## 4. AI keyword bearing files

### `tools\discover_runtime_wiring.py`
- Matched terms: ai, bayes, bayesian, classifier, clustering, context_assembler, embedding, engine, feature_registry, governance, inference, intelligence, ml, model, orchestrator, predict, ranking, regression, score, similarity, trained, training, unified_ai_engine, vector
  - L8: - Trace likely route -> service -> AI/module wiring
  - L9: - Detect AI/orchestrator/model signals
  - L20: discovery_output/ai_signals.json
  - L47: "htmlcov",
  - L53: AI_KEYWORDS = {
  - L54: "ai",
  - L55: "model",
  - L56: "ml",

### `services\backend_api\services\enrichment\ai_enrichment_orchestrator.py`
- Matched terms: ai, bayes, bayesian, classifier, clustering, embedding, engine, inference, ml, model, orchestrator, predict, regression, score, similarity, trained, vector
  - L2: AI Enrichment Orchestrator V3.0 - COMPREHENSIVE 100% MODEL COVERAGE
  - L4: Loads ALL AI/ML model types:
  - L5: ✓ 15 Statistical Methods (T-Tests, Chi-Square, ANOVA, Correlation, Regression, PCA, Factor Analysis, K-Means, DBSCAN, Hierarchical, Time Series, Survival, Bayesian)
  - L7: ✓ Bayesian Inference (Naive Bayes, Bayesian Networks, Hierarchical, MCMC)
  - L8: ✓ Expert Systems (Rule engines, Forward/Backward chaining, Knowledge graphs, CBR)
  - L9: ✓ NLP & LLM (Tokenization, NER, POS, Sentiment, Text Classification, Word2Vec, BERT, GPT, Topic Modeling)
  - L13: NO MOCK DATA - ALL predictions from real trained models
  - L28: from services.backend_api.services.enrichment.job_title_similarity import enrich_job_titles_with_similarity_and_migration

### `services\backend_api\services\ai\unified_ai_engine.py`
- Matched terms: ai, bayes, bayesian, classifier, clustering, embedding, engine, inference, intelligence, ml, model, predict, score, similarity, trained, training, vector
  - L3: IntelliCV Unified AI Engine - Production Ready Intelligence System
  - L6: Combines ALL AI techniques into a single, cohesive engine:
  - L7: - Bayesian Inference Engine for pattern recognition and probability analysis
  - L8: - Advanced NLP Engine for semantic understanding and context analysis
  - L9: - LLM Integration Engine for content enhancement and generation
  - L10: - Fuzzy Logic Engine for handling uncertain and ambiguous data
  - L11: - AI Learning Table with configurable thresholds
  - L14: This engine replaces the scattered AI functionality across pages 08 and 09,

### `services\workers\ai\ai-workers\training\train_hybrid_career_engine.py`
- Matched terms: ai, classifier, clustering, embedding, engine, inference, ml, model, orchestrator, predict, regression, score, similarity, trained, training, vector
  - L3: Hybrid Career Engine Training
  - L5: Orchestrates all 8 trained models into unified system:
  - L7: 8 Models Integrated:
  - L8: 1. Sentence Embeddings (384-dim semantic understanding)
  - L9: 2. Job Title Classifier (6 categories, 99.7% accuracy)
  - L10: 3. Linear Regression (salary prediction)
  - L11: 4. Logistic Regression (placement success)
  - L12: 5. Multiple Regression (job match scoring)

### `services\ai_engine\training_orchestrator.py`
- Matched terms: ai, bayes, bayesian, classifier, embedding, engine, inference, ml, model, orchestrator, predict, trained, training, unified_ai_engine, vector
  - L2: Training Orchestrator - Master Controller for AI Model Training
  - L6: - Coordinate training of all 7 AI models
  - L8: - Track training progress and metrics
  - L9: - Register models in model registry
  - L10: - Generate comprehensive training reports
  - L13: - Sequential training with checkpoints
  - L16: - Automatic model registration
  - L17: - Pre/post training validation

### `services\workers\ai\ai-workers\training\train_all_models.py`
- Matched terms: ai, bayes, bayesian, classifier, embedding, engine, model, predict, regression, score, similarity, trained, training, vector
  - L2: AI Model Training Pipeline for IntelliCV Platform
  - L5: This script trains all AI models on your 328k CV records:
  - L6: 1. Bayesian Classifier (sklearn) - Job categorization
  - L7: 2. TF-IDF Vectorizer - Text feature extraction
  - L8: 3. Sentence-BERT Embeddings - Semantic similarity
  - L9: 4. Statistical Models - Salary/experience prediction
  - L12: python train_all_models.py
  - L15: - admin_portal/models/*.pkl (trained model files)

### `services\workers\ai\ai-workers\orchestrator\ai_training_orchestrator.py`
- Matched terms: ai, classifier, clustering, embedding, engine, ml, model, orchestrator, predict, score, similarity, trained, training, vector
  - L2: AI Training Orchestrator
  - L5: Comprehensive AI model training pipeline that integrates:
  - L6: 1. Data ingestion from ai_data_final
  - L7: 2. Statistical methods (embeddings, clustering, TF-IDF)
  - L8: 3. Model training (job matching, skill extraction, industry classification)
  - L10: 5. Model persistence and versioning
  - L13: - Sentence Transformers (embeddings)
  - L14: - TF-IDF vectorization

### `services\ai_engine\unified_ai_engine.py`
- Matched terms: ai, bayes, bayesian, classifier, engine, inference, model, orchestrator, predict, score, trained, training, unified_ai_engine, vector
  - L2: Unified AI Engine - Coordinated Inference Across All Models
  - L6: - Load all trained AI models
  - L7: - Execute inference across multiple models
  - L8: - Aggregate and reconcile predictions
  - L10: - Provide confidence scores and explanations
  - L13: - Multi-model inference orchestration
  - L14: - Ensemble predictions (voting, averaging)
  - L15: - Confidence scoring and uncertainty quantification

### `services\ai_engine\train_all_models.py`
- Matched terms: ai, bayes, bayesian, classifier, embedding, engine, model, predict, regression, score, similarity, trained, training, vector
  - L2: AI Model Training Pipeline for IntelliCV Platform
  - L5: This script trains all AI models on your 328k CV records:
  - L6: 1. Bayesian Classifier (sklearn) - Job categorization
  - L7: 2. TF-IDF Vectorizer - Text feature extraction
  - L8: 3. Sentence-BERT Embeddings - Semantic similarity
  - L9: 4. Statistical Models - Salary/experience prediction
  - L12: python train_all_models.py
  - L15: - admin_portal/models/*.pkl (trained model files)

### `services\ai_engine\ai_training_orchestrator.py`
- Matched terms: ai, classifier, clustering, embedding, engine, ml, model, orchestrator, predict, score, similarity, trained, training, vector
  - L2: AI Training Orchestrator
  - L5: Comprehensive AI model training pipeline that integrates:
  - L6: 1. Data ingestion from ai_data_final
  - L7: 2. Statistical methods (embeddings, clustering, TF-IDF)
  - L8: 3. Model training (job matching, skill extraction, industry classification)
  - L10: 5. Model persistence and versioning
  - L13: - Sentence Transformers (embeddings)
  - L14: - TF-IDF vectorization

### `services\workers\ai\ai-workers\inference\unified_ai_engine.py`
- Matched terms: ai, bayes, bayesian, engine, inference, ml, model, predict, regression, trained, unified_ai_engine, vector
  - L2: Unified AI Engine - Coordinated Inference Across All Models
  - L7: 1. Classic ML Models (Bayesian, Regression)
  - L10: - Execute inference across multiple models
  - L11: - Aggregate and reconcile predictions
  - L14: from unified_ai_engine import UnifiedAIEngine
  - L15: engine = UnifiedAIEngine()
  - L16: results = engine.ensemble_infer("Senior Python Developer...")
  - L31: from model_registry import ModelRegistry

### `services\backend_api\services\career\career_coach.py`
- Matched terms: ai, bayes, bayesian, classifier, embedding, engine, model, orchestrator, predict, regression, score, similarity
  - L1: """Career Coach Service – Hybrid AI Orchestrator
  - L3: This module provides a *backend* career coaching engine that plugs
  - L4: directly into the existing hybrid AI stack in `admin_portal.ai`.
  - L29: from admin_portal.config import AIConfig
  - L30: from admin_portal.ai.nlp_engine import NLPEngine
  - L31: from admin_portal.ai.embeddings_engine import EmbeddingEngine
  - L32: from admin_portal.ai.bayesian_engine import BayesianJobClassifier
  - L33: from admin_portal.ai.regression_models import MatchScoreRegressor

### `scripts\run_full_pipeline.py`
- Matched terms: ai, bayes, bayesian, classifier, embedding, engine, model, predict, score, trained, training, vector
  - L5: Executes the complete ingestion → parsing → collocation → training pipeline.
  - L8: 1. Smoke Test      - Verify paths and data availability
  - L11: 4. Training        - Train all AI models on processed data
  - L33: sys.path.insert(0, str(PROJECT_ROOT / "services" / "ai_engine"))
  - L62: """Verify all required paths and data availability."""
  - L64: results = {"pass": [], "fail": [], "warn": []}
  - L68: ("ai_data_final", paths.ai_data_final),
  - L72: ("trained_models", paths.trained_models),

### `services\workers\ai\ai-workers\training\train_statistical_methods.py`
- Matched terms: ai, bayes, bayesian, clustering, ml, model, predict, regression, score, trained, training
  - L3: Complete Statistical Methods Training Pipeline
  - L8: 1. T-Tests, 2. Chi-Square, 3. ANOVA, 15. Bayesian Analysis
  - L10: GROUP 2: Regression (4 methods)
  - L11: 4. Correlation, 5. Linear Regression, 6. Multiple Regression, 7. Logistic Regression
  - L13: GROUP 3: Dimensionality & Clustering (4 methods)
  - L14: 8. PCA, 9. Factor Analysis, 10. K-Means, 11. DBSCAN, 12. Hierarchical Clustering
  - L19: Output: ai_data_final/analytics/ + statistical reports
  - L49: from sklearn.linear_model import LinearRegression, LogisticRegression

### `services\backend_api\services\linkedin_industry_classifier.py`
- Matched terms: ai, classifier, engine, governance, intelligence, ml, model, predict, score, training, vector
  - L6: official industry taxonomy with detailed subcategories and business software
  - L9: Author: IntelliCV-AI Team
  - L29: class LinkedInIndustryClassifier(LoggingMixin, SafeOperationsMixin):
  - L30: """Enhanced industry classifier using LinkedIn's official taxonomy"""
  - L42: "Dairy", "Farming", "Fishery", "Ranching",
  - L51: "Animation", "Broadcast Media", "Computer Games", "Entertainment",
  - L56: "Building Materials", "Civil Engineering", "Construction",
  - L57: "Building industry", "Civil and marine engineering contractors",

### `services\backend_api\routers\intelligence.py`
- Matched terms: ai, bayes, bayesian, engine, inference, intelligence, model, regression, score, trained, training
  - L4: from pydantic import BaseModel
  - L10: from services.backend_api.services.ai.statistical_analysis_engine import StatisticalAnalysisEngine
  - L11: from services.backend_api.services.web_intelligence_service import WebIntelligenceService
  - L15: router = APIRouter(prefix="/api/intelligence/v1", tags=["intelligence"])
  - L16: engine = StatisticalAnalysisEngine()
  - L17: web_intel = WebIntelligenceService()
  - L31: def _tail_jsonl(path: Path, max_lines: int = 1) -> List[Dict[str, Any]]:
  - L55: ingest_last = _tail_jsonl(ingest_log, max_lines=1)

### `services\ai_engine\train_statistical_methods.py`
- Matched terms: ai, bayes, bayesian, clustering, ml, model, predict, regression, score, trained, training
  - L3: Complete Statistical Methods Training Pipeline
  - L8: 1. T-Tests, 2. Chi-Square, 3. ANOVA, 15. Bayesian Analysis
  - L10: GROUP 2: Regression (4 methods)
  - L11: 4. Correlation, 5. Linear Regression, 6. Multiple Regression, 7. Logistic Regression
  - L13: GROUP 3: Dimensionality & Clustering (4 methods)
  - L14: 8. PCA, 9. Factor Analysis, 10. K-Means, 11. DBSCAN, 12. Hierarchical Clustering
  - L19: Output: ai_data_final/analytics/ + statistical reports
  - L49: from sklearn.linear_model import LinearRegression, LogisticRegression

### `scripts\run_orchestrator_discovery.py`
- Matched terms: ai, embedding, engine, governance, inference, intelligence, model, orchestrator, score, training, vector
  - L2: """Generate discovery-first orchestrator reports for CareerTrojan."""
  - L46: py_mains = sorted(str(p.relative_to(ROOT)).replace("\\", "/") for p in ROOT.rglob("main.py") if "node_modules" not in str(p))
  - L48: for pattern in ("apps/**/src/main.tsx", "apps/**/src/App.tsx"):
  - L52: return {"python_main": sorted(py_mains), "frontend_entries": sorted(set(fe_entries))}
  - L60: from services.backend_api.main import app  # type: ignore
  - L84: def main() -> int:
  - L91: route_count, route_head, route_tail = fastapi_routes()
  - L93: ai_engine_files = sorted(

### `services\workers\ai\ai-workers\training\train_full_ml_models.py`
- Matched terms: ai, clustering, embedding, ml, model, predict, regression, score, trained, training
  - L3: Full ML Models Training Pipeline
  - L5: Trains remaining 6 ML models:
  - L6: 1. Linear Regression (salary prediction)
  - L7: 2. Logistic Regression (placement success)
  - L8: 3. Multiple Regression (job match scoring)
  - L9: 4. Random Forest Regressor (advanced predictions)
  - L11: 6. Hierarchical Clustering (dendrograms)
  - L13: Output: trained_models/ + ai_data_final/analytics/

### `services\workers\ai\ai-workers\training\train_bayesian_models.py`
- Matched terms: ai, bayes, bayesian, classifier, inference, model, predict, score, trained, training
  - L2: ðŸŽ¯ Bayesian Model Training Module
  - L4: Trains all Bayesian inference models:
  - L5: - Naive Bayes Classifier (Gaussian, Multinomial, Bernoulli)
  - L6: - Bayesian Networks (DAG models)
  - L7: - Hierarchical Bayesian Models
  - L8: - Markov Chain Monte Carlo (MCMC)
  - L9: - Variational Inference
  - L22: from services.shared.training_data_loader import TrainingDataLoader

### `services\ai_engine\train_bayesian_models.py`
- Matched terms: ai, bayes, bayesian, classifier, inference, model, predict, score, trained, training
  - L2: 🎯 Bayesian Model Training Module
  - L4: Trains all Bayesian inference models:
  - L5: - Naive Bayes Classifier (Gaussian, Multinomial, Bernoulli)
  - L6: - Bayesian Networks (DAG models)
  - L7: - Hierarchical Bayesian Models
  - L8: - Markov Chain Monte Carlo (MCMC)
  - L9: - Variational Inference
  - L28: class BayesianModelTrainer:

### `services\workers\ai\ai-workers\training\train_nlp_llm_models.py`
- Matched terms: ai, bayes, classifier, embedding, model, similarity, trained, training, vector
  - L2: ðŸ”¤ NLP & LLM Training Module
  - L4: Trains all NLP and LLM models:
  - L10: - Embedding Models (Word2Vec, GloVe, BERT)
  - L11: - Transformer models (GPT, T5, BART)
  - L12: - Semantic Similarity
  - L13: - Topic Modeling (LDA, NMF)
  - L26: from services.shared.training_data_loader import TrainingDataLoader
  - L35: class NLPLLMTrainer:

### `services\workers\ai\ai-workers\training\train_ensemble_methods.py`
- Matched terms: ai, classifier, ml, model, predict, regression, score, trained, training
  - L2: ðŸŽ² Ensemble Methods Training Module
  - L4: Trains all ensemble learning models:
  - L8: - Voting Classifiers
  - L21: from services.shared.training_data_loader import TrainingDataLoader
  - L30: class EnsembleTrainer:
  - L31: """Comprehensive ensemble methods trainer"""
  - L35: self.data_path = CareerTrojanPaths().ai_data_final
  - L36: self.models_path = self.base_path / "trained_models" / "ensemble"

### `services\ai_engine\train_nlp_llm_models.py`
- Matched terms: ai, bayes, classifier, embedding, model, similarity, trained, training, vector
  - L2: 🔤 NLP & LLM Training Module
  - L4: Trains all NLP and LLM models:
  - L10: - Embedding Models (Word2Vec, GloVe, BERT)
  - L11: - Transformer models (GPT, T5, BART)
  - L12: - Semantic Similarity
  - L13: - Topic Modeling (LDA, NMF)
  - L32: class NLPLLMTrainer:
  - L33: """Comprehensive NLP & LLM trainer"""

### `services\ai_engine\model_registry.py`
- Matched terms: ai, bayes, bayesian, classifier, inference, model, trained, training, vector
  - L2: Model Registry - Unified Management of Trained AI Models
  - L6: - Track all trained model versions, metrics, and metadata
  - L7: - Load best/latest models for inference
  - L8: - Manage model deployment and versioning
  - L9: - Support A/B testing between model versions
  - L12: from model_registry import ModelRegistry
  - L13: registry = ModelRegistry()
  - L14: model = registry.get_model('bayesian_classifier', version='latest')

### `services\workers\ai\ai-workers\training\train_fuzzy_logic.py`
- Matched terms: ai, clustering, inference, model, predict, score, trained, training
  - L7: - Fuzzy inference systems (Mamdani, Sugeno)
  - L8: - Fuzzy clustering (FCM)
  - L34: self.data_path = CareerTrojanPaths().ai_data_final
  - L35: self.models_path = self.base_path / "trained_models" / "fuzzy"
  - L36: self.models_path.mkdir(parents=True, exist_ok=True)
  - L39: logger.info(f"Systems will be saved to: {self.models_path}")
  - L92: "match_score": {
  - L135: with open(self.models_path / "membership_functions.json", 'w') as f:

### `services\backend_api\services\enhanced_job_title_engine.py`
- Matched terms: ai, classifier, engine, intelligence, model, score, similarity, training
  - L2: Enhanced Job Title & LinkedIn Industry Integration Engine
  - L6: classification and business software categorization for advanced AI enrichment.
  - L8: Author: IntelliCV-AI Team
  - L29: # Import the LinkedIn classifier
  - L31: from services.linkedin_industry_classifier import LinkedInIndustryClassifier
  - L32: LINKEDIN_CLASSIFIER_AVAILABLE = True
  - L34: LINKEDIN_CLASSIFIER_AVAILABLE = False
  - L36: class EnhancedJobTitleEngine(LoggingMixin, SafeOperationsMixin):

### `services\backend_api\services\auto_screen_system.py`
- Matched terms: ai, bayes, bayesian, engine, intelligence, model, score, unified_ai_engine
  - L5: Automatic data screening and AI processing for user login events.
  - L11: - AI enrichment pipeline integration
  - L15: Author: IntelliCV AI Team
  - L16: Purpose: Automated user data screening with AI intelligence
  - L28: # Import our AI services
  - L30: from services.unified_ai_engine import get_unified_ai_engine
  - L33: from services.ai_data_manager import get_ai_data_manager
  - L34: from services.ai_feedback_loop import get_feedback_loop_system

### `services\backend_api\services\ai\ai_model_loader.py`
- Matched terms: ai, bayes, bayesian, classifier, model, predict, trained, vector
  - L2: Centralized AI Model Loader
  - L5: Loads all trained models at startup and provides global access.
  - L14: class AIModelLoader:
  - L15: """Central model loading and caching"""
  - L18: self.models_dir = Path(__file__).parent.parent / "models"
  - L19: self.models = {}
  - L22: def load_all_models(self):
  - L23: """Load all available trained models"""

### `services\backend_api\services\advanced_analytics_service.py`
- Matched terms: ai, engine, intelligence, ml, model, predict, regression, score
  - L3: Connects statistical engine with existing IntelliCV services
  - L17: from analytics.stats_engine import ZeroCostStatsEngine, get_stats_engine
  - L25: High-level analytics service integrating statistical engine
  - L30: - Job market intelligence
  - L32: - Predictive analytics
  - L42: data_dir: Path to ai_data_final directory
  - L46: data_dir = CareerTrojanPaths().ai_data_final
  - L49: self.stats_engine = get_stats_engine(data_dir=self.data_dir)

### `services\ai_engine\train_fuzzy_logic.py`
- Matched terms: ai, clustering, inference, model, predict, score, trained, training
  - L7: - Fuzzy inference systems (Mamdani, Sugeno)
  - L8: - Fuzzy clustering (FCM)
  - L32: self.data_path = self.base_path / "ai_data_final"
  - L33: self.models_path = self.base_path / "trained_models" / "fuzzy"
  - L34: self.models_path.mkdir(parents=True, exist_ok=True)
  - L37: logger.info(f"Systems will be saved to: {self.models_path}")
  - L90: "match_score": {
  - L133: with open(self.models_path / "membership_functions.json", 'w') as f:

### `services\workers\ai\ai-workers\training\train_neural_networks.py`
- Matched terms: ai, classifier, embedding, model, trained, training, vector
  - L2: ðŸ§  Neural Network Training Module
  - L4: Trains all neural network architectures:
  - L22: from services.shared.training_data_loader import TrainingDataLoader
  - L32: class NeuralNetworkTrainer:
  - L33: """Comprehensive neural network trainer"""
  - L37: self.data_path = CareerTrojanPaths().ai_data_final
  - L38: self.models_path = self.base_path / "trained_models" / "neural"
  - L39: self.models_path.mkdir(parents=True, exist_ok=True)

### `services\workers\ai\ai-workers\inference\model_registry.py`
- Matched terms: ai, bayes, bayesian, classifier, inference, model, trained
  - L2: Model Registry - Unified Management of Trained AI Models
  - L6: - Track all trained model versions, metrics, and metadata
  - L7: - Load best/latest models for inference
  - L8: - Manage model deployment and versioning
  - L9: - Support A/B testing between model versions
  - L12: from model_registry import ModelRegistry
  - L13: registry = ModelRegistry()
  - L14: model = registry.get_model('bayesian_classifier', version='latest')

### `services\backend_api\services\feedback\feedback_logger.py`
- Matched terms: ai, clustering, model, predict, score, similarity, training
  - L3: Logs user feedback for model retraining and improvement.
  - L6: Location: ai_data_final/feedback.jsonl
  - L30: Logs user feedback for model improvement and retraining.
  - L34: - ats_score: ATS score accuracy feedback
  - L36: - job_title_similarity: Job title similarity accuracy
  - L37: - clustering: Clustering assignment feedback
  - L46: If None, uses ai_data_final/feedback.jsonl
  - L49: # Auto-detect ai_data_final directory

### `services\backend_api\services\ai\statistical_analysis_engine.py`
- Matched terms: ai, bayes, bayesian, clustering, engine, ml, regression
  - L2: Statistical Analysis Engine
  - L9: 2. Regression Analysis
  - L17: 10. Bayesian Analysis (Naive)
  - L31: class StatisticalAnalysisEngine:
  - L49: # 2. Regression Analysis (Simple Linear)
  - L50: def linear_regression(self, x: List[float], y: List[float]) -> Dict[str, float]:
  - L89: # Welch-Satterthwaite equation for degrees of freedom
  - L140: # 8. Clustering (K-Means Simplified)

### `services\backend_api\routers\lenses.py`
- Matched terms: ai, bayes, bayesian, engine, model, orchestrator, score
  - L7: from pydantic import BaseModel, Field
  - L9: from services.backend_api.models.spider_covey import SpiderProfile, CoveyActionLens
  - L20: class BuildSpiderRequest(BaseModel):
  - L27: class BuildCoveyRequest(BaseModel):
  - L32: class BuildCompositeRequest(BaseModel):
  - L37: class CompositeResponse(BaseModel):
  - L42: @router.post("/spider", response_model=SpiderProfile)
  - L45: # In a fully wired mode, this would call the AI Engine/Orchestrator to get the real axes score.

### `services\ai_engine\train_neural_networks.py`
- Matched terms: ai, classifier, embedding, model, trained, training, vector
  - L2: 🧠 Neural Network Training Module
  - L4: Trains all neural network architectures:
  - L29: class NeuralNetworkTrainer:
  - L30: """Comprehensive neural network trainer"""
  - L34: self.data_path = self.base_path / "ai_data_final"
  - L35: self.models_path = self.base_path / "trained_models" / "neural"
  - L36: self.models_path.mkdir(parents=True, exist_ok=True)
  - L38: logger.info(f"Neural Network Trainer initialized")

### `services\workers\ai\ai-workers\training\train_expert_systems.py`
- Matched terms: ai, engine, inference, model, similarity, trained
  - L5: - Rule-based inference engines
  - L6: - Forward/Backward chaining
  - L34: self.data_path = CareerTrojanPaths().ai_data_final
  - L35: self.models_path = self.base_path / "trained_models" / "expert"
  - L36: self.models_path.mkdir(parents=True, exist_ok=True)
  - L39: logger.info(f"Systems will be saved to: {self.models_path}")
  - L41: def build_rule_engine(self):
  - L42: """Build rule-based inference engine"""

### `services\backend_api\services\sqlite_manager.py`
- Matched terms: ai, bayes, bayesian, model, score, training
  - L2: SQLite Database Manager for IntelliCV AI Learning System
  - L16: SQLITE_AVAILABLE = False
  - L22: SQLITE_AVAILABLE = True
  - L26: print("[ERROR] Built-in sqlite3 not available")
  - L29: if not SQLITE_AVAILABLE:
  - L32: SQLITE_AVAILABLE = True
  - L39: if not SQLITE_AVAILABLE:
  - L40: print("[ERROR] SQLite not available")

### `services\backend_api\services\intelligence_hub_connector.py`
- Matched terms: ai, bayes, bayesian, engine, intelligence, unified_ai_engine
  - L2: Intelligence Hub Real Data Connector
  - L5: Connects Intelligence Hub to real AI services and engines instead of demo data.
  - L7: - UnifiedAIEngine (Bayesian, NLP, LLM, Fuzzy, Fusion)
  - L8: - RealAIConnector (34k+ CV database)
  - L9: - Portal Bridge Intelligence Services
  - L12: Author: IntelliCV-AI Team
  - L32: class IntelligenceHubConnector:
  - L33: """Real data connector for Intelligence Hub - NO MORE DEMO DATA!"""

### `services\backend_api\services\blocker\detector.py`
- Matched terms: ai, engine, ml, model, ranking, score
  - L7: Author: IntelliCV AI System
  - L22: - Job matching engine
  - L35: # MAIN DETECTION METHOD
  - L66: # Rank and score
  - L114: 'criticality_score': patterns['default_criticality'],
  - L163: 'criticality_score': criticality,
  - L184: 'criticality_score': 7.0,
  - L229: 'criticality_score': 7.0 if is_required else 4.5,

### `services\backend_api\services\ai\ai_router.py`
- Matched terms: ai, bayes, bayesian, engine, intelligence, trained
  - L3: AI Router - Intelligent Workload Distribution
  - L5: Routes AI workloads to the most appropriate engine based on:
  - L6: - Task type (parsing, chat, market intelligence)
  - L18: class AIRouter:
  - L19: """Intelligently routes AI workloads to appropriate engines"""
  - L22: # Initialize available engines
  - L23: self.engines_available = self._detect_engines()
  - L25: def _detect_engines(self) -> Dict[str, bool]:

### `services\backend_api\services\ai\ai_feedback_loop.py`
- Matched terms: ai, engine, ml, model, orchestrator, score
  - L3: IntelliCV AI Feedback Loop System - Intelligent Research & Learning
  - L12: - Detect patterns in failed parsing attempts
  - L18: - Wikipedia and domain-specific knowledge extraction
  - L20: 💬 CHAT AI RESEARCH:
  - L21: - OpenAI/Claude queries for term definitions
  - L23: - Confidence scoring for AI responses
  - L29: - Retrain models with verified data
  - L34: - Scheduled research runs (daily/weekly)

### `services\backend_api\services\ai\ai_data_manager.py`
- Matched terms: ai, engine, ml, model, score, training
  - L3: IntelliCV AI Data Manager - Modular Data Directory System
  - L6: Creates and manages intelligent data directory structure for AI processing:
  - L8: 📁 ai_data_main/           # Cleaned, processed data ready for production use
  - L10: ├── high_confidence/     # AI confidence > 90% (auto-approved)
  - L14: 📁 ai_data_pending/        # Data requiring AI interrogation and validation
  - L16: ├── low_confidence/      # AI confidence < 70% (manual review required)
  - L20: 📁 ai_learning/           # Learning system data and configuration
  - L24: └── training_data/      # Training datasets for AI models

### `services\backend_api\services\ai\ai_chat_integration.py`
- Matched terms: ai, engine, ml, orchestrator, score, similarity
  - L2: AI Job Title Chat Integration Service
  - L5: Provides AI-powered chat functionality for job title descriptions, meanings,
  - L6: and career insights. Integrates with various AI services and maintains a
  - L9: Author: IntelliCV-AI Team
  - L22: from shared_backend.services.web_search_orchestrator import two_tier_web_search  # type: ignore
  - L32: # Try to import AI services (can be expanded with OpenAI, Anthropic, etc.)
  - L34: import openai
  - L35: OPENAI_AVAILABLE = True

### `scripts\e2e_golden_path.py`
- Matched terms: ai, engine, intelligence, predict, regression, score
  - L5: This script simulates a complete user journey against the live FastAPI backend.
  - L7: AI routing, processing, spider plotting, and data endpoints return live results.
  - L11: (e.g., `uvicorn services.backend_api.main:app --reload`)
  - L15: 2. AI Market Intelligence (Test predictive routing)
  - L16: 3. Regression & Statistics (Verify math engine)
  - L17: 4. Data Processing/Ingestion (Trigger AI worker queue)
  - L46: print(f"{RED}[FAIL] {context} - Expected {expected_status}, got {response.status_code}{RESET}")
  - L47: print(f"Details: {response.text}")

### `tools\enhance_training_data.py`
- Matched terms: ai, engine, model, score, training
  - L3: Enhance Training Data
  - L6: by training workflows.
  - L9: - ai_data_final/metadata/enhanced_keywords.json
  - L10: - ai_data_final/metadata/enriched_knowledge_graph.json
  - L11: - ai_data_final/metadata/expanded_case_base.json
  - L12: - ai_data_final/metadata/enhance_training_data_report.json
  - L56: "data engineering",
  - L193: "technology": ["engineer", "developer", "data", "cloud", "devops"],

### `services\workers\ai_orchestrator_enrichment.py`
- Matched terms: ai, model, orchestrator, score, training
  - L2: CareerTrojan — AI Orchestrator Enrichment Worker
  - L5: into ai_data_final to continuously improve the AI knowledge base.
  - L9: - Match accepted/rejected → update job_matching/ training data
  - L36: AI_DATA_ROOT = _paths.ai_data_final
  - L43: format="%(asctime)s [AI-ORCH] %(levelname)s %(message)s",
  - L46: logging.FileHandler(LOG_DIR / "ai_orchestrator.log", encoding="utf-8"),
  - L49: logger = logging.getLogger("ai_orchestrator")
  - L51: # ── Enrichment Targets in ai_data_final ──────────────────────

### `services\backend_api\services\web_intelligence_service.py`
- Matched terms: ai, intelligence, ml, orchestrator, score
  - L2: Web Intelligence Service for IntelliCV Admin Portal
  - L3: Provides real web-based company research and competitive intelligence
  - L16: from shared_backend.services.web_search_orchestrator import two_tier_web_search as _two_tier_web_search  # type: ignore
  - L20: class WebIntelligenceService:
  - L21: """Service to perform real web-based company research and intelligence gathering"""
  - L26: 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
  - L68: response.raise_for_status()
  - L71: soup = BeautifulSoup(response.text, 'html.parser')

### `services\backend_api\services\resume_parser.py`
- Matched terms: ai, engine, intelligence, ml, score
  - L3: IntelliCV Complete Data Parser - Master Historical Data Processing Engine
  - L8: - Email attachments and archives (going back to 2011)
  - L11: - Web-scraped company intelligence data
  - L12: - Enriched AI outputs from previous runs
  - L15: data for AI enrichment and provide a complete dataset for analysis.
  - L46: and prepares it for AI enrichment in the IntelliCV system.
  - L58: self.output_dir = self.base_path / "ai_data" / "complete_parsing_output"
  - L62: self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

### `services\backend_api\services\company_intelligence_parser.py`
- Matched terms: ai, intelligence, ml, model, score
  - L14: ENHANCED_SIDEBAR_AVAILABLE = True
  - L16: ENHANCED_SIDEBAR_AVAILABLE = False
  - L20: if ENHANCED_SIDEBAR_AVAILABLE:
  - L27: IntelliCV Company Intelligence Parser — Refactored (Robust + Safe)
  - L28: - Safer search via DuckDuckGo HTML (no Google SERP scraping).
  - L30: - Canonical domain keys + SQLite persistence, JSON export mirror.
  - L32: - Weighted industry heuristic (easy to upgrade to ML later).
  - L33: - Batch concurrency with domain locks + polite sleep.

### `services\backend_api\services\company_intelligence\enrich.py`
- Matched terms: ai, embedding, engine, intelligence, ml
  - L9: from tenacity import retry, wait_exponential, stop_after_attempt
  - L12: from ..company_ai.semantic_enrichment import generate_embeddings
  - L13: from ..company_ai.api_integration import expose_api_endpoints
  - L17: @retry(wait=wait_exponential(multiplier=1, min=4, max=60), stop=stop_after_attempt(5))
  - L31: Returns a dictionary with company intelligence fields.
  - L42: logger.warning(f"[CACHE] Date parse failed for {company_name}: {e}")
  - L48: logger.warning(f"[WARN] Google search failed for {company_name}")
  - L50: soup = BeautifulSoup(response.content, 'html.parser')

### `services\backend_api\services\azure_integration.py`
- Matched terms: ai, intelligence, ml, model, score
  - L17: AZURE_AVAILABLE = {}
  - L21: from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
  - L23: AZURE_AVAILABLE['storage'] = True
  - L25: AZURE_AVAILABLE['storage'] = False
  - L26: print("[WARNING] Azure Storage SDK not available - install: pip install azure-storage-blob")
  - L32: AZURE_AVAILABLE['identity'] = True
  - L34: AZURE_AVAILABLE['identity'] = False
  - L35: print("[WARNING] Azure Identity SDK not available - install: pip install azure-identity")

### `services\backend_api\routers\insights.py`
- Matched terms: ai, engine, governance, model, score
  - L11: # Try to import DataLoader — graceful fallback if not available
  - L13: from services.ai_engine.data_loader import DataLoader
  - L36: "risk_modelling",
  - L68: "risk_modelling": ["risk", "scenario", "sensitivity", "mitigation", "exposure"],
  - L80: "functional_expertise": ["finance", "engineering", "marketing", "product", "operations", "sales"],
  - L85: "reporting_rigour": ["reporting", "governance", "status", "audit", "tracking"],
  - L111: def _axis_score(text: str, axis: str) -> float:
  - L120: def _domain_series_from_text(text: str) -> Dict[str, List[float]]:

### `services\backend_api\routers\career_compass.py`
- Matched terms: ai, engine, model, score, vector
  - L10: from pydantic import BaseModel
  - L15: from services.backend_api.db.models import Job, Mentor, Resume
  - L22: _VECTOR_AXES = [
  - L29: "domain_expertise",
  - L57: def _norm_score(matches: int, max_matches: int = 8) -> float:
  - L63: def _vector_from_text(text: str) -> Dict[str, float]:
  - L72: "domain_expertise": ["industry", "domain", "specialist", "expert"],
  - L75: for axis in _VECTOR_AXES:

### `services\ai_engine\schema_adapter.py`
- Matched terms: ai, engine, model, score, training
  - L4: Normalizes heterogeneous record schemas from ai_data_final into a unified
  - L5: training format consumed by model trainers.
  - L20: "technology": ["software", "developer", "engineering", "cloud", "devops", "data"],
  - L23: "education": ["education", "teacher", "lecturer", "training", "university"],
  - L25: "operations": ["operations", "logistics", "supply chain", "procurement"],
  - L26: "marketing": ["marketing", "seo", "campaign", "brand", "growth"],
  - L77: scores: Dict[str, int] = {}
  - L79: scores[industry] = sum(1 for key in keys if key in haystack)

### `tools\ingest_deep_v3.py`
- Matched terms: ai, engine, model, trained
  - L5: Phased deep-ingest utility that mines parser + ai_data_final sources and
  - L67: EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
  - L75: "email": "emails.json",
  - L137: for email in EMAIL_RE.findall(text):
  - L138: item = make_entry(email, "email", 0.95)
  - L169: def mine_data_cloud_solutions(ai_data: Path, limit_files: int = 5000) -> List[Entry]:
  - L171: root = ai_data / "data_cloud_solutions"
  - L192: def mine_enhanced_job_titles_extended(ai_data: Path, limit_rows: int = 200000) -> List[Entry]:

### `tools\e_drive_audit.py`
- Matched terms: ai, ml, model, trained
  - L13: "node_modules", ".git", "__pycache__", "trained_models",
  - L14: "ai_data_final", "Klayiyo - sdk", ".venv", ".venv-j", "venv",
  - L15: "data-mounts"  # exclude raw data dumps - they have email content with RE:\"
  - L17: EXTS = {".py", ".yaml", ".yml", ".env", ".toml", ".cfg", ".ini", ".json", ".md", ".txt", ".sh", ".ps1", ".bat"}
  - L19: # Match actual E:\ drive paths (E:\something), not regex fragments or email "RE:\""

### `services\workers\ai\ai-workers\shared\real_ai_connector.py`
- Matched terms: ai, engine, intelligence, ranking
  - L2: Real AI Data Connector for Portal Bridge
  - L4: Connects portal_bridge to actual parsed AI data (ai_data_final/)
  - L5: Replaces all mock/demo data with real intelligence from 34k+ CVs
  - L10: - Real company intelligence
  - L24: class RealAIDataConnector:
  - L26: Connects to REAL AI data from ai_data_final directory.
  - L31: self.base_path = CareerTrojanPaths().ai_data_final
  - L103: This contains actual career patterns from 34,112 CVs!

### `services\workers\ai\ai-workers\inference\ollama_connector.py`
- Matched terms: ai, embedding, inference, model
  - L5: Provides a unified interface to local LLM models via Ollama.
  - L8: - Embeddings (nomic-embed-text)
  - L9: - Health Checks & Model Pulling
  - L12: from services.ai_workers.inference.ollama_connector import OllamaConnector
  - L14: response = client.generate("Summarize this CV", model="llama3")
  - L37: def list_models(self) -> List[str]:
  - L38: """List available local models"""
  - L42: models = res.json().get('models', [])

### `services\shared\training_data_loader.py`
- Matched terms: ai, model, training, vector
  - L2: Shared training data loader for all model trainers.
  - L7: - Extracts text, skills, education, experience, email, and phone
  - L8: - Provides helpers for feature vectors and text corpora
  - L24: logger = logging.getLogger("training_data_loader")
  - L27: EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
  - L44: class TrainingRecord:
  - L45: """Canonical schema for training samples."""
  - L54: email: str

### `services\backend_api\services\zendesk_ai_agent.py`
- Matched terms: ai, classifier, ml, model
  - L2: CareerTrojan — Zendesk AI Agent Worker
  - L4: Polls the AI job queue for pending Zendesk jobs and runs LLM-powered
  - L9: python -m services.backend_api.services.zendesk_ai_agent
  - L29: from services.backend_api.services.ai_queue_service import (
  - L30: claim_next,
  - L33: fail_job,
  - L47: logger = logging.getLogger("zendesk_ai_agent")
  - L55: """Return 'openai' or 'anthropic' based on env config."""

### `services\backend_api\services\test_smart_enrichment.py`
- Matched terms: ai, engine, model, score
  - L2: from enrichment.ats_scorer import ATSScorer
  - L18: ENHANCED_SIDEBAR_AVAILABLE = True
  - L20: ENHANCED_SIDEBAR_AVAILABLE = False
  - L24: if ENHANCED_SIDEBAR_AVAILABLE:
  - L34: {'title': 'Software Engineer', 'description': 'Worked on team projects. Demonstrated leadership and communication.', 'start_date': '2020-01-01', 'end_date': '2021-01-01'},
  - L43: self.ats = ATSScorer(self.config.get('ats_keywords', []))
  - L48: self.assertIn('ats_score', enriched)
  - L59: results = ATSScorer.enrich_batch(profiles)

### `services\backend_api\services\job_title_enhancement_engine.py`
- Matched terms: ai, engine, intelligence, training
  - L2: IntelliCV-AI Job Title Normalization and Enhancement Engine
  - L6: the AI engine's capability for:
  - L13: Author: IntelliCV-AI Team
  - L23: class JobTitleEnhancementEngine:
  - L24: """Advanced job title processing and enhancement engine"""
  - L71: 'Specilaist': 'Specialist',
  - L72: 'Spcilaist': 'Specialist',
  - L73: 'Specilait': 'Specialist',

### `services\backend_api\services\interview_coaching_service.py`
- Matched terms: ai, engine, model, score
  - L19: "engineering": "OPS",
  - L40: "days_31_60": ["Drive cross-functional execution", "Unblock structural constraints"],
  - L41: "days_61_90": ["Deliver strategic milestone", "Publish operating model + next quarter plan"],
  - L107: answer_score: Optional[int] = None,
  - L116: answer_score=answer_score,

### `services\backend_api\services\industry_taxonomy_service.py`
- Matched terms: ai, engine, ml, score
  - L2: Industry Taxonomy Service for IntelliCV-AI
  - L10: - AI enrichment pipeline
  - L15: • NAICS 2022 (North American Industry Classification System)
  - L22: - .load_naics()
  - L27: - If a dataset path is missing, the loader fails *gracefully*.
  - L32: - 18_Job_Title_AI_Integration.py
  - L47: INTELLICV_NAICS_STRUCTURE         – NAICS 2022 structure Excel
  - L48: INTELLICV_NAICS_DESCRIPTIONS      – NAICS 2022 descriptions Excel

### `services\backend_api\services\enrichment\keyword_enricher.py`
- Matched terms: bayes, bayesian, score, similarity
  - L3: - Integrates keyword extraction, similarity, and thesaurus building into the enrichment pipeline
  - L4: - Ready for LLM/NLP/Bayesian hybrid enrichment
  - L11: from services.backend_api.services.enrichment.job_title_similarity import detect_industry_migrations, job_title_similarity
  - L94: def score_pmi(
  - L99: Compute a simple PMI score for a given bigram using a corpus.
  - L141: Advanced keyword enrichment: keywords, acronyms, pseudo-acronyms, near-phrases, industry migrations, and job title similarity.
  - L154: # Job title similarity (if job_titles provided)
  - L155: similarity = {}

### `services\backend_api\services\enrichment\ats_scorer.py`
- Matched terms: ai, engine, model, score
  - L17: # --- spaCy and rapidfuzz model loading at module level ---
  - L25: NLP_MODEL = None
  - L28: NLP_MODEL = spacy.load('en_core_web_sm')
  - L30: logging.warning(f"spaCy model load failed: {e}")
  - L31: NLP_MODEL = None
  - L35: class ATSScorer:
  - L37: Main enrichment and ATS scoring engine for user profiles.
  - L57: def contextual_score(self, profile: Dict[str, Any], job_target: Optional[str]) -> float:

### `services\backend_api\services\email_data_service.py`
- Matched terms: ai, inference, intelligence, score
  - L22: def _normalize_email(value: str) -> str:
  - L26: PERSONAL_EMAIL_DOMAINS = {
  - L27: "gmail.com",
  - L28: "googlemail.com",
  - L30: "hotmail.com",
  - L38: "protonmail.com",
  - L67: SUSPICIOUS_DOMAIN_MARKERS = {
  - L69: "mailinator",

### `services\backend_api\services\career\interview_coach_service.py`
- Matched terms: ai, engine, predict, score
  - L16: "marketing", "brand", "campaign", "cac", "seo", "sem", "content", "attribution", "channel",
  - L22: "software", "developer", "engineering manager", "code", "api", "backend", "frontend", "microservice", "deployment", "pr",
  - L30: "engineering": [
  - L44: "How does customer feedback move from insights into campaign decisions here?",
  - L50: "How do you balance deployment speed against security/compliance requirements?",
  - L54: "How does the team protect deep work time for engineers?",
  - L56: "Tell me about a failed engineering experiment and what leadership learned from it.",
  - L70: "engineering": [

### `services\backend_api\services\ai_data_index_service.py`
- Matched terms: ai, ml, model, training
  - L2: AI Data Index Service
  - L5: Provides full indexing capabilities for ai_data_final and automated_parser directories.
  - L40: INDUSTRY_FIELDS = ["industry", "industries", "sector", "domain", "field", "vertical"]
  - L121: source_type: str  # ai_data_final | automated_parser
  - L137: class AIDataIndexSummary:
  - L138: """Summary of indexed ai_data_final content."""
  - L161: failure_reason: str = ""
  - L197: class DataIndexState:

### `services\backend_api\routers\ops.py`
- Matched terms: ai, engine, model, score
  - L3: from pydantic import BaseModel
  - L23: # --- Processing (Live AI Routine) ---
  - L24: class ProcessOptions(BaseModel):
  - L39: logger.error(f"[JOB {job_id}] Critical failure in background ingestion: {str(e)}")
  - L46: return {"job_id": job_id, "status": "started", "engine": "automatic_data_ingestion_service"}
  - L64: raise HTTPException(status_code=403, detail="Admin required")
  - L66: raise HTTPException(status_code=401, detail="Invalid token")
  - L87: class GateCheck(BaseModel):

### `services\backend_api\routers\analytics.py`
- Matched terms: ai, model, trained, training
  - L19: AI_DATA_PATH = runtime_paths.ai_data_final
  - L24: Get system-wide statistics from ai_data_final directories
  - L37: "email_extracted": int
  - L51: "email_extracted"
  - L55: dir_path = AI_DATA_PATH / dir_name
  - L80: "training_status": dict,
  - L81: "models": dict
  - L86: stats_response = await get_statistics()

### `services\backend_api\middleware\interaction_logger.py`
- Matched terms: ai, embedding, orchestrator, ranking
  - L2: InteractionLoggerMiddleware — AI Data Enrichment Loop (Section 13)
  - L4: Captures every API request as an interaction record for the AI enrichment pipeline.
  - L7: The ai_orchestrator_enrichment.py watchdog picks up these files and routes them
  - L8: to the appropriate enrichment pipeline (embedding, ranking feedback, coaching, UX).
  - L13: [ai_orchestrator_enrichment.py] (watchdog)
  - L15: [ai_data_final/ enriched datasets]
  - L58: Checks: JWT claim, query param, header, or 'anonymous'.
  - L65: # 2. From Authorization header (decode JWT sub claim)

### `services\ai_engine\config.py`
- Matched terms: ai, engine, model, trained
  - L23: if path.name.casefold() == "ai_data_final":
  - L47: ai_data_override = os.getenv("CAREERTROJAN_AI_DATA")
  - L48: if ai_data_override:
  - L49: AI_DATA_DIR = Path(ai_data_override).expanduser()
  - L51: AI_DATA_DIR = data_root / "ai_data_final"
  - L59: # AI Engine Paths
  - L60: ai_engine_root = runtime_root / "services" / "ai_engine"
  - L61: models_path = ai_engine_root / "trained_models"

### `scripts\review_api_matrix.py`
- Matched terms: ai, engine, intelligence, regression
  - L3: Review Pack 1: API Regression Matrix
  - L4: Runs a deterministic endpoint matrix against a running CareerTrojan stack.
  - L36: raise ValueError(f"Unsupported method: {method}")
  - L52: tag = "PASS" if ok else "FAIL"
  - L56: def main() -> int:
  - L57: parser = argparse.ArgumentParser(description="Run CareerTrojan API regression matrix")
  - L72: EndpointCase("Intelligence Market", "GET", "/api/intelligence/v1/market", (200,)),
  - L88: "job_family": "Software Engineering",

### `tests\unit\test_webhooks.py`
- Matched terms: ai, engine, model
  - L6: - Health endpoint availability
  - L7: - Braintree webhook signature verification stub
  - L28: from services.backend_api.main import app
  - L30: return TestClient(app, raise_server_exceptions=False)
  - L34: def db_engine():
  - L35: """In-memory SQLite engine + tables for webhook DB operations.
  - L39: from sqlalchemy import create_engine
  - L41: from services.backend_api.db.models import Base

### `tests\unit\test_v1_contract_routes.py`
- Matched terms: ai, engine, vector
  - L3: from services.backend_api.main import app
  - L6: client = TestClient(app, raise_server_exceptions=False)
  - L50: "selected_target_role": "Engineering Manager",
  - L132: def test_v1_user_vector_current_missing_resume_contract():
  - L133: response = client.get("/api/v1/user-vector/current", params={"user_id": 909090})

### `tests\unit\test_models.py`
- Matched terms: ai, engine, model
  - L2: Unit tests — DB models instantiation (no real DB needed).
  - L15: class TestModels:
  - L17: def test_user_model_fields(self):
  - L18: from services.backend_api.db.models import User
  - L19: u = User(email="a@b.com", hashed_password="xxx", full_name="Test")
  - L20: assert u.email == "a@b.com"
  - L25: def test_job_model_fields(self):
  - L26: from services.backend_api.db.models import Job

### `tests\integration\test_observability.py`
- Matched terms: ai, engine, model
  - L7: from services.backend_api.main import app
  - L8: from services.backend_api.db.connection import engine
  - L9: from services.backend_api.db.models import Base
  - L11: Base.metadata.create_all(bind=engine)

### `tests\integration\test_gdpr_endpoints.py`
- Matched terms: ai, engine, model
  - L2: Integration tests for GDPR endpoints and admin AI-loop endpoints.
  - L8: from services.backend_api.main import app
  - L9: from services.backend_api.db.connection import engine
  - L10: from services.backend_api.db.models import Base
  - L15: Base.metadata.create_all(bind=engine)
  - L39: def _get_auth_headers(email: str = "gdpr-test@careertrojan.com", role: str = "user"):
  - L41: token = security.create_access_token(data={"sub": email, "role": role})
  - L49: def _ensure_user(db, email="gdpr-test@careertrojan.com", role="user"):

### `tests\api_probe_v2.py`
- Matched terms: ai, engine, intelligence
  - L25: ("GET",  "/api/admin/v1/email/logs", "admin-email-logs", None),
  - L26: ("GET",  "/api/admin/v1/email/analytics", "admin-email-analytics", None),
  - L27: ("GET",  "/api/admin/v1/email/status", "admin-email-status", None),
  - L35: ("GET",  "/api/admin/v1/email/jobs", "admin-email-jobs", None),
  - L39: ("GET",  "/api/admin/v1/ai/enrichment/status", "admin-enrich-status", None),
  - L40: ("GET",  "/api/admin/v1/ai/enrichment/jobs", "admin-enrich-jobs", None),
  - L41: ("GET",  "/api/admin/v1/ai/content/status", "admin-content-status", None),
  - L42: ("GET",  "/api/admin/v1/ai/content/jobs", "admin-content-jobs", None),

### `tests\api_probe.py`
- Matched terms: ai, engine, intelligence
  - L5: Pass/Fail for each route, grouped by router.
  - L28: ("GET",  "/api/admin/v1/email/logs", "admin-email-logs", None),
  - L29: ("GET",  "/api/admin/v1/email/analytics", "admin-email-analytics", None),
  - L30: ("GET",  "/api/admin/v1/email/status", "admin-email-status", None),
  - L38: ("GET",  "/api/admin/v1/email/jobs", "admin-email-jobs", None),
  - L42: ("GET",  "/api/admin/v1/ai/enrichment/status", "admin-enrichment-status", None),
  - L43: ("GET",  "/api/admin/v1/ai/enrichment/jobs", "admin-enrichment-jobs", None),
  - L44: ("GET",  "/api/admin/v1/ai/content/status", "admin-content-status", None),

### `services\workers\ai\ai-workers\parser\automated_parser_engine.py`
- Matched terms: ai, engine, ml
  - L2: Automated Parser Engine - Production Ready Data Extraction
  - L10: python automated_parser_engine.py
  - L14: from automated_parser_engine import AutomatedParserEngine
  - L15: parser = AutomatedParserEngine()
  - L39: class AutomatedParserEngine:
  - L45: def __init__(self, parser_root='automated_parser', output_root='ai_data_final'):
  - L56: self.failed_index_file = self.output_root / '_failed_sources.json'
  - L60: self.failed_sources = self._load_failed_sources()

### `services\shared\paths.py`
- Matched terms: ai, model, trained
  - L5: points to the data-root folder (containing `ai_data_final/`) or directly to
  - L6: the `ai_data_final/` directory itself.
  - L33: def _looks_like_ai_data_final(path: Path) -> bool:
  - L34: if path.name.casefold() == "ai_data_final":
  - L42: if expanded.name.casefold() == "ai_data_final":
  - L54: Path(r"L:\VS ai_data final - version"),
  - L55: Path(r"L:\antigravity_version_ai_data_final"),
  - L60: Path("/mnt/ai-data"),

### `services\backend_api\services\resume_universal_parser.py`
- Matched terms: ai, intelligence, score
  - L8: Extracts: candidate info, skills, education, experience, certifications, contact info, file metadata, and advanced intelligence features.
  - L22: from enrichment.ats_scorer import ATSScorer
  - L36: OUTPUT_DIR = PROJECT_ROOT / "ai_data" / "normalized"
  - L59: RESUME_PARSER_AVAILABLE = True
  - L60: logger.info("[SUCCESS] Resume parser available")
  - L62: RESUME_PARSER_AVAILABLE = False
  - L63: logger.warning(f"[WARNING] Resume parser not available: {e}")
  - L68: """Comprehensive universal document parser with advanced intelligence features"""

### `services\backend_api\services\real_ai_data_service.py`
- Matched terms: ai, intelligence, ml
  - L2: Real AI Data Service for IntelliCV Admin Portal
  - L3: Connects to actual ai_data_final and live data sources instead of mock data
  - L19: class RealAIDataService:
  - L20: """Service to provide real AI data from actual ai_data_final and live sources"""
  - L24: self.ai_data_final_path = self.base_path / "ai_data_final"
  - L25: self.ai_data_path = self.base_path / "ai_data" if not self.ai_data_final_path.exists() else self.ai_data_final_path
  - L30: self.ai_profiles_cache = []
  - L38: self.load_real_ai_data()

### `services\backend_api\services\pdf_export_service.py`
- Matched terms: ai, engine, ml
  - L5: for AI-generated content, resumes, cover letters, and job descriptions.
  - L171: HTML-formatted text for ReportLab
  - L173: # Replace markdown bold with HTML
  - L176: # Replace markdown italic with HTML
  - L199: BytesIO object containing PDF
  - L254: BytesIO object containing PDF
  - L309: BytesIO object containing PDF
  - L327: # Application details

### `services\backend_api\services\model\model_config.py`
- Matched terms: ai, model, orchestrator
  - L2: Model Config Module
  - L3: - Provides model registry, config toggles, and admin controls
  - L4: - Exposes hooks for orchestrator and admin UI
  - L6: def get_model_config():
  - L7: # Placeholder: implement model config logic
  - L8: return {"models": [], "toggles": {}}
  - L10: # TODO: Integrate with hybrid AI harness and admin dashboard

### `services\backend_api\services\keyword_extractor.py`
- Matched terms: ai, similarity, vector
  - L12: # --- AI enrichment integration hook ---
  - L15: Hook for User_final/AI enrichment: Extract, enrich, and attach keywords and similarities to user profile.
  - L29: from sklearn.feature_extraction.text import CountVectorizer
  - L30: vectorizer = CountVectorizer(ngram_range=(n, n), stop_words='english').fit([text])
  - L31: ngrams = vectorizer.get_feature_names_out()
  - L32: counts = vectorizer.transform([text]).toarray().flatten()
  - L41: - Computes keyword similarity (for thesaurus/acronym/psuedo-acronym enrichment)
  - L42: - Designed for AI enrichment and user profile integration

### `services\backend_api\services\job_description_parser.py`
- Matched terms: ai, engine, ml
  - L18: {"title": "Software Engineer", "description": "Develop and maintain software applications.", "requirements": ["Python", "SQL"]}
  - L25: soup = BeautifulSoup(resp.text, 'html.parser')

### `services\backend_api\services\intellicv_data_manager.py`
- Matched terms: ai, model, training
  - L6: - AI training data in ai_data_final
  - L7: - Email integration data
  - L9: - Backend AI services data (neural network, expert system, etc.)
  - L38: # Main data root and AI training data
  - L40: self.ai_data_path = paths.ai_data_final
  - L42: # Email integration data
  - L43: self.email_data_path = self.data_root / "email_integration"
  - L44: self.email_extracted_path = self.data_root / "email_extracted"

### `services\backend_api\services\data_parser_service.py`
- Matched terms: ai, ml, score
  - L20: self.ai_data_path = self.base_path / "ai_data_final" if (self.base_path / "ai_data_final").exists() else self.base_path / "ai_data"
  - L96: # Check AI data directories for processing issues
  - L97: if self.ai_data_path.exists():
  - L98: for subdir in self.ai_data_path.iterdir():
  - L103: "File": f"{subdir.name}/ (AI data)",
  - L193: if self.ai_data_path.exists():
  - L194: all_files = list(self.ai_data_path.rglob("*"))
  - L231: # Keep default metrics if analysis fails

### `services\backend_api\services\credit_system.py`
- Matched terms: ai, intelligence, score
  - L4: Single credit currency replacing dual token/AI-call system.
  - L8: - PAID: Unlock full functionality with graduated limits
  - L84: blocker_detection=False,         # Sees that blockers exist, not details
  - L183: preview_available: bool = False      # Can free users see a preview?
  - L205: description="View main dashboard",
  - L227: name="View Job Details",
  - L249: # CAREER ANALYSIS (Preview for free, full for paid)
  - L256: preview_available=True,

### `services\backend_api\services\covey_builder.py`
- Matched terms: ai, model, score
  - L10: from services.backend_api.models.spider_covey import (
  - L30: "domain_fit": 1.10,
  - L96: return float(max(0, 100 - axis.score))
  - L149: time_score = _clip_0_100((time_minutes / 180.0) * 100.0)
  - L150: complexity_score = _clip_0_100(((complexity - 1.0) / 4.0) * 100.0)
  - L151: dependency_score = _clip_0_100(dependency * 100.0)
  - L154: EFFORT_TIME_WEIGHT * time_score
  - L155: + EFFORT_COMPLEXITY_WEIGHT * complexity_score

### `services\backend_api\services\company_jd_auto_updater.py`
- Matched terms: ai, model, score
  - L46: jd_storage_path = base_path / "ai_data_final" / "job_descriptions"
  - L67: company_domain TEXT,
  - L81: company_domain TEXT,
  - L86: priority_score REAL DEFAULT 0,
  - L133: logger.error(f"❌ Failed to initialize database: {e}")
  - L134: raise
  - L262: def _update_company_status(self, company_name: str, domain: Optional[str] = None):
  - L269: INSERT OR IGNORE INTO company_status (company_name, company_domain)

### `services\backend_api\services\company_intelligence_api.py`
- Matched terms: ai, engine, intelligence
  - L11: ENHANCED_SIDEBAR_AVAILABLE = True
  - L13: ENHANCED_SIDEBAR_AVAILABLE = False
  - L17: if ENHANCED_SIDEBAR_AVAILABLE:
  - L22: FastAPI and Flask integration for CompanyIntel enrichment engine.
  - L31: from services.company_intelligence_parser import CompanyIntel
  - L33: app = FastAPI(title="IntelliCV Company Intelligence API")
  - L82: if __name__ == "__main__":
  - L83: # To run FastAPI: uvicorn services.company_intelligence_api:app --reload

### `services\backend_api\services\company_ai\semantic_enrichment.py`
- Matched terms: ai, embedding, vector
  - L2: Semantic Enrichment Module: Generates embeddings for company data.
  - L5: def generate_embeddings(company_data: dict) -> dict:
  - L6: """Generate semantic vectors for company descriptions."""
  - L7: # Implementation will use OpenAI/HuggingFace

### `services\backend_api\services\company_ai\feedback_learning.py`
- Matched terms: ai, model, training
  - L2: Feedback & Continuous Learning Module: Captures feedback and improves models.
  - L6: """Ingest feedback and update models or data."""
  - L7: # Implementation will use feedback loops, retraining

### `services\backend_api\services\company_ai\__init__.py`
- Matched terms: ai, embedding, intelligence
  - L2: IntelliCV-AI Company Intelligence Package
  - L4: This package provides modular, production-grade company intelligence and enrichment tools for the IntelliCV platform.
  - L7: - nlp_extraction: AI/NLP entity extraction (spaCy)
  - L8: - semantic_enrichment: Embedding generation
  - L16: Main API:
  - L17: - CompanyIntel: Robust, safe, and scalable company enrichment (see market_intelligence.py)
  - L23: # Optionally, expose CompanyIntel if placed here or importable from market_intelligence.py
  - L24: # from .company_intelligence import CompanyIntel

### `services\backend_api\services\blocker_connector.py`
- Matched terms: ai, engine, ml
  - L9: Author: IntelliCV AI System
  - L20: BLOCKER_SERVICES_AVAILABLE = True
  - L73: 'error': 'Blocker detection service unavailable'
  - L224: def is_available(self) -> bool:
  - L225: """Check if blocker services are available"""
  - L226: return BLOCKER_SERVICES_AVAILABLE and self.detector is not None
  - L231: 'services_available': BLOCKER_SERVICES_AVAILABLE,
  - L234: 'ready': self.is_available()

### `services\backend_api\services\abuse_policy_service.py`
- Matched terms: ai, score, similarity
  - L4: Evaluates new resume uploads against fingerprints of recent submissions
  - L19: SIMILARITY_THRESHOLD = 0.85    # 0-1; above this = duplicate flag
  - L31: risk_score: int             # 0-100
  - L48: # ── similarity ───────────────────────────────────────────────────
  - L56: # ── main evaluation ──────────────────────────────────────────────
  - L67: score = 0
  - L73: score += RISK_WEIGHTS["duplicate_text"]
  - L80: codes.append("daily_limit_exceeded")

### `services\backend_api\routers\user_vector_v1.py`
- Matched terms: ai, model, vector
  - L9: from services.backend_api.db.models import Resume
  - L10: from services.backend_api.routers.career_compass import _vector_from_text
  - L14: router = APIRouter(prefix="/api/v1/user-vector", tags=["user-vector-v1"])
  - L18: def get_current_user_vector(
  - L31: message="No live parsed resume available for this user.",
  - L32: data={"vector": None, "confidence": None},
  - L43: message="The resolved resume does not contain parsed content.",
  - L44: data={"vector": None, "confidence": None},

### `services\backend_api\routers\rewards.py`
- Matched terms: ai, governance, model
  - L15: - Top contributors get governance rights
  - L22: from pydantic import BaseModel, Field
  - L32: from services.backend_api.db.models import (
  - L67: "referral_subscribe": {"tokens": 250, "description": "Referred user subscribes to paid plan"},
  - L78: # PYDANTIC MODELS
  - L81: class RewardItem(BaseModel):
  - L91: class RewardsOut(BaseModel):
  - L93: available_tokens: int

### `services\backend_api\routers\resume.py`
- Matched terms: ai, intelligence, model
  - L8: from pydantic import BaseModel
  - L44: # Models
  - L46: class UploadIn(BaseModel):
  - L51: class ResumeView(BaseModel):
  - L58: ai_json: Optional[dict] = None
  - L83: text_content = await extract_text_from_upload(file_bytes, file.filename)
  - L85: raise HTTPException(status_code=422, detail="Unable to extract text from resume")
  - L94: # Company Intelligence hook (non-blocking): mine company names from uploaded text

### `services\backend_api\routers\coaching.py`
- Matched terms: ai, model, score
  - L7: from pydantic import BaseModel, Field
  - L13: from services.backend_api.db import models
  - L31: COACH_SERVICE_AVAILABLE = True
  - L34: COACH_SERVICE_AVAILABLE = False
  - L38: _TAXONOMY_AVAILABLE = True
  - L41: _TAXONOMY_AVAILABLE = False
  - L51: Your goal is to help the user enrich the “Profile” section of their CV by uncovering specific experiences, habits, and strengths that differentiate them from other candidates, including details they might consider trivial or obvious.
  - L62: Remind the user occasionally that even “trivial” details can be the gold that differentiates them from their competitors.

### `services\backend_api\routers\admin.py`
- Matched terms: ai, model, trained
  - L11: from services.backend_api.db import models
  - L40: "mode": "mass_mail"
  - L42: "gmail": {
  - L50: _email_dispatch_log = []
  - L55: braintree_env = (os.getenv("BRAINTREE_ENVIRONMENT") or "").strip().lower()
  - L66: if braintree_env == "production":
  - L67: braintree_mode = "live"
  - L68: elif braintree_env:

### `services\backend_api\models\spider_covey.py`
- Matched terms: ai, model, score
  - L6: from pydantic import BaseModel, Field, conint, confloat
  - L14: class SpiderAxis(BaseModel):
  - L17: score: conint(ge=0, le=100)
  - L24: class SpiderProfile(BaseModel):
  - L29: overall_fit_score: Optional[conint(ge=0, le=100)] = None
  - L34: class ActionBecause(BaseModel):
  - L41: class CoveyAction(BaseModel):
  - L57: class CoveyAxisSpec(BaseModel):

### `services\backend_api\main.py`
- Matched terms: ai, intelligence, vector
  - L22: from services.backend_api.routers import admin, user, mentor, shared, auth, mentorship, intelligence, coaching, ops, resume, blockers, payment, rewards, credits, ai_data, jobs, taxonomy, sessions, ontology, support
  - L24: from services.backend_api.routers import profile_coach_v1, profile_v1, user_vector_v1
  - L47: "http://localhost:8500",  # Main Backend
  - L99: # ── AI Enrichment Loop — logs every request as interaction ────
  - L107: """Mount optional routers with explicit error logging (no silent failures)."""
  - L111: logger.exception("Failed to mount optional router '%s': %s", router_name, exc)
  - L120: app.include_router(intelligence.router)
  - L126: app.include_router(ai_data.router)

### `services\backend_api\db\models.py`
- Matched terms: ai, model, score
  - L9: # ── GDPR & Audit Models ──────────────────────────────────────
  - L29: """Immutable audit trail for data-sensitive operations (GDPR Art. 30)."""
  - L38: detail = Column(Text)
  - L49: status = Column(String, default="pending")  # "pending", "processing", "completed", "failed"
  - L97: # ── Core Application Models ──────────────────────────────────
  - L102: email = Column(String, unique=True, index=True, nullable=False)
  - L111: # ── Payment / Braintree linkage ──
  - L112: braintree_customer_id = Column(String, nullable=True, index=True)

### `services\backend_api\db\connection.py`
- Matched terms: ai, engine, model
  - L2: from sqlalchemy import create_engine
  - L4: from .models import Base
  - L15: DEFAULT_SQLITE_URL = f"sqlite:///{db_root / 'ai_learning_table.db'}"
  - L22: engine_kwargs = {}
  - L24: engine_kwargs["connect_args"] = {"check_same_thread": False}
  - L26: engine = create_engine(DB_PATH, **engine_kwargs)
  - L27: SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
  - L37: Base.metadata.create_all(bind=engine)

### `services\ai_engine\expert_system.py`
- Matched terms: ai, engine, predict
  - L4: Rule-based consistency checks and explainability helpers for AI predictions.
  - L34: class ExpertSystemEngine:
  - L47: logger.warning("Failed loading expert rules from %s: %s", self.rules_path, exc)
  - L60: condition={"prediction_contains": ["senior"], "experience_lt": 5},
  - L62: message="Prediction includes senior but candidate experience is below 5 years.",
  - L70: condition={"prediction_contains": ["developer", "engineer"], "skills_any": ["python", "java", "javascript", "sql"]},
  - L72: message="Technical role predicted without expected technical skills evidence.",
  - L80: condition={"profile_contains": ["sales", "account executive", "business development"], "prediction_contains": ["python developer", "machine learning engineer"]},

### `services\ai_engine\data_loader.py`
- Matched terms: ai, engine, score
  - L10: from services.ai_engine.config import PROFILES_DIR
  - L14: PROFILES_DIR = Path(os.getenv("CAREERTROJAN_DATA_ROOT", r"L:\Codec-Antigravity Data set")) / "ai_data_final" / "profiles"
  - L16: logger = logging.getLogger("AI_DataLoader")
  - L19: def _derive_match_score(profile: Dict[str, Any]) -> float:
  - L25: score = 0.15
  - L26: score += min(years / 15.0, 0.45)
  - L27: score += min(skills_count / 30.0, 0.35)
  - L29: score += 0.08

### `services\ai_engine\collocation_engine.py`
- Matched terms: ai, engine, score
  - L2: CareerTrojan — Collocation Engine
  - L23: score: float
  - L27: class CollocationEngine:
  - L79: score=round(float(pmi), 4),
  - L84: results.sort(key=lambda item: (item.score, item.frequency), reverse=True)
  - L87: def find_near_pairs(
  - L95: pair_hits = Counter()
  - L96: hit_details: List[Dict[str, int]] = []

### `scripts\review_new_elements.py`
- Matched terms: ai, engine, intelligence
  - L17: def main() -> int:
  - L25: def add(name: str, ok: bool, detail: str) -> None:
  - L26: checks.append({"name": name, "ok": ok, "detail": detail})
  - L27: print(f"[{'PASS' if ok else 'FAIL'}] {name} :: {detail}")
  - L48: "/api/intelligence/v1/market",
  - L61: "job_family": "Software Engineering",
  - L83: "failed": len(checks) - passed,
  - L96: if __name__ == "__main__":

### `scripts\ingestion_smoke_test.py`
- Matched terms: ai, model, trained
  - L16: def print_fail(msg: str) -> None:
  - L17: print(f"[FAIL] {msg}")
  - L52: print(f"ai_data_final:  {paths.ai_data_final}")
  - L60: print_fail("Data root missing")
  - L62: if paths.ai_data_final.exists():
  - L63: print_pass("AI data root exists")
  - L65: print_fail("AI data root missing")
  - L73: def check_ai_structure(paths: CareerTrojanPaths) -> None:

### `scripts\extract_emails_deep.py`
- Matched terms: ai, inference, ml
  - L27: "com", "net", "org", "co", "us", "ai", "io", "xyz", "shop", "pro",
  - L38: EMAIL_PATTERN = re.compile(
  - L45: def load_tld_hints(domain_file: Path | None) -> set[str]:
  - L47: if not domain_file or not domain_file.exists():
  - L50: raw = domain_file.read_text(encoding="utf-8", errors="ignore")
  - L58: def is_valid_email(value: str, tlds: set[str]) -> bool:
  - L61: local, domain = value.rsplit("@", 1)
  - L62: if not local or not domain or "." not in domain:

### `conftest.py`
- Matched terms: ai, engine, model
  - L24: from services.backend_api.main import app as _app
  - L39: from sqlalchemy import create_engine
  - L41: from services.backend_api.db.models import Base
  - L43: engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
  - L44: Base.metadata.create_all(bind=engine)
  - L45: Session = sessionmaker(bind=engine)
  - L49: engine.dispose()

### `_test_diag.py`
- Matched terms: ai, engine, model
  - L5: from sqlalchemy import create_engine, inspect
  - L7: from services.backend_api.db.models import Base
  - L8: from services.backend_api.main import app
  - L12: engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
  - L13: Base.metadata.create_all(bind=engine)
  - L16: insp = inspect(engine)
  - L19: TestSession = sessionmaker(bind=engine)
  - L36: if p == "/api/webhooks/v1/braintree":

### `tests\unit\test_support_bridge.py`
- Matched terms: ai, model
  - L8: from services.backend_api.main import app
  - L9: return TestClient(app, raise_server_exceptions=False)
  - L17: "requester_email": "user@example.com",
  - L52: "requester_email": "billing@example.com",
  - L56: "tokens_remaining": 42,
  - L74: "requester_email": "feature@example.com",
  - L93: "requester_email": "webhook@example.com",
  - L99: from services.backend_api.db import models

### `tests\unit\test_rewards.py`
- Matched terms: ai, model
  - L10: from services.backend_api.db.models import (
  - L22: from services.backend_api.main import app
  - L23: return TestClient(app, raise_server_exceptions=False)
  - L37: user.email = "test@example.com"
  - L94: for action, details in REWARD_ACTIONS.items():
  - L95: assert "tokens" in details
  - L96: assert details["tokens"] > 0
  - L99: for action, details in REWARD_ACTIONS.items():

### `tests\unit\test_profile_coach_routes.py`
- Matched terms: ai, engine
  - L3: from services.backend_api.main import app
  - L6: client = TestClient(app, raise_server_exceptions=False)
  - L45: "user_message": "I improved our bug workflow and mentored a junior engineer.",
  - L121: "differentiators": ["Turned around failing release process"],
  - L127: "I mentor newer engineers during incidents.",

### `tests\unit\test_paths_resolution.py`
- Matched terms: ai, model
  - L16: "CAREERTROJAN_AI_DATA",
  - L22: "CAREERTROJAN_MODELS",
  - L25: monkeypatch.delenv(key, raising=False)
  - L30: def test_parent_data_root_resolves_ai_data_child(self, tmp_path, monkeypatch):
  - L32: ai_data_final = data_root / "ai_data_final"
  - L33: ai_data_final.mkdir(parents=True)
  - L40: assert resolved.ai_data_final == ai_data_final
  - L44: def test_ai_data_root_value_is_normalized_to_parent(self, tmp_path, monkeypatch):

### `tests\unit\test_observability.py`
- Matched terms: ai, ml
  - L13: # Should not raise
  - L30: # Should not raise
  - L33: def test_structlog_imported_in_main(self):
  - L34: """main.py should use configure_logging, not bare logging.basicConfig."""
  - L36: from services.backend_api import main
  - L37: src = inspect.getsource(main)
  - L51: from services.backend_api.main import app
  - L61: from services.backend_api.main import app

### `tests\unit\test_gdpr_models.py`
- Matched terms: ai, model
  - L2: Unit tests for GDPR models and Tier 2 additions.
  - L9: class TestGDPRModels:
  - L10: """Verify the new GDPR / audit DB models exist with correct columns."""
  - L13: from services.backend_api.db.models import ConsentRecord
  - L23: from services.backend_api.db.models import AuditLog
  - L33: from services.backend_api.db.models import DataExportRequest
  - L42: def test_interaction_model_fields(self):
  - L43: from services.backend_api.db.models import Interaction

### `tests\unit\test_covey_builder.py`
- Matched terms: model, score
  - L1: from services.backend_api.models.spider_covey import SpiderAxis, SpiderProfile
  - L14: score=38,
  - L22: score=45,
  - L30: score=52,

### `tests\integration\test_contamination_trap.py`
- Matched terms: ai, engine
  - L4: Feed a "Sales Person" profile to AI classification endpoints.
  - L6: FAIL: suggests "Python Developer" (hardcoded data leaking into AI).
  - L52: "python developer", "software engineer", "backend developer",
  - L53: "data scientist", "devops", "machine learning engineer", "react developer",
  - L60: """Verify AIs don't suggest tech roles for a pure sales profile."""
  - L97: """Term cloud from sales-only data must not contain 'python' or 'react'."""
  - L117: """Network graph from a sales profile should contain sales skills, not tech."""

### `tests\integration\test_api_endpoints.py`
- Matched terms: ai, intelligence
  - L16: from services.backend_api.main import app
  - L59: # May fail if DB not available, but endpoint should respond
  - L73: # Should fail validation (422) or return success structure
  - L79: "email": "test@example.com",
  - L82: # Will fail login but endpoint should respond
  - L138: class TestDataIndexEndpoints:
  - L139: """Test AI data indexing system endpoints."""
  - L146: assert "ai_data" in data

### `shared_backend\registry_loader.py`
- Matched terms: ai, ml
  - L2: import yaml
  - L5: DATA_ROOT = os.getenv("CAREERTROJAN_DATA_ROOT", "/data/ai_data_final")
  - L6: REGISTRY_PATH = os.path.join(DATA_ROOT, "config", "registry.yaml")
  - L15: Loads the capability registry from ai_data_final.
  - L20: self.config = yaml.safe_load(f)
  - L23: logger.error(f"Failed to load registry: {e}")

### `shared_backend\registry\capability_registry.py`
- Matched terms: ai, ml
  - L2: import yaml
  - L18: cls._instance.config_path = os.path.join(cls._instance.data_root, "config", "registry.yaml")
  - L30: self.config = yaml.safe_load(f) or {}
  - L33: logger.error(f"Failed to load registry yaml: {e}")

### `services\workers\ai\ai-workers\run_full_ingest.py`
- Matched terms: ai, orchestrator
  - L6: 1. Consolidate all ai_data_final directories into a single canonical root.
  - L7: 2. Execute the admin_portal Complete Data Parser against automated_parser assets.
  - L8: 3. Bulk-ingest the parser outputs into ai_data_final using the automatic ingestion service.
  - L45: AutomaticDataIngestionService,
  - L49: get_ai_data_root,
  - L54: class AutomatedParserOrchestrator:
  - L59: self.ai_root = get_ai_data_root(ensure_exists=False)
  - L60: self.legacy_ai_dirs = [

### `services\shared\types\models.py`
- Matched terms: ai, model
  - L1: from pydantic import BaseModel
  - L3: class User(BaseModel):
  - L5: email: str

### `services\backend_api\utils\file_parser.py`
- Matched terms: ai, ml
  - L57: Convert an uploaded file (bytes) to plain text.
  - L62: file_bytes = await uploaded_file.read()
  - L69: # Plain text-like formats
  - L86: if suffix in {'.html', '.htm'}:
  - L87: html = file_bytes.decode('utf-8', errors='ignore')
  - L90: return BeautifulSoup(html, "html.parser").get_text("\n").strip()
  - L94: text = re.sub(r'<[^>]+>', ' ', html)
  - L105: raise ValueError(f"Unable to read ZIP archive: {e}")

### `services\backend_api\services\zendesk_bridge_service.py`
- Matched terms: ai, ml
  - L16: subdomain = (os.getenv("ZENDESK_SUBDOMAIN") or "").strip()
  - L17: if subdomain:
  - L18: return f"https://{subdomain}.zendesk.com"
  - L20: raise RuntimeError("Zendesk is not configured: set ZENDESK_BASE_URL or ZENDESK_SUBDOMAIN")
  - L24: email = (os.getenv("ZENDESK_EMAIL") or "").strip()
  - L27: if not email or not api_token:
  - L28: raise RuntimeError("Zendesk auth missing: set ZENDESK_EMAIL and ZENDESK_API_TOKEN")
  - L30: return f"{email}/token", api_token

### `services\backend_api\services\system_health_service.py`
- Matched terms: ai, ml
  - L50: # Check AI data sources
  - L51: ai_status = self._check_ai_data_health()
  - L52: health_status['components']['ai_data'] = ai_status
  - L80: for component, details in health_status['components'].items():
  - L81: if 'errors' in details:
  - L82: health_status['errors'].extend(details['errors'])
  - L83: if 'warnings' in details:
  - L84: health_status['warnings'].extend(details['warnings'])

### `services\backend_api\services\llm_service.py`
- Matched terms: ai, score
  - L7: self.available = True
  - L13: return f"Simulated AI Response to: {prompt[:50]}..."
  - L18: "score": 85,

### `services\backend_api\services\live_gmail_service.py`
- Matched terms: ai, ml
  - L2: Live Gmail Service for IntelliCV Admin Portal
  - L5: Real-time Gmail integration service that provides live data instead of mock data.
  - L6: This service connects to the actual Gmail account and extracts CV documents.
  - L8: Author: IntelliCV AI System
  - L15: import email
  - L26: class LiveGmailService:
  - L27: """Live Gmail service for real-time email extraction"""
  - L30: """Initialize the live Gmail service"""

### `services\backend_api\services\enrichment\job_description_enricher.py`
- Matched terms: clustering, similarity
  - L3: - Enriches job descriptions with analytics (e.g., skill extraction, title linkage, requirements clustering)
  - L9: # Placeholder: implement enrichment logic (e.g., skill extraction, title similarity, requirements analysis)

### `services\backend_api\services\enrichment\education_enricher.py`
- Matched terms: clustering, ranking
  - L3: - Analyzes education history for advanced insights (e.g., degree prestige, typical graduation age, field clustering)
  - L9: # Placeholder: implement enrichment logic (e.g., degree ranking, field mapping)

### `services\backend_api\services\email_contact_parser.py`
- Matched terms: ai, clustering
  - L3: Email & Contact Parser Module (Expanded)
  - L11: EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
  - L22: emails = EMAIL_REGEX.findall(text)
  - L30: for i, email in enumerate(emails):
  - L36: "Email": email,
  - L40: if validate_email(email):
  - L44: def validate_email(email: str) -> bool:
  - L46: return bool(EMAIL_REGEX.fullmatch(email)) and len(email) <= 100

### `services\backend_api\services\compliance_data_service.py`
- Matched terms: ai, score
  - L22: self.ai_data_path = self.base_path / "ai_data_final" if (self.base_path / "ai_data_final").exists() else self.base_path / "ai_data"
  - L33: data_quality_score = self._analyze_data_quality()
  - L34: security_score = self._analyze_security_compliance()
  - L38: # Calculate overall compliance score
  - L39: compliance_score = (data_quality_score + security_score) / 2
  - L42: 'compliance_score': compliance_score,
  - L43: 'compliance_delta': self._calculate_trend(compliance_score),
  - L48: 'risk_level': 'Low' if compliance_score > 90 else 'Medium' if compliance_score > 75 else 'High',

### `services\backend_api\services\company_intelligence_auto_enrich.py`
- Matched terms: ai, intelligence
  - L2: Company Intelligence Auto-Enrichment Service
  - L11: from company_intelligence_parser import get_company_intelligence, db, DB_PATH
  - L12: from market_intelligence.extract import extract_companies
  - L19: # Example: Directory containing user-uploaded resumes (PDF/text)
  - L27: Uses pypdf for PDFs, python-docx for DOCX, plain read for TXT.
  - L50: logger.warning("No PDF library available")
  - L68: # Plain text files
  - L112: enriched_results[c] = get_market_intelligence(c)

### `services\backend_api\services\company_intelligence\main.py`
- Matched terms: ai, intelligence
  - L2: Main runner for Company Intelligence Parser (modular, robust, scalable)
  - L36: logger.info("[DONE] Company intelligence parsing complete.")
  - L38: if __name__ == "__main__":

### `services\backend_api\services\company_intelligence\config.py`
- Matched terms: ai, intelligence
  - L2: Configuration for Company Intelligence Parser
  - L11: AI_DATA_DIR = Path(os.getenv('AI_DATA_DIR', PROJECT_ROOT / 'ai_data'))
  - L12: COMPANY_DB = AI_DATA_DIR / 'companies' / 'company_intelligence_database.json'
  - L13: LOGOS_DIR = AI_DATA_DIR / 'companies' / 'logos'
  - L14: LOGS_DIR = AI_DATA_DIR / 'companies' / 'logs'

### `services\backend_api\services\company_intel_service.py`
- Matched terms: ai, intelligence
  - L13: from services.backend_api.services.company_intelligence.extract import extract_companies
  - L41: self.registry_path = self.paths.ai_data_final / "metadata" / "company_intel_registry.json"

### `services\backend_api\services\company_ai\nlp_extraction.py`
- Matched terms: ai, model
  - L2: AI/NLP Extraction Module: Extracts companies, roles, products, locations, and relationships using spaCy.
  - L7: # Load spaCy model (en_core_web_sm for demo; use en_core_web_trf for production)
  - L26: if __name__ == "__main__":

### `services\backend_api\services\company_ai\data_quality.py`
- Matched terms: ai, ml
  - L6: """Flag and correct data issues using AI."""
  - L7: # Implementation will use ML/heuristics

### `services\backend_api\services\chrome_web_scraper.py`
- Matched terms: ai, ml
  - L14: from selenium.webdriver.support.ui import WebDriverWait
  - L35: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  - L36: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  - L37: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  - L42: 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
  - L84: logger.error(f"Failed to setup Chrome driver: {e}")
  - L85: raise
  - L98: response.raise_for_status()

### `services\backend_api\services\blocker\service.py`
- Matched terms: model, score
  - L4: from services.backend_api.db.models import ApplicationBlocker, BlockerImprovementPlan
  - L25: ).order_by(ApplicationBlocker.criticality_score.desc()).all()

### `services\backend_api\services\automatic_data_ingestion_service.py`
- Matched terms: ai, intelligence
  - L3: Automatic Data Ingestion Service - Real-Time AI Enrichment Pipeline
  - L6: This service automatically enriches the IntelliCV AI system whenever:
  - L7: - A user registers (adds profile data to AI database)
  - L8: - A user uploads a resume (adds CV data to AI enrichment)
  - L9: - A user updates their profile (updates AI intelligence)
  - L15: 3. THIS SERVICE automatically copies to ai_data_final →
  - L16: 4. AI enrichment runs automatically →
  - L19: This ensures the AI system continuously learns from every user interaction.

### `services\backend_api\services\analytics\user_analytics.py`
- Matched terms: ai, orchestrator
  - L3: Generate tuning recommendations based on enriched keywords and analytics from the orchestrator.
  - L5: enrichment_output: Dict from Hybrid AI Harness
  - L11: high_value = {'cloud', 'leadership', 'innovation', 'sustainability', 'strategy', 'ai', 'python', 'data', 'analytics'}
  - L19: - Exposes hooks for UI and enrichment orchestrator

### `services\backend_api\services\ai\ai_learning_tracker.py`
- Matched terms: ai, score
  - L2: AI Learning Pattern Tracker
  - L3: Provides visibility into AI learning progress for admin dashboard
  - L13: class AILearningPatternTracker:
  - L15: Track and display AI learning patterns for admin visibility
  - L16: Shows concrete evidence of AI improvement over time
  - L20: self.db_path = Path(__file__).parent.parent / "admin_portal" / "db" / "ai_learning_history.db"
  - L52: failed INTEGER,
  - L60: # Confidence score history

### `services\backend_api\services\ai\ai_chat_service.py`
- Matched terms: ai, model
  - L2: ai_chat_service.py
  - L4: Unified AI Chat Service for Perplexity and Gemini APIs
  - L7: using external AI services (Perplexity for web search, Gemini for analysis).
  - L9: Priority order: Perplexity → Gemini → Unavailable
  - L25: class AIChatService:
  - L26: """Unified interface for Perplexity and Gemini AI chat services"""
  - L29: """Initialize AI chat service with API keys"""
  - L32: self.perplexity_base_url = "https://api.perplexity.ai/chat/completions"

### `services\backend_api\services\advanced_web_scraper.py`
- Matched terms: ai, ml
  - L14: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  - L15: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
  - L16: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  - L37: # --- Main scraping function ---
  - L47: # Blocked or rate-limited, try again
  - L61: # html = driver.page_source
  - L63: # return html
  - L69: return {"url": url, "error": "Failed to fetch page"}

### `services\backend_api\services\admin_contracts.py`
- Matched terms: intelligence, score
  - L12: # Web Company Intelligence contracts (admin backend must provide these keys)
  - L14: WEB_INTEL_COMPANY_RESULT_KEYS: Final[List[str]] = ["company_name", "confidence_score", "timestamp", "data_sources"]

### `services\backend_api\services\admin_api_client_ci_endpoints.py`
- Matched terms: ai, intelligence
  - L1: """services.admin_api_client – Competitive Intelligence endpoints (PATCH)
  - L14: Backend contract is strict: the page will raise if expected keys are missing.

### `services\backend_api\services\admin_api_client.py`
- Matched terms: ai, intelligence
  - L33: def _raise(self, r: requests.Response) -> None:
  - L40: raise RuntimeError(f"Admin API error {r.status_code} {r.request.method} {r.url}: {body}")
  - L44: self._raise(r)
  - L49: self._raise(r)
  - L86: # Web Company Intelligence endpoints

### `services\backend_api\routers\webhooks.py`
- Matched terms: ai, model
  - L7: POST /api/webhooks/v1/braintree   — Braintree notifications
  - L15: 4. Marked processed / failed
  - L27: # AI agent queue — enqueue zendesk jobs for LLM processing
  - L29: from services.backend_api.services.ai_queue_service import enqueue as ai_enqueue
  - L31: ai_enqueue = None  # type: ignore
  - L43: from services.backend_api.db import models
  - L45: # Braintree webhook parsing
  - L47: import braintree

### `services\backend_api\routers\user.py`
- Matched terms: ai, model
  - L10: from services.backend_api.db import models
  - L12: # Import pydantic models if we had them, using dicts/params for now to save time in migration
  - L20: email: str = payload.get("sub")
  - L21: if email is None:
  - L22: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
  - L24: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
  - L26: user = db.query(models.User).filter(models.User.email == email).first()
  - L28: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

### `services\backend_api\routers\touchpoints.py`
- Matched terms: ai, engine
  - L15: from services.ai_engine.data_loader import DataLoader
  - L80: In production this queries the gap-analysis engine.

### `services\backend_api\routers\support.py`
- Matched terms: ai, model
  - L7: from pydantic import BaseModel
  - L11: from services.backend_api.db import models
  - L27: # AI agent queue — enqueue jobs for LLM processing
  - L28: from services.backend_api.services.ai_queue_service import enqueue as ai_enqueue
  - L29: from services.backend_api.services.ai_queue_service import (
  - L30: queue_stats as ai_queue_stats,
  - L31: list_jobs as ai_list_jobs,
  - L32: read_job as ai_read_job,

### `services\backend_api\routers\sessions.py`
- Matched terms: ai, model
  - L19: from pydantic import BaseModel
  - L36: # ── Models ────────────────────────────────────────────────────
  - L37: class SessionEvent(BaseModel):
  - L44: class SessionSummary(BaseModel):
  - L55: for sub in ["sessions", "interactions", "profiles", "cv_uploads", "ai_matches", "session_logs"]:
  - L103: # Also append to session log (immutable audit trail)
  - L116: @router.get("/summary/{user_id}", response_model=SessionSummary)
  - L225: # AI Matches

### `services\backend_api\routers\runtime_contract.py`
- Matched terms: ai, model
  - L19: "model_unavailable": 503,

### `services\backend_api\routers\profile_v1.py`
- Matched terms: model, vector
  - L8: from pydantic import BaseModel, Field
  - L10: from services.backend_api.routers.career_compass import _vector_from_text
  - L18: class BuildProfileRequest(BaseModel):
  - L24: class BuildSignalsRequest(BaseModel):
  - L94: signals: Dict[str, float] = _vector_from_text(source_text)

### `services\backend_api\routers\profile_coach_v1.py`
- Matched terms: ai, model
  - L9: from pydantic import BaseModel, Field
  - L19: class ProfileCoachStartRequest(BaseModel):
  - L25: class ProfileCoachRespondRequest(BaseModel):
  - L31: class ProfileCoachFinishRequest(BaseModel):
  - L36: class _StoredSession(BaseModel):
  - L141: if coaching._contains_stop_phrase(answer):

### `services\backend_api\routers\payment.py`
- Matched terms: ai, model
  - L6: - Payment processing (Braintree integration — sandbox + production)
  - L17: Gateway: Braintree (sandbox → production switchable via BRAINTREE_ENVIRONMENT)
  - L21: Updated: February 9, 2026 — Braintree integration
  - L25: from pydantic import BaseModel, Field
  - L35: from services.backend_api.db import models
  - L37: # Braintree service (lazy — only fails at call time if not configured)
  - L39: from services.backend_api.services import braintree_service
  - L40: BRAINTREE_AVAILABLE = True

### `services\backend_api\routers\mentorship.py`
- Matched terms: ai, model
  - L14: from pydantic import BaseModel, Field
  - L23: from services.backend_api.db import models
  - L32: # PYDANTIC MODELS (Request/Response)
  - L35: class CreateLinkRequest(BaseModel):
  - L40: class CreateNoteRequest(BaseModel):
  - L49: class UpdateNoteRequest(BaseModel):
  - L54: class CreateDocumentRequest(BaseModel):
  - L61: class SignDocumentRequest(BaseModel):

### `services\backend_api\routers\mentor.py`
- Matched terms: ai, model
  - L7: - Availability settings
  - L15: from pydantic import BaseModel, Field
  - L22: from services.backend_api.db import models
  - L30: # PYDANTIC MODELS
  - L33: class MentorProfileOut(BaseModel):
  - L41: availability_status: str = "available"
  - L46: class ServicePackageCreate(BaseModel):
  - L56: class ServicePackageOut(BaseModel):

### `services\backend_api\routers\logs.py`
- Matched terms: ai, model
  - L6: from pydantic import BaseModel
  - L11: class LogTailResponse(BaseModel):
  - L18: @router.get("/tail", response_model=LogTailResponse, dependencies=[Depends(require_admin)])
  - L19: def tail_log(
  - L29: return LogTailResponse(file=str(fp), lines=[], matched_errors=[])
  - L37: return LogTailResponse(

### `services\backend_api\routers\gdpr.py`
- Matched terms: ai, model
  - L25: from services.backend_api.db import models
  - L37: email: str = payload.get("sub")
  - L38: if email is None:
  - L39: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
  - L41: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
  - L42: user = db.query(models.User).filter(models.User.email == email).first()
  - L44: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
  - L49: resource_id: str = None, detail: str = None, ip: str = None):

### `services\backend_api\routers\data_index.py`
- Matched terms: ai, ml
  - L5: API endpoints for the AI data indexing system.
  - L13: from services.backend_api.services.ai_data_index_service import (
  - L14: get_ai_data_index_service,
  - L15: AIDataIndexSummary,
  - L29: service = get_ai_data_index_service()
  - L32: ai_summary = state.ai_data_summary
  - L38: "ai_data": {
  - L39: "indexed": ai_summary is not None,

### `services\backend_api\routers\credits.py`
- Matched terms: ai, model
  - L6: Replaces the dual token/AI-call system with single credit currency.
  - L13: from pydantic import BaseModel, Field
  - L21: from services.backend_api.db import models
  - L33: CREDIT_SYSTEM_AVAILABLE = True
  - L35: CREDIT_SYSTEM_AVAILABLE = False
  - L44: # PYDANTIC MODELS
  - L47: class PlanInfo(BaseModel):
  - L58: class PlansResponse(BaseModel):

### `services\backend_api\routers\auth.py`
- Matched terms: ai, model
  - L15: from services.backend_api.db import models
  - L23: GOOGLE_OAUTH_DOMAIN = os.getenv("GOOGLE_OAUTH_DOMAIN", "https://www.careertrojan.com").strip().rstrip("/")
  - L37: "scope": "openid email profile",
  - L83: return f"{GOOGLE_OAUTH_DOMAIN}/login"
  - L86: def _ensure_user_from_google(db: Session, email: str, full_name: str | None = None) -> models.User:
  - L87: user = db.query(models.User).filter(models.User.email == email).first()
  - L97: user = models.User(email=email, hashed_password=hashed_password, full_name=full_name, is_active=True)
  - L108: detail="Could not validate credentials",

### `services\backend_api\routers\anti_gaming.py`
- Matched terms: model, score
  - L8: from pydantic import BaseModel, Field
  - L20: class GateIn(BaseModel):
  - L28: class GateOut(BaseModel):
  - L30: risk_score: int
  - L37: @router.post("/check", response_model=GateOut)
  - L63: "risk_score": decision.risk_score,
  - L73: risk_score=decision.risk_score,

### `services\backend_api\models\schemas.py`
- Matched terms: ai, model
  - L1: from pydantic import BaseModel, EmailStr
  - L6: class Token(BaseModel):
  - L10: class TokenData(BaseModel):
  - L11: email: Optional[str] = None
  - L14: class UserBase(BaseModel):
  - L15: email: EmailStr
  - L31: class UserProfileBase(BaseModel):
  - L50: class ResumeBase(BaseModel):

### `services\ai_engine\llm_service.py`
- Matched terms: ai, model
  - L8: OPENAI = "openai"
  - L22: model_name: str
  - L35: class OpenAIService(BaseLLMService):
  - L37: self.api_key = api_key or os.getenv("OPENAI_API_KEY")
  - L39: print("⚠️ OpenAIService initialized without API Key. Calls will fail.")
  - L42: from openai import OpenAI
  - L43: self.client = OpenAI(api_key=self.api_key)
  - L45: print("❌ 'openai' package not installed. Please run: pip install openai")

### `services\ai_engine\ingest_ai_data.py`
- Matched terms: ai, engine
  - L2: Unified Data Ingestion Runner for CareerTrojan AI Engine.
  - L3: Bridges L: Drive Data -> AI Runtime.
  - L17: from config import AI_DATA_DIR, RAW_DATA_DIR, log_root
  - L24: logging.FileHandler(log_root / "ai_ingestion.log"),
  - L28: logger = logging.getLogger("AI_Ingest")
  - L34: details: str
  - L36: class DataIngestionEngine:
  - L38: self.data_dir = AI_DATA_DIR

### `scripts\validate_route_governance.py`
- Matched terms: ai, governance
  - L21: candidates = sorted(REPORTS_DIR.glob("ROUTE_GOVERNANCE_REPORT_*.json"))
  - L61: parser = argparse.ArgumentParser(description="Validate route governance report against gate thresholds")
  - L66: help="Optional path to ROUTE_GOVERNANCE_REPORT_*.json; latest report is used when omitted.",
  - L75: def main() -> int:
  - L80: print("ROUTE_GOVERNANCE_GATE_FAIL")
  - L81: print("- no governance report found")
  - L88: print("ROUTE_GOVERNANCE_GATE_FAIL")
  - L94: print("ROUTE_GOVERNANCE_GATE_OK")

### `scripts\validate_governance_artifacts.py`
- Matched terms: ai, governance
  - L15: ROOT / "data" / "governance" / "README.md",
  - L16: ROOT / "data" / "governance" / "outcome_labels.jsonl",
  - L42: jsonl_path = ROOT / "data" / "governance" / "outcome_labels.jsonl"
  - L67: def main() -> int:
  - L73: print("GOVERNANCE_ARTIFACTS_INVALID")
  - L78: print("GOVERNANCE_ARTIFACTS_OK")
  - L82: if __name__ == "__main__":
  - L83: raise SystemExit(main())

### `scripts\smoke_test.py`
- Matched terms: ai, ml
  - L15: AI_DATA_ROOT_WIN = os.environ.get("CAREERTROJAN_DATA_ROOT", r"L:\Codec-Antigravity Data set")
  - L16: AI_DATA_ROOT_LINUX = "/mnt/careertrojan"  # Canonical Linux mount
  - L21: def print_fail(msg):
  - L22: print(f"[\033[91mFAIL\033[0m] {msg}")
  - L38: print_fail(f"Runtime Root NOT found: {RUNTIME_ROOT}")
  - L41: target_data_root = AI_DATA_ROOT_WIN if is_windows else AI_DATA_ROOT_LINUX
  - L45: print_pass(f"AI Data Root found: {target_data_root}")
  - L47: print_warn(f"AI Data Root not found at {target_data_root}. (Expected if running outside of dedicated runtime VM)")

### `scripts\run_super_experience_harness.py`
- Matched terms: ai, model
  - L19: from services.backend_api.main import app  # noqa: E402
  - L21: from services.backend_api.db import models  # noqa: E402
  - L29: detail: str = ""
  - L45: ai_learning_signals: Dict[str, Any]
  - L55: self.client = TestClient(app, raise_server_exceptions=False)
  - L58: def _result(self, name: str, response=None, *, ok: bool = True, detail: str = "") -> StepResult:
  - L69: return StepResult(name=name, ok=ok, status_code=status_code, detail=detail, payload_preview=preview)
  - L84: "stdout_tail": "\n".join(proc.stdout.splitlines()[-20:]),

### `scripts\run_parser_until_complete.py`
- Matched terms: ai, engine
  - L13: PARSER_MODULE_DIR = PROJECT_ROOT / "services" / "workers" / "ai" / "ai-workers" / "parser"
  - L17: from automated_parser_engine import AutomatedParserEngine
  - L26: def main() -> None:
  - L32: output_root = paths.ai_data_final / "parsed_from_automated"
  - L42: engine = AutomatedParserEngine(
  - L46: results = engine.run(max_files=batch_size)
  - L83: if __name__ == "__main__":
  - L84: main()

### `scripts\route_governance_report.py`
- Matched terms: ai, governance
  - L21: from services.backend_api.main import app
  - L261: lines.append("# Route Governance Report")
  - L324: def main() -> None:
  - L360: json_path = REPORTS_DIR / f"ROUTE_GOVERNANCE_REPORT_{stamp}.json"
  - L361: md_path = REPORTS_DIR / f"ROUTE_GOVERNANCE_REPORT_{stamp}.md"
  - L380: if __name__ == "__main__":
  - L381: main()

### `scripts\coaching_endpoint_uptime_check.py`
- Matched terms: ai, score
  - L28: print(f"[FAIL] {method} {url} -> {status} (expected {sorted(expected_statuses)})")
  - L35: print(f"[FAIL] {method} {url} -> {status} (expected {sorted(expected_statuses)})")
  - L38: print(f"[FAIL] {method} {url} -> {exc}")
  - L42: def main() -> int:
  - L60: "fit": {"score": 0.73},
  - L68: "question": "Tell me about a campaign you improved.",
  - L70: "resume": {"skills": ["SEO", "campaign analytics"]},
  - L98: if __name__ == "__main__":

### `scripts\aggregate_training_corpus.py`
- Matched terms: ai, training
  - L8: def extract_email(text: str) -> str:
  - L25: personal_details = profile.get("Personal Details") or ""
  - L36: email = profile.get("email") or extract_email(" ".join([personal_details, qualifications, career_summary]))
  - L37: phone = profile.get("phone") or extract_phone(" ".join([personal_details, qualifications, career_summary]))
  - L43: "email": email,
  - L55: email = resume.get("email") or extract_email(raw_text)
  - L62: "email": email,
  - L78: def consolidate(ai_data_final: Path, output: Path, manifest: Path, limit: int = None) -> None:

### `tools\react_api_scan.py`
- Matched terms: ai
  - L19: def main():
  - L64: if __name__ == "__main__":
  - L65: main()

### `tools\join_endpoint_graph.py`
- Matched terms: ai
  - L27: def main():
  - L102: if __name__ == "__main__":
  - L103: main()

### `tools\fastapi_introspect_routes.py`
- Matched terms: ai
  - L6: python tools/fastapi_introspect_routes.py --app-import "app.main:app" --out "./exports"
  - L21: def main():
  - L23: ap.add_argument("--app-import", required=True, help="e.g. app.main:app")
  - L64: if __name__ == "__main__":
  - L65: main()

### `tools\_test_import.py`
- Matched terms: ai
  - L3: from services.backend_api.main import app

### `tests\unit\test_support_stub.py`
- Matched terms: ai
  - L8: from services.backend_api.main import app
  - L9: return TestClient(app, raise_server_exceptions=False)
  - L22: response = client.get('/api/support/v1/widget-config?portal=admin&user_id=tester&user_email=test@example.com')
  - L55: providers = {item['provider'] for item in payload['available']}

### `tests\unit\test_security.py`
- Matched terms: ai
  - L21: plain = "SuperSecret123!"
  - L22: hashed = get_password_hash(plain)
  - L23: assert hashed != plain
  - L24: assert verify_password(plain, hashed)
  - L26: def test_wrong_password_fails(self):
  - L57: with pytest.raises(jose_jwt.ExpiredSignatureError):
  - L60: def test_invalid_secret_fails(self):
  - L65: with pytest.raises(jose_jwt.JWTError):

### `tests\unit\test_data_index_service.py`
- Matched terms: ai
  - L2: Unit tests for the AI Data Index Service
  - L12: from services.backend_api.services.ai_data_index_service import (
  - L13: AIDataIndexService,
  - L14: AIDataIndexSummary,
  - L148: class TestAIDataIndexService:
  - L149: """Test the main index service."""
  - L154: ai_data_final = tmp_path / "ai_data_final"
  - L157: ai_data_final.mkdir(parents=True)

### `tests\unit\test_company_intel_service.py`
- Matched terms: ai
  - L9: ai_data = data_root / "ai_data_final"
  - L10: ai_data.mkdir(parents=True)
  - L16: monkeypatch.setenv("CAREERTROJAN_AI_DATA", str(ai_data))
  - L22: "ai_data": ai_data,

### `tests\unit\test_braintree.py`
- Matched terms: ai
  - L2: Tests for Braintree payment integration — CareerTrojan
  - L6: - Braintree service configuration checks
  - L12: - Graceful degradation when Braintree not configured
  - L26: from services.backend_api.main import app
  - L31: return TestClient(app, raise_server_exceptions=False)
  - L47: # UNIT: braintree_service configuration
  - L50: class TestBraintreeServiceConfig:
  - L51: """Test the braintree_service module configuration logic."""

### `tests\unit\test_app_bootstrap.py`
- Matched terms: ai
  - L24: from services.backend_api.main import app
  - L28: from services.backend_api.main import app
  - L33: from services.backend_api.main import app
  - L45: from services.backend_api.main import app
  - L77: # ── Core domain endpoints ────────────────────────────────────────
  - L90: from services.backend_api.main import app
  - L106: """Every /api/... route should contain /v1/ (legacy compat routes excluded)."""
  - L107: from services.backend_api.main import app

### `tests\unit\test_ai_queue.py`
- Matched terms: ai
  - L2: Tests for AI Agent Queue Service — CareerTrojan
  - L6: - Job enqueue / claim / complete / fail lifecycle
  - L9: - Edge cases (empty queue, race on claim)
  - L18: from services.backend_api.services.ai_queue_service import (
  - L19: claim_next,
  - L23: fail_job,
  - L81: # ── Claim ────────────────────────────────────────────────────
  - L83: class TestClaim:

### `tests\integration\test_portal_bridge.py`
- Matched terms: ai
  - L9: Service location: services/shared/portal-bridge/main.py
  - L21: _bridge_main = os.path.join(
  - L23: "services", "shared", "portal-bridge", "main.py",
  - L25: _bridge_main = os.path.normpath(_bridge_main)
  - L26: _spec = importlib.util.spec_from_file_location("portal_bridge_main", _bridge_main)
  - L85: assert "detail" in data
  - L86: assert data["detail"] == "Invalid credentials"
  - L190: def test_openapi_available(self):

### `tests\integration\test_http_endpoints.py`
- Matched terms: ai
  - L17: from services.backend_api.main import app
  - L19: client = TestClient(app, raise_server_exceptions=False)

### `tests\integration\test_auth_provider_modes.py`
- Matched terms: ai
  - L17: from services.backend_api.main import app
  - L20: client = TestClient(app, raise_server_exceptions=False)
  - L51: def _raise(_token):
  - L52: raise security.TokenValidationError("bad token")
  - L54: monkeypatch.setattr(security, "decode_access_token", _raise)

### `tests\integration\test_admin_email_integration_endpoints.py`
- Matched terms: ai
  - L4: from services.backend_api.main import app
  - L29: admin_router._email_dispatch_log.clear()
  - L34: admin_router._email_dispatch_log.clear()
  - L78: "/api/admin/v1/email/send_test",
  - L97: "/api/admin/v1/email/send_bulk",
  - L124: def test_email_logs_and_analytics(client, admin_headers):
  - L131: "/api/admin/v1/email/send_test",
  - L136: "/api/admin/v1/email/send_bulk",

## 5. What to inspect manually next

Focus first on these categories:

1. Route handlers whose call chains include `service`, `router`, `engine`, `predict`, `score`, `inference`, or `orchestrator`
2. Files with names such as `unified_ai_engine.py`, `orchestrator.py`, `router.py`, `feature_registry.py`, `context_assembler.py`
3. Frontend pages that call analysis, scoring, insight, structural, radar, or chart endpoints
4. Any places where runtime routes bypass the advanced engine and fall back to simple heuristics

## 6. Limits of this static pass

- This script is static analysis, not runtime tracing
- Dynamic imports, dependency injection, and factory-created services may not be fully resolved
- It identifies likely wiring and hotspots, then shortens the manual review path
