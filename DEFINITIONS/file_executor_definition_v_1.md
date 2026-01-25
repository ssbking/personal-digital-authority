# FILE EXECUTOR — DEFINITION

**STATUS:** DRAFT → FOR LOCKING  
**VERSION:** 1.0  
**LAYER:** EXECUTION / CAPABILITY

---

## 1. PURPOSE

The File Executor is a concrete implementation of the **Executor Interface**.

Its sole responsibility is to perform **explicit, filesystem-scoped side effects** under a valid Lease, without inference, recursion, or interpretation.

It exists to safely execute the most fundamental real‑world operations:

- moving files
- copying files
- deleting files (reversible only)

---

## 2. SUPPORTED CAPABILITIES (CLOSED SET)

The File Executor MUST implement **only** the following capability_ids:

- `FILE_MOVE`
- `FILE_COPY`
- `FILE_DELETE`

Any other capability_id MUST be rejected.

---

## 3. NON‑GOALS (STRICT)

The File Executor MUST NOT:

- execute shell commands
- perform recursive directory traversal
- follow symlinks
- accept wildcards or glob patterns
- modify permissions or ownership
- operate outside declared base directories
- access network or remote filesystems

---

## 4. INPUT CONTRACT

### 4.1 Required Inputs (from Task Manifest)

Each Task Manifest MUST include:

- `inputs.source_path` (absolute path)
- `inputs.destination_path` (absolute path, if applicable)

Rules:
- Paths MUST be absolute
- Paths MUST refer to files only (not directories)
- Path normalization MUST occur before use

---

## 5. SECURITY BOUNDARIES

### 5.1 Base Directory Constraint

The File Executor MUST operate only within **explicitly configured base directories**.

Rules:
- All paths MUST be children of an allowed base directory
- Path traversal (`..`) MUST be rejected
- Symlink resolution MUST be disabled or rejected

Failure:
- `EXECUTION_FAILED`

---

## 6. CAPABILITY SEMANTICS

### 6.1 FILE_MOVE

Behavior:
- Atomically move source_path → destination_path

Rules:
- Source MUST exist
- Destination MUST NOT exist
- Operation MUST be atomic if supported by filesystem

Reversibility:
- MUST capture original location as undo metadata

---

### 6.2 FILE_COPY

Behavior:
- Copy source_path → destination_path

Rules:
- Source MUST exist
- Destination MUST NOT exist

Reversibility:
- No undo metadata required

---

### 6.3 FILE_DELETE

Behavior:
- Remove source_path

Rules:
- `manifest.constraints.reversible` MUST be true
- Non‑reversible delete is FORBIDDEN

Reversibility:
- MUST capture file contents or recovery reference

---

## 7. IDEMPOTENCY RULES

- task_id MUST be treated as the idempotency key
- If a task_id has already completed successfully:
  - The previous ExecutionResult SHOULD be returned
  - No side effects may re‑occur

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

If SUCCESS, output MUST include:

- `task_id`
- `capability_id`
- `result_summary` (structured)
- `undo_metadata` (if reversible)

Output MUST be deterministic and structured.

---

## 10. ACCEPTANCE CRITERIA

The File Executor is complete when:

- No operation occurs without a valid lease
- Path traversal is impossible
- Irreversible deletion is impossible
- Undo metadata is captured when required
- Idempotent re‑invocation is safe

---

## 11. NEXT STEP

After this definition is locked:

→ Create `FILE_EXECUTOR_SPEC_v1.0` (implementable specification)

No code may be written before that step.

---

## END OF DEFINITION

