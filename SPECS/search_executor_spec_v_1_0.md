# SEARCH EXECUTOR — IMPLEMENTATION SPECIFICATION

STATUS: DRAFT → FINAL CANDIDATE  
VERSION: 1.0  
DERIVED FROM: SEARCH_EXECUTOR_DEFINITION_v1.0

---

## 1. EXECUTION MODEL

- Synchronous execution
- Wall-clock time enforcement (30 seconds)
- No partial results on timeout
- Host termination on quota violation

---

## 2. PRE-EXECUTION CHECKS (ORDERED)

1. Verify LeaseToken signature
2. Verify lease.task_id == manifest.task_id
3. Verify current_time < lease.expires_at
4. Verify capability_id supported

Failure halts execution immediately.

---

## 3. INPUT VALIDATION

- Trim query
- Validate UTF-8
- Validate query length 1–4096 code points
- Validate max_results ∈ [1,1000]
- Validate target_scope allowlisted

Failures:
- INVALID_QUERY
- SCOPE_NOT_ALLOWED

---

## 4. SCOPE RESOLUTION

- Resolve scope via static configuration
- Permission denied or missing → SCOPE_UNAVAILABLE

---

## 5. SEARCH ALGORITHMS

### Common Rules

- Case-sensitive Unicode substring match
- Iterate in deterministic source order
- No mutation of data

---

### SEARCH_FILES

- Walk directory tree
- Reject symlinks
- Match filename only
- Sort by Unicode code point order

---

### SEARCH_EMAILS

- Match From, To, Subject, Body
- Require ISO 8601 UTC timestamp
- Sort by received_timestamp ascending

---

### SEARCH_DATASETS

- Iterate records by primary key
- Match all string fields

---

## 6. TRUNCATION LOGIC

- Compute full ordered result list
- count = total matches
- results = first max_results entries
- truncated = (count > max_results)

---

## 7. RESULT FORMAT

```json
{
  "task_id": "string",
  "capability_id": "SEARCH_*",
  "target_scope": "string",
  "results": [
    {
      "id": "string",
      "match_field": "string",
      "match_snippet": "string"
    }
  ],
  "count": number,
  "truncated": boolean
}
```

---

## 8. RESOURCE LIMITS

- Wall-clock timeout: 30s
- Memory limit: 256MB

Exceeded → RESOURCE_EXHAUSTED

---

## 9. IDEMPOTENCY

- task_id is idempotency key
- Re-execution MUST return identical output

---

## 10. FAILURE CODES

- INVALID_LEASE
- LEASE_EXPIRED
- UNSUPPORTED_CAPABILITY
- INVALID_QUERY
- SCOPE_NOT_ALLOWED
- SCOPE_UNAVAILABLE
- EXECUTION_FAILED
- RESOURCE_EXHAUSTED

---

## 11. TESTABILITY REQUIREMENTS

- Deterministic ordering allows golden-file tests
- Data sources MUST be mockable
- No randomness permitted

---

END OF SPECIFICATION

