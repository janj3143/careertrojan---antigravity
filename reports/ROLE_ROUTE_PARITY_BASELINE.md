# Role Route Parity Baseline

Date: 2026-02-24

## Route Declaration Snapshot
- Admin route declarations: 76
- User route declarations: 20
- Mentor route declarations: 14

Sources:
- `apps/admin/src/App.tsx`
- `apps/user/src/App.tsx`
- `apps/mentor/src/App.tsx`

## Page-Order Reference Packs
- `Archive Scripts/pages order/Admin Pages Order`
- `Archive Scripts/pages order/User Pages Order`
- `Archive Scripts/pages order/Mentor Pages Order`

## Baseline Notes
- Admin has broad route surface (main + tools + ops), and requires explicit parity mapping against legacy ordering semantics.
- User and Mentor route surfaces are smaller but still require role-outcome acceptance checks, not only route existence checks.
- This baseline is structural only (route declarations); behavioral parity and endpoint parity are covered in governance spec phases.

## Next Required Artifacts
- `reports/ROLE_PAGE_ORDER_PARITY_MATRIX.md`
- `reports/ROLE_OUTPUT_ACCEPTANCE_CRITERIA.md`
- `reports/ROLE_FACTORIAL_TEST_MATRIX.md`
