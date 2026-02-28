# Role Factorial Test Matrix

Date: 2026-02-24

## Purpose

Define deterministic role-journey permutations for Admin/User/Mentor acceptance and regression gates.

## Factors

- Role: `admin`, `user`, `mentor`
- Auth state: `authenticated`, `expired_token`
- Data state: `fresh_data`, `stale_data`, `missing_optional`
- API mode: `normal`, `latency_injected`, `expected_4xx`
- Workflow action: role-specific critical action

## Core Matrix

| Suite ID | Role | Workflow Action | Auth | Data | API Mode | Expected Result |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | admin | View dashboard snapshot | authenticated | fresh_data | normal | 2xx + populated summary payload |
| A2 | admin | Approve mentor application | authenticated | fresh_data | normal | 2xx + status transition to approved |
| A3 | admin | Reject mentor application | authenticated | fresh_data | normal | 2xx + status transition to rejected |
| A4 | admin | Access compliance/audit | expired_token | fresh_data | expected_4xx | 401/403 and no internal error |
| U1 | user | Login + dashboard load | authenticated | fresh_data | normal | 2xx + route loads + no schema break |
| U2 | user | Update profile | authenticated | missing_optional | normal | 2xx + persisted round-trip |
| U3 | user | Mentorship summary read | authenticated | stale_data | latency_injected | success within latency SLO |
| U4 | user | Access protected route | expired_token | fresh_data | expected_4xx | redirect/deny with expected status |
| M1 | mentor | Resolve profile by user | authenticated | fresh_data | normal | 2xx + mentor_profile_id returned |
| M2 | mentor | Load dashboard stats | authenticated | fresh_data | normal | 2xx + numeric stats fields present |
| M3 | mentor | Create package | authenticated | missing_optional | normal | 2xx/201 + package visible on list |
| M4 | mentor | Read invoices | authenticated | stale_data | latency_injected | success within latency SLO |
| X1 | cross-role | Admin action visible in Mentor/User view | authenticated | fresh_data | normal | state consistency across portals |
| X2 | cross-role | Unauthorized cross-role route access | authenticated | fresh_data | expected_4xx | strict role guard behavior |

## Minimum Execution Counts

- Per-suite minimum runs: 5
- Required pass rate per suite: >= 95%
- Critical suites (`A2`, `A3`, `U1`, `M1`, `M3`, `X1`, `X2`) pass rate: >= 99%

## Failure Classification

- P0: data corruption, auth bypass, cross-role privacy leak.
- P1: critical workflow blocked, incorrect status transition.
- P2: non-critical UI/API degradation with workaround.
- P3: cosmetic or low-severity inconsistency.

## Output Contract

Each suite execution must emit:

- `suite_id`
- `role`
- `request_id` / trace id
- `result` (`pass|fail`)
- `latency_ms`
- `error_class` (if fail)
- `created_at`

## Gate Rule

Release gate fails if:

- any critical suite falls below threshold,
- any P0/P1 is open,
- cross-role consistency suites (`X1`, `X2`) fail.
