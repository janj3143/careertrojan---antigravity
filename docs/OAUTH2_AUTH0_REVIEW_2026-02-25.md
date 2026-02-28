# OAuth2/Auth0 Runtime Review — 2026-02-25

## Summary Assessment
Current runtime is **partially aligned** with OAuth2 concepts but **not yet Auth0-integrated**.

- Uses bearer JWT auth internally (`/api/auth/v1/login`) with local credential verification.
- Has global API rate limiting middleware (100 req / 60s per IP by default).
- Does **not** currently validate Auth0-issued JWTs (issuer/audience/JWKS) for API access.
- Does **not** currently implement Auth0 Management API operations in runtime.

## What is already good
1. **Bearer token model exists**
   - Login endpoint returns bearer access token.
2. **Protected-route pattern exists**
   - Many routers depend on decoded JWT claims (`sub`, role checks).
3. **Rate limiting exists**
   - Middleware throttles requests and returns `429`.

## What was fixed in this pass
1. Fixed OAuth `tokenUrl` path mismatch to `/api/auth/v1/login`.
2. Moved JWT secret/algorithm/expiry to env-driven config (with fallback).
3. Added Auth0 env scaffolding in `.env.example`.

## Gaps vs your Auth0/OAuth2 notes
1. **No Auth0 JWT verification path**
   - Missing issuer/audience/JWKS validation for inbound access tokens.
2. **No dual-provider auth mode**
   - Need explicit `AUTH_PROVIDER=local|auth0` behavior in auth dependencies.
3. **No Auth0 management-plane automation**
   - Branding, anomaly protection, organizations, etc. are not required for runtime auth baseline and should be phased in.
4. **No endpoint-specific authz scopes**
   - Role checks exist, but OAuth2 scopes/claims policy is not centrally enforced.

## Essential vs optional from your list
### Essential now (runtime security baseline)
- Auth0 OIDC/OAuth2 token validation for API (`iss`, `aud`, signature via JWKS)
- Keep rate limiting enabled (already present)
- Strong secrets management and key rotation policy
- Scope/role-based authorization policy for sensitive endpoints

### Optional later (admin/tenant management)
- Branding/theme APIs
- Log streams, event streams
- Forms/flows/templates automation
- Most Auth0 Management API collections unless they support explicit product features

## Recommended implementation plan
1. Add `AUTH_PROVIDER` switch and central verifier module.
2. Implement Auth0 JWT verification path (JWKS caching + issuer/audience checks).
3. Update protected dependencies to accept local JWT (current) or Auth0 JWT (when enabled).
4. Add auth integration tests for both provider modes.
5. Add runbook for rotating secrets and monitoring auth failures.
