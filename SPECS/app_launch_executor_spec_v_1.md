# APP_LAUNCH_EXECUTOR — IMPLEMENTATION SPECIFICATION

**STATUS:** DRAFT → FOR REVIEW & LOCKING  
**VERSION:** 1.0  
**DERIVED FROM:** APP_LAUNCH_EXECUTOR_DEFINITION_v1.0

**CANONICAL FILE NAME:** APP_LAUNCH_EXECUTOR_SPEC_v1.0.md  
**LAYER:** EXECUTION / CAPABILITY

---

## 1. PURPOSE

This specification defines the **exact, implementable behavior** of the App Launch Executor in the Personal Digital Authority (PDA) system.

The App Launch Executor performs **explicit, foreground application lifecycle actions** strictly under a valid Lease issued by the Kernel.

This document is a **single source of truth**. Implementations MUST follow it verbatim.

---

## 2. EXECUTION MODEL

- Runs as a sandboxed, host-managed process
- Invoked synchronously by the Execution Host
- Receives exactly:
  - `TaskManifest`
  - `LeaseToken`
- Terminates immediately on host kill or quota violation
- Performs no background or deferred work

---

## 3. FUNCTION SIGNATURE (REFERENCE)

```text
execute_task(
  manifest: TaskManifest,
  lease: LeaseToken
) -> ExecutionResult
```

No additional entry points are permitted.

---

## 4. SUPPORTED CAPABILITIES (CLOSED SET)

The App Launch Executor MUST implement **only** the following capability_ids:

- `APP_LAUNCH`
- `APP_FOCUS`
- `APP_CLOSE`

Any other capability_id MUST result in:
- `UNSUPPORTED_CAPABILITY`

---

## 5. PRE-EXECUTION CHECKS (MANDATORY)

Execution MUST proceed in strict order. Failure at any step aborts execution.

### 5.1 Lease Verification

Checks:
- Verify LeaseToken signature using Kernel public key
- Verify `lease.task_id == manifest.task_id`
- Verify current time < `lease.expires_at`

Failure:
- `INVALID_LEASE`
- `LEASE_EXPIRED`

---

### 5.2 Capability Verification

Checks:
- `manifest.capability_id` ∈ supported capability set

Failure:
- `UNSUPPORTED_CAPABILITY`

---

## 6. INPUT SCHEMA (STRICT)

### 6.1 Required Inputs (from Task Manifest)

```json
{
  "app_id": "explicit_application_identifier",
  "target_environment": "desktop | mobile | tv"
}
```

Rules:
- `app_id` MUST exactly match an allowlisted identifier
- `target_environment` MUST be explicit
- No normalization, fuzzy matching, or inference

---

## 7. APPLICATION CONFINEMENT

### 7.1 Static Application Allowlist

- Executor MUST be configured with a static, host-owned allowlist
- Allowlist binds:
  - `app_id → executable / bundle reference`

Rules:
- Unknown `app_id` MUST be rejected
- Allowlist MUST NOT be mutable at runtime

Failure:
- `EXECUTION_FAILED`

---

## 8. CAPABILITY SEMANTICS

### 8.1 APP_LAUNCH

Execution:
- Launch the specified application in the foreground

Rules:
- If application is already running, Executor MUST deterministically choose ONE:
  - bring to foreground, OR
  - no-op
- Chosen behavior MUST be consistent across executions

Reversibility:
- Reversible via `APP_CLOSE`

---

### 8.2 APP_FOCUS

Execution:
- Bring an already-running application to the foreground

Rules:
- Application MUST be running
- No-op is FORBIDDEN if application is not running

Failure:
- `EXECUTION_FAILED`

---

### 8.3 APP_CLOSE

Execution:
- Request graceful application termination

Rules:
- Force-kill is FORBIDDEN
- If graceful termination fails or exceeds host time limits:
  - Return FAILURE

Reversibility:
- Reversible via `APP_LAUNCH`

---

## 9. IDEMPOTENCY

- `task_id` MUST be treated as the idempotency key
- Re-execution of a completed `task_id` MUST NOT:
  - spawn duplicate processes
  - re-close already closed applications

Executor SHOULD return the previously recorded `ExecutionResult`.

---

## 10. RESOURCE BOUNDS

Execution MUST be subject to host-enforced limits:

- Maximum wall-clock execution time
- Maximum memory usage
- Maximum OS handle usage

Exceeding any limit MUST result in:
- Process termination
- `RESOURCE_EXHAUSTED`

---

## 11. RESULT FORMAT & INTEGRITY

### 11.1 ExecutionResult.output

On SUCCESS:

```json
{
  "task_id": "...",
  "capability_id": "APP_*",
  "app_id": "...",
  "status": "applied"
}
```

---

### 11.2 Result Signature

- ExecutionResult MUST be cryptographically signed
- Signature MUST bind:
  - `task_id`
  - `capability_id`
  - `status`
  - `output`

Unsigned or unverifiable results MUST be rejected by the Kernel.

---

## 12. FAILURE MODES (CLOSED SET)

Allowed error codes:

- `INVALID_LEASE`
- `LEASE_EXPIRED`
- `UNSUPPORTED_CAPABILITY`
- `EXECUTION_FAILED`
- `RESOURCE_EXHAUSTED`

No other error codes are permitted.

---

## 13. FORBIDDEN BEHAVIOR

The App Launch Executor MUST NOT:

- Discover installed applications
- Search or infer app identity
- Install, update, or uninstall applications
- Launch background services or daemons
- Escalate OS privileges
- Persist state across executions
- Access network resources

---

## 14. ACCEPTANCE CRITERIA

Implementation is accepted if:

- No action executes without a valid lease
- Only allowlisted applications can be controlled
- Foreground-only behavior is enforced
- No inference or discovery exists
- Idempotent re-execution is safe
- Results are signed and verifiable

---

## 15. NEXT STEP

Once this specification is locked:

→ Generate App Launch Executor implementation via DeepSeek

Kernel, DSL, and Executor Interface code MUST NOT be modified.

---

## END OF SPECIFICATION

