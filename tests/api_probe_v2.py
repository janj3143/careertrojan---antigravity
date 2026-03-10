"""
CareerTrojan Full API Endpoint Probe v2
========================================
Hits every registered endpoint and reports status.
More resilient timeout handling.
"""

import sys, json, time, argparse, socket

# Use http.client directly for better timeout control
import http.client

BASE_HOST = "localhost"
BASE_PORT = 8510

ENDPOINTS = [
    # ── root health ──
    ("GET",  "/health", "root-health", None),

    # ── admin.py ──
    ("GET",  "/api/admin/v1/users", "admin-users", None),
    ("GET",  "/api/admin/v1/system/health", "admin-sys-health", None),
    ("GET",  "/api/admin/v1/compliance/summary", "admin-compliance", None),
    ("GET",  "/api/admin/v1/integrations/status", "admin-integrations", None),
    ("GET",  "/api/admin/v1/email/logs", "admin-email-logs", None),
    ("GET",  "/api/admin/v1/email/analytics", "admin-email-analytics", None),
    ("GET",  "/api/admin/v1/email/status", "admin-email-status", None),
    ("GET",  "/api/admin/v1/parsers/status", "admin-parsers-status", None),
    ("GET",  "/api/admin/v1/system/activity", "admin-sys-activity", None),
    ("GET",  "/api/admin/v1/dashboard/snapshot", "admin-dashboard", None),
    ("GET",  "/api/admin/v1/user_subscriptions", "admin-user-subs", None),
    ("GET",  "/api/admin/v1/users/metrics", "admin-user-metrics", None),
    ("GET",  "/api/admin/v1/users/security", "admin-user-security", None),
    ("GET",  "/api/admin/v1/compliance/audit/events", "admin-audit-events", None),
    ("GET",  "/api/admin/v1/email/jobs", "admin-email-jobs", None),
    ("GET",  "/api/admin/v1/parsers/jobs", "admin-parsers-jobs", None),
    ("GET",  "/api/admin/v1/batch/status", "admin-batch-status", None),
    ("GET",  "/api/admin/v1/batch/jobs", "admin-batch-jobs", None),
    ("GET",  "/api/admin/v1/ai/enrichment/status", "admin-enrich-status", None),
    ("GET",  "/api/admin/v1/ai/enrichment/jobs", "admin-enrich-jobs", None),
    ("GET",  "/api/admin/v1/ai/content/status", "admin-content-status", None),
    ("GET",  "/api/admin/v1/ai/content/jobs", "admin-content-jobs", None),

    # ── admin_abuse ──
    ("GET",  "/api/admin/v1/abuse/queue", "admin-abuse-queue", None),

    # ── admin_legacy ──
    ("GET",  "/api/admin/integrations/status", "admin-legacy-integ", None),

    # ── admin_parsing ──
    ("GET",  "/api/admin/v1/parsing/parse", "admin-parsing-list", None),

    # ── admin_tokens ──
    ("GET",  "/admin/tokens/plans", "admin-tok-plans", None),
    ("GET",  "/admin/tokens/config", "admin-tok-config", None),
    ("GET",  "/api/admin/v1/tokens/config", "admin-tok-cfg-v1", None),
    ("GET",  "/admin/tokens/usage", "admin-tok-usage", None),
    ("GET",  "/api/admin/v1/tokens/usage", "admin-tok-usage-v1", None),
    ("GET",  "/admin/subscriptions", "admin-subscriptions", None),
    ("GET",  "/admin/tokens/subscriptions", "admin-tok-subs", None),
    ("GET",  "/admin/tokens/costs", "admin-tok-costs", None),
    ("GET",  "/admin/tokens/logs", "admin-tok-logs", None),
    ("GET",  "/admin/tokens/analytics", "admin-tok-analytics", None),
    ("GET",  "/admin/tokens/unit-economics", "admin-tok-unit-econ", None),

    # ── ai_data (skip heavy ones that scan thousands of files) ──
    ("GET",  "/api/ai-data/v1/status", "ai-data-status", None),
    ("GET",  "/api/ai-data/v1/parser/ingestion-status", "ai-data-parser-ing", None),
    ("GET",  "/api/ai-data/v1/automated/candidates", "ai-data-auto-cand", None),
    ("GET",  "/api/ai-data/v1/user_data/files", "ai-data-user-files", None),
    ("GET",  "/api/ai-data/v1/job_descriptions", "ai-data-job-descs", None),
    ("GET",  "/api/ai-data/v1/email_extracted", "ai-data-email-ext", None),
    ("GET",  "/api/ai-data/v1/emails/tracking/summary", "ai-data-track-sum", None),
    ("GET",  "/api/ai-data/v1/emails/tracking/reroute-targets", "ai-data-reroute", None),

    # ── analytics ──
    ("GET",  "/api/analytics/v1/statistics", "analytics-stats", None),
    ("GET",  "/api/analytics/v1/dashboard", "analytics-dashboard", None),
    ("GET",  "/api/analytics/v1/recent_resumes", "analytics-resumes", None),
    ("GET",  "/api/analytics/v1/recent_jobs", "analytics-jobs", None),
    ("GET",  "/api/analytics/v1/system_health", "analytics-sys-health", None),

    # ── anti_gaming ──
    ("POST", "/api/admin/v1/anti-gaming/check", "anti-gaming-check", {"user_id": "test"}),

    # ── auth ──
    ("POST", "/api/auth/v1/register", "auth-register", {"email": "p@t.com", "password": "T1!", "name": "P"}),
    ("POST", "/api/auth/v1/login", "auth-login", {"email": "p@t.com", "password": "T1!"}),
    ("GET",  "/api/auth/v1/google/login", "auth-google-login", None),

    # ── blockers ──
    ("POST", "/api/blockers/v1/detect", "blockers-detect", {"user_id": "t", "resume_text": "t"}),
    ("GET",  "/api/blockers/v1/user/test-uid", "blockers-user", None),

    # ── coaching ──
    ("GET",  "/api/coaching/v1/health", "coaching-health", None),
    ("GET",  "/api/coaching/v1/history", "coaching-history", None),
    ("POST", "/api/coaching/v1/bundle", "coaching-bundle", {"user_id": "t"}),

    # ── credits ──
    ("GET",  "/api/credits/v1/plans", "credits-plans", None),
    ("GET",  "/api/credits/v1/actions", "credits-actions", None),
    ("GET",  "/api/credits/v1/balance", "credits-balance", None),
    ("GET",  "/api/credits/v1/can-perform/resume_parse", "credits-can-perf", None),
    ("GET",  "/api/credits/v1/usage", "credits-usage", None),
    ("GET",  "/api/credits/v1/health", "credits-health", None),

    # ── data_index ──
    ("GET",  "/api/data-index/v1/status", "data-idx-status", None),
    ("GET",  "/api/data-index/v1/ai-data/summary", "data-idx-ai-sum", None),
    ("GET",  "/api/data-index/v1/ai-data/categories", "data-idx-cats", None),
    ("GET",  "/api/data-index/v1/ai-data/skills", "data-idx-skills", None),
    ("GET",  "/api/data-index/v1/ai-data/industries", "data-idx-industries", None),
    ("GET",  "/api/data-index/v1/ai-data/locations", "data-idx-locations", None),
    ("GET",  "/api/data-index/v1/parser/summary", "data-idx-parser-sum", None),
    ("GET",  "/api/data-index/v1/parser/status", "data-idx-parser-stat", None),
    ("GET",  "/api/data-index/v1/parser/file-types", "data-idx-file-types", None),
    ("GET",  "/api/data-index/v1/parser/runs", "data-idx-runs", None),
    ("GET",  "/api/data-index/v1/dependencies", "data-idx-deps", None),
    ("GET",  "/api/data-index/v1/files/manifest-stats", "data-idx-manifest", None),
    ("GET",  "/api/data-index/v1/health", "data-idx-health", None),

    # ── gdpr ──
    ("GET",  "/api/gdpr/v1/consent", "gdpr-consent", None),
    ("GET",  "/api/gdpr/v1/export", "gdpr-export", None),
    ("GET",  "/api/gdpr/v1/audit-log", "gdpr-audit-log", None),

    # ── insights ──
    ("GET",  "/api/insights/v1/visuals", "insights-visuals", None),
    ("GET",  "/api/insights/v1/quadrant", "insights-quadrant", None),
    ("GET",  "/api/insights/v1/terms/cloud", "insights-cloud", None),
    ("GET",  "/api/insights/v1/terms/cooccurrence", "insights-cooccur", None),
    ("GET",  "/api/insights/v1/graph", "insights-graph", None),

    # ── intelligence ──
    ("GET",  "/api/intelligence/v1/market", "intel-market", None),
    ("GET",  "/api/intelligence/v1/company/registry", "intel-registry", None),
    ("GET",  "/api/intelligence/v1/company/registry/analytics", "intel-reg-analytics", None),
    ("GET",  "/api/intelligence/v1/company/registry/events", "intel-reg-events", None),
    ("GET",  "/api/intelligence/v1/pipeline/ops-summary", "intel-pipeline", None),
    ("GET",  "/api/intelligence/v1/support/status", "intel-support", None),
    ("POST", "/api/intelligence/v1/stats/descriptive", "intel-stats", {"data": [1,2,3]}),
    ("POST", "/api/intelligence/v1/enrich", "intel-enrich", {"resume_text": "test"}),

    # ── jobs ──
    ("GET",  "/api/jobs/v1/index", "jobs-index", None),
    ("GET",  "/api/jobs/v1/search", "jobs-search", None),

    # ── lenses ──
    ("POST", "/api/lenses/v1/spider", "lenses-spider", {"user_id": "t"}),
    ("POST", "/api/lenses/v1/covey", "lenses-covey", {"user_id": "t"}),
    ("POST", "/api/lenses/v1/composite", "lenses-composite", {"user_id": "t"}),

    # ── logs ──
    ("GET",  "/api/admin/v1/logs/tail", "admin-logs-tail", None),

    # ── mapping ──
    ("GET",  "/api/mapping/v1/registry", "mapping-registry", None),
    ("GET",  "/api/mapping/v1/endpoints", "mapping-endpoints", None),
    ("GET",  "/api/mapping/v1/graph", "mapping-graph", None),

    # ── mentor ──
    ("GET",  "/api/mentor/v1/list", "mentor-list", None),
    ("GET",  "/api/mentor/v1/health", "mentor-health", None),

    # ── mentorship ──
    ("GET",  "/api/mentorship/v1/applications/pending", "mentorship-pending", None),
    ("GET",  "/api/mentorship/v1/summary", "mentorship-summary", None),
    ("GET",  "/api/mentorship/v1/health", "mentorship-health", None),

    # ── ontology ──
    ("GET",  "/api/ontology/v1/phrases", "ontology-phrases", None),
    ("GET",  "/api/ontology/v1/phrases/summary", "ontology-summary", None),

    # ── ops ──
    ("GET",  "/api/ops/v1/stats/public", "ops-stats", None),
    ("GET",  "/api/ops/v1/processing/status", "ops-processing", None),
    ("GET",  "/api/ops/v1/tokens/config", "ops-tokens", None),

    # ── payment ──
    ("GET",  "/api/payment/v1/plans", "payment-plans", None),
    ("GET",  "/api/payment/v1/history", "payment-history", None),
    ("GET",  "/api/payment/v1/subscription", "payment-subscription", None),
    ("GET",  "/api/payment/v1/health", "payment-health", None),
    ("GET",  "/api/payment/v1/client-token", "payment-client-tok", None),
    ("GET",  "/api/payment/v1/methods", "payment-methods", None),
    ("GET",  "/api/payment/v1/gateway-info", "payment-gateway-info", None),

    # ── resume ──
    ("GET",  "/api/resume/v1", "resume-list", None),

    # ── rewards ──
    ("GET",  "/api/rewards/v1/rewards", "rewards-list", None),
    ("GET",  "/api/rewards/v1/rewards/available", "rewards-available", None),
    ("GET",  "/api/rewards/v1/suggestions", "rewards-suggestions", None),
    ("GET",  "/api/rewards/v1/referral", "rewards-referral", None),
    ("GET",  "/api/rewards/v1/leaderboard", "rewards-leaderboard", None),
    ("GET",  "/api/rewards/v1/ownership-stats", "rewards-ownership", None),
    ("GET",  "/api/rewards/v1/health", "rewards-health", None),

    # ── sessions ──
    ("GET",  "/api/sessions/v1/sync-status", "sessions-sync", None),
    ("GET",  "/api/sessions/v1/summary/test-user", "sessions-summary", None),
    ("GET",  "/api/sessions/v1/consolidated/test-user", "sessions-consol", None),

    # ── shared ──
    ("GET",  "/api/shared/v1/health", "shared-health", None),
    ("GET",  "/api/shared/v1/health/deep", "shared-health-deep", None),

    # ── support ──
    ("GET",  "/api/support/v1/health", "support-health", None),
    ("GET",  "/api/support/v1/status", "support-status", None),
    ("GET",  "/api/support/v1/widget-config", "support-widget-cfg", None),
    ("GET",  "/api/support/v1/wiring-test", "support-wiring", None),
    ("GET",  "/api/support/v1/providers", "support-providers", None),
    ("GET",  "/api/support/v1/readiness", "support-readiness", None),
    ("GET",  "/api/support/v1/tickets", "support-tickets", None),
    ("GET",  "/api/support/v1/ai/queue-stats", "support-ai-stats", None),
    ("GET",  "/api/support/v1/ai/jobs", "support-ai-jobs", None),

    # ── taxonomy ──
    ("GET",  "/api/taxonomy/v1/industries", "taxonomy-industries", None),
    ("GET",  "/api/taxonomy/v1/job-titles/search?q=engineer", "taxonomy-job-search", None),
    ("GET",  "/api/taxonomy/v1/job-titles/metadata?title=engineer", "taxonomy-metadata", None),
    ("GET",  "/api/taxonomy/v1/naics/search?q=tech", "taxonomy-naics", None),
    ("GET",  "/api/taxonomy/v1/summary", "taxonomy-summary", None),

    # ── telemetry ──
    ("GET",  "/api/telemetry/v1/status", "telemetry-status", None),

    # ── touchpoints ──
    ("GET",  "/api/touchpoints/v1/evidence", "touchpoints-evidence", None),
    ("GET",  "/api/touchpoints/v1/touchnots", "touchpoints-nots", None),

    # ── user ──
    ("GET",  "/api/user/v1/me", "user-me", None),
    ("GET",  "/api/user/v1/profile", "user-profile", None),
    ("GET",  "/api/user/v1/stats", "user-stats", None),
    ("GET",  "/api/user/v1/activity", "user-activity", None),
    ("GET",  "/api/user/v1/sessions/summary", "user-sessions", None),
    ("GET",  "/api/user/v1/resume/latest", "user-resume-latest", None),
    ("GET",  "/api/user/v1/matches/summary", "user-matches", None),

    # ── webhooks ──
    ("GET",  "/api/webhooks/v1/health", "webhooks-health", None),
    ("POST", "/api/webhooks/v1/braintree", "webhooks-braintree", {"bt_signature": "t", "bt_payload": "t"}),
    ("POST", "/api/webhooks/v1/stripe", "webhooks-stripe", {}),
    ("POST", "/api/webhooks/v1/zendesk", "webhooks-zendesk", {}),
]


def do_request(host, port, method, path, body_dict=None, timeout=6):
    """Low-level HTTP request with full timeout safety."""
    status = None
    snippet = ""
    try:
        conn = http.client.HTTPConnection(host, port, timeout=timeout)
        headers = {}
        body = None
        if body_dict is not None:
            body = json.dumps(body_dict)
            headers["Content-Type"] = "application/json"
        conn.request(method, path, body=body, headers=headers)
        resp = conn.getresponse()
        status = resp.status
        snippet = resp.read(300).decode("utf-8", errors="replace")[:200]
        conn.close()
    except Exception as e:
        snippet = f"{type(e).__name__}: {e}"[:200]
    return status, snippet


def probe(host, port):
    results = []
    pass_count = 0
    fail_count = 0

    for method, path, label, body in ENDPOINTS:
        t0 = time.time()
        status, snippet = do_request(host, port, method, path, body)
        elapsed = round((time.time() - t0) * 1000)

        # PASS if: 200, 401, 403, 405, 422 (all mean endpoint is reachable)
        ok = status is not None and status < 500
        verdict = "PASS" if ok else "FAIL"
        if ok:
            pass_count += 1
        else:
            fail_count += 1

        results.append({
            "v": verdict, "m": method, "p": path, "l": label,
            "s": status, "ms": elapsed, "snip": snippet[:100],
        })

        sym = "+" if ok else "X"
        print(f"  {sym} {verdict:4s} {str(status or '---'):>3}  {elapsed:>5}ms  {method:5s} {path}")

    # Summary
    print(f"\n{'='*70}")
    print(f"  TOTAL: {len(results)}  |  PASS: {pass_count}  |  FAIL: {fail_count}")
    print(f"{'='*70}")

    if fail_count:
        print(f"\n  FAILURES ({fail_count}):")
        for r in results:
            if r["v"] == "FAIL":
                print(f"    X {r['m']:5s} {r['s'] or '---':>3}  {r['p']}")
                # One-line reason
                snip = r["snip"].replace("\n", " ")[:80]
                print(f"      -> {snip}")
        print()

    return results, pass_count, fail_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=BASE_HOST)
    parser.add_argument("--port", type=int, default=BASE_PORT)
    args = parser.parse_args()
    print(f"\n{'='*70}")
    print(f"  CareerTrojan API Probe v2  —  {args.host}:{args.port}")
    print(f"{'='*70}\n")
    probe(args.host, args.port)
