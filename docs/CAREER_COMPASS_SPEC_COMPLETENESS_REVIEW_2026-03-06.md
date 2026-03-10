# CareerTrojan Spec Completeness Review (2026-03-06)

## Scope Reviewed
- Source document: `l:\Spider - covey overlay and AI questioning.txt`
- Runtime backend implementation cross-check in:
  - `services/backend_api/routers/career_compass.py`
  - `services/backend_api/routers/coaching.py`
  - `services/backend_api/main.py`

## Executive Verdict
Your master spec is **strong and now materially complete for product strategy + architecture governance intent**.

No major product pillar is missing (purpose, live-data policy, profile coach behavior, vector model, market validation, mentor matching, wiring checklist, phases, and definition of done are all present).

The previously missing governance contract items have now been appended to the master spec in Section 15 (**Runtime Contract and Governance Appendix**).

Remaining gaps are now primarily **implementation parity gaps** (route coverage and runtime migration), not documentation gaps.

---

## Previously Missing / Now Addressed in Spec

Addressed in new Section 15.1 and 15.15:

- Canonical response envelope
- Canonical naming standards
- Version compatibility guidance

Addressed in Section 15.2.

Addressed in Section 15.3.

Addressed in Section 15.5.

Addressed in Section 15.4.

Addressed in Section 15.6.

Addressed in Section 15.7.

Addressed in Section 15.8.

Addressed in Section 15.9.

Addressed in Section 15.10.

Addressed in Section 15.11.

Addressed in Section 15.12.

Addressed in Section 15.13.

Addressed in Section 15.14.

---

## Cross-Check: Current Backend Coverage vs Spec Routes

### Implemented now (backend)
- Career Compass:
  - `/career-compass/map`
  - `/career-compass/cluster/{cluster_id}`
  - `/career-compass/spider-overlay`
  - `/career-compass/market-signal`
  - `/career-compass/runway`
  - `/career-compass/mentor-match`
- Profile Coach:
  - `/api/coaching/v1/profile/system-prompt`
  - `/api/coaching/v1/profile/config`
  - `/api/coaching/v1/profile/reflect`
  - `/api/coaching/v1/profile/cv-upload-step`
  - `/api/coaching/v1/profile/bridge-lockstep`

### Still missing vs your route list
- `/api/v1/profile-coach/start`
- `/api/v1/profile-coach/respond`
- `/api/v1/profile-coach/finish`
- `/api/v1/profile/build`
- `/api/v1/profile/signals`
- `/api/v1/user-vector/current`
- `/api/v1/career-compass/routes`
- `/api/v1/career-compass/culdesac-check`
- `/api/v1/career-compass/save-scenario`

### Notable naming mismatch
- Spec path family is mostly `/api/v1/...`
- Current implemented Career Compass prefix is `/career-compass`.

If intentional, document this as current-phase compatibility mode; otherwise define migration aliases.

---

## Remaining Work (Implementation Parity)
Documentation gaps are now closed; implementation gaps remain:

1. Add route parity for `/api/v1` path family (or stable aliases)
2. Implement missing endpoints (`routes`, `culdesac-check`, `save-scenario`, profile start/respond/finish parity)
3. Normalize runtime response fields to the canonical envelope in all relevant routers
4. Enforce status→HTTP mapping consistently in route handlers
5. Add contract/integration tests aligned to Section 15.12

---

## Final Conclusion
Your document now contains the missing governance elements and is ready for engineering execution with reduced ambiguity.

Next highest-value work is implementing route and envelope parity in code against the new Section 15 appendix.
