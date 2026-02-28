# Test Harness Execution Plan

**Date:** 2026-02-22 (Phase 10 — Launch Readiness)
**Author:** Build Agent (Session 11)

---

## 1. Overview

The CareerTrojan test harness is a three-tier pytest suite (unit → integration → e2e) that validates everything from individual class behaviour to full HTTP flows and a 20-item launch readiness checklist. This document describes the structure, how to run each tier, and how to integrate into CI.

---

## 2. Test Tiers

### Tier 1 — Unit Tests (`tests/unit/`)
| File | Coverage Focus | Approx Tests |
|---|---|---|
| `test_login_protection.py` | Per-IP brute-force lockout logic | 14 |
| `test_auth_roles.py` | JWT claims, admin guard, role matrix, token manipulation | 25 |
| `test_security.py` | bcrypt hashing, JWT encode/decode | ~10 |
| `test_rate_limiter.py` | In-memory sliding-window throttle | ~8 |
| *(existing unit files)* | ResumeAI, JD parser, skills matching, etc. | ~50 |

**Characteristics:** No database, no network, sub-second per test.

### Tier 2 — Integration Tests (`tests/integration/`)
| File | Coverage Focus | Approx Tests |
|---|---|---|
| `test_auth_endpoints.py` | Register/login/brute-force via TestClient + SQLite | 25 |
| `test_launch_checklist.py` | 20-item Phase 10 launch checklist | 40 |
| *(existing integration files)* | GDPR, mentorship, admin, payment routes | ~30 |

**Characteristics:** In-memory SQLite, Starlette TestClient, ~1s each.

### Tier 3 — End-to-End Tests (`tests/e2e/`)
| File | Coverage Focus | Approx Tests |
|---|---|---|
| *(existing e2e files)* | Upload → parse → enrich → match pipeline | ~15 |

**Characteristics:** May require Docker services; slower.

---

## 3. Running Tests

### 3a. Full Suite
```powershell
cd C:\careertrojan
.venv\Scripts\python -m pytest tests/ -v --tb=short
```

### 3b. Unit-Only (fastest — run first)
```powershell
.venv\Scripts\python -m pytest tests/unit/ -v -m unit
```

### 3c. Integration-Only (includes launch checklist)
```powershell
.venv\Scripts\python -m pytest tests/integration/ -v -m integration
```

### 3d. Launch Checklist Only
```powershell
.venv\Scripts\python -m pytest tests/integration/test_launch_checklist.py -v
```

### 3e. Auth & Security Harness Only
```powershell
.venv\Scripts\python -m pytest tests/unit/test_login_protection.py tests/unit/test_auth_roles.py tests/integration/test_auth_endpoints.py -v
```

### 3f. Skip Slow / Docker-Dependent
```powershell
.venv\Scripts\python -m pytest tests/ -v -k "not skip and not e2e"
```

---

## 4. Pytest Configuration

**`pytest.ini`** at project root:
```ini
[pytest]
testpaths = tests
markers =
    unit: fast isolated tests
    integration: tests using TestClient or DB
    e2e: end-to-end pipeline tests
```

**`conftest.py`** provides:
| Fixture | Scope | Purpose |
|---|---|---|
| `app` | session | FastAPI application instance |
| `test_client` | session | Starlette TestClient |
| `db_session` | function | In-memory SQLite session (auto-rollback) |
| `make_auth_headers()` | session | Factory: create Bearer headers for any role |
| `create_test_user()` | session | Factory: insert User row with hashed password |
| `user_headers` | session | Pre-built headers for role=user |
| `admin_headers` | session | Pre-built headers for role=admin |
| `mentor_headers` | session | Pre-built headers for role=mentor |
| `expired_headers` | session | Expired JWT for negative tests |

---

## 5. Auth & Role Test Matrix

### Roles Tested
| Role | JWT Claim | Can Access Admin | Can Access User | Can Access Mentor |
|---|---|---|---|---|
| `user` | `role: "user"` | ❌ 403 | ✅ | ❌ |
| `admin` | `role: "admin"` | ✅ | ✅ | ✅ |
| `mentor` | `role: "mentor"` | ❌ 403 | ❌ | ✅ |

### Auth Flows Tested
1. **Registration** — success, duplicate email, password not leaked
2. **Login** — per-role JWT issuance, wrong password, nonexistent user
3. **Brute-Force Lockout** — 5 failures → locked, correct password blocked during lockout, Retry-After header
4. **Token Attacks** — expired, empty bearer, garbage, missing role, role escalation
5. **Cross-Role Matrix** — parametrized: every admin endpoint × every role

---

## 6. Launch Checklist Items (Automated)

| # | Checklist Item | Status | Test Class |
|---|---|---|---|
| 1 | Phase 4 items closed | ✅ Automated | `TestChecklist01_Phase4Complete` |
| 2 | Endpoint count ≥ 170 | ✅ Automated | `TestChecklist02_EndpointCount` |
| 3 | Zero legacy callsites in React | ✅ Automated | `TestChecklist03_NoLegacyCallsites` |
| 4 | Contamination trap clean | ✅ Automated | `TestChecklist04_ContaminationTrap` |
| 5 | Data junction health | ✅ Automated | `TestChecklist05_JunctionHealth` |
| 6 | Docker Compose valid | ✅ Automated | `TestChecklist06_ComposeValid` |
| 7 | Test user can auth | ✅ Automated | `TestChecklist07_TestUserAuth` |
| 8 | Admin impersonation | ✅ Automated | `TestChecklist08_AdminImpersonation` |
| 9 | GDPR endpoints exist | ✅ Automated | `TestChecklist09_GDPR` |
| 10 | Braintree endpoint exists | ✅ Automated | `TestChecklist10_Braintree` |
| 11 | Logo asset path exists | ✅ Automated | `TestChecklist11_Logo` |
| 12 | Zero "Intellicv-AI" in live code | ✅ Automated | `TestChecklist12_NoBrandLeak` |
| 13 | Test suite ≥ 136 tests | ✅ Automated | `TestChecklist13_TestSuite` |
| 14 | Phase 8 cleanup done | ✅ Automated | `TestChecklist14_Cleanup` |
| 15-20 | Zendesk helpdesk items | ⏳ Skipped | `TestChecklist15to20_Helpdesk` |
| — | Phase 9 hardening artefacts | ✅ Automated | `TestPhase9_Hardening` |

---

## 7. CI / Pre-Deploy Integration

### GitHub Actions (recommended)
```yaml
name: Test Harness
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements-dev.txt
      - run: pytest tests/ -v --tb=short -k "not e2e and not skip"
```

### Pre-Deploy Gate
Before deploying to staging/production, run:
```powershell
.venv\Scripts\python -m pytest tests/ -v --tb=short -k "not skip" --strict-markers
```
**All tests must pass.** Any failure blocks deployment.

---

## 8. Adding New Tests

1. Place unit tests in `tests/unit/test_*.py`, integration in `tests/integration/test_*.py`
2. Decorate with `@pytest.mark.unit` or `@pytest.mark.integration`
3. Use `conftest.py` fixtures (`test_client`, `admin_headers`, etc.) — do NOT create standalone clients
4. For role tests, use the parametrized pattern in `test_auth_roles.py::TestEndpointRoleMatrix`
5. Run `pytest --collect-only` to verify discovery before committing

---

## 9. Known Limitations

- **E2E tests** require a running Docker Compose stack and are not part of the fast CI loop
- **Braintree sandbox tests** verify the endpoint exists but POST flows require sandbox credentials
- **Logo directory test** only runs when the L: drive is mounted
- **Zendesk tests** are stubbed pending Phase 7b implementation
- **Test DB is SQLite** — some Postgres-specific behaviour (e.g., `SERIAL`, `JSONB`) is not exercised at the unit/integration level
