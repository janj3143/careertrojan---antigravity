# Zendesk Production Wiring Checklist

## Goal
Enable production Zendesk support mode (replace stub mode) for the support APIs under `/api/support/v1`.

## 1) Environment Configuration
Set these variables in deployment environment (or `.env`):

Reference template: `.env.zendesk.template`

Helper command to merge missing keys into local `.env`:
- `pwsh -File scripts/setup_zendesk_env.ps1 -TemplatePath .env.zendesk.template -TargetPath .env`

- `HELPDESK_PROVIDER=zendesk`
- `HELPDESK_WIDGET_ENABLED=true`
- `HELPDESK_SSO_ENABLED=true`
- `ZENDESK_SHARED_SECRET=<secure secret>`
- `ZENDESK_SUBDOMAIN=<your_subdomain>` **or** `ZENDESK_BASE_URL=https://<your_subdomain>.zendesk.com`
- `HELPDESK_WIDGET_SCRIPT_URL=<zendesk widget snippet url>` or `ZENDESK_WIDGET_SCRIPT_URL=<...>`

Optional claim mappings:
- `ZENDESK_JWT_EMAIL_CLAIM=email`
- `ZENDESK_JWT_NAME_CLAIM=name`
- `ZENDESK_JWT_EXTERNAL_ID_CLAIM=external_id`

## 2) Backend Verification
Run these checks after deploy:

One-command check:
- `pwsh -File scripts/verify_zendesk_wiring.ps1 -BaseUrl http://localhost:8500 -Strict`

Deep verification (includes token + widget bootstrap checks):
- `pwsh -File scripts/verify_zendesk_wiring.ps1 -BaseUrl http://localhost:8500 -Strict -Deep`

The verifier now checks `GET /health` first and prints a backend startup command if the API is not running.

1. `GET /api/support/v1/providers`
   - Expect active provider: `zendesk`
2. `GET /api/support/v1/readiness`
   - Expect `ready: true`
   - Expect `missing: []`
3. `GET /api/support/v1/status`
   - Confirm `mode: zendesk`
   - Confirm readiness payload present
4. `POST /api/support/v1/token`
   - Verify a token is returned and accepted by Zendesk SSO flow
5. `GET /api/support/v1/widget-config?portal=user`
   - Verify widget bootstrap config contains Zendesk script/base URL

## 3) Portal/UI Validation
- Confirm `window.__CAREERTROJAN_HELPDESK__` bootstrap exists in each portal runtime.
- Open widget and verify authenticated user identity maps correctly.
- Confirm support queue and macro links resolve to Zendesk URLs.

## 4) Rollback Safety
- To rollback quickly, set `HELPDESK_PROVIDER=stub`.
- Re-check `/api/support/v1/readiness` and `/api/support/v1/status`.

## 5) Security Notes
- Never commit `ZENDESK_SHARED_SECRET` to source control.
- Rotate secret via environment management tooling.
- Keep SSO token TTL short for production sessions.
