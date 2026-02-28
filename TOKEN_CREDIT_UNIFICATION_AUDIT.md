# CareerTrojan Token/Credit Management — Comprehensive Audit & Unification Plan

**Date:** February 25, 2026  
**Author:** System Audit  
**Status:** AUDIT COMPLETE — Action Required

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Three Existing Systems](#2-the-three-existing-systems)
3. [Side-by-Side Tier Comparison](#3-side-by-side-tier-comparison)
4. [Braintree Integration Status](#4-braintree-integration-status)
5. [Database Persistence Status](#5-database-persistence-status)
6. [Frontend Credit Display Status](#6-frontend-credit-display-status)
7. [Detailed Unification Plan](#7-detailed-unification-plan)
8. [Canonical System Recommendation](#8-canonical-system-recommendation)

---

## 1. Executive Summary

CareerTrojan has **THREE independent, incompatible** token/credit systems that evolved separately over time. None of them are fully wired end-to-end. This creates a critical gap: **users can pay via Braintree, but no credits are allocated as a result, and the frontend shows no balance.**

| System | Location | Currency Unit | Storage | Connected to Payments? | Connected to Frontend? |
|--------|----------|--------------|---------|----------------------|----------------------|
| **System A: Legacy Streamlit Tokens** | `apps/user/token_management_system.py` | "Tokens" (page-based) | `st.session_state` (RAM only) | ❌ No | Partially (Streamlit sidebar) |
| **System B: Payment Router** | `services/backend_api/routers/payment.py` | "token_limit" + "ai_calls_per_month" | Python dicts (RAM only) | ✅ Yes (Braintree) | ✅ Yes (PaymentPage.tsx) |
| **System C: Unified Credit System** | `services/backend_api/services/credit_system.py` + `routers/credits.py` | "Credits" (action-based) | Python dicts (RAM only) | ❌ No | ❌ No |

**Critical Finding:** All three systems store data in-memory only. A server restart loses all balances, subscriptions, and usage history.

---

## 2. The Three Existing Systems

### System A — Legacy Streamlit Token Management
**File:** `apps/user/token_management_system.py` (472 lines)  
**Created:** October 23, 2025  
**Architecture:** Streamlit-native, `st.session_state` storage

#### Tier Definitions (Plan → Token Allocation)
| Plan | Monthly Tokens |
|------|---------------|
| Free | 10 |
| Monthly | 100 |
| Annual | 250 |
| Enterprise | 1,000 |

#### Currency Model: **Page-based tokens**
Each Streamlit page has a fixed token cost (0–30 tokens per page visit):

| Tier | Cost Range | Examples |
|------|-----------|----------|
| Free (0 tokens) | 0 | Home, Welcome, Registration, Dashboard, Payment, Pricing |
| Basic (1-2) | 1–2 | Profile, Application Tracker, Resume History, Word Cloud |
| Standard (3-5) | 3–5 | Resume Upload, Job Match, Resume Tuner, Resume Diff |
| Advanced (6-10) | 7–10 | Enhanced AI Resume, AI Interview Coach, Career Intelligence |
| Premium (11-20) | 12–15 | Advanced Career Tools, AI Career Intelligence Enhanced |
| Enterprise (21-50) | 25–30 | Mentorship Hub, Mentorship Marketplace |

#### Key Properties
- Tokens are consumed per **page visit**, not per action
- Token balance stored in `st.session_state['user_token_balance']`
- Usage log stored in `st.session_state['token_usage_log']`
- Admin sync is stubbed (`_sync_to_admin_portal` is a TODO)
- 45 distinct pages with assigned costs
- No database persistence whatsoever
- No connection to payment system
- **Status: LEGACY — superseded by React frontend migration**

---

### System B — Payment Router (Braintree-connected)
**File:** `services/backend_api/routers/payment.py` (589 lines)  
**Created:** February 2, 2026 (Updated February 9 for Braintree)  
**Architecture:** FastAPI REST router, in-memory dicts

#### Tier Definitions
| Plan | Price | Token Limit | AI Calls/Month |
|------|-------|-------------|----------------|
| Free Trial | $0 | 50 | 5 |
| Monthly Pro | $15.99/mo | 500 | 100 |
| Annual Pro | $149.99/yr | 1,000 | 200 |
| Elite Pro | $299.99/yr | 5,000 | 500 |

#### Currency Model: **Dual currency** — "token_limit" + "ai_calls_per_month"
- `token_limit`: Generic resource budget (50–5,000)
- `ai_calls_per_month`: Separate AI operation counter (5–500)
- These two metrics are defined but **never enforced**. No code consumes or checks them.

#### Key Properties
- Full Braintree integration (client token, Drop-in UI, sale, refund, vault)
- In-memory storage: `_user_subscriptions` and `_payment_history` dicts
- Promo codes: LAUNCH20 (20% off), CAREER10 (10% off)
- Subscription lifecycle: create, cancel, history
- Payment processing works end-to-end with Braintree sandbox
- **But:** After payment succeeds, tokens are NOT allocated to any balance system
- API prefix: `/api/payment/v1`
- **Status: ACTIVE — the only system connected to real payments**

---

### System C — Unified Credit System (The Spec / Target System)
**File:** `services/backend_api/services/credit_system.py` (769 lines) + `routers/credits.py` (355 lines)  
**Created:** February 2, 2026  
**Architecture:** FastAPI service + router, in-memory CreditManager class

#### Tier Definitions
| Plan | Credits/Month | Price Monthly | Price Yearly | Max Applications | Max Coaching |
|------|--------------|---------------|-------------|-----------------|--------------|
| Free Trial | 15 | $0 | — | 0 | 0 |
| Monthly Pro | 150 | $15.99 | — | 20 | 3 |
| Annual Pro | 350 | $12.49 eff. | $149.99 | 35 | 10 |
| Elite Pro | 500 | $24.99 eff. | $299.99 | 999 | 999 |

#### Currency Model: **Single credit currency** — action-based costs
Target: Monthly Pro user can afford ~20 full job applications/month  
(20 apps × 7 credits avg = 140 credits, leaving 10 for extras)

##### Action Costs (Complete List)
| Action | Credits | Notes |
|--------|---------|-------|
| **Free Actions** | | |
| Login, Dashboard, Profile View/Update | 0 | Always free |
| Job Search, Job View | 0 | Hook — show value |
| Resume Upload, Resume View | 0 | The entry hook |
| **Career Analysis** | | |
| Career Analysis Preview | 5 | Free tier can afford once |
| Career Analysis Full | 10 | Requires Monthly+ |
| **Visualizations** | | |
| Keyword Overlap Visual | 1 | |
| Job Suitability Gauge | 1 | |
| Connected Word Cloud | 2 | |
| Multi-Job Compare | 2 | |
| **Job Application Workflow** (7 credits/app) | | |
| Fit Analysis Preview | 5 | Free tier can see ONE |
| Fit Analysis Full | 2 | Per job |
| Blocker Detection Preview | 5 | Shows count only |
| Blocker Detection Full | 2 | Per job |
| Resume Tuning Preview | 0 | Free preview (blurred) |
| Resume Tuning Full | 3 | Per job — most valuable |
| **Application Tracking** | | |
| Track Application | 0 | Free to track (Monthly+ required) |
| Update Application Status | 0 | Free (Monthly+ required) |
| **Coaching** | | |
| AI Coaching Session | 8 | Monthly+ |
| Interview Questions | 3 | Monthly+ |
| STAR Story Builder | 5 | Monthly+ |
| **Mentorship** | | |
| Search Mentors | 0 | Free to browse |
| Contact Mentor | 15 | Annual+ |
| Mentorship Session | 25 | Annual+ |
| **Premium** | | |
| Dual Career Analysis | 15 | Annual+ |
| Career Intelligence Report | 20 | Annual+ |
| Geo Career Analysis | 10 | Monthly+ |

#### Feature Flags Per Plan
| Feature | Free | Monthly | Annual | Elite |
|---------|------|---------|--------|-------|
| Full Career Analysis | ❌ Preview | ✅ | ✅ | ✅ |
| Full Job Applications | ❌ | ✅ | ✅ | ✅ |
| Resume Tuning | ❌ Preview | ✅ | ✅ | ✅ |
| Blocker Detection | ❌ Preview | ✅ | ✅ | ✅ |
| Coaching Access | ❌ | ✅ | ✅ | ✅ |
| Mentorship Access | ❌ | ❌ | ✅ Basic | ✅ Full |
| Dual Career | ❌ | ❌ | ✅ | ✅ |
| API Access | ❌ | ❌ | ❌ | ✅ |
| Max Resumes Stored | 1 | 5 | 10 | 50 |

#### Free Tier Teaser System
System C includes sophisticated teaser templates for free users:
- Job Search: Shows match count but not details
- Fit Analysis: Shows score with blurred details
- Blocker Detection: Shows count with severity hidden
- Resume Tuning: Shows sample with content obscured

#### Key Properties
- Most complete design: single-currency, action-gated, preview/teaser system
- `CreditManager` class with full `can_perform_action()` → `consume_credits()` flow
- `CreditAction` enum for type-safe action references
- API prefix: `/api/credits/v1`
- Endpoints: plans, actions, balance, can-perform, consume, usage, teaser, upgrade
- **But:** `_get_user_id()` always raises 401 (auth not wired)
- **But:** In-memory only (`self._user_credits: Dict[str, UserCredits] = {}`)
- **But:** `upgrade_plan` endpoint exists but has no payment connection
- Credits router IS mounted in `main.py` (line 88: `app.include_router(credits.router)`)
- **Status: DESIGNED BUT DISCONNECTED — needs DB + auth + payment wiring**

---

## 3. Side-by-Side Tier Comparison

### Pricing (All Three Systems)
| Tier | System A (Legacy) | System B (Payment) | System C (Credits) |
|------|------------------|-------------------|-------------------|
| Free | $0 | $0 | $0 |
| Monthly | _(implied)_ | $15.99/mo | $15.99/mo |
| Annual | _(implied)_ | $149.99/yr | $149.99/yr ($12.49 eff/mo) |
| Elite/Enterprise | _(implied)_ | $299.99/yr | $299.99/yr ($24.99 eff/mo) |

**Prices are consistent across B and C.** ✅

### Credit/Token Allocations (Wildly Different)
| Tier | System A (Tokens) | System B (token_limit) | System B (ai_calls) | System C (Credits) |
|------|------------------|----------------------|--------------------|--------------------|
| Free | 10 | 50 | 5 | 15 |
| Monthly | 100 | 500 | 100 | 150 |
| Annual | 250 | 1,000 | 200 | 350 |
| Elite | 1,000 | 5,000 | 500 | 500 |

**These numbers are completely incompatible.** System A and B use arbitrary large numbers; System C uses carefully calculated credits tied to real action costs (7 credits ≈ 1 job application).

### Enum Values
| System | Free | Monthly | Annual | Elite |
|--------|------|---------|--------|-------|
| System A | 'free' | 'monthly' | 'annual' | 'enterprise' |
| System B | 'free' | 'monthly' | 'annual' | 'elitepro' |
| System C | 'free' | 'monthly' | 'annual' | 'elite' |

**Elite tier ID is different across all three ("enterprise" vs "elitepro" vs "elite").**

---

## 4. Braintree Integration Status

### What Works
**File:** `services/backend_api/services/braintree_service.py` (384 lines)

The Braintree integration is **fully implemented and functional**:
- ✅ Gateway configuration (sandbox ↔ production via env var)
- ✅ Client token generation (for Drop-in UI)
- ✅ Customer management (find_or_create_customer)
- ✅ Payment method vaulting (cards, PayPal)
- ✅ One-off sales (create_sale)
- ✅ Subscription management (create, cancel, find)
- ✅ Transaction management (find, void, refund)
- ✅ Plan mapping via env vars (`BRAINTREE_PLAN_MONTHLY`, `BRAINTREE_PLAN_ANNUAL`, `BRAINTREE_PLAN_ELITE`)

### What's Missing (The Gap)
The payment router processes payments successfully but **stops there**:

```
User clicks "Pay" → Braintree charges card → payment_result returned → subscription stored in RAM dict → DONE
                                                                                                        ↓
                                                                              NO credits allocated
                                                                              NO DB record created  
                                                                              NO credit_system.set_user_plan() called
```

**There is no bridge between `payment.py` and `credit_system.py`.** The payment router stores subscriptions in `_user_subscriptions` (an in-memory dict), and the credit system stores credits in `_user_credits` (a different in-memory dict). They don't talk to each other.

### Payment Router → Credit System Integration (Code That Should Exist But Doesn't)
In `payment.py` line ~325 (after successful payment), this code is needed but missing:

```python
# THIS DOES NOT EXIST YET:
from services.backend_api.services.credit_system import get_credit_manager, PlanTier
manager = get_credit_manager()
manager.set_user_plan(user_id, PlanTier(payload.plan_id))
```

---

## 5. Database Persistence Status

### Current State: ALL THREE SYSTEMS ARE MEMORY-ONLY ❌

| System | Storage Mechanism | Survives Restart? |
|--------|------------------|-------------------|
| System A (Streamlit) | `st.session_state` | ❌ No — per-browser-tab RAM |
| System B (Payment) | `_user_subscriptions: Dict` + `_payment_history: Dict` | ❌ No — process RAM |
| System C (Credits) | `CreditManager._user_credits: Dict` | ❌ No — process RAM |

### Database Models That DO Exist (But Aren't Used)
**File:** `services/backend_api/db/models.py` contains:

1. **`Subscription`** model — tracks plan, gateway subscription ID, status, billing dates
2. **`PaymentTransaction`** model — tracks gateway transaction ID, amount, status

These SQLAlchemy models are defined but **never imported or used** by `payment.py` or `credit_system.py`.

### Database Models That DON'T Exist Yet
There is **no** `UserCreditBalance` or `CreditUsageLog` SQLAlchemy model. The credit system's `UserCredits` dataclass and usage history have no DB backing.

---

## 6. Frontend Credit Display Status

### User Dashboard (`apps/user/src/pages/Dashboard.tsx`)
**Status: NO credit/token display** ❌

The Dashboard is a simple grid of navigation links (Payment, Verification, Profile, Resume, UMarketU, Coaching, Mentorship, Dual Career, Rewards). It shows **zero** information about the user's credit balance, plan, or usage.

### Payment Page (`apps/user/src/pages/PaymentPage.tsx`)
**Status: Functional for purchasing, no credit display** ⚠️

- Fetches plans from `/api/payment/v1/plans` (System B)
- Shows plan cards with prices and features
- Integrates Braintree Drop-in UI for card/PayPal
- Supports saved payment methods and promo codes
- Shows sandbox indicator
- **Does NOT display** current credit balance or usage
- **Does NOT call** `/api/credits/v1/balance` at any point

### Admin Token Management (`apps/admin/src/pages/TokenManagement.tsx`)
**Status: UI exists, fetches from non-existent endpoints** ⚠️

- Fetches from `/api/admin/v1/tokens/config` and `/api/admin/v1/tokens/usage`
- These endpoints return from `admin_tokens` router (a stubs file)
- Shows: Total Allocated, Total Used, Remaining, This Month
- Shows Credit Plans with credits_per_month, price_monthly, price_annual
- Displays in GBP (£) — inconsistent with USD ($) in payment system

### Summary: No User-Facing Credit Balance
**The user has no way to see how many credits they have, what they've used, or what actions cost.** The entire credit display pipeline is missing from the React frontend.

---

## 7. Detailed Unification Plan

### Phase 1: Database Models (Foundation)

#### 1.1 Add Credit Balance Model to `services/backend_api/db/models.py`

```python
class UserCreditBalance(Base):
    """Persistent credit balance per user, per billing period."""
    __tablename__ = "user_credit_balances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_tier = Column(String, nullable=False, default="free")  # free, monthly, annual, elite
    credits_total = Column(Integer, nullable=False, default=15)
    credits_remaining = Column(Integer, nullable=False, default=15)
    credits_used = Column(Integer, nullable=False, default=0)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="credit_balance")
```

#### 1.2 Add Credit Usage Log Model

```python
class CreditUsageLog(Base):
    """Immutable log of every credit consumption."""
    __tablename__ = "credit_usage_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action_id = Column(String, nullable=False, index=True)
    action_name = Column(String)
    credits_consumed = Column(Integer, nullable=False)
    credits_remaining_after = Column(Integer, nullable=False)
    is_preview = Column(Boolean, default=False)
    context_json = Column(Text, nullable=True)  # JSON blob
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", backref="credit_usage")
```

#### 1.3 Create Alembic Migration
```bash
alembic revision --autogenerate -m "add_credit_balance_and_usage_tables"
alembic upgrade head
```

---

### Phase 2: Unify Credit System Backend

#### 2.1 Refactor `credit_system.py` to Use DB

Replace `CreditManager._user_credits` dict with SQLAlchemy queries:

- `get_user_credits(user_id)` → `SELECT FROM user_credit_balances WHERE user_id = ?`
- `set_user_plan(user_id, plan)` → `UPDATE/INSERT user_credit_balances`
- `consume_credits(user_id, action, ...)` → `UPDATE credits_remaining` + `INSERT credit_usage_log`
- Add `reset_monthly_credits(user_id)` for billing cycle reset

#### 2.2 Standardize Elite Tier Enum

All systems must use `"elite"` (matching System C, the canonical spec):

| File | Change |
|------|--------|
| `payment.py` | `PlanTier.ELITE = "elitepro"` → `PlanTier.ELITE = "elite"` |
| `payment.py` | `PLANS["elitepro"]` → `PLANS["elite"]` |
| `braintree_service.py` | `BRAINTREE_PLAN_MAP["elitepro"]` → `BRAINTREE_PLAN_MAP["elite"]` |
| `PaymentPage.tsx` | Plan card styling for `'elitepro'` → `'elite'` |

#### 2.3 Align Token/Credit Numbers to System C Values

Replace System B's `PLANS` dict to use System C's credit values:

```python
# payment.py — REPLACE token_limit and ai_calls_per_month with credits_per_month
PLANS = {
    "free":    { ..., "credits_per_month": 15,  ... },
    "monthly": { ..., "credits_per_month": 150, ... },
    "annual":  { ..., "credits_per_month": 350, ... },
    "elite":   { ..., "credits_per_month": 500, ... },
}
```

Remove `token_limit` and `ai_calls_per_month` from payment.py — these should come from `credit_system.py` only.

---

### Phase 3: Wire Payment → Credits

#### 3.1 After Successful Payment, Allocate Credits

In `payment.py`, after the Braintree sale succeeds and subscription is stored, add:

```python
# After payment_result["success"] check:
from services.backend_api.services.credit_system import get_credit_manager, PlanTier as CreditPlanTier

credit_mgr = get_credit_manager()
credit_mgr.set_user_plan(user_id, CreditPlanTier(payload.plan_id))
logger.info(f"Credits allocated for {user_id} on plan {payload.plan_id}")
```

#### 3.2 Persist Subscription to Database

Replace in-memory dict with DB:

```python
# Instead of: _user_subscriptions[user_id] = {...}
# Use:
from services.backend_api.db.models import Subscription, PaymentTransaction
from services.backend_api.db.session import get_db

db = next(get_db())
subscription = Subscription(
    user_id=int(user_id),
    plan_id=payload.plan_id,
    gateway="braintree",
    gateway_subscription_id=subscription_id,
    gateway_customer_id=user_id,
    amount=final_amount,
    currency="USD",
    interval=plan["interval"],
    status="active",
    next_billing_date=next_billing,
)
db.add(subscription)
db.commit()
```

#### 3.3 Add Webhook Handler for Braintree Events

```python
# In webhooks.py or payment.py:
@router.post("/webhooks/braintree")
async def braintree_webhook(request: Request):
    """Handle subscription lifecycle events from Braintree."""
    # subscription_charged_successfully → reset monthly credits
    # subscription_canceled → downgrade to free
    # subscription_expired → downgrade to free
    # subscription_went_past_due → flag account
```

---

### Phase 4: Wire Auth to Credits Router

#### 4.1 Replace `_get_user_id()` Stub in `credits.py`

```python
from services.backend_api.routers.auth import get_current_user

def _get_user_id(current_user = Depends(get_current_user)) -> str:
    return str(current_user.id)
```

Apply same fix to `payment.py`'s `_get_user_id_from_token()`.

---

### Phase 5: Frontend Integration

#### 5.1 Add Credit Balance to Dashboard

`apps/user/src/pages/Dashboard.tsx`:

```tsx
// Fetch credit balance on mount
const [balance, setBalance] = useState(null);
useEffect(() => {
    fetch(`${API.credits}/balance`, { headers: authHeaders })
        .then(res => res.json())
        .then(setBalance);
}, []);

// Display credit widget
<CreditBalanceWidget
    plan={balance?.plan_name}
    remaining={balance?.credits_remaining}
    total={balance?.credits_total}
    usagePercent={balance?.usage_percentage}
/>
```

#### 5.2 Add Credit Cost Pre-check to Feature Pages

Before any credit-gated action:

```tsx
const canPerform = await fetch(`${API.credits}/can-perform/${actionId}`);
if (!canPerform.can_perform) {
    showUpgradeModal(canPerform.upgrade_info);
    return;
}
```

#### 5.3 Create `CreditBalanceWidget` Component

A reusable widget showing:
- Current plan name
- Credit bar (used / total)
- Percentage used
- "Upgrade" button if on free/monthly

#### 5.4 Update PaymentPage to Show Current Balance

After plan selection, display: "Your current plan: X — Y credits remaining"

---

### Phase 6: Remove Legacy System

#### 6.1 Deprecate `apps/user/token_management_system.py`

This file is Streamlit-native and no longer relevant for the React frontend. Steps:
1. Add deprecation warning at module import
2. Ensure no remaining Streamlit pages import it
3. Move to `_archive/` or delete after full migration

#### 6.2 Remove Dual-Currency from Payment Router

Remove `token_limit` and `ai_calls_per_month` from `payment.py`'s `PLANS` dict and `PlanOut` model. Replace with a reference to credit_system's plan config.

#### 6.3 Single Source of Truth for Plans

Create `services/backend_api/services/plan_config.py`:

```python
"""Single source of truth for plan definitions.
Both payment.py and credit_system.py import from here."""

PLAN_DEFINITIONS = {
    "free": PlanConfig(tier="free", credits=15, price=0, ...),
    "monthly": PlanConfig(tier="monthly", credits=150, price=15.99, ...),
    "annual": PlanConfig(tier="annual", credits=350, price=149.99, ...),
    "elite": PlanConfig(tier="elite", credits=500, price=299.99, ...),
}
```

---

### Phase 7: Admin Integration

#### 7.1 Wire Admin Token Management to Real Data

Replace stub endpoints that `TokenManagement.tsx` calls:
- `/api/admin/v1/tokens/config` → reads from `PLANS` in credit_system
- `/api/admin/v1/tokens/usage` → aggregates from `credit_usage_log` table
- Fix currency display: `£` → `$` (or make configurable)

#### 7.2 Add Admin Credit Override

```python
@router.post("/admin/credits/override")
async def admin_credit_override(user_id: int, credits: int, reason: str):
    """Admin can manually adjust a user's credit balance."""
```

---

## 8. Canonical System Recommendation

### **System C (`credit_system.py` + `credits.py`) is the canonical system.**

Rationale:

| Criterion | Winner | Why |
|-----------|--------|-----|
| Design completeness | System C | Action-based costs, preview/teaser system, feature flags, upgrade prompts |
| Business alignment | System C | Credits calibrated to real usage (20 apps/month = 140 credits on Monthly Pro) |
| Single currency | System C | One credit system vs dual token_limit + ai_calls |
| Free-to-paid conversion | System C | Sophisticated teaser system with blurred previews |
| Plan gating | System C | `requires_plan` per action with graduated access |
| Code quality | System C | Clean dataclasses, type-safe enums, manager pattern |
| Extensibility | System C | Easy to add new actions with cost definitions |

### What to Keep from Other Systems

| From System A (Legacy) | Keep? | Notes |
|------------------------|-------|-------|
| Page-cost mapping | ❌ No | Replaced by action-based costs in System C |
| Admin sync concept | ✅ Yes | Implement properly via DB + admin API |
| Usage analytics dashboard | ✅ Yes | Port to React component |

| From System B (Payment) | Keep? | Notes |
|-------------------------|-------|-------|
| Braintree integration | ✅ Yes | This is the payment backbone |
| Plan pricing ($15.99, $149.99, $299.99) | ✅ Yes | Already consistent with System C |
| Promo code system | ✅ Yes | LAUNCH20, CAREER10 |
| Payment method vault | ✅ Yes | Cards + PayPal |
| Drop-in UI frontend | ✅ Yes | PaymentPage.tsx works |

---

## Implementation Priority & Effort Estimate

| Phase | Description | Effort | Priority |
|-------|-------------|--------|----------|
| Phase 1 | DB Models + Migration | 4 hrs | 🔴 Critical |
| Phase 2 | Unify Backend (enums, numbers, DB queries) | 8 hrs | 🔴 Critical |
| Phase 3 | Wire Payment → Credits | 4 hrs | 🔴 Critical |
| Phase 4 | Wire Auth → Credits | 2 hrs | 🔴 Critical |
| Phase 5 | Frontend Balance Display | 6 hrs | 🟠 High |
| Phase 6 | Remove Legacy + Single Source of Truth | 4 hrs | 🟡 Medium |
| Phase 7 | Admin Integration | 4 hrs | 🟡 Medium |
| **Total** | | **~32 hrs** | |

---

## Files Involved (Complete List)

| File | Action |
|------|--------|
| `services/backend_api/db/models.py` | ADD `UserCreditBalance`, `CreditUsageLog` |
| `services/backend_api/services/credit_system.py` | REFACTOR to use DB instead of in-memory dict |
| `services/backend_api/routers/credits.py` | FIX `_get_user_id()` to use auth dependency |
| `services/backend_api/routers/payment.py` | WIRE to credit_system after payment; fix elite enum; remove dual currency |
| `services/backend_api/services/braintree_service.py` | FIX elite plan mapping key |
| `apps/user/src/pages/Dashboard.tsx` | ADD credit balance widget |
| `apps/user/src/pages/PaymentPage.tsx` | ADD current balance display; fix elite ID |
| `apps/admin/src/pages/TokenManagement.tsx` | WIRE to real credit endpoints; fix currency |
| `apps/user/token_management_system.py` | DEPRECATE and archive |
| `services/backend_api/services/plan_config.py` | CREATE — single source of truth for plans |
| `services/backend_api/routers/webhooks.py` | ADD Braintree subscription lifecycle handlers |

---

*End of Audit Report*
