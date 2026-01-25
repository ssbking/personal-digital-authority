# APP LAUNCH EXECUTOR — DEFINITION

**STATUS:** DRAFT → FOR LOCKING  
**VERSION:** 1.0  
**LAYER:** EXECUTION / CAPABILITY

---

## 1. PURPOSE

The App Launch Executor is a concrete implementation of the **Executor Interface**.

Its sole responsibility is to **invoke an explicit application or system handler** on a specific device, under a valid Lease, without inference, discovery, or background behavior.

This enables user-facing actions such as opening Maps, launching a music app, or starting navigation — nothing more.

---

## 2. SUPPORTED CAPABILITIES (CLOSED SET)

The App Launch Executor MUST implement **only** the following capability_ids:

- `APP_LAUNCH`
- `APP_OPEN_URI`

Any other capability_id MUST be rejected.

---

## 3. NON-GOALS (STRICT)

The App Launch Executor MUST NOT:

- search for applications
- choose between multiple apps
- infer user preference
- install or update applications
- bypass OS-level permission models
- persist application state
- perform background automation

---

## 4. INPUT CONTRACT

### 4.1 Required Inputs (from Task Manifest)

Each Task Manifest MUST include:

- `inputs.app_identifier` (string)
- `inputs.target_device` (string identifier)

Optional (capability-specific):
- `inputs.uri` (string, for APP_OPEN_URI)

Rules:
- app_identifier MUST be explicit
- target_device MUST be explicit
- uri MUST be explicit (no search queries)

---

## 5. SECURITY & DEVICE BOUNDARIES

### 5.1 Device Allowlist

The App Launch Executor MUST operate only on **explicitly configured devices**.

Rules:
- target_device MUST match a configured device identifier
- Unknown devices MUST be rejected

Failure:
- `EXECUTION_FAILED`

---

## 6. CAPABILITY SEMANTICS

### 6.1 APP_LAUNCH

Behavior:
- Launch the application identified by app_identifier on target_device

Rules:
- Executor MUST NOT supply arguments
- Executor MUST NOT modify application state

Reversibility:
- No undo metadata required

---

### 6.2 APP_OPEN_URI

Behavior:
- Launch the application and open the provided uri

Rules:
- uri MUST be passed verbatim
- No transformation or inference

Reversibility:
- No undo metadata required

---

## 7. IDEMPOTENCY RULES

- task_id MUST be treated as the idempotency key
- Repeated execution of the same task_id MUST NOT cause additional side effects beyond re-invocation

---

## 8. FAILURE MODES (CLOSED SET)

Allowed error codes:

- `UNSUPPORTED_CAPABILITY`
- `INVALID_LEASE`
- `LEASE_EXPIRED`
- `EXECUTION_FAILED`
- `RESOURCE_EXHAUSTED`

---

## 9. OUTPUT CONTRACT

### 9.1 ExecutionResult.output

On SUCCESS:

```json
{
  "task_id": "...",
  "capability_id": "APP_*",
  "app": "app_identifier",
  "device": "target_device",
  "status": "launched"
}
```

Output MUST be structured and deterministic.

---

## 10. ACCEPTANCE CRITERIA

The App Launch Executor is complete when:

- Applications launch only with a valid lease
- Only explicit apps and devices are used
- No app selection or inference occurs
- Execution is idempotent and auditable

---

## 11. NEXT STEP

→ Delegate combined Definition + Spec + Implementation to DeepSeek

---

## END OF DEFINITION

