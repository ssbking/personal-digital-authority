# FILE EXECUTOR — IMPLEMENTATION SPECIFICATION

**STATUS:** DRAFT → FOR REVIEW & LOCKING  
**VERSION:** 1.0  
**DERIVED FROM:** FILE_EXECUTOR_DEFINITION_v1.0

---

## 1. PURPOSE

This specification defines the **exact, implementable behavior** of the File Executor.

The File Executor performs **explicit, filesystem-scoped side effects** under a valid Lease, implementing a minimal, safe subset of file operations.

No inference, recursion, or interpretation is permitted.

---

## 2. EXECUTION MODEL

- Runs as a sandboxed process under host control
- Receives a Task Manifest and Lease Token
- Performs synchronous execution
- Terminates immediately on host kill signals

---

## 3. SUPPORTED CAPABILITIES (CLOSED SET)

The File Executor MUST implement **only**:

- `FILE_MOVE`
- `FILE_COPY`
- `FILE_DELETE`

Any other capability_id MUST result in `UNSUPPORTED_CAPABILITY`.

---

## 4. INPUT SCHEMA (STRICT)

### 4.1 Common Requirements

All inputs MUST:

- be absolute filesystem paths
- refer to regular files only
- be UTF-8 encoded strings
- be canonicalized before use

---

### 4.2 Capability-Specific Inputs

#### FILE_MOVE / FILE_COPY

```json
{
  "source_path": "/absolute/path/to/source",
  "destination_path": "/absolute/path/to/destination"
}
```

Rules:
- source_path MUST exist
- destination_path MUST NOT exist

---

#### FILE_DELETE

```json
{
  "source_path": "/absolute/path/to/source"
}
```

Rules:
- source_path MUST exist
- manifest.constraints.reversible MUST be true

---

## 5. PATH VALIDATION & CONFINEMENT

### 5.1 Base Directory Enforcement

- Executor MUST be configured with a static list of allowed base directories
- All paths MUST be descendants of one of these directories

Failure:
- `EXECUTION_FAILED`

---

### 5.2 Path Normalization

Before any operation:

- Resolve absolute path
- Reject any path containing `..`
- Reject symlinks (before and after resolution)

---

## 6. CAPABILITY SEMANTICS

### 6.1 FILE_MOVE

Execution:
- Perform atomic move if supported by filesystem

Undo Metadata (REQUIRED):
```json
{
  "original_path": "/absolute/path/to/source"
}
```

---

### 6.2 FILE_COPY

Execution:
- Perform byte-for-byte copy

Undo Metadata:
- None required

---

### 6.3 FILE_DELETE

Execution:
- Remove the file

Undo Metadata (REQUIRED):
```json
{
  "recovery": "file_snapshot_or_backup_reference"
}
```

The recovery method is implementation-defined but MUST be sufficient to restore the file.

---

## 7. IDEMPOTENCY

- task_id MUST be treated as the idempotency key
- If the same task_id is re-executed:
  - Executor SHOULD return the previously stored ExecutionResult
  - No filesystem side effects may reoccur

---

## 8. RESOURCE BOUNDS

Execution MUST be subject to host-enforced quotas:

- Maximum execution time
- Maximum memory usage
- Maximum disk I/O

Exceeding any quota MUST result in:

- Process termination
- `RESOURCE_EXHAUSTED`

---

## 9. RESULT FORMAT & INTEGRITY

### 9.1 ExecutionResult.output

On SUCCESS:

```json
{
  "task_id": "...",
  "capability_id": "FILE_MOVE | FILE_COPY | FILE_DELETE",
  "result_summary": {
    "source": "...",
    "destination": "..."
  },
  "undo_metadata": { }
}
```

---

### 9.2 Result Signature

- ExecutionResult MUST be cryptographically signed
- Signature MUST bind:
  - task_id
  - capability_id
  - status
  - output

Unsigned or unverifiable results MUST be rejected by the Kernel.

---

## 10. FAILURE MODES (CLOSED SET)

Allowed error codes:

- `UNSUPPORTED_CAPABILITY`
- `INVALID_LEASE`
- `LEASE_EXPIRED`
- `EXECUTION_FAILED`
- `RESOURCE_EXHAUSTED`

---

## 11. FORBIDDEN BEHAVIOR

The File Executor MUST NOT:

- Execute shell commands
- Traverse directories recursively
- Follow symlinks
- Perform wildcard operations
- Modify permissions or ownership
- Operate outside base directories
- Access network resources

---

## 12. ACCEPTANCE CRITERIA

The File Executor implementation is accepted if:

- All operations require a valid lease
- Path traversal attacks are impossible
- Irreversible deletes are impossible
- Undo metadata is captured correctly
- Idempotent re-execution is safe

---

## 13. NEXT STEP

Once this specification is locked:

→ Generate File Executor implementation via DeepSeek

Kernel and interface code MUST NOT be modified.

---

## END OF SPECIFICATION

