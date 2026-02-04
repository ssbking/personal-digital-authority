# NAVIGATION EXECUTOR — DEFINITION

STATUS: DRAFT → FOR LOCKING  
VERSION: 1.0  
LAYER: EXECUTION / CAPABILITY

---

## 1. PURPOSE

The Navigation Executor is a concrete implementation of the Executor Interface.

Its sole responsibility is to perform **explicit, user-facing navigation and focus transitions** between already-known targets under a valid Lease.

This executor moves the user to a specific, pre‑identified destination. It does NOT discover, search for, or infer targets.

All behavior MUST be deterministic, synchronous, and side‑effect‑limited to the requested navigation.

---

## 2. NON‑GOALS (STRICT)

The Navigation Executor MUST NOT:

- discover targets
- search for targets
- rank or infer destinations
- modify target content
- launch targets unless explicitly allowed by capability semantics
- monitor or track user state
- chain multiple navigation steps
- operate in background beyond the requested mode
- bypass OS‑level focus or security policies

---

## 3. SUPPORTED CAPABILITIES (CLOSED SET)

- `NAVIGATE_APP`
- `NAVIGATE_WINDOW`
- `NAVIGATE_URL`
- `NAVIGATE_FILE`

Any other capability_id MUST be rejected.

---

## 4. INPUT CONTRACT

Each Task Manifest MUST include:

- `inputs.target_type` (string)
- `inputs.target_id` (string)
- `inputs.navigation_mode` (string)
- `inputs.focus_policy` (string)

### 4.1 Field Semantics

#### target_type
One of:
- `app`
- `window`
- `url`
- `file`

#### target_id
- Opaque, explicit identifier
- No fuzzy resolution
- MUST correspond to an existing, accessible entity

#### navigation_mode
One of:
- `foreground`
- `background`

#### focus_policy
One of:
- `steal`
- `request`
- `none`

---

## 5. SECURITY & BOUNDARIES

### 5.1 Target Existence Validation

The executor MUST verify that `target_id` corresponds to an existing, accessible entity.

Failures:
- `TARGET_NOT_FOUND`
- `TARGET_NOT_ACCESSIBLE`

### 5.2 OS‑Level Respect

- MUST NOT escalate privileges
- MUST respect OS focus‑management policies
- MUST NOT inject synthetic input events

---

## 6. CAPABILITY SEMANTICS

### 6.1 NAVIGATE_APP

- Navigate to an already‑running application
- If app is not running → `TARGET_NOT_FOUND`
- `navigation_mode` controls foreground/background activation
- `focus_policy` determines focus behavior

### 6.2 NAVIGATE_WINDOW

- Bring a specific window to foreground/background
- Window MUST exist → `TARGET_NOT_FOUND`
- `focus_policy` determines whether focus is taken (`steal`) or requested (`request`)

### 6.3 NAVIGATE_URL

- Navigate a browser or viewer to a specific URL
- URL MUST be explicit and valid
- If the viewer cannot render the URL → `NAVIGATION_BLOCKED`

### 6.4 NAVIGATE_FILE

- Open a file in its default viewer/editor
- File MUST exist and be readable → `TARGET_NOT_ACCESSIBLE`
- Viewer/editor is launched only if not already running (capability‑specific exception)

---

## 7. IDEMPOTENCY

- `task_id` is the idempotency key
- Re‑execution MUST result in the same visible system state
- No additional side effects beyond the navigation action

---

## 8. FAILURE MODES (CLOSED SET)

- `INVALID_LEASE`
- `LEASE_EXPIRED`
- `UNSUPPORTED_CAPABILITY`
- `TARGET_NOT_FOUND`
- `TARGET_NOT_ACCESSIBLE`
- `NAVIGATION_BLOCKED`
- `EXECUTION_FAILED`

No other error codes are permitted.

---

## 9. OUTPUT CONTRACT

### 9.1 SUCCESS

```json
{
  "task_id": "...",
  "capability_id": "NAVIGATE_*",
  "target_type": "...",
  "target_id": "...",
  "navigation_result": "success" | "no_op"
}