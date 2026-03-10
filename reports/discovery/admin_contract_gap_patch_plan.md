# Admin Contract Gap Patch Plan

Date: 2026-03-10
Branch: runtime-env-oauth-lens-20260228

## Scope

This plan addresses unmatched or weakly matched admin frontend-to-backend contracts discovered in `discovery_output/frontend_api_calls.json` and `discovery_output/frontend_to_backend_matches.json`.

## First Fix Applied

1. Admin login payload contract alignment
- Frontend file: `apps/admin/src/pages/AdminLogin.tsx`
- Route: `POST /api/auth/v1/login`
- Issue: Frontend sent JSON body (`email` / `password`) while backend expects OAuth2 form fields (`username` / `password`) via `OAuth2PasswordRequestForm`.
- Fix: Switched request body to `application/x-www-form-urlencoded` with `username` and `password`.
- Expected outcome: login requests resolve against auth contract without payload-shape mismatch.

## Remaining Review Targets

1. `apps/admin/src/pages/AIEnrichment.tsx`
- Observed path: `/api/admin/v1/ai/enrichment/run`
- Discovery marked a GET mismatch for this path.
- Current code behavior is POST-only for execution call.
- Action: treat as parser/method-inference false positive unless runtime shows a GET caller.

2. `apps/admin/src/pages/APIIntegration.tsx`
- Observed path: `/api/admin/v1/integrations/reminders/non-live`
- Discovery marked a GET mismatch for this path.
- Current code behavior is POST-only for reminder call.
- Action: treat as parser/method-inference false positive unless runtime shows a GET caller.

3. Discovery matcher hardening
- Root cause candidate: static parser is inferring default GET for string path occurrences that are also used in POST calls.
- Action: update full wiring discovery method inference to tie endpoint strings to invocation context and explicit `method` override.

## Validation Checklist

1. Run `python scripts/e2e_golden_path.py`
2. Run `python scripts/e2e_braintree_test.py`
3. Run `python tools/discover_full_wiring.py .`
4. Re-check admin unmatched call count

## Exit Criteria

1. Admin login succeeds end-to-end with form-encoded credentials.
2. No true unmatched admin endpoints remain (excluding intentional placeholders).
3. Discovery output reflects method-accurate FE call classification.
