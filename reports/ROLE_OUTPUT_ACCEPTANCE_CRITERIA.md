# Role Output Acceptance Criteria

Date: 2026-02-24

## Purpose

Define release-blocking role outcome criteria for Admin, User, and Mentor journeys.

This report is the behavior-level companion to:

- `reports/ROLE_ROUTE_PARITY_BASELINE.md` (route structure)
- `reports/ENDPOINT_TOPOLOGY_MAP.md` (endpoint contract parity)
- `reports/GOVERNANCE_CONTROL_PLANE_EXECUTION_SPEC.md` (control-plane phases)

## Global Gate Rules

All role suites must satisfy these baseline conditions:

1. Endpoint contract parity: `unmatched=0` for Admin/User/Mentor.
2. Critical route load success: >= 99% for declared role routes.
3. Critical API success: >= 99% (2xx/expected 4xx only).
4. Schema-valid responses on critical APIs: >= 99%.
5. No P0/P1 errors in role journey logs.
6. No data-root path drift (`services.shared.paths` source of truth only).

## Admin Acceptance Criteria

### Admin required outcomes

- Can view platform snapshot/analytics and parser status surfaces.
- Can manage mentor application lifecycle (list, approve, reject).
- Can review email tracking summary and recent tracking events.
- Can access compliance/audit surfaces without contract failures.

### Admin critical evidence points

- API health:
  - `/api/admin/v1/dashboard/snapshot`
  - `/api/admin/v1/parsers/status`
  - `/api/analytics/v1/dashboard`
  - `/api/mentorship/v1/applications/pending`
  - `/api/mentorship/v1/applications/{application_id}/approve`
  - `/api/mentorship/v1/applications/{application_id}/reject`
  - `/api/ai-data/v1/emails/tracking/summary`
- UI routes:
  - `/admin`, `/admin/analytics`, `/admin/mentors`, `/admin/email`, `/admin/parser`

### Admin pass thresholds

- Admin critical API success rate >= 99%.
- Mentor app state transition success >= 95% in controlled test fixtures.
- Zero unresolved endpoint mismatches for Admin in topology report.

## User Acceptance Criteria

### User required outcomes

- Can authenticate and access dashboard/profile/resume/mentorship/payment routes.
- Can execute job-swipe and coaching/recommendation flows without schema failures.
- Can submit mentorship application intent and receive deterministic outcome states.

### User critical evidence points

- API health:
  - `/api/auth/v1/login`
  - `/api/user/v1/profile`
  - `/api/jobs/v1/index`
  - `/api/coaching/v1/sessions`
  - `/api/mentorship/v1/summary`
- UI routes:
  - `/dashboard`, `/profile`, `/resume`, `/jobs/swipe`, `/mentorship`, `/payment`

### User pass thresholds

- User critical API success rate >= 99%.
- Resume/profile save round-trip correctness >= 99%.
- Zero unresolved endpoint mismatches for User in topology report.

## Mentor Acceptance Criteria

### Mentor required outcomes

- Can resolve mentor profile from authenticated user.
- Can access dashboard/financials/packages with valid API responses.
- Can create/update package payloads and observe consistent persisted state.

### Mentor critical evidence points

- API health:
  - `/api/mentor/v1/profile-by-user/{user_id}`
  - `/api/mentor/v1/{mentor_profile_id}/dashboard-stats`
  - `/api/mentor/v1/{mentor_profile_id}/packages`
  - `/api/mentorship/v1/invoices/mentor/{mentor_id}`
- UI routes:
  - `/mentor/dashboard`, `/mentor/financials`, `/mentor/packages`

### Mentor pass thresholds

- Mentor critical API success rate >= 99%.
- Package create/read consistency >= 99% in fixture tests.
- Zero unresolved endpoint mismatches for Mentor in topology report.

## Cross-Role Consistency Gates

- Shared entity consistency:
  - Mentor application status reflects identically in Admin + Mentor surfaces.
  - Invoice status transitions are monotonic and role-consistent.
  - Email tracking outcomes are visible in Admin analytics without stale lag > 5 min.
- Identity/authorization gates:
  - Role-only routes reject unauthorized access with expected status.

## Release Decision Matrix

- PASS: all role thresholds satisfied, no P0/P1 defects, no parity mismatches.
- CONDITIONAL PASS: only documented non-critical waivers with owner+expiry.
- FAIL: any critical threshold miss or unresolved parity mismatch.

## Required Artifacts for Sign-Off

- `reports/ENDPOINT_TOPOLOGY_MAP.md`
- `reports/ENDPOINT_BRIDGE_TOUCHPOINT_MAP.md`
- `reports/ROLE_FACTORIAL_TEST_MATRIX.md`
- `data/governance/outcome_labels.jsonl`
- Runtime logs from passive harness + role journey suite execution
