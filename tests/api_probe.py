"""
CareerTrojan Full API Endpoint Probe
=====================================
Hits every registered endpoint and reports status.
Pass/Fail for each route, grouped by router.

Usage:
    python tests/api_probe.py [--base http://localhost:8510]
"""

import sys, json, time, argparse, urllib.request, urllib.error, urllib.parse

BASE = "http://localhost:8510"

# ── endpoints: (method, path, label, body_or_none) ──
# For POST/PUT/PATCH/DELETE that need bodies we send minimal JSON
# For auth-protected routes we expect 401/403 which still counts as "reachable"

ENDPOINTS = [
    # ── root health ──
    ("GET",  "/health", "root-health", None),

    # ── admin.py  /api/admin/v1 ──
    ("GET",  "/api/admin/v1/users", "admin-users", None),
    ("GET",  "/api/admin/v1/system/health", "admin-system-health", None),
    ("GET",  "/api/admin/v1/compliance/summary", "admin-compliance-summary", None),
    ("GET",  "/api/admin/v1/integrations/status", "admin-integrations-status", None),
    ("GET",  "/api/admin/v1/email/logs", "admin-email-logs", None),
    ("GET",  "/api/admin/v1/email/analytics", "admin-email-analytics", None),
    ("GET",  "/api/admin/v1/email/status", "admin-email-status", None),
    ("GET",  "/api/admin/v1/parsers/status", "admin-parsers-status", None),
    ("GET",  "/api/admin/v1/system/activity", "admin-system-activity", None),
    ("GET",  "/api/admin/v1/dashboard/snapshot", "admin-dashboard-snapshot", None),
    ("GET",  "/api/admin/v1/user_subscriptions", "admin-user-subscriptions", None),
    ("GET",  "/api/admin/v1/users/metrics", "admin-users-metrics", None),
    ("GET",  "/api/admin/v1/users/security", "admin-users-security", None),
    ("GET",  "/api/admin/v1/compliance/audit/events", "admin-audit-events", None),
    ("GET",  "/api/admin/v1/email/jobs", "admin-email-jobs", None),
    ("GET",  "/api/admin/v1/parsers/jobs", "admin-parsers-jobs", None),
    ("GET",  "/api/admin/v1/batch/status", "admin-batch-status", None),
    ("GET",  "/api/admin/v1/batch/jobs", "admin-batch-jobs", None),
    ("GET",  "/api/admin/v1/ai/enrichment/status", "admin-enrichment-status", None),
    ("GET",  "/api/admin/v1/ai/enrichment/jobs", "admin-enrichment-jobs", None),
    ("GET",  "/api/admin/v1/ai/content/status", "admin-content-status", None),
    ("GET",  "/api/admin/v1/ai/content/jobs", "admin-content-jobs", None),

    # ── admin_abuse.py ──
    ("GET",  "/api/admin/v1/abuse/queue", "admin-abuse-queue", None),

    # ── admin_legacy.py ──
    ("GET",  "/api/admin/integrations/status", "admin-legacy-integrations", None),

    # ── admin_parsing.py ──
    ("GET",  "/api/admin/v1/parsing/parse", "admin-parsing-list", None),

    # ── admin_tokens.py ──
    ("GET",  "/admin/tokens/plans", "admin-tokens-plans", None),
    ("GET",  "/admin/tokens/config", "admin-tokens-config", None),
    ("GET",  "/api/admin/v1/tokens/config", "admin-tokens-config-v1", None),
    ("GET",  "/admin/tokens/usage", "admin-tokens-usage", None),
    ("GET",  "/api/admin/v1/tokens/usage", "admin-tokens-usage-v1", None),
    ("GET",  "/admin/subscriptions", "admin-subscriptions", None),
    ("GET",  "/admin/tokens/subscriptions", "admin-tokens-subscriptions", None),
    ("GET",  "/admin/tokens/costs", "admin-tokens-costs", None),
    ("GET",  "/admin/tokens/logs", "admin-tokens-logs", None),
    ("GET",  "/admin/tokens/analytics", "admin-tokens-analytics", None),
    ("GET",  "/admin/tokens/unit-economics", "admin-tokens-unit-economics", None),

    # ── ai_data.py ──
    ("GET",  "/api/ai-data/v1/parsed_resumes", "ai-data-parsed-resumes", None),
    ("GET",  "/api/ai-data/v1/job_descriptions", "ai-data-job-descriptions", None),
    ("GET",  "/api/ai-data/v1/companies", "ai-data-companies", None),
    ("GET",  "/api/ai-data/v1/job_titles", "ai-data-job-titles", None),
    ("GET",  "/api/ai-data/v1/locations", "ai-data-locations", None),
    ("GET",  "/api/ai-data/v1/metadata", "ai-data-metadata", None),
    # ("GET",  "/api/ai-data/v1/normalized", "ai-data-normalized", None),  # SLOW — skipped
    ("GET",  "/api/ai-data/v1/email_extracted", "ai-data-email-extracted", None),
    ("GET",  "/api/ai-data/v1/emails", "ai-data-emails", None),
    ("GET",  "/api/ai-data/v1/emails/summary", "ai-data-emails-summary", None),
    ("GET",  "/api/ai-data/v1/emails/diagnostics", "ai-data-emails-diagnostics", None),
    ("GET",  "/api/ai-data/v1/emails/tracking", "ai-data-emails-tracking", None),
    ("GET",  "/api/ai-data/v1/emails/tracking/summary", "ai-data-tracking-summary", None),
    ("GET",  "/api/ai-data/v1/emails/tracking/reroute-targets", "ai-data-tracking-reroute", None),
    ("GET",  "/api/ai-data/v1/status", "ai-data-status", None),
    ("GET",  "/api/ai-data/v1/parser/ingestion-status", "ai-data-parser-ingestion", None),
    ("GET",  "/api/ai-data/v1/automated/candidates", "ai-data-automated-candidates", None),
    ("GET",  "/api/ai-data/v1/user_data/files", "ai-data-user-files", None),

    # ── analytics.py ──
    ("GET",  "/api/analytics/v1/statistics", "analytics-statistics", None),
    ("GET",  "/api/analytics/v1/dashboard", "analytics-dashboard", None),
    ("GET",  "/api/analytics/v1/recent_resumes", "analytics-recent-resumes", None),
    ("GET",  "/api/analytics/v1/recent_jobs", "analytics-recent-jobs", None),
    ("GET",  "/api/analytics/v1/system_health", "analytics-system-health", None),

    # ── anti_gaming.py ──
    ("POST", "/api/admin/v1/anti-gaming/check", "anti-gaming-check", {"user_id": "test"}),

    # ── auth.py ──
    ("POST", "/api/auth/v1/register", "auth-register", {"email": "probe@test.com", "password": "Test1234!", "name": "Probe"}),
    ("POST", "/api/auth/v1/login", "auth-login", {"email": "probe@test.com", "password": "Test1234!"}),
    ("GET",  "/api/auth/v1/google/login", "auth-google-login", None),

    # ── blockers.py ──
    ("POST", "/api/blockers/v1/detect", "blockers-detect", {"user_id": "test", "resume_text": "test"}),
    ("GET",  "/api/blockers/v1/user/test-user-1", "blockers-user", None),

    # ── coaching.py ──
    ("GET",  "/api/coaching/v1/health", "coaching-health", None),
    ("GET",  "/api/coaching/v1/history", "coaching-history", None),
    ("POST", "/api/coaching/v1/bundle", "coaching-bundle", {"user_id": "test"}),

    # ── credits.py ──
    ("GET",  "/api/credits/v1/plans", "credits-plans", None),
    ("GET",  "/api/credits/v1/actions", "credits-actions", None),
    ("GET",  "/api/credits/v1/balance", "credits-balance", None),
    ("GET",  "/api/credits/v1/can-perform/resume_parse", "credits-can-perform", None),
    ("GET",  "/api/credits/v1/usage", "credits-usage", None),
    ("GET",  "/api/credits/v1/health", "credits-health", None),

    # ── data_index.py ──
    ("GET",  "/api/data-index/v1/status", "data-index-status", None),
    ("GET",  "/api/data-index/v1/ai-data/summary", "data-index-ai-summary", None),
    ("GET",  "/api/data-index/v1/ai-data/categories", "data-index-categories", None),
    ("GET",  "/api/data-index/v1/ai-data/skills", "data-index-skills", None),
    ("GET",  "/api/data-index/v1/ai-data/industries", "data-index-industries", None),
    ("GET",  "/api/data-index/v1/ai-data/locations", "data-index-locations", None),
    ("GET",  "/api/data-index/v1/parser/summary", "data-index-parser-summary", None),
    ("GET",  "/api/data-index/v1/parser/status", "data-index-parser-status", None),
    ("GET",  "/api/data-index/v1/parser/file-types", "data-index-file-types", None),
    ("GET",  "/api/data-index/v1/parser/runs", "data-index-parser-runs", None),
    ("GET",  "/api/data-index/v1/dependencies", "data-index-dependencies", None),
    ("GET",  "/api/data-index/v1/files/manifest-stats", "data-index-manifest-stats", None),
    ("GET",  "/api/data-index/v1/health", "data-index-health", None),

    # ── gdpr.py ──
    ("GET",  "/api/gdpr/v1/consent", "gdpr-consent", None),
    ("GET",  "/api/gdpr/v1/export", "gdpr-export", None),
    ("GET",  "/api/gdpr/v1/audit-log", "gdpr-audit-log", None),

    # ── insights.py ──
    ("GET",  "/api/insights/v1/visuals", "insights-visuals", None),
    ("GET",  "/api/insights/v1/skills/radar", "insights-skills-radar", None),
    ("GET",  "/api/insights/v1/quadrant", "insights-quadrant", None),
    ("GET",  "/api/insights/v1/terms/cloud", "insights-term-cloud", None),
    ("GET",  "/api/insights/v1/terms/cooccurrence", "insights-cooccurrence", None),
    ("GET",  "/api/insights/v1/graph", "insights-graph", None),

    # ── intelligence.py ──
    ("GET",  "/api/intelligence/v1/market", "intelligence-market", None),
    ("GET",  "/api/intelligence/v1/company/registry", "intelligence-company-registry", None),
    ("GET",  "/api/intelligence/v1/company/registry/analytics", "intelligence-registry-analytics", None),
    ("GET",  "/api/intelligence/v1/company/registry/events", "intelligence-registry-events", None),
    ("GET",  "/api/intelligence/v1/pipeline/ops-summary", "intelligence-pipeline-ops", None),
    ("GET",  "/api/intelligence/v1/support/status", "intelligence-support-status", None),
    ("POST", "/api/intelligence/v1/stats/descriptive", "intelligence-stats", {"data": [1,2,3]}),
    ("POST", "/api/intelligence/v1/enrich", "intelligence-enrich", {"resume_text": "test"}),

    # ── jobs.py ──
    ("GET",  "/api/jobs/v1/index", "jobs-index", None),
    ("GET",  "/api/jobs/v1/search", "jobs-search", None),

    # ── lenses.py ──
    ("POST", "/api/lenses/v1/spider", "lenses-spider", {"user_id": "test"}),
    ("POST", "/api/lenses/v1/covey", "lenses-covey", {"user_id": "test"}),
    ("POST", "/api/lenses/v1/composite", "lenses-composite", {"user_id": "test"}),

    # ── logs.py ──
    ("GET",  "/api/admin/v1/logs/tail", "admin-logs-tail", None),

    # ── mapping.py ──
    ("GET",  "/api/mapping/v1/registry", "mapping-registry", None),
    ("GET",  "/api/mapping/v1/endpoints", "mapping-endpoints", None),
    ("GET",  "/api/mapping/v1/graph", "mapping-graph", None),

    # ── mentor.py ──
    ("GET",  "/api/mentor/v1/list", "mentor-list", None),
    ("GET",  "/api/mentor/v1/health", "mentor-health", None),

    # ── mentorship.py ──
    ("GET",  "/api/mentorship/v1/applications/pending", "mentorship-pending", None),
    ("GET",  "/api/mentorship/v1/summary", "mentorship-summary", None),
    ("GET",  "/api/mentorship/v1/health", "mentorship-health", None),

    # ── ontology.py ──
    ("GET",  "/api/ontology/v1/phrases", "ontology-phrases", None),
    ("GET",  "/api/ontology/v1/phrases/summary", "ontology-phrases-summary", None),

    # ── ops.py ──
    ("GET",  "/api/ops/v1/stats/public", "ops-stats-public", None),
    ("GET",  "/api/ops/v1/processing/status", "ops-processing-status", None),
    ("GET",  "/api/ops/v1/tokens/config", "ops-tokens-config", None),

    # ── payment.py ──
    ("GET",  "/api/payment/v1/plans", "payment-plans", None),
    ("GET",  "/api/payment/v1/history", "payment-history", None),
    ("GET",  "/api/payment/v1/subscription", "payment-subscription", None),
    ("GET",  "/api/payment/v1/health", "payment-health", None),
    ("GET",  "/api/payment/v1/client-token", "payment-client-token", None),
    ("GET",  "/api/payment/v1/methods", "payment-methods", None),
    ("GET",  "/api/payment/v1/gateway-info", "payment-gateway-info", None),

    # ── resume.py ──
    ("GET",  "/api/resume/v1", "resume-list", None),

    # ── rewards.py ──
    ("GET",  "/api/rewards/v1/rewards", "rewards-list", None),
    ("GET",  "/api/rewards/v1/rewards/available", "rewards-available", None),
    ("GET",  "/api/rewards/v1/suggestions", "rewards-suggestions", None),
    ("GET",  "/api/rewards/v1/referral", "rewards-referral", None),
    ("GET",  "/api/rewards/v1/leaderboard", "rewards-leaderboard", None),
    ("GET",  "/api/rewards/v1/ownership-stats", "rewards-ownership-stats", None),
    ("GET",  "/api/rewards/v1/health", "rewards-health", None),

    # ── sessions.py ──
    ("GET",  "/api/sessions/v1/sync-status", "sessions-sync-status", None),
    ("GET",  "/api/sessions/v1/summary/test-user", "sessions-summary", None),
    ("GET",  "/api/sessions/v1/consolidated/test-user", "sessions-consolidated", None),

    # ── shared.py ──
    ("GET",  "/api/shared/v1/health", "shared-health", None),
    ("GET",  "/api/shared/v1/health/deep", "shared-health-deep", None),

    # ── support.py ──
    ("GET",  "/api/support/v1/health", "support-health", None),
    ("GET",  "/api/support/v1/status", "support-status", None),
    ("GET",  "/api/support/v1/widget-config", "support-widget-config", None),
    ("GET",  "/api/support/v1/wiring-test", "support-wiring-test", None),
    ("GET",  "/api/support/v1/providers", "support-providers", None),
    ("GET",  "/api/support/v1/readiness", "support-readiness", None),
    ("GET",  "/api/support/v1/tickets", "support-tickets-list", None),
    ("GET",  "/api/support/v1/ai/queue-stats", "support-ai-queue-stats", None),
    ("GET",  "/api/support/v1/ai/jobs", "support-ai-jobs", None),

    # ── taxonomy.py ──
    ("GET",  "/api/taxonomy/v1/industries", "taxonomy-industries", None),
    ("GET",  "/api/taxonomy/v1/job-titles/search?q=engineer", "taxonomy-job-search", None),
    ("GET",  "/api/taxonomy/v1/job-titles/metadata?title=engineer", "taxonomy-metadata", None),
    ("GET",  "/api/taxonomy/v1/naics/search?q=tech", "taxonomy-naics-search", None),
    ("GET",  "/api/taxonomy/v1/summary", "taxonomy-summary", None),

    # ── telemetry.py ──
    ("GET",  "/api/telemetry/v1/status", "telemetry-status", None),

    # ── touchpoints.py ──
    ("GET",  "/api/touchpoints/v1/evidence", "touchpoints-evidence", None),
    ("GET",  "/api/touchpoints/v1/touchnots", "touchpoints-touchnots", None),

    # ── user.py ──
    ("GET",  "/api/user/v1/me", "user-me", None),
    ("GET",  "/api/user/v1/profile", "user-profile", None),
    ("GET",  "/api/user/v1/stats", "user-stats", None),
    ("GET",  "/api/user/v1/activity", "user-activity", None),
    ("GET",  "/api/user/v1/sessions/summary", "user-sessions-summary", None),
    ("GET",  "/api/user/v1/resume/latest", "user-resume-latest", None),
    ("GET",  "/api/user/v1/matches/summary", "user-matches-summary", None),

    # ── webhooks.py ──
    ("GET",  "/api/webhooks/v1/health", "webhooks-health", None),
    ("POST", "/api/webhooks/v1/braintree", "webhooks-braintree", {"bt_signature": "test", "bt_payload": "test"}),
    ("POST", "/api/webhooks/v1/stripe", "webhooks-stripe", {}),
    ("POST", "/api/webhooks/v1/zendesk", "webhooks-zendesk", {}),
]


def probe(base: str):
    results = []
    pass_count = 0
    fail_count = 0

    for method, path, label, body in ENDPOINTS:
        url = base + path
        t0 = time.time()
        status = None
        snippet = ""
        ok = False

        try:
            data = None
            headers = {"Content-Type": "application/json"} if body is not None else {}
            if body is not None:
                data = json.dumps(body).encode()

            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=8) as resp:
                status = resp.status
                raw = resp.read().decode("utf-8", errors="replace")[:200]
                snippet = raw
                ok = True
        except urllib.error.HTTPError as e:
            status = e.code
            try:
                raw = e.read().decode("utf-8", errors="replace")[:200]
                snippet = raw
            except:
                snippet = str(e.reason)
            # 401/403 = endpoint EXISTS but needs auth → still "reachable"
            # 405 = method not allowed → still reachable
            # 422 = validation error → endpoint exists
            if status in (401, 403, 405, 422):
                ok = True
        except urllib.error.URLError as e:
            snippet = str(e.reason)[:200]
        except (TimeoutError, ConnectionError, OSError) as e:
            snippet = f"TIMEOUT/CONN: {e}"[:200]
        except Exception as e:
            snippet = str(e)[:200]

        elapsed = round((time.time() - t0) * 1000)

        verdict = "PASS" if ok else "FAIL"
        if ok:
            pass_count += 1
        else:
            fail_count += 1

        results.append({
            "verdict": verdict,
            "method": method,
            "path": path,
            "label": label,
            "status": status,
            "ms": elapsed,
            "snippet": snippet[:120],
        })

        sym = "✓" if ok else "✗"
        print(f"  {sym} {verdict:4s} {status or '---':>3}  {elapsed:>5}ms  {method:5s} {path}")

    # Summary
    print("\n" + "=" * 80)
    print(f"  TOTAL: {len(results)}  |  PASS: {pass_count}  |  FAIL: {fail_count}")
    print("=" * 80)

    if fail_count:
        print("\n  FAILURES:")
        for r in results:
            if r["verdict"] == "FAIL":
                print(f"    ✗ {r['method']:5s} {r['path']}")
                print(f"      Status: {r['status']}  →  {r['snippet'][:100]}")
        print()

    return results, pass_count, fail_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=BASE)
    args = parser.parse_args()
    print(f"\n{'=' * 80}")
    print(f"  CareerTrojan API Probe  —  {args.base}")
    print(f"{'=' * 80}\n")
    probe(args.base)
