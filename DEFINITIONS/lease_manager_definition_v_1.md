# LEASE MANAGER — DEFINITION

**STATUS:** DRAFT → FOR LOCKING  
**VERSION:** 1.0  
**SCOPE:** DETERMINISTIC KERNEL ONLY

---

## 1. PURPOSE

The Lease Manager is the **third core component** of the Personal Digital Authority (PDA) Deterministic Kernel.

Its responsibility is to **grant, track, and revoke time-bound execution authority** for Task Manifests produced by the Blueprint Compiler.

The Lease Manager answers one question only:

> “Is this Task Manifest currently authorized to execute, and under what constraints?”

It does **not** execute tasks.

---

## 2. NON-GOALS (STRICT)

The Lease Manager MUST NOT:
- execute tasks
- interpret intent
- modify Task Manifests
- infer trust
- bypass Hardware-Rooted Confirmation (HRC)
- interact with devices
- perform scheduling

---

## 3. INPUT CONTRACT

### 3.1 Primary Input

- A Task Manifest produced by the Blueprint Compiler

### 3.2 Secondary Inputs

- Current system time (monotonic)
- Trust Matrix snapshot (read-only)
- Optional HRC confirmation token

---

## 4. OUTPUT CONTRACT

The Lease Manager MUST produce exactly one of:

### 4.1 GRANT

- A Lease Token authorizing execution

### 4.2 DENY

- A deterministic error explaining why execution is not authorized

No partial grants are allowed.

---

## 5. CORE RESPONSIBILITIES

### 5.1 Lease Granting

A lease MAY be granted only if:

- Task Manifest is structurally valid
- Current time is within allowed execution window
- Trust Matrix score meets minimum threshold
- HRC is satisfied if `hrc_required == true`

---

### 5.2 Lease Token Issuance

The Lease Token MUST:

- be cryptographically verifiable
- include expiration timestamp
- bind to exactly one Task Manifest (via task_id)
- be non-transferable

---

### 5.3 Lease Revocation

The Lease Manager MUST revoke a lease if:

- expiration time is reached
- Trust Matrix score decays below threshold
- explicit user revocation occurs

Revocation is **fail-closed**.

---

## 6. DETERMINISM GUARANTEE

Given identical inputs (Task Manifest, Trust state, time window), the Lease Manager MUST:

- issue identical GRANT or DENY decisions
- issue identical Lease Tokens (excluding timestamps where applicable)

Randomness is **forbidden**.

---

## 7. ERROR CATEGORIES

Minimum required error types:

- `LEASE_EXPIRED`
- `INSUFFICIENT_TRUST`
- `HRC_REQUIRED`
- `INVALID_MANIFEST`
- `LEASE_REVOKED`

Errors MUST be explicit and enumerable.

---

## 8. ACCEPTANCE CRITERIA

The Lease Manager is complete when:

- No task can execute without a valid lease
- Leases expire deterministically
- Revocation is immediate and fail-closed
- No execution logic exists in this component

---

## 9. NEXT STEP

After this definition is locked:

→ Create `LEASE_MANAGER_SPEC_v1.0` (implementable specification)

No code may be written before that step.

---

## END OF DEFINITION

