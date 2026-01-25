# MEDIA EXECUTOR — IMPLEMENTATION SPECIFICATION

**STATUS:** DRAFT → FOR REVIEW & LOCKING  
**VERSION:** 1.0  
**DERIVED FROM:** MEDIA_EXECUTOR_DEFINITION_v1.0

---

## 1. PURPOSE

This specification defines the **exact, implementable behavior** of the Media Executor.

The Media Executor performs **explicit media playback control actions** on authorized output devices under a valid Lease.

No content discovery, inference, or background activity is permitted.

---

## 2. EXECUTION MODEL

- Runs as a sandboxed process under host control
- Receives a Task Manifest and Lease Token
- Executes synchronously
- Terminates immediately on host kill signals

---

## 3. SUPPORTED CAPABILITIES (CLOSED SET)

The Media Executor MUST implement **only**:

- `MEDIA_PLAY`
- `MEDIA_PAUSE`
- `MEDIA_STOP`
- `MEDIA_SEEK`

Any other capability_id MUST result in `UNSUPPORTED_CAPABILITY`.

---

## 4. INPUT SCHEMA (STRICT)

### 4.1 Common Inputs

```json
{
  "media_uri": "explicit_media_uri",
  "target_device": "device_identifier"
}
```

Rules:
- media_uri MUST be explicit (no search queries)
- media_uri MUST be accessible to the target device
- target_device MUST be explicitly specified

---

### 4.2 Capability-Specific Inputs

#### MEDIA_SEEK

```json
{
  "position_seconds": number
}
```

Rules:
- position_seconds MUST be >= 0

---

## 5. DEVICE CONFINEMENT

### 5.1 Device Allowlist

- Executor MUST be configured with a static allowlist of devices
- target_device MUST match one allowlisted identifier

Failure:
- `EXECUTION_FAILED`

---

## 6. CAPABILITY SEMANTICS

### 6.1 MEDIA_PLAY

Execution:
- Initiate playback of media_uri on target_device

Rules:
- Executor MUST NOT modify media content
- Executor MUST NOT infer playback settings

---

### 6.2 MEDIA_PAUSE

Execution:
- Pause current playback on target_device

---

### 6.3 MEDIA_STOP

Execution:
- Stop current playback on target_device

---

### 6.4 MEDIA_SEEK

Execution:
- Seek playback to position_seconds

---

## 7. IDEMPOTENCY

- task_id MUST be treated as the idempotency key
- Repeated execution of the same task_id MUST NOT cause additional side effects

---

## 8. RESOURCE BOUNDS

Execution MUST be subject to host-enforced quotas:

- Maximum execution time
- Maximum memory usage
- Maximum I/O

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
  "capability_id": "MEDIA_*",
  "device": "target_device",
  "status": "applied"
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

The Media Executor MUST NOT:

- Select or infer media
- Browse the internet
- Download content
- Persist playback state
- Control non-allowlisted devices
- Perform background actions

---

## 12. ACCEPTANCE CRITERIA

The Media Executor implementation is accepted if:

- All actions require a valid lease
- Only allowlisted devices are controlled
- No content is inferred or fetched
- Actions are idempotent and reversible
- Results are signed and verifiable

---

## 13. NEXT STEP

Once this specification is locked:

→ Generate Media Executor implementation via DeepSeek

Kernel and interface code MUST NOT be modified.

---

## END OF SPECIFICATION

