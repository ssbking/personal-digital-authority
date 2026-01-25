# EXECUTOR INTERFACE — IMPLEMENTATION SPECIFICATION

**STATUS:** DRAFT → FOR REVIEW & LOCKING  
**VERSION:** 1.0  
**DERIVED FROM:** EXECUTOR_INTERFACE_DEFINITION_v1.0

---

## 1. PURPOSE

This specification defines the **exact, implementable behavior** of Executors in the Personal Digital Authority (PDA) system.

Executors are responsible for performing **real-world side effects** strictly under the authority granted by a **Task Manifest** and a **valid Lease Token**.

Executors are **non-authoritative**, **replaceable**, and **host-controlled**.

---

## 2. EXECUTION MODEL

- Executors run in a **host-managed sandbox** (process, container, or VM)
- Executors are invoked synchronously by an execution host
- Executors MUST treat all inputs as untrusted
- Executors MUST terminate on host kill signals

---

## 3. FUNCTION SIGNATURE (REFERENCE)

```text
execute_task(
  manifest: TaskManifest,
  lease: LeaseToken
) -> ExecutionResult
```

Executors MUST NOT expose additional entry points.

---

## 4. DATA STRUCTURES (CLOSED WORLD)

### 4.1 ExecutionResult

```json
{
  "status": "SUCCESS" | "FAILURE",
  "output": object | null,
  "error": ExecutionError | null
}
```

Rules:
- `output` MUST be present iff status == SUCCESS
- `error` MUST be present iff status == FAILURE

---

### 4.2 ExecutionError

```json
{
  "error_code": ErrorCode,
  "message": string
}
```

---

### 4.3 ExecutionResult Signature (NEW)

Executors MUST cryptographically bind results to the task execution.

Rules:
- ExecutionResult MUST include a signature over:
  - task_id
  - capability_id
  - status
  - output (if any)
- Signature MUST be verifiable using the Executor’s Public Key
- Kernel MUST treat unsigned or unverifiable results as invalid

---

## 5. PRE-EXECUTION CHECKS (MANDATORY)

Execution MUST proceed in the following order. Failure at any step aborts execution.

---

### 5.1 Lease Verification

Checks:
- Verify LeaseToken signature using **asymmetric cryptography**
- Executor MUST verify using the Kernel **Public Key only**
- Executor MUST NOT possess or access the Kernel signing (Private) Key
- Verify lease.task_id == manifest.task_id
- Verify current time < lease.expires_at

Failure:
- `INVALID_LEASE`
- `LEASE_EXPIRED`

---

### 5.2 Capability Verification

Checks:
- Executor implements manifest.capability_id

Failure:
- `UNSUPPORTED_CAPABILITY`

---

## 6. RESOURCE BOUNDS (MANDATORY)

Execution MUST be subject to **strict resource quotas** enforced by the host environment.

### 6.1 Required Resource Limits

At minimum, the host MUST enforce:

- Maximum wall-clock execution time (timeout)
- Maximum memory usage
- Maximum disk I/O (read/write)

Executors MUST:
- Assume they may be killed at any time
- NOT attempt to bypass or self-extend limits

---

### 6.2 Resource Exhaustion Handling

If any resource limit is exceeded:

- The Executor process MUST be terminated by the host
- The execution result MUST be recorded as:

```
RESOURCE_EXHAUSTED
```

No partial success is allowed.

---

## 7. EXECUTION SEMANTICS

### 7.1 Idempotency (SHOULD)

Executors SHOULD be idempotent where feasible.

Rules:
- `task_id` MUST be treated as the idempotency key
- If a task with the same task_id has already completed successfully:
  - The Executor SHOULD return the previous result
  - The Executor MUST NOT re-run irreversible side effects

---

### 7.2 Reversibility Handling (SHOULD)

If `manifest.constraints.reversible == true`:

- Executor SHOULD capture sufficient undo metadata
- Undo metadata MAY include:
  - original file contents
  - previous system state identifiers
- Undo metadata MUST be included in ExecutionResult.output

If reversible == false:
- Executor MUST NOT attempt to fabricate undo data

---

### 7.2 Side Effect Attribution

All side effects MUST be attributable to:

- task_id
- capability_id

Executors MUST NOT perform background or speculative actions.

---

## 8. FAILURE MODES (CLOSED SET)

Allowed error codes:

- `INVALID_LEASE`
- `LEASE_EXPIRED`
- `UNSUPPORTED_CAPABILITY`
- `EXECUTION_FAILED`
- `RESOURCE_EXHAUSTED`

No other error codes are permitted.

---

## 9. FORBIDDEN BEHAVIOR

Executors MUST NOT:

- Possess or access the Kernel signing (Private) Key
- Generate or forge LeaseTokens
- Access kernel internals
- Issue or modify leases
- Store long-term authority
- Retry execution autonomously
- Perform network access unless explicitly required by capability
- Emit unstructured logs as output

---

## 10. ACCEPTANCE CRITERIA

An Executor implementation is accepted if:

- No execution occurs without a valid lease
- Resource exhaustion is fail-closed
- Idempotency rules are respected where applicable
- All failures are explicit and structured
- Side effects are attributable and auditable

---

## 11. NEXT STEP

Once this specification is locked:

→ Implement concrete Executors (e.g., FileExecutor, MediaExecutor)

Kernel code MUST NOT be modified.

---

## END OF SPECIFICATION

