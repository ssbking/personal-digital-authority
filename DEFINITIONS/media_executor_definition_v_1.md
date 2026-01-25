# MEDIA EXECUTOR — DEFINITION

**STATUS:** DRAFT → FOR LOCKING  
**VERSION:** 1.0  
**LAYER:** EXECUTION / CAPABILITY

---

## 1. PURPOSE

The Media Executor is a concrete implementation of the **Executor Interface**.

Its responsibility is to perform **explicit, user-facing media playback actions** on authorized output devices (e.g., TV, speakers, local display) under a valid Lease.

It enables simple, reversible, non-destructive media interactions such as play, pause, stop, and seek.

---

## 2. SUPPORTED CAPABILITIES (CLOSED SET)

The Media Executor MUST implement **only** the following capability_ids:

- `MEDIA_PLAY`
- `MEDIA_PAUSE`
- `MEDIA_STOP`
- `MEDIA_SEEK`

Any other capability_id MUST be rejected.

---

## 3. NON-GOALS (STRICT)

The Media Executor MUST NOT:

- browse the internet
- download media
- infer user preferences
- select content automatically
- control volume beyond explicit commands
- persist playback state beyond execution
- bypass device-level permissions

---

## 4. INPUT CONTRACT

### 4.1 Required Inputs (from Task Manifest)

Each Task Manifest MUST include:

- `inputs.media_uri` (string)
- `inputs.target_device` (string identifier)

Optional (capability-specific):
- `inputs.position_seconds` (number, for SEEK)

Rules:
- media_uri MUST be explicit (no search queries)
- target_device MUST be explicitly named

---

## 5. SECURITY & DEVICE BOUNDARIES

### 5.1 Device Allowlist

The Media Executor MUST operate only on **explicitly configured output devices**.

Rules:
- target_device MUST match a configured device identifier
- Unknown devices MUST be rejected

Failure:
- `EXECUTION_FAILED`

---

## 6. CAPABILITY SEMANTICS

### 6.1 MEDIA_PLAY

Behavior:
- Initiate playback of media_uri on target_device

Rules:
- media_uri MUST be accessible to the device
- Executor MUST NOT modify media content

Reversibility:
- Playback state change only (no undo metadata required)

---

### 6.2 MEDIA_PAUSE

Behavior:
- Pause playback on target_device

Reversibility:
- Reversible by MEDIA_PLAY

---

### 6.3 MEDIA_STOP

Behavior:
- Stop playback on target_device

Reversibility:
- Reversible by MEDIA_PLAY

---

### 6.4 MEDIA_SEEK

Behavior:
- Seek to position_seconds within media

Rules:
- position_seconds MUST be >= 0

Reversibility:
- Reversible by another MEDIA_SEEK

---

## 7. IDEMPOTENCY RULES

- task_id MUST be treated as the idempotency key
- Repeated execution of the same task_id MUST NOT cause additional side effects

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
  "capability_id": "MEDIA_*",
  "device": "target_device",
  "status": "applied"
}
```

Output MUST be structured and deterministic.

---

## 10. ACCEPTANCE CRITERIA

The Media Executor is complete when:

- Playback actions require a valid lease
- Only allowlisted devices are controlled
- No media is selected or inferred
- Actions are reversible by subsequent commands
- Re-execution is idempotent

---

## 11. NEXT STEP

After this definition is locked:

→ Create `MEDIA_EXECUTOR_SPEC_v1.0`

No implementation may occur before that step.

---

## END OF DEFINITION

