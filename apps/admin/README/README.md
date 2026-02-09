# Token Management — Merged Best-of-Breed (Admin)

This bundle contains a single, canonical Streamlit page:

- `pages/10_token_management.py`

Key properties:
- **No demo data**
- **No fallback values**
- **Backend-only truth**
- **Hard contract enforcement**: missing keys/endpoints raise errors

## Expected backend endpoints

Set `ADMIN_API_BASE_URL` (e.g., `http://localhost:8000`).

The UI expects these JSON endpoints to exist:

- `GET  /admin/tokens/plans` → `{ "plans": { free|monthly|annual|elitepro: {...} } }`
- `POST /admin/tokens/plans` → `{ "plans": {...} }` (echo saved)
- `GET  /admin/tokens/usage` → `{ "orgs": [ ... ] }`
- `GET  /admin/tokens/subscriptions` → `{ "subscriptions": [ { "plan": ... }, ... ] }`
- `GET  /admin/tokens/ledger/{user_id}` → `{ "entries": [ ... ] }`
- `GET  /admin/tokens/costs` → `{ "costs": [ { "feature": "...", "tokens": 0, ... } ] }`
- `POST /admin/tokens/costs` → `{ "cost": { "feature": "...", "tokens": ... } }`
- `GET  /admin/tokens/logs?days=14` → `{ "logs": [ ... ] }`
- `GET  /admin/tokens/analytics?days=30` → `{ "kpis": {...}, "timeseries": [ ... ] }`
- `GET  /admin/health` → `{ "status": "ok", "contracts": [ ... ] }`

If your backend uses different paths/keys, align them (preferred) or adjust the client methods.

## Session requirements

Before opening the page, your Admin login flow must set:

- `st.session_state["admin_authenticated"] = True` (or `user_role="admin"`)
- `st.session_state["access_token"] = "<jwt>"`

