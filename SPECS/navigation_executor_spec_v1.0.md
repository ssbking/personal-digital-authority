
**navigation_executor_spec_v1.0.md**
```markdown
# NAVIGATION EXECUTOR — IMPLEMENTATION SPECIFICATION

STATUS: DRAFT → FOR REVIEW & LOCKING  
VERSION: 1.0  
DERIVED FROM: NAVIGATION_EXECUTOR_DEFINITION_v1.0

---

## 1. EXECUTION MODEL

- Synchronous execution
- Wall‑clock timeout: 10 seconds
- No partial navigation
- Process termination on quota violation

---

## 2. PRE‑EXECUTION CHECKS (ORDERED)

1. Verify LeaseToken signature (delegate to host)
2. Verify lease.task_id == manifest.task_id
3. Verify current_time < lease.expires_at
4. Verify capability_id ∈ supported set

Failure halts execution immediately.

---

## 3. INPUT VALIDATION

Required inputs:

- `target_type`: must be one of `["app", "window", "url", "file"]`
- `target_id`: non‑empty string
- `navigation_mode`: one of `["foreground", "background"]`
- `focus_policy`: one of `["steal", "request", "none"]`

Failures:
- `UNSUPPORTED_CAPABILITY` (if target_type invalid)
- `EXECUTION_FAILED` (if any required field missing)

---

## 4. TARGET RESOLUTION

- Target resolution is host‑provided
- Executor receives a resolved handle or failure
- Unknown target → `TARGET_NOT_FOUND`
- Permission denied → `TARGET_NOT_ACCESSIBLE`

---

## 5. CAPABILITY SEMANTICS

### 5.1 Common Rules

- Navigation MUST be synchronous
- Focus behavior MUST be deterministic
- No background monitoring or state retention

### 5.2 NAVIGATE_APP

- Target MUST be a running application process
- If not running → `TARGET_NOT_FOUND`
- `navigation_mode`:
  - `foreground` → bring to front
  - `background` → activate without stealing focus
- `focus_policy`:
  - `steal` → take focus immediately
  - `request` → ask OS to focus (may be ignored)
  - `none` → do not affect focus

### 5.3 NAVIGATE_WINDOW

- Target MUST be an existing window
- If window does not exist → `TARGET_NOT_FOUND`
- Window MUST belong to current user session
- Same focus policies as NAVIGATE_APP

### 5.4 NAVIGATE_URL

- Target MUST be a valid, absolute URL
- URL scheme MUST be `http`, `https`, `file`, or `app‑specific`
- If scheme not supported → `NAVIGATION_BLOCKED`
- Opens in default handler for URL scheme
- `navigation_mode` determines foreground/background activation

### 5.5 NAVIGATE_FILE

- File MUST exist and be readable
- If not readable → `TARGET_NOT_ACCESSIBLE`
- Opens in default viewer/editor
- If viewer not running, it MAY be launched (capability‑specific exception)
- `navigation_mode` controls foreground/background activation

---

## 6. RESULT REPORTING

### 6.1 SUCCESS

```json
{
  "task_id": "...",
  "capability_id": "NAVIGATE_*",
  "target_type": "...",
  "target_id": "...",
  "navigation_result": "success" | "no_op"
}