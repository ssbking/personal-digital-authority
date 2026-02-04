# HOST ADAPTER INTERFACE — SPECIFICATION

STATUS: DRAFT → FOR REVIEW & LOCKING  
VERSION: 1.0  
LAYER: HOST / PLATFORM ADAPTER

---

## 1. PURPOSE

The Host Adapter Interface defines the **only permitted boundary** between the PDA Core (Kernel + Executors) and a concrete operating environment (OS, browser, desktop session).

It provides **mechanical, deterministic hooks** for verification, resolution, and execution of actions that PDA itself must not perform.

The Host Adapter:
- Is platform-specific
- Is stateless
- Contains no policy or inference
- Implements capability effects on the host

---

## 2. NON-GOALS (STRICT)

The Host Adapter MUST NOT:
- interpret user intent
- infer targets
- search or discover resources
- cache or persist state
- bypass OS security or permissions
- escalate privileges
- decide whether an action is allowed (that is PDA’s role)

---

## 3. DESIGN CONSTRAINTS

- All functions are synchronous
- No background work
- No retries
- No side effects beyond requested action
- No exceptions may escape the adapter
- All outcomes MUST be returned as explicit result codes

---

## 4. TYPE SYSTEM (NORMATIVE)

### 4.1 Enumerations (Closed Sets)

#### FocusPolicy
- FOREGROUND
- BACKGROUND
- NO_FOCUS

#### LeaseVerificationResult
- VERIFIED
- INVALID

#### TargetResolutionResult
- RESOLVED
- TARGET_NOT_FOUND
- TARGET_NOT_ACCESSIBLE
- INVALID_TARGET_FORMAT

#### NavigationResult
- SUCCESS
- NO_OP
- NAVIGATION_BLOCKED
- EXECUTION_FAILED

---

## 5. LEASE VERIFICATION HOOK


```python
def verify_lease_signature(
    payload: bytes,
    signature: bytes,
    kernel_public_key: bytes
) -> LeaseVerificationResult
```

Rules:
- Adapter MUST NOT reconstruct or generate signatures
- Adapter MUST treat all inputs as opaque
- Adapter MUST return VERIFIED or INVALID only

---

## 6. TARGET RESOLUTION HOOK

```python
def resolve_target(
    target_type: str,
    target_id: str
) -> TargetResolutionResult
```

Rules:
- Adapter MUST NOT infer or normalize target_id
- Adapter MUST NOT perform search
- Adapter MUST return exactly one resolution result

---

## 7. HOST CAPABILITY DISCOVERY

```python
def get_host_capabilities() -> dict
```

Returns a deterministic description of supported host features.

Example (non-normative):
```json
{
  "platform": "linux",
  "adapter_version": "1.0",
  "navigation_types": ["app", "window", "url", "file"]
}
```

Rules:
- MUST be static for adapter lifetime
- MUST NOT probe dynamically

---

## 8. NAVIGATION ACTION HOOKS

All navigation hooks MUST:
- Perform exactly one action
- Respect OS focus and permission rules
- Return a NavigationResult

### 7.1 Application Navigation

```python
def navigate_app(
    target_id: str,
    navigation_mode: str,
    focus_policy: str
) -> NavigationResult
```

---

### 7.2 Window Navigation

```python
def navigate_window(
    target_id: str,
    navigation_mode: str,
    focus_policy: str
) -> NavigationResult
```

---

### 7.3 URL Navigation

```python
def navigate_url(
    target_id: str,
    navigation_mode: str,
    focus_policy: str
) -> NavigationResult
```

Rules:
- target_id MUST be a valid absolute URL
- Unsupported schemes → NAVIGATION_BLOCKED

---

### 7.4 File Navigation

```python
def navigate_file(
    target_id: str,
    navigation_mode: str,
    focus_policy: str
) -> NavigationResult
```

Rules:
- target_id MUST be a valid path
- File must exist and be readable

---

## 9. ERROR HANDLING RULES

- Adapter MUST catch all internal exceptions
- Adapter MUST map failures to explicit result codes
- Adapter MUST NOT raise exceptions upward

---

## 10. IDEMPOTENCY & DETERMINISM

- Given identical inputs and identical host state, adapter MUST return identical results
- Adapter MUST NOT store state between calls

---

## 11. SECURITY BOUNDARY

- Adapter operates with user-level privileges only
- Adapter MUST respect sandboxing and window manager policies
- Adapter MUST NOT inject synthetic input

---

## 12. VERSIONING

- Any change to this interface requires a version bump
- Executors bind to a specific adapter version

---

END OF SPECIFICATION

