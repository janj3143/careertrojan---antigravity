# Full Endpoint Audit — 2026-02-27

Generated: `2026-02-27T15:35:40.727504+00:00`

## Summary

- Total probed: **272**
- error: **108**
- exists_requires_auth_or_payload: **49**
- missing_or_wrong_method: **4**
- ok: **109**
- skipped_heavy: **2**

## Endpoints With Problems

| Method | Path | Status | Classification |
|---|---|---:|---|
| POST | /api/auth/v1/2fa/generate | 599 | error |
| GET | /api/user/v1/me | 599 | error |
| GET | /api/user/v1/profile | 599 | error |
| PUT | /api/user/v1/profile | 599 | error |
| GET | /api/user/v1/stats | 599 | error |
| GET | /api/user/v1/activity | 599 | error |
| GET | /api/user/v1/sessions/summary | 599 | error |
| GET | /api/user/v1/resume/latest | 599 | error |
| GET | /api/user/v1/matches/summary | 599 | error |
| GET | /api/admin/v1/users | 599 | error |
| GET | /api/admin/v1/compliance/summary | 599 | error |
| POST | /api/admin/v1/integrations/{provider}/disconnect | 404 | missing_or_wrong_method |
| GET | /api/admin/v1/email/status | 501 | error |
| GET | /api/admin/v1/system/activity | 599 | error |
| GET | /api/admin/v1/dashboard/snapshot | 599 | error |
| GET | /api/admin/v1/tokens/users/{user_id}/ledger | 501 | error |
| GET | /api/admin/v1/user_subscriptions | 501 | error |
| PUT | /api/admin/v1/users/{user_id}/plan | 501 | error |
| PUT | /api/admin/v1/users/{user_id}/disable | 501 | error |
| GET | /api/admin/v1/compliance/audit/events | 599 | error |
| POST | /api/admin/v1/email/sync | 501 | error |
| GET | /api/admin/v1/email/jobs | 501 | error |
| POST | /api/admin/v1/parsers/run | 501 | error |
| GET | /api/admin/v1/parsers/jobs | 501 | error |
| GET | /api/admin/v1/batch/status | 501 | error |
| POST | /api/admin/v1/batch/run | 501 | error |
| GET | /api/admin/v1/batch/jobs | 501 | error |
| GET | /api/admin/v1/ai/enrichment/status | 599 | error |
| GET | /api/admin/v1/ai/content/status | 501 | error |
| POST | /api/admin/v1/ai/content/run | 501 | error |
| GET | /api/admin/v1/ai/content/jobs | 501 | error |
| GET | /api/mentorship/v1/links/mentor/{mentor_id} | 500 | error |
| GET | /api/mentorship/v1/links/user/{user_id} | 500 | error |
| GET | /api/mentorship/v1/notes/{link_id} | 500 | error |
| GET | /api/mentorship/v1/invoices/mentor/{mentor_id} | 500 | error |
| GET | /api/mentorship/v1/applications/pending | 500 | error |
| GET | /api/mentorship/v1/summary | 599 | error |
| POST | /api/coaching/v1/bundle | 599 | error |
| GET | /api/coaching/v1/history | 599 | error |
| POST | /api/coaching/v1/learning/feedback | 599 | error |
| GET | /api/coaching/v1/learning/profile | 599 | error |
| POST | /api/resume/v1/upload | 599 | error |
| GET | /api/resume/v1/{resume_id} | 599 | error |
| GET | /api/resume/v1 | 599 | error |
| POST | /api/resume/v1/parse | 599 | error |
| POST | /api/resume/v1/enrich | 599 | error |
| GET | /api/credits/v1/plans | 599 | error |
| GET | /api/credits/v1/balance | 599 | error |
| GET | /api/credits/v1/can-perform/{action_id} | 599 | error |
| POST | /api/credits/v1/consume | 599 | error |
| GET | /api/credits/v1/usage | 599 | error |
| POST | /api/credits/v1/upgrade/{plan_tier} | 599 | error |
| GET | /api/ai-data/v1/parsed_resumes/{doc_id} | 404 | missing_or_wrong_method |
| GET | /api/ai-data/v1/companies | 404 | missing_or_wrong_method |
| SKIP | /api/ai-data/v1/metadata | 0 | skipped_heavy |
| SKIP | /api/ai-data/v1/normalized | 0 | skipped_heavy |
| GET | /api/ai-data/v1/emails/providers/{provider} | 599 | error |
| GET | /api/ai-data/v1/emails/providers/{provider}/guarded-payload | 400 | error |
| POST | /api/ai-data/v1/emails/tracking | 400 | error |
| GET | /api/jobs/v1/index | 503 | error |
| GET | /api/taxonomy/v1/industries | 599 | error |
| GET | /api/taxonomy/v1/industries/{high_level}/subindustries | 599 | error |
| GET | /api/taxonomy/v1/summary | 599 | error |
| POST | /api/data-index/v1/index/ai-data | 599 | error |
| POST | /api/data-index/v1/index/parser | 599 | error |
| GET | /api/payment/v1/plans | 599 | error |
| GET | /api/payment/v1/plans/{plan_id} | 404 | missing_or_wrong_method |
| POST | /api/payment/v1/process | 599 | error |
| GET | /api/payment/v1/history | 599 | error |
| GET | /api/payment/v1/subscription | 599 | error |
| POST | /api/payment/v1/cancel | 599 | error |
| GET | /api/payment/v1/client-token | 599 | error |
| POST | /api/payment/v1/methods | 599 | error |
| GET | /api/payment/v1/methods | 599 | error |
| DELETE | /api/payment/v1/methods/{token} | 503 | error |
| GET | /api/payment/v1/transactions/{transaction_id} | 503 | error |
| POST | /api/payment/v1/refund/{transaction_id} | 503 | error |
| POST | /api/rewards/v1/rewards/award/{action_key} | 599 | error |
| GET | /api/rewards/v1/rewards | 599 | error |
| GET | /api/rewards/v1/rewards/available | 599 | error |
| POST | /api/rewards/v1/suggestions | 599 | error |
| GET | /api/rewards/v1/suggestions | 599 | error |
| POST | /api/rewards/v1/rewards/redeem | 599 | error |
| GET | /api/rewards/v1/referral | 599 | error |
| GET | /api/rewards/v1/leaderboard | 599 | error |
| GET | /api/rewards/v1/ownership-stats | 599 | error |
| GET | /api/mentor/v1/profile-by-user/{user_id} | 599 | error |
| GET | /api/mentor/v1/{mentor_profile_id}/profile | 599 | error |
| GET | /api/mentor/v1/list | 599 | error |
| GET | /api/mentor/v1/{mentor_profile_id}/packages | 501 | error |
| GET | /api/mentor/v1/{mentor_profile_id}/packages/{package_id} | 501 | error |
| PUT | /api/mentor/v1/{mentor_profile_id}/packages/{package_id} | 501 | error |
| DELETE | /api/mentor/v1/{mentor_profile_id}/packages/{package_id} | 501 | error |
| GET | /api/mentor/v1/{mentor_profile_id}/dashboard-stats | 501 | error |
| GET | /api/mapping/v1/registry | 599 | error |
| GET | /api/mapping/v1/endpoints | 599 | error |
| GET | /api/mapping/v1/graph | 599 | error |
| GET | /api/gdpr/v1/consent | 599 | error |
| POST | /api/gdpr/v1/consent | 599 | error |
| GET | /api/gdpr/v1/export | 599 | error |
| DELETE | /api/gdpr/v1/delete-account | 599 | error |
| GET | /api/gdpr/v1/audit-log | 599 | error |
| POST | /api/admin/v1/parsing/parse | 599 | error |
| GET | /api/admin/v1/parsing/parse/{parse_id} | 599 | error |
| GET | /api/admin/v1/parsing/parse | 599 | error |
| PUT | /api/admin/v1/tokens/config | 400 | error |
| PUT | /admin/tokens/plans | 400 | error |
| POST | /admin/tokens/plans | 400 | error |
| PUT | /admin/tokens/costs/{feature} | 400 | error |
| POST | /admin/tokens/costs/update | 400 | error |
| POST | /admin/tokens/ledger/emit | 400 | error |
| POST | /api/admin/v1/anti-gaming/check | 429 | error |
| GET | /api/admin/v1/logs/tail | 429 | error |
| GET | /api/telemetry/v1/status | 429 | error |

## Notes

- `exists_requires_auth_or_payload` means the route exists but needs proper auth and/or domain-specific payload.
- `missing_or_wrong_method` is the main breakage signal for route availability mismatches.

JSON output: `J:/Codec - runtime version/Antigravity/careertrojan/reports/FULL_ENDPOINT_AUDIT_2026-02-27.json`