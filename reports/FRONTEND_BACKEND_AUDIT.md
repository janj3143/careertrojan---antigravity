# CareerTrojan — Frontend Routes & Backend Endpoints Audit

**Generated:** 2026-02-15  
**Scope:** `apps/user`, `apps/admin`, `apps/mentor` (React/Vite) + `services/backend_api` (FastAPI)

---

## 1. FRONTEND ROUTES

### 1.1 User Portal (`apps/user`) — 20 routes

| # | Route | Component | Auth | Notes |
|---|-------|-----------|------|-------|
| 1 | `/` | Home | Public | |
| 2 | `/login` | LoginPage | Public | |
| 3 | `/register` | RegisterPage | Public | |
| 4 | `/privacy` | PrivacyPolicy | Public | |
| 5 | `/quick` | MobileQuickDash | Private | Mobile-only |
| 6 | `/jobs/swipe` | JobSwipe | Private | Mobile-only |
| 7 | `/mobile/cv` | MobileCVUpload | Private | Mobile-only |
| 8 | `/dashboard` | Dashboard | Private | |
| 9 | `/payment` | PaymentPage | Private | |
| 10 | `/verify` | VerificationPage | Private | |
| 11 | `/profile` | ProfilePage | Private | |
| 12 | `/resume` | ResumeUpload | Private | |
| 13 | `/umarketu` | UMarketU | Private | |
| 14 | `/coaching` | CoachingHub | Private | |
| 15 | `/mentorship` | MentorshipMarketplace | Private | |
| 16 | `/mentor/apply` | MentorApplication | Private | |
| 17 | `/dual-career` | DualCareer | Private | |
| 18 | `/rewards` | RewardsPage | Private | |
| 19 | `/visuals` | VisualisationsHub | Private | |
| 20 | `/consolidation` | ConsolidationPage | Private | |

---

### 1.2 Admin Portal (`apps/admin`) — 73 routes

#### Main Pages (34 routes)

| # | Route | Component | Auth |
|---|-------|-----------|------|
| 1 | `/admin/login` | AdminLogin | Public |
| 2 | `/admin` | AdminHome | Private |
| 3 | `/admin/status` | ServiceStatus | Private |
| 4 | `/admin/analytics` | Analytics | Private |
| 5 | `/admin/users` | UserManagement | Private |
| 6 | `/admin/compliance` | ComplianceAudit | Private |
| 7 | `/admin/email` | EmailIntegration | Private |
| 8 | `/admin/parser` | DataParser | Private |
| 9 | `/admin/batch` | BatchProcessing | Private |
| 10 | `/admin/ai-enrich` | AIEnrichment | Private |
| 11 | `/admin/ai-content` | AIContentGenerator | Private |
| 12 | `/admin/market-intel` | MarketIntelligence | Private |
| 13 | `/admin/tokens` | TokenManagement | Private |
| 14 | `/admin/competitive` | CompetitiveIntel | Private |
| 15 | `/admin/web-intel` | WebCompanyIntel | Private |
| 16 | `/admin/api-integration` | APIIntegration | Private |
| 17 | `/admin/contact` | ContactComm | Private |
| 18 | `/admin/settings` | AdvancedSettings | Private |
| 19 | `/admin/logs` | LoggingErrors | Private |
| 20 | `/admin/job-title-ai` | JobTitleAI | Private |
| 21 | `/admin/job-cloud` | JobTitleCloud | Private |
| 22 | `/admin/mentors` | MentorManagement | Private |
| 23 | `/admin/model-training` | ModelTraining | Private |
| 24 | `/admin/requirements` | RequirementsMgmt | Private |
| 25 | `/admin/tokens-alt` | TokenManagementAlt | Private |
| 26 | `/admin/intel-hub` | IntelligenceHub | Private |
| 27 | `/admin/career-patterns` | CareerPatterns | Private |
| 28 | `/admin/exa-web` | ExaWebIntel | Private |
| 29 | `/admin/unified-analytics` | UnifiedAnalytics | Private |
| 30 | `/admin/mentor-review` | MentorAppReview | Private |
| 31 | `/admin/connectivity` | ConnectivityAudit | Private |
| 32 | `/admin/api-health` | APIHealthDashboard | Private |
| 33 | `/admin/blocker-test` | BlockerDetectionTest | Private |
| 34 | `/admin/portal-entry` | AdminPortalEntry | Private |

#### Tools Pages (29 routes)

| # | Route | Component |
|---|-------|-----------|
| 35 | `/admin/tools/data-health` | DataRootsHealth |
| 36 | `/admin/tools/datasets` | DatasetsBrowser |
| 37 | `/admin/tools/resume-viewer` | ResumeJSONViewer |
| 38 | `/admin/tools/parser-runs` | ParserRuns |
| 39 | `/admin/tools/enrichment` | EnrichmentRuns |
| 40 | `/admin/tools/keywords` | KeywordOntology |
| 41 | `/admin/tools/phrases` | PhraseManager |
| 42 | `/admin/tools/email-capture` | EmailCapture |
| 43 | `/admin/tools/email-analytics` | EmailAnalytics |
| 44 | `/admin/tools/job-index` | JobIndex |
| 45 | `/admin/tools/taxonomy` | RoleTaxonomy |
| 46 | `/admin/tools/scoring` | ScoringAnalytics |
| 47 | `/admin/tools/fairness` | BiasAndFairness |
| 48 | `/admin/tools/models` | ModelRegistry |
| 49 | `/admin/tools/prompts` | PromptRegistry |
| 50 | `/admin/tools/evaluation` | EvaluationHarness |
| 51 | `/admin/tools/queue` | QueueMonitor |
| 52 | `/admin/tools/blob` | BlobStorage |
| 53 | `/admin/tools/user-audit` | UserAudit |
| 54 | `/admin/tools/admin-audit` | AdminAudit |
| 55 | `/admin/tools/notifications` | Notifications |
| 56 | `/admin/tools/config` | SystemConfig |
| 57 | `/admin/tools/logs-viewer` | LogsViewer |
| 58 | `/admin/tools/diagnostics` | Diagnostics |
| 59 | `/admin/tools/exports` | Exports |
| 60 | `/admin/tools/backup` | BackupRestore |
| 61 | `/admin/tools/route-map` | RouteMap |
| 62 | `/admin/tools/api-explorer` | APIExplorer |
| 63 | `/admin/tools/about` | About |

#### Operations Pages (10 routes)

| # | Route | Component |
|---|-------|-----------|
| 64 | `/admin/ops/admin-audit` | OpsAdminAudit |
| 65 | `/admin/ops/notifications` | OpsNotifications |
| 66 | `/admin/ops/config` | OpsSystemConfig |
| 67 | `/admin/ops/logs` | OpsLogsViewer |
| 68 | `/admin/ops/diagnostics` | OpsDiagnostics |
| 69 | `/admin/ops/exports` | OpsExports |
| 70 | `/admin/ops/backup` | OpsBackupRestore |
| 71 | `/admin/ops/route-map` | OpsRouteMap |
| 72 | `/admin/ops/api-explorer` | OpsAPIExplorer |
| 73 | `/admin/ops/about` | OpsAbout |

---

### 1.3 Mentor Portal (`apps/mentor`) — 13 routes

| # | Route | Component | Auth |
|---|-------|-----------|------|
| 1 | `/mentor/login` | MentorLogin | Public |
| 2 | `/mentor` | Dashboard | Private |
| 3 | `/mentor/dashboard` | MentorDashboard | Private |
| 4 | `/mentor/financials` | FinancialDashboard | Private |
| 5 | `/mentor/agreements` | MenteeAgreements | Private |
| 6 | `/mentor/communication` | CommunicationCenter | Private |
| 7 | `/mentor/guardian-feedback` | GuardianFeedback | Private |
| 8 | `/mentor/mentee-progress` | MenteeProgress | Private |
| 9 | `/mentor/ai-assistant` | AIAssistant | Private |
| 10 | `/mentor/my-agreements` | MyAgreements | Private |
| 11 | `/mentor/packages` | ServicePackages | Private |
| 12 | `/mentor/services` | ServicesAgreement | Private |
| 13 | `/mentor/calendar` | SessionsCalendar | Private |

---

## 2. BACKEND API ENDPOINTS

### 2.1 Auth (`/api/auth/v1`) — 4 endpoints

| Method | Path | Status |
|--------|------|--------|
| POST | `/api/auth/v1/register` | ✅ live |
| POST | `/api/auth/v1/login` | ✅ live |
| POST | `/api/auth/v1/2fa/generate` | ✅ live |
| POST | `/api/auth/v1/2fa/verify` | ✅ live |

### 2.2 User (`/api/user/v1`) — 3 endpoints

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/user/v1/me` | ✅ live |
| GET | `/api/user/v1/profile` | ✅ live |
| PUT | `/api/user/v1/profile` | ✅ live |

### 2.3 Admin (`/api/admin/v1`) — 29 endpoints

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/admin/v1/users` | ✅ live |
| GET | `/api/admin/v1/users/{user_id}` | ✅ live |
| GET | `/api/admin/v1/system/health` | ✅ live |
| GET | `/api/admin/v1/system/activity` | ✅ live |
| GET | `/api/admin/v1/dashboard/snapshot` | ✅ live |
| GET | `/api/admin/v1/compliance/summary` | ✅ live |
| GET | `/api/admin/v1/compliance/audit/events` | ✅ live |
| GET | `/api/admin/v1/email/status` | ⚠️ 501 stub |
| POST | `/api/admin/v1/email/sync` | ⚠️ 501 stub |
| GET | `/api/admin/v1/email/jobs` | ⚠️ 501 stub |
| GET | `/api/admin/v1/parsers/status` | ✅ mock |
| POST | `/api/admin/v1/parsers/run` | ⚠️ 501 stub |
| GET | `/api/admin/v1/parsers/jobs` | ⚠️ 501 stub |
| GET | `/api/admin/v1/batch/status` | ⚠️ 501 stub |
| POST | `/api/admin/v1/batch/run` | ⚠️ 501 stub |
| GET | `/api/admin/v1/batch/jobs` | ⚠️ 501 stub |
| GET | `/api/admin/v1/ai/enrichment/status` | ✅ live |
| POST | `/api/admin/v1/ai/enrichment/run` | ✅ placeholder |
| GET | `/api/admin/v1/ai/enrichment/jobs` | ✅ live |
| GET | `/api/admin/v1/ai/content/status` | ⚠️ 501 stub |
| POST | `/api/admin/v1/ai/content/run` | ⚠️ 501 stub |
| GET | `/api/admin/v1/ai/content/jobs` | ⚠️ 501 stub |
| GET | `/api/admin/v1/ai/monitoring` | ✅ live |
| GET | `/api/admin/v1/user_subscriptions` | ✅ live |
| GET | `/api/admin/v1/tokens/users/{user_id}/ledger` | ⚠️ 501 stub |
| GET | `/api/admin/v1/users/metrics` | ⚠️ 501 stub |
| GET | `/api/admin/v1/users/security` | ⚠️ 501 stub |
| PUT | `/api/admin/v1/users/{user_id}/plan` | ⚠️ 501 stub |
| PUT | `/api/admin/v1/users/{user_id}/disable` | ⚠️ 501 stub |

### 2.4 Admin Extensions

#### API Health (`/api/admin/v1/api-health`) — 3 endpoints

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/admin/v1/api-health/endpoints` | ✅ live |
| POST | `/api/admin/v1/api-health/run-all` | ✅ live |
| GET | `/api/admin/v1/api-health/summary` | ✅ live |

#### Admin Abuse (`/api/admin/v1/abuse`) — 1 endpoint

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/admin/v1/abuse/queue` | ✅ live |

#### Admin Parsing (`/api/admin/v1/parsing`) — 3 endpoints

| Method | Path | Status |
|--------|------|--------|
| POST | `/api/admin/v1/parsing/parse` | ✅ live |
| GET | `/api/admin/v1/parsing/parse/{parse_id}` | ✅ live |
| GET | `/api/admin/v1/parsing/parse` | ✅ live |

#### Admin Tokens (`/api/admin/v1/tokens`) — 3 endpoints

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/admin/v1/tokens/config` | ⚠️ unwired (empty store) |
| PUT | `/api/admin/v1/tokens/config` | ⚠️ unwired (empty store) |
| GET | `/api/admin/v1/tokens/usage` | ⚠️ unwired (empty store) |

#### Anti-Gaming (`/api/admin/v1/anti-gaming`) — 1 endpoint

| Method | Path | Status |
|--------|------|--------|
| POST | `/api/admin/v1/anti-gaming/check` | ✅ live |

#### Logs (`/api/admin/v1/logs`) — 1 endpoint

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/admin/v1/logs/tail` | ✅ live |

### 2.5 Shared (`/api/shared/v1`) — 2 endpoints

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/shared/v1/health` | ✅ live |
| GET | `/api/shared/v1/health/deep` | ✅ live |

### 2.6 Mentor (`/api/mentor/v1`) — 11 endpoints

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/mentor/v1/profile-by-user/{user_id}` | ✅ live (in-memory) |
| GET | `/api/mentor/v1/{mentor_profile_id}/profile` | ✅ live (in-memory) |
| PUT | `/api/mentor/v1/{mentor_profile_id}/availability` | ✅ live (in-memory) |
| GET | `/api/mentor/v1/list` | ✅ live (in-memory) |
| GET | `/api/mentor/v1/{mentor_profile_id}/packages` | ✅ live (in-memory) |
| POST | `/api/mentor/v1/{mentor_profile_id}/packages` | ✅ live (in-memory) |
| GET | `/api/mentor/v1/{mentor_profile_id}/packages/{package_id}` | ✅ live (in-memory) |
| PUT | `/api/mentor/v1/{mentor_profile_id}/packages/{package_id}` | ✅ live (in-memory) |
| DELETE | `/api/mentor/v1/{mentor_profile_id}/packages/{package_id}` | ✅ live (in-memory) |
| GET | `/api/mentor/v1/{mentor_profile_id}/dashboard-stats` | ✅ live (in-memory) |
| GET | `/api/mentor/v1/health` | ✅ live |

### 2.7 Mentorship (`/api/mentorship/v1`) — 21 endpoints

| Method | Path | Status |
|--------|------|--------|
| POST | `/api/mentorship/v1/links` | ✅ live |
| GET | `/api/mentorship/v1/links/mentor/{mentor_id}` | ✅ live |
| GET | `/api/mentorship/v1/links/user/{user_id}` | ✅ live |
| PATCH | `/api/mentorship/v1/links/{link_id}/status` | ✅ live |
| POST | `/api/mentorship/v1/notes` | ✅ live |
| GET | `/api/mentorship/v1/notes/{link_id}` | ✅ live |
| PATCH | `/api/mentorship/v1/notes/{note_id}` | ✅ live |
| POST | `/api/mentorship/v1/documents` | ✅ live |
| GET | `/api/mentorship/v1/documents/{doc_id}` | ✅ live |
| POST | `/api/mentorship/v1/documents/{doc_id}/sign` | ✅ live |
| POST | `/api/mentorship/v1/documents/{doc_id}/reject` | ✅ live |
| POST | `/api/mentorship/v1/invoices` | ✅ live |
| GET | `/api/mentorship/v1/invoices/mentor/{mentor_id}` | ✅ live |
| POST | `/api/mentorship/v1/invoices/{invoice_id}/mark-paid` | ✅ live |
| POST | `/api/mentorship/v1/invoices/{invoice_id}/service-delivered` | ✅ live |
| POST | `/api/mentorship/v1/invoices/{invoice_id}/confirm-completion` | ✅ live |
| POST | `/api/mentorship/v1/invoices/{invoice_id}/dispute` | ✅ live |
| POST | `/api/mentorship/v1/applications` | ✅ live |
| GET | `/api/mentorship/v1/applications/pending` | ✅ live |
| POST | `/api/mentorship/v1/applications/{application_id}/approve` | ✅ live |
| GET | `/api/mentorship/v1/health` | ✅ live |

### 2.8 Intelligence (`/api/intelligence/v1`) — 4 endpoints

| Method | Path | Status |
|--------|------|--------|
| POST | `/api/intelligence/v1/stats/descriptive` | ✅ live |
| POST | `/api/intelligence/v1/stats/regression` | ✅ live |
| GET | `/api/intelligence/v1/market` | ✅ live |
| POST | `/api/intelligence/v1/enrich` | ✅ placeholder |

### 2.9 Coaching (`/api/coaching/v1`) — 5 endpoints

| Method | Path | Status |
|--------|------|--------|
| POST | `/api/coaching/v1/bundle` | ✅ live |
| GET | `/api/coaching/v1/health` | ✅ live |
| POST | `/api/coaching/v1/questions/generate` | ✅ rule-based |
| POST | `/api/coaching/v1/answers/review` | ✅ rule-based |
| POST | `/api/coaching/v1/stories/generate` | ✅ simulated |

### 2.10 Ops (`/api/ops/v1`) — 6 endpoints

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/ops/v1/stats/public` | ✅ mock |
| POST | `/api/ops/v1/processing/start` | ✅ live |
| GET | `/api/ops/v1/processing/status` | ✅ mock |
| POST | `/api/ops/v1/logs/lock` | ✅ simulated |
| GET | `/api/ops/v1/tokens/config` | ✅ live |
| POST | `/api/ops/v1/anti-gaming/check` | ✅ live |

### 2.11 Resume (`/api/resume/v1`) — 5 endpoints

| Method | Path | Status |
|--------|------|--------|
| POST | `/api/resume/v1/upload` | ✅ live |
| GET | `/api/resume/v1/{resume_id}` | ✅ live |
| GET | `/api/resume/v1` | ✅ live |
| POST | `/api/resume/v1/parse` | ⛔ deprecated |
| POST | `/api/resume/v1/enrich` | ⛔ not implemented |

### 2.12 Blockers (`/api/blockers/v1`) — 3 endpoints

| Method | Path | Status |
|--------|------|--------|
| POST | `/api/blockers/v1/detect` | ✅ live |
| GET | `/api/blockers/v1/user/{user_id}` | ✅ live |
| POST | `/api/blockers/v1/improvement-plans/generate` | ⚠️ 501 stub |

### 2.13 Payment (`/api/payment/v1`) — 15 endpoints

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/payment/v1/plans` | ✅ live |
| GET | `/api/payment/v1/plans/{plan_id}` | ✅ live |
| POST | `/api/payment/v1/process` | ✅ live (Braintree) |
| GET | `/api/payment/v1/history` | ✅ live |
| GET | `/api/payment/v1/subscription` | ✅ live |
| POST | `/api/payment/v1/cancel` | ✅ live |
| GET | `/api/payment/v1/health` | ✅ live |
| GET | `/api/payment/v1/client-token` | ✅ live (Braintree) |
| POST | `/api/payment/v1/methods` | ✅ live |
| GET | `/api/payment/v1/methods` | ✅ live |
| DELETE | `/api/payment/v1/methods/{token}` | ✅ live |
| GET | `/api/payment/v1/transactions/{transaction_id}` | ✅ live |
| POST | `/api/payment/v1/refund/{transaction_id}` | ✅ live |
| GET | `/api/payment/v1/gateway-info` | ✅ live |
| POST | `/api/payment/v1/webhooks` | ✅ live (Braintree) |

### 2.14 Rewards (`/api/rewards/v1`) — 10 endpoints

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/rewards/v1/rewards` | ✅ live (in-memory) |
| GET | `/api/rewards/v1/rewards/available` | ✅ live |
| POST | `/api/rewards/v1/suggestions` | ✅ live |
| GET | `/api/rewards/v1/suggestions` | ✅ live |
| POST | `/api/rewards/v1/rewards/redeem` | ✅ live |
| GET | `/api/rewards/v1/referral` | ✅ live |
| POST | `/api/rewards/v1/referral/claim` | ✅ live |
| GET | `/api/rewards/v1/leaderboard` | ✅ mock |
| GET | `/api/rewards/v1/ownership-stats` | ✅ mock |
| GET | `/api/rewards/v1/health` | ✅ live |

### 2.15 Credits (`/api/credits/v1`) — 9 endpoints

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/credits/v1/plans` | ✅ live |
| GET | `/api/credits/v1/actions` | ✅ live |
| GET | `/api/credits/v1/balance` | ✅ live |
| GET | `/api/credits/v1/can-perform/{action_id}` | ✅ live |
| POST | `/api/credits/v1/consume` | ✅ live |
| GET | `/api/credits/v1/usage` | ✅ live |
| POST | `/api/credits/v1/teaser` | ✅ live |
| POST | `/api/credits/v1/upgrade/{plan_tier}` | ✅ live |
| GET | `/api/credits/v1/health` | ✅ live |

### 2.16 AI Data (`/api/ai-data/v1`) — 15 endpoints

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/ai-data/v1/parsed_resumes` | ✅ live |
| GET | `/api/ai-data/v1/parsed_resumes/{doc_id}` | ✅ live |
| GET | `/api/ai-data/v1/job_descriptions` | ✅ live |
| GET | `/api/ai-data/v1/companies` | ✅ live |
| GET | `/api/ai-data/v1/job_titles` | ✅ live |
| GET | `/api/ai-data/v1/locations` | ✅ live |
| GET | `/api/ai-data/v1/metadata` | ✅ live |
| GET | `/api/ai-data/v1/normalized` | ✅ live |
| GET | `/api/ai-data/v1/email_extracted` | ✅ live |
| GET | `/api/ai-data/v1/status` | ✅ live |
| GET | `/api/ai-data/v1/automated/candidates` | ✅ live |
| GET | `/api/ai-data/v1/user_data/files` | ✅ live |
| POST | `/api/ai-data/v1/model/reload` | ✅ live |
| POST | `/api/ai-data/v1/model/switch` | ✅ live |
| GET | `/api/ai-data/v1/model/status` | ✅ live |

### 2.17 Jobs (`/api/jobs/v1`) — 2 endpoints

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/jobs/v1/index` | ✅ mock |
| GET | `/api/jobs/v1/search` | ✅ mock |

### 2.18 Taxonomy (`/api/taxonomy/v1`) — 8 endpoints

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/taxonomy/v1/industries` | ✅ live |
| GET | `/api/taxonomy/v1/industries/{high_level}/subindustries` | ✅ live |
| GET | `/api/taxonomy/v1/job-titles/search` | ✅ live |
| GET | `/api/taxonomy/v1/job-titles/metadata` | ✅ live |
| GET | `/api/taxonomy/v1/job-titles/infer-industries` | ✅ live |
| GET | `/api/taxonomy/v1/naics/search` | ✅ live |
| GET | `/api/taxonomy/v1/naics/title` | ✅ live |
| GET | `/api/taxonomy/v1/job-titles/naics-mapping` | ✅ live |

### 2.19 Sessions (`/api/sessions/v1`) — 4 endpoints

| Method | Path | Status |
|--------|------|--------|
| POST | `/api/sessions/v1/log` | ✅ live |
| GET | `/api/sessions/v1/summary/{user_id}` | ✅ live |
| GET | `/api/sessions/v1/sync-status` | ✅ live |
| GET | `/api/sessions/v1/consolidated/{user_id}` | ✅ live |

### 2.20 Insights (`/api/insights/v1`) — 6 endpoints

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/insights/v1/visuals` | ✅ live |
| GET | `/api/insights/v1/skills/radar` | ✅ live |
| GET | `/api/insights/v1/quadrant` | ✅ live |
| GET | `/api/insights/v1/terms/cloud` | ✅ live |
| GET | `/api/insights/v1/terms/cooccurrence` | ✅ live |
| GET | `/api/insights/v1/graph` | ✅ live |

### 2.21 Touchpoints (`/api/touchpoints/v1`) — 2 endpoints

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/touchpoints/v1/evidence` | ✅ live |
| GET | `/api/touchpoints/v1/touchnots` | ✅ live |

### 2.22 Mapping (`/api/mapping/v1`) — 3 endpoints

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/mapping/v1/registry` | ✅ live |
| GET | `/api/mapping/v1/endpoints` | ✅ live |
| GET | `/api/mapping/v1/graph` | ✅ live |

### 2.23 Analytics (`/api/analytics/v1`) — 5 endpoints

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/analytics/v1/statistics` | ✅ live |
| GET | `/api/analytics/v1/dashboard` | ✅ live |
| GET | `/api/analytics/v1/recent_resumes` | ✅ live |
| GET | `/api/analytics/v1/recent_jobs` | ✅ live |
| GET | `/api/analytics/v1/system_health` | ✅ live |

### 2.24 GDPR (`/api/gdpr/v1`) — 4 endpoints

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/gdpr/v1/consent` | ✅ live |
| POST | `/api/gdpr/v1/consent` | ✅ live |
| GET | `/api/gdpr/v1/export` | ✅ live |
| DELETE | `/api/gdpr/v1/delete-account` | ✅ live |
| GET | `/api/gdpr/v1/audit-log` | ✅ live |

### 2.25 Telemetry (`/api/telemetry/v1`) — 1 endpoint

| Method | Path | Status |
|--------|------|--------|
| GET | `/api/telemetry/v1/status` | ✅ live |

---

## 3. TOTALS

| Category | Count |
|----------|-------|
| **User Portal routes** | 20 |
| **Admin Portal routes** | 73 |
| **Mentor Portal routes** | 13 |
| **Total frontend routes** | **106** |
| **Backend API endpoints** | **164** |
| **501 Not-Implemented stubs** | 15 |
| **Deprecated endpoints** | 2 |

---

## 4. BROKEN / MISMATCHED LINKS

### 4.1 Frontend calling NON-EXISTENT backend endpoints ❌

| Frontend File | Call | Expected Backend Path | Actual Backend Path | Issue |
|---------------|------|----------------------|---------------------|-------|
| `apps/user/src/lib/api.ts` | `getUserStats()` | `GET /api/user/v1/stats` | — | **MISSING**: No `/stats` endpoint on user router |
| `apps/user/src/lib/api.ts` | `getUserActivity()` | `GET /api/user/v1/activity` | — | **MISSING**: No `/activity` endpoint on user router |
| `apps/user/src/lib/api.ts` | `detectBlockers()` | `POST /api/coaching/v1/blockers/detect` | `POST /api/blockers/v1/detect` | **WRONG PREFIX**: Frontend uses coaching prefix, backend uses blockers prefix |
| `apps/user/src/lib/api.ts` | `getUserBlockers()` | `GET /api/coaching/v1/blockers/user/{id}` | `GET /api/blockers/v1/user/{id}` | **WRONG PREFIX**: Same prefix mismatch |
| `apps/user/src/lib/api.ts` | `generateImprovementPlans()` | `POST /api/coaching/v1/blockers/improvement-plans/generate` | `POST /api/blockers/v1/improvement-plans/generate` | **WRONG PREFIX** + backend returns 501 |
| `apps/user/src/lib/api.ts` | `resolveCohort()` | `POST /api/insights/v1/cohort/resolve` | — | **MISSING**: No `/cohort/resolve` endpoint on insights router |
| `apps/admin/src/lib/apiConfig.ts` | `API.logs` | `/api/logs/v1` | `/api/admin/v1/logs` | **WRONG PREFIX**: Admin config says `/api/logs/v1` but backend uses `/api/admin/v1/logs` |

### 4.2 Backend endpoints WITHOUT frontend consumers 🔇

These backend endpoints exist but are not referenced in any frontend `apiConfig.ts`:

| Router | Endpoint | Notes |
|--------|----------|-------|
| GDPR | All 5 endpoints | No GDPR config in any frontend `apiConfig.ts`; no privacy settings page for users |
| Intelligence | `POST /stats/descriptive`, `POST /stats/regression`, `POST /enrich` | Not wired to any frontend page |
| Ops | `POST /processing/start`, `POST /logs/lock` | Admin-only ops, no dedicated admin page wiring |
| Admin Abuse | `GET /abuse/queue` | No frontend page calls this |
| Admin Parsing | All 3 endpoints | Not referenced in admin `apiConfig.ts` |
| Admin Anti-Gaming | `POST /anti-gaming/check` | Separate from ops duplicate at same path |
| Telemetry | `GET /status` | Listed in admin config but likely never called from UI |
| Webhooks | `POST /webhooks` | Inbound-only (from Braintree), not called by frontend |
| Shared | `GET /health`, `GET /health/deep` | Infrastructure probes, not called from UI |

### 4.3 Frontend pages with NO dedicated backend endpoints ⚠️

These admin pages exist in the frontend router but have no obvious dedicated backend endpoint:

| Frontend Route | Page Component | Missing Backend |
|----------------|---------------|-----------------|
| `/admin/market-intel` | MarketIntelligence | Only `GET /api/intelligence/v1/market` exists (mock data) |
| `/admin/competitive` | CompetitiveIntel | No competitive intelligence endpoint |
| `/admin/web-intel` | WebCompanyIntel | No web company intelligence endpoint |
| `/admin/contact` | ContactComm | No contact/communication endpoint |
| `/admin/settings` | AdvancedSettings | No settings CRUD endpoint |
| `/admin/intel-hub` | IntelligenceHub | No intelligence hub aggregation endpoint |
| `/admin/career-patterns` | CareerPatterns | No career patterns endpoint |
| `/admin/exa-web` | ExaWebIntel | No Exa web intelligence endpoint |
| `/admin/requirements` | RequirementsMgmt | No software requirements endpoint |
| `/admin/portal-entry` | AdminPortalEntry | Likely navigational-only |
| `/admin/tools/data-health` | DataRootsHealth | No data roots health check endpoint |
| `/admin/tools/notifications` | Notifications | No notifications endpoint |
| `/admin/tools/config` | SystemConfig | No system config CRUD endpoint |
| `/admin/tools/diagnostics` | Diagnostics | No diagnostics endpoint |
| `/admin/tools/exports` | Exports | No data exports endpoint |
| `/admin/tools/backup` | BackupRestore | No backup/restore endpoint |
| All `/admin/ops/*` pages | OpsXxx | Exact same situation — likely duplicate of tools pages |
| `/mentor/calendar` | SessionsCalendar | No calendar/scheduling endpoint in mentor or sessions router |
| `/mentor/guardian-feedback` | GuardianFeedback | No guardian feedback endpoint |

---

## 5. DUPLICATE / CONFLICTING ENDPOINTS

| Issue | Details |
|-------|---------|
| **Duplicate token config** | `GET /api/ops/v1/tokens/config` (ops.py) AND `GET /api/admin/v1/tokens/config` (admin_tokens.py) — two different implementations |
| **Duplicate anti-gaming** | `POST /api/ops/v1/anti-gaming/check` (ops.py — simple) AND `POST /api/admin/v1/anti-gaming/check` (anti_gaming.py — full AbusePolicyService) |
| **Duplicate token pages** | `/admin/tokens` (TokenManagement) AND `/admin/tokens-alt` (TokenManagementAlt) — two frontend routes for same concept |
| **Tools vs Ops duplication** | 10 routes under `/admin/tools/*` are duplicated under `/admin/ops/*` (admin-audit, notifications, config, logs-viewer, diagnostics, exports, backup, route-map, api-explorer, about) |

---

## 6. SUMMARY OF ACTION ITEMS

### Critical Fixes (breaking)
1. **Add `GET /api/user/v1/stats`** — Dashboard calls this; returns 404
2. **Add `GET /api/user/v1/activity`** — Dashboard calls this; returns 404  
3. **Fix blocker prefix mismatch** — Frontend uses `/api/coaching/v1/blockers/*` but backend is at `/api/blockers/v1/*`. Either update frontend `apiConfig.ts` to add a `blockers` key or add proxy routes under coaching router
4. **Add `POST /api/insights/v1/cohort/resolve`** — VisualisationsHub calls this; returns 404
5. **Fix admin logs prefix** — Admin `apiConfig.ts` declares `logs: /api/logs/v1` but backend is at `/api/admin/v1/logs`

### Recommended Improvements
6. Add GDPR endpoints to user portal `apiConfig.ts` and create a Privacy/Data Rights page
7. Implement the 15 remaining 501 stubs or remove them from admin pages
8. Consolidate `/admin/ops/*` and `/admin/tools/*` — they are duplicates
9. Consolidate token config endpoints (ops.py vs admin_tokens.py)
10. Add calendar/scheduling endpoints for mentor portal
11. Wire admin parsing and abuse queue to their respective admin pages
