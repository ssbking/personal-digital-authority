# EXECUTOR INTERFACE — DEFINITION

**STATUS:** DRAFT → FOR LOCKING  
**VERSION:** 1.0  
**SCOPE:** POST-KERNEL / CAPABILITY EXECUTION LAYER

---

## 1. PURPOSE

The Executor Interface defines the **only permitted contract** between the Deterministic Kernel and any code that performs real-world actions.

It answers one question:

> “Given a valid Task Manifest and an active Lease, how may execution occur safely and observably?”

Executors are **replaceable**, **sandboxed**, and **non-authoritative**.

---

## 2. NON-GOALS (STRICT)

Executors MUST NOT:
- validate DSL
- compile intents
- issue or modify leases
- infer user intent
- bypass kernel decisions
- access kernel internals
- store long-term authority

Executors do **exactly** what they are told — nothing more.

---

## 3. INPUT CONTRACT

### 3.1 Required Inputs

An Executor receives:

- `TaskManifest` (from Blueprint Compiler)
- `LeaseToken` (from Lease Manager)

Both inputs MUST be verified before execution.

---

## 4. OUTPUT CONTRACT

Executors MUST return exactly one of:

### 4.1 SUCCESS

- A structured ExecutionResult

### 4.2 FAILURE

- A structured ExecutionError

Executors MUST NOT throw uncaught exceptions.

---

## 5. CORE RESPONSIBILITIES

### 5.1 Lease Verification

Before execution, an Executor MUST:

- Verify LeaseToken signature
- Verify task_id match
- Verify lease is unexpired

Failure at any step MUST abort execution.

---

### 5.2 Capability Enforcement

An Executor MUST:

- Execute only the `capability_id` it implements
- Reject all other capability_ids

No dynamic dispatch allowed.

---

### 5.3 Sandboxing

Execution MUST occur:

- with least privilege
- in a constrained environment
- without access to kernel memory or secrets

---

### 5.4 Result Reporting

Executors MUST:

- Report execution outcome
- Include structured metadata
- Avoid free-form text

---

## 6. DETERMINISM & OBSERVABILITY

- Execution MAY be non-deterministic (real world)
- Reporting MUST be deterministic and structured
- Side effects MUST be attributable to a task_id

---

## 7. FAILURE MODES

Minimum required error types:

- `INVALID_LEASE`
- `LEASE_EXPIRED`
- `UNSUPPORTED_CAPABILITY`
- `EXECUTION_FAILED`

Failures MUST be explicit.

---

## 8. SECURITY BOUNDARIES

- Executors trust the kernel
- The kernel does NOT trust executors
- All inputs are treated as hostile

This boundary is **intentional**.

---

## 9. ACCEPTANCE CRITERIA

The Executor Interface is complete when:

- Executors cannot execute without a valid lease
- Executors cannot escalate privilege
- Executors cannot invent actions
- All execution is auditable

---

## 10. NEXT STEP

After this definition is locked:

→ Create `EXECUTOR_INTERFACE_SPEC_v1.0` (implementable specification)

No executors may be implemented before that.

---

## END OF DEFINITION

