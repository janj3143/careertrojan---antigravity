# CareerTrojan Agent Rules

These rules apply to any autonomous coding/testing agent operating in this repository.

## Core Safety
- Never commit or print secrets from `.env`, cloud credentials, API tokens, or private keys.
- Never disable auth, signature verification, or payment/webhook safety checks to make tests pass.
- Never change production URLs, domains, or webhook secrets without explicit operator instruction.

## Data & Runtime Integrity
- No mock/demo fallback in production runtime paths unless explicitly flagged as test-only.
- Preserve real integration pathways (Zendesk, Braintree, Stripe, AI queues) and validate wiring.
- Keep idempotency and audit traces intact for payment and support event processing.

## Change Discipline
- Prefer small, reversible patches.
- Fix root cause where possible; avoid broad unrelated refactors.
- Update docs/tasks when introducing new test or run pathways.

## Testing Requirements
- For backend changes, run at minimum: unit tests and integration tests.
- For orchestration/infrastructure changes, run `scripts/full_harness.ps1` when feasible.
- For performance/load changes, include a reproducible `k6` command and expected thresholds.

## Evidence Requirements
- Always report:
  - files changed,
  - commands executed,
  - test results,
  - any known limitations/blockers.

## Role Test Expectations
- Validate at least one scenario per role when relevant:
  - user
  - admin
  - mentor
