# LEASE MANAGER — IMPLEMENTATION SPECIFICATION

**STATUS:** DRAFT → FOR REVIEW & LOCKING  
**VERSION:** 1.0  
**DERIVED FROM:** LEASE_MANAGER_DEFINITION_v1.0

---

## 1. PURPOSE

This specification defines the **exact, implementable behavior** of the Lease Manager component in the Personal Digital Authority (PDA) Deterministic Kernel.

The Lease Manager evaluates whether a **Task Manifest** is authorized to execute **at a specific point in time**, and if so, issues a **Lease Token** that proves this authorization.

This component performs **no execution**, **no scheduling**, and **no policy inference**.

---

## 2. EXECUTION MODEL

- Pure, synchronous function
- Inputs are explicit and immutable
- No I/O
- No external state mutation
- No randomness

---

## 3. FUNCTION SIGNATURE (REFERENCE)

```text
evaluate_lease(
  manifest: TaskManifest,
  trust_snapshot: TrustSnapshot,
  now: Timestamp,
  hrc_token: HRCToken | null
) -> LeaseDecision
```

---

## 4. DATA STRUCTURES (CLOSED WORLD)

### 4.1 LeaseDecision

```json
{
  "status": "GRANTED" | "DENIED",
  "lease": LeaseToken | null,
  "error": LeaseError | null
}
```

Rules:
- `lease` MUST be present iff status == GRANTED
- `error` MUST be present iff status == DENIED

---

### 4.2 LeaseToken

```json
{
  "task_id": string,
  "issued_at": Timestamp,
  "expires_at": Timestamp,
  "signature": string
}
```

Rules:
- Token binds to exactly one task_id
- Token MUST be cryptographically verifiable
- No randomness in signature generation

---

### 4.3 LeaseError

```json
{
  "error_code": ErrorCode,
  "message": string
}
```

---

### 4.4 TrustSnapshot

```json
{
  "trust_score": number,
  "minimum_required": number
}
```

Rules:
- Snapshot is read-only
- Lease Manager MUST NOT modify trust state

---

### 4.5 HRCToken

```json
{
  "confirmed": boolean,
  "confirmed_at": Timestamp
}
```

---

## 5. LEASE EVALUATION PIPELINE (STRICT ORDER)

Evaluation MUST proceed in the following order. Failure at any step halts evaluation.

---

### 5.1 Manifest Integrity Check

Checks:
- Manifest contains required fields
- task_id present and non-empty

Failure:
- `INVALID_MANIFEST`

---

### 5.2 Time Window Validation

Checks:
- now < expires_at (if precomputed)

Failure:
- `LEASE_EXPIRED`

---

### 5.3 Trust Threshold Validation

Checks:
- trust_snapshot.trust_score >= trust_snapshot.minimum_required

Failure:
- `INSUFFICIENT_TRUST`

---

### 5.4 Hardware-Rooted Confirmation (HRC)

Checks:
- If manifest.constraints.hrc_required == true:
  - hrc_token MUST be present
  - hrc_token.confirmed == true

Failure:
- `HRC_REQUIRED`

---

### 5.5 Lease Granting

If all checks pass:

- Issue LeaseToken
- Set issued_at = now
- Set expires_at = now + lease_duration

Lease duration MUST be deterministic and system-defined.

---

## 6. CRYPTOGRAPHIC SIGNING

The LeaseToken signature MUST be generated as:

```
signature = HMAC_SHA256(
  secret_key,
  task_id || issued_at || expires_at
)
```

Rules:
- secret_key is system-provided
- No randomness allowed
- Same inputs MUST yield same signature

---

## 7. ERROR CATALOG (CLOSED SET)

Allowed error codes:

- `INVALID_MANIFEST`
- `LEASE_EXPIRED`
- `INSUFFICIENT_TRUST`
- `HRC_REQUIRED`
- `LEASE_REVOKED`

No other error codes permitted.

---

## 8. FORBIDDEN BEHAVIOR

- No execution
- No retries
- No logging
- No network access
- No trust inference
- No modification of Task Manifest

---

## 9. ACCEPTANCE CRITERIA

Implementation is accepted if:

- Identical inputs yield identical LeaseDecision
- Leases cannot be forged or reused for other tasks
- HRC is strictly enforced
- Expired or revoked leases always DENY

---

## 10. NEXT STEP

Once this spec is locked:

→ DeepSeek may generate the Lease Manager implementation.

---

## END OF SPECIFICATION

