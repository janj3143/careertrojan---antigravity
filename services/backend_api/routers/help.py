"""
Help Router — Serves contextual page help text for the help icon system (spec §24 UX).

Routes:
  GET /api/help/v1/pages         — return help data for all pages across all portals
  GET /api/help/v1/pages/{page}  — return help data for a single page by slug
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/help/v1", tags=["help"])

# ── Comprehensive page help registry ──────────────────────────────
# Each entry: slug → { portal, header, description }
# Covers all 106 pages across user / admin / mentor portals.

PAGE_HELP: dict[str, dict] = {
    # ── User Portal (18 pages) ─────────────────────────────────
    "home": {
        "portal": "user",
        "header": "Build a Smarter, Stronger Career.",
        "description": "Your landing page — see what CareerTrojan can do for you and get started with your career upgrade journey.",
    },
    "dashboard": {
        "portal": "user",
        "header": "User Dashboard",
        "description": "Your personal command centre. See resume status, coaching progress, job matches, mentor sessions and key metrics at a glance.",
    },
    "login": {
        "portal": "user",
        "header": "Sign in to CareerTrojan",
        "description": "Sign in with your email and password to access your personalised career dashboard.",
    },
    "register": {
        "portal": "user",
        "header": "Create your account",
        "description": "Create a free CareerTrojan account to upload your CV, access coaching, and start mapping your career.",
    },
    "verify": {
        "portal": "user",
        "header": "✅ Account Verification",
        "description": "Verify your email address to activate your account and unlock all platform features.",
    },
    "profile": {
        "portal": "user",
        "header": "Your Profile",
        "description": "View and edit your personal details, career summary, and notification preferences.",
    },
    "resume": {
        "portal": "user",
        "header": "📄 Resume Upload & Analysis",
        "description": "Upload your CV to receive AI-powered analysis. Your resume is parsed into structured data that powers every CareerTrojan feature — coaching, compass, matching, and insights.",
    },
    "compass": {
        "portal": "user",
        "header": "🧭 Career Compass",
        "description": "Your career navigation engine. Explore peer clusters on the career map, compare your skill vector against targets with spider overlays, discover natural next steps vs strategic stretches, check cul-de-sac risk, plan your runway, and find mentors who complement your gaps.",
    },
    "coaching": {
        "portal": "user",
        "header": "🧠 Coaching Hub",
        "description": "AI-driven interview preparation and career gap coaching. Generate targeted questions, practise answers with real-time feedback, and build STAR stories from your experience.",
    },
    "consolidation": {
        "portal": "user",
        "header": "My CareerTrojan — Everything in One Place",
        "description": "A unified view of all your career data — resume analysis, coaching notes, mentor sessions, rewards, and saved scenarios — in one consolidated dashboard.",
    },
    "dual-career": {
        "portal": "user",
        "header": "⚖️ Dual Career Suite",
        "description": "Manage your primary career alongside a side venture or hustle. Orbit-shifting strategy helps you balance focus and spot transition points.",
    },
    "umarketu": {
        "portal": "user",
        "header": "🎯 MarketU Suite",
        "description": "Browse featured job opportunities and explore industries. MarketU positions you against live market demand so you can target the right roles.",
    },
    "mentor-apply": {
        "portal": "user",
        "header": "🎓 Become A Mentor",
        "description": "Apply to become a CareerTrojan mentor. Share your expertise, help others, and earn through the mentorship marketplace.",
    },
    "mentorship": {
        "portal": "user",
        "header": "🤝 Mentorship Marketplace",
        "description": "Browse available mentors by expertise, industry and reviews. Book sessions, manage agreements, and track your mentoring journey.",
    },
    "payment": {
        "portal": "user",
        "header": "💳 Select Your Plan",
        "description": "Choose a subscription plan that fits your needs. Compare features across Free, Premium, and Enterprise tiers, then checkout securely.",
    },
    "rewards": {
        "portal": "user",
        "header": "🎁 User Rewards",
        "description": "Track your achievements, earn badges, and level up. Rewards are earned by using coaching, uploading CVs, connecting with mentors, and hitting milestones.",
    },
    "visuals": {
        "portal": "user",
        "header": "📊 Visualisations Hub",
        "description": "Interactive chart gallery — leadership spiders, skills competency radars, quadrant fit maps, career mind maps, word clouds, and touchpoint networks. Select any visual and explore your data.",
    },
    "privacy": {
        "portal": "user",
        "header": "Privacy Policy",
        "description": "Our UK GDPR-compliant privacy policy explaining how we collect, process, store, and protect your personal data.",
    },

    # ── Admin Portal — Main Pages (36) ─────────────────────────
    "admin-home": {
        "portal": "admin",
        "header": "🏠 Admin Dashboard",
        "description": "Admin home with quick-action tiles, system health indicators, and key platform metrics at a glance.",
    },
    "admin-login": {
        "portal": "admin",
        "header": "Admin Portal",
        "description": "Admin authentication — secure sign-in for platform operators.",
    },
    "admin-dashboard": {
        "portal": "admin",
        "header": "📊 Dashboard",
        "description": "Admin summary dashboard showing user growth, active mentors, revenue, and system health.",
    },
    "admin-advanced-settings": {
        "portal": "admin",
        "header": "⚙️ Advanced Settings",
        "description": "Platform-wide advanced configuration — feature flags, rate limits, third-party API keys, and environment overrides.",
    },
    "admin-ai-content": {
        "portal": "admin",
        "header": "✨ AI Content Generator",
        "description": "AI-powered content generation for career materials, coaching scripts, and marketing copy.",
    },
    "admin-ai-enrichment": {
        "portal": "admin",
        "header": "🤖 AI Enrichment",
        "description": "Trigger and monitor AI enrichment pipelines that enhance user data with NLP, classification, and scoring.",
    },
    "admin-analytics": {
        "portal": "admin",
        "header": "📊 Analytics",
        "description": "User growth trends, engagement charts, top mentor rankings, and funnel conversion analytics.",
    },
    "admin-api-health": {
        "portal": "admin",
        "header": "⚡ API Health Dashboard",
        "description": "Real-time monitoring of all API endpoints — latency, error rates, uptime, and dependency status.",
    },
    "admin-api-integration": {
        "portal": "admin",
        "header": "🔌 API Integration",
        "description": "Configure and test connections to external APIs — job boards, email providers, payment gateways, and AI services.",
    },
    "admin-api-smoke": {
        "portal": "admin",
        "header": "API Smoke Test",
        "description": "Quick one-click smoke test runner that hits every registered endpoint and reports pass/fail.",
    },
    "admin-batch": {
        "portal": "admin",
        "header": "⚙️ Batch Processing",
        "description": "Manage and trigger large-scale batch jobs — resume re-parsing, vector recalculation, and data migrations.",
    },
    "admin-blocker-test": {
        "portal": "admin",
        "header": "Blocker Detection Test",
        "description": "Test blocker detection rules against sample data to validate coaching logic.",
    },
    "admin-career-patterns": {
        "portal": "admin",
        "header": "📊 Career Patterns",
        "description": "Analyse career progression patterns across the user base — common transitions, skill clusters, and trajectory insights.",
    },
    "admin-competitive-intel": {
        "portal": "admin",
        "header": "🎯 Competitive Intelligence",
        "description": "Competitive market intelligence — benchmark platform capabilities against industry alternatives.",
    },
    "admin-compliance": {
        "portal": "admin",
        "header": "🛡️ Compliance Audit",
        "description": "Regulatory compliance audit dashboard — GDPR, data retention, consent tracking, and policy enforcement.",
    },
    "admin-connectivity": {
        "portal": "admin",
        "header": "System Connectivity Audit",
        "description": "Health checks for all system connections — database, cache, queues, external APIs, and storage.",
    },
    "admin-contact-comm": {
        "portal": "admin",
        "header": "💬 Contact Communication",
        "description": "Manage user communications — in-app messages, support threads, and notification delivery.",
    },
    "admin-data-parser": {
        "portal": "admin",
        "header": "📄 Data Parser",
        "description": "Upload and parse data files (CSV, JSON, XLSX). View structured results and trigger enrichment.",
    },
    "admin-email": {
        "portal": "admin",
        "header": "📧 Email Intelligence & Campaigns",
        "description": "Email campaign management — create, schedule, and track email campaigns across SendGrid, Klaviyo, and Resend.",
    },
    "admin-exa-web": {
        "portal": "admin",
        "header": "🌐 Exa Web Intelligence",
        "description": "Web intelligence via Exa search API — discover company data, job trends, and market insights from the live web.",
    },
    "admin-intelligence-hub": {
        "portal": "admin",
        "header": "🧠 Intelligence Hub",
        "description": "Central aggregation hub for all intelligence feeds — AI insights, market data, and user analytics.",
    },
    "admin-job-title-ai": {
        "portal": "admin",
        "header": "💼 Job Title AI",
        "description": "AI-powered job title classification, normalisation, and seniority detection.",
    },
    "admin-job-title-cloud": {
        "portal": "admin",
        "header": "☁️ Job Title Cloud",
        "description": "Interactive word-cloud visualisation of job titles across the platform's data.",
    },
    "admin-logging": {
        "portal": "admin",
        "header": "⚠️ Logging & Errors",
        "description": "System error logs, warning trends, and logging configuration for debugging and monitoring.",
    },
    "admin-market-intel": {
        "portal": "admin",
        "header": "📈 Market Intelligence",
        "description": "Labour market trends, salary benchmarks, demand signals, and skill gap analysis.",
    },
    "admin-mentor-review": {
        "portal": "admin",
        "header": "🎓 Mentor Application Review",
        "description": "Review, approve, or reject pending mentor applications with full profile details.",
    },
    "admin-mentor-mgmt": {
        "portal": "admin",
        "header": "🎓 Mentor Management",
        "description": "Manage active mentors — verify credentials, adjust rates, and monitor performance.",
    },
    "admin-model-training": {
        "portal": "admin",
        "header": "🤖 Model Training",
        "description": "ML model training pipeline — trigger training runs, view metrics, and deploy new model versions.",
    },
    "admin-requirements": {
        "portal": "admin",
        "header": "📋 Requirements Management",
        "description": "Track platform requirements, feature requests, and technical debt with priority labelling.",
    },
    "admin-service-status": {
        "portal": "admin",
        "header": "🔧 Service Status",
        "description": "Backend service health — uptime, memory usage, response times, and dependency connectivity.",
    },
    "admin-tokens": {
        "portal": "admin",
        "header": "🔑 Token Management",
        "description": "API token lifecycle management — create, rotate, revoke tokens and manage credit plan allocations.",
    },
    "admin-unified-analytics": {
        "portal": "admin",
        "header": "📊 Unified Analytics",
        "description": "Cross-platform unified analytics — combine user, mentor, admin, and market data in one dashboard.",
    },
    "admin-users": {
        "portal": "admin",
        "header": "👥 User Management",
        "description": "User account CRUD — create, view, edit, deactivate accounts and manage roles and permissions.",
    },
    "admin-web-company": {
        "portal": "admin",
        "header": "🏢 Web Company Intel",
        "description": "Company intelligence scraped from the live web — size, industry, tech stack, and hiring signals.",
    },

    # ── Admin Portal — Tools (29) ──────────────────────────────
    "tools-about": {"portal": "admin-tools", "header": "About", "description": "About the admin tools suite — version, capabilities, and documentation links."},
    "tools-admin-audit": {"portal": "admin-tools", "header": "Admin Audit", "description": "Audit trail of every admin action — who did what and when."},
    "tools-api-explorer": {"portal": "admin-tools", "header": "API Explorer", "description": "Interactive API explorer — browse endpoints, send test requests, view responses."},
    "tools-backup-restore": {"portal": "admin-tools", "header": "Backup & Restore", "description": "Database backup creation, scheduling, and point-in-time restore."},
    "tools-bias-fairness": {"portal": "admin-tools", "header": "Bias and Fairness", "description": "AI model bias and fairness testing — demographic parity, equal opportunity, and disparate impact checks."},
    "tools-blob-storage": {"portal": "admin-tools", "header": "Blob Storage", "description": "Manage uploaded files and blob storage — browse, download, and purge."},
    "tools-data-roots": {"portal": "admin-tools", "header": "Data Roots & Health", "description": "Health status of data source roots — AI data folders, parser outputs, and enrichment stores."},
    "tools-datasets": {"portal": "admin-tools", "header": "Datasets Browser", "description": "Browse and inspect all datasets — row counts, schema, freshness, and sample records."},
    "tools-diagnostics": {"portal": "admin-tools", "header": "Diagnostics", "description": "System diagnostics and troubleshooting — environment variables, dependency versions, and connectivity checks."},
    "tools-email-analytics": {"portal": "admin-tools", "header": "Email Analytics", "description": "Email delivery and engagement analytics — open rates, click rates, bounces, and unsubscribes."},
    "tools-email-capture": {"portal": "admin-tools", "header": "Email Capture", "description": "Email capture and extraction management — import contacts, validate addresses, manage lists."},
    "tools-enrichment-runs": {"portal": "admin-tools", "header": "Enrichment Runs", "description": "View and manage AI enrichment run history — status, duration, records processed, and errors."},
    "tools-evaluation": {"portal": "admin-tools", "header": "Evaluation Harness", "description": "Model evaluation test harness — run accuracy, precision, recall benchmarks against held-out data."},
    "tools-exports": {"portal": "admin-tools", "header": "Exports", "description": "Data export and download management — CSV/JSON exports for users, resumes, analytics, and reports."},
    "tools-job-index": {"portal": "admin-tools", "header": "Job Index", "description": "Searchable job title index with taxonomy mapping and frequency stats."},
    "tools-keyword-ontology": {"portal": "admin-tools", "header": "Keyword Ontology", "description": "Keyword taxonomy / ontology management — add, edit, classify keywords and map synonyms."},
    "tools-logs": {"portal": "admin-tools", "header": "Logs Viewer", "description": "Searchable system logs viewer — filter by level, timestamp, service, and request ID."},
    "tools-model-registry": {"portal": "admin-tools", "header": "Model Registry", "description": "ML model version registry — track model versions, metrics, deployment status, and rollback."},
    "tools-notifications": {"portal": "admin-tools", "header": "Notifications", "description": "Notification templates and delivery management — push, email, in-app notifications."},
    "tools-parser-runs": {"portal": "admin-tools", "header": "Parser Runs", "description": "Resume/data parser run history — view parsing results, errors, and success rates."},
    "tools-phrase-manager": {"portal": "admin-tools", "header": "Phrase Manager", "description": "Manage glossary phrases, term mappings, and collocation rules for AI processing."},
    "tools-prompt-registry": {"portal": "admin-tools", "header": "Prompt Registry", "description": "AI prompt template registry — version, test, and deploy prompt templates."},
    "tools-queue-monitor": {"portal": "admin-tools", "header": "Queue Monitor", "description": "Background job queue monitoring — pending, running, completed, and failed jobs."},
    "tools-resume-json": {"portal": "admin-tools", "header": "Resume JSON Viewer", "description": "View parsed resume data as structured JSON — inspect every extracted field."},
    "tools-role-taxonomy": {"portal": "admin-tools", "header": "Role Taxonomy", "description": "Role classification taxonomy management — hierarchies, seniority levels, and industry mapping."},
    "tools-route-map": {"portal": "admin-tools", "header": "Route Map", "description": "API and app route map — visualise all registered endpoints and their governance status."},
    "tools-scoring": {"portal": "admin-tools", "header": "Scoring Analytics", "description": "Resume and candidate scoring analytics — score distributions, top/bottom analysis, and drift detection."},
    "tools-system-config": {"portal": "admin-tools", "header": "System Config", "description": "Platform system configuration — environment variables, feature flags, and runtime settings."},
    "tools-user-audit": {"portal": "admin-tools", "header": "User Audit", "description": "Audit trail of user actions — logins, uploads, coaching sessions, and data requests."},

    # ── Admin Portal — Ops (10) ────────────────────────────────
    "ops-about": {"portal": "admin-ops", "header": "About (Ops)", "description": "About the ops view — scope, access level, and operational tools overview."},
    "ops-admin-audit": {"portal": "admin-ops", "header": "Admin Audit (Ops)", "description": "Ops-scoped admin audit trail — filtered to operational actions only."},
    "ops-api-explorer": {"portal": "admin-ops", "header": "API Explorer (Ops)", "description": "Ops-scoped API endpoint explorer — read-only operational endpoints."},
    "ops-backup-restore": {"portal": "admin-ops", "header": "Backup & Restore (Ops)", "description": "Ops-scoped backup and restore — trigger backups and view restore points."},
    "ops-diagnostics": {"portal": "admin-ops", "header": "Diagnostics (Ops)", "description": "Ops-scoped system diagnostics — quick health checks and environment info."},
    "ops-exports": {"portal": "admin-ops", "header": "Exports (Ops)", "description": "Ops-scoped data exports — operational reports and metrics downloads."},
    "ops-logs": {"portal": "admin-ops", "header": "Logs Viewer (Ops)", "description": "Ops-scoped logs viewer — recent errors, warnings, and request traces."},
    "ops-notifications": {"portal": "admin-ops", "header": "Notifications (Ops)", "description": "Ops-scoped notifications — operational alerts and system notifications."},
    "ops-route-map": {"portal": "admin-ops", "header": "Route Map (Ops)", "description": "Ops-scoped route map — registered endpoints and health status."},
    "ops-system-config": {"portal": "admin-ops", "header": "System Config (Ops)", "description": "Ops-scoped system configuration — read-only view of runtime settings."},

    # ── Mentor Portal (13 pages) ───────────────────────────────
    "mentor-dashboard": {
        "portal": "mentor",
        "header": "📊 Mentor Dashboard",
        "description": "Your mentor command centre — active mentees, upcoming sessions, earnings, and performance metrics.",
    },
    "mentor-login": {
        "portal": "mentor",
        "header": "Mentor Portal",
        "description": "Mentor authentication — sign in to manage your mentorship practice.",
    },
    "mentor-ai": {
        "portal": "mentor",
        "header": "🤖 Mentorship AI Assistant",
        "description": "AI-powered mentoring assistant — get session prep suggestions, mentee summaries, and coaching insights.",
    },
    "mentor-comms": {
        "portal": "mentor",
        "header": "💬 Communication Center",
        "description": "Messaging hub — chat with mentees, share resources, and manage session notes.",
    },
    "mentor-financial": {
        "portal": "mentor",
        "header": "💰 Financial Dashboard",
        "description": "Earnings overview — session revenue, payout history, and upcoming payments.",
    },
    "mentor-guardian": {
        "portal": "mentor",
        "header": "🛡️ Guardian Feedback",
        "description": "Guardian/parent feedback for mentee sessions — review and respond to safeguarding notes.",
    },
    "mentor-mentee-agreements": {
        "portal": "mentor",
        "header": "📝 Mentee Agreements",
        "description": "View agreements from your mentees' perspective — terms, progress, and deliverables.",
    },
    "mentor-mentee-progress": {
        "portal": "mentor",
        "header": "📊 Mentee Progress",
        "description": "Track individual mentee progress — milestones, session logs, and skill development.",
    },
    "mentor-my-agreements": {
        "portal": "mentor",
        "header": "📄 My Agreements",
        "description": "Your own service agreements — active, pending, and archived contracts.",
    },
    "mentor-packages": {
        "portal": "mentor",
        "header": "📦 Service Packages",
        "description": "Create and manage your mentoring service packages — pricing, duration, and deliverables.",
    },
    "mentor-services-agreement": {
        "portal": "mentor",
        "header": "📋 Services Agreement",
        "description": "Review and sign the CareerTrojan mentor services agreement.",
    },
    "mentor-calendar": {
        "portal": "mentor",
        "header": "📅 Sessions Calendar",
        "description": "Calendar view of all scheduled mentoring sessions — upcoming, past, and cancelled.",
    },
}


@router.get("/pages")
async def get_all_page_help():
    """Return help data for all pages across all portals."""
    return {"status": "ok", "pages": PAGE_HELP}


@router.get("/pages/{slug}")
async def get_page_help(slug: str):
    """Return help data for a single page by slug."""
    entry = PAGE_HELP.get(slug)
    if not entry:
        raise HTTPException(status_code=404, detail=f"No help entry for page '{slug}'")
    return {"status": "ok", "slug": slug, **entry}
