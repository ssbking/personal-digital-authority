# SEARCH EXECUTOR — DEFINITION

STATUS: DRAFT → FINAL CANDIDATE  
VERSION: 1.0  
LAYER: EXECUTION / CAPABILITY

---

## 1. PURPOSE

The Search Executor is a concrete implementation of the Executor Interface.

Its sole responsibility is to perform explicit, read-only search operations over explicitly allowlisted data sources, under a valid Lease issued by the Kernel.

All behavior MUST be deterministic, bounded, and reproducible across implementations.

---

## 2. NON-GOALS (STRICT)

The Search Executor MUST NOT:
- modify any data
- crawl, index, or pre-scan sources
- infer intent, relevance, or priority
- rank results heuristically
- personalize results
- learn from queries
- chain or compose searches
- perform background or deferred work
- cache results beyond execution lifetime
- access non-allowlisted scopes
- bypass operating-system read permissions
- access network resources unless explicitly scoped

---

## 3. SUPPORTED CAPABILITIES (CLOSED SET)

- SEARCH_FILES
- SEARCH_EMAILS
- SEARCH_DATASETS

Any other capability_id MUST be rejected.

---

## 4. INPUT CONTRACT

Each Task Manifest MUST include:
- inputs.query (string)
- inputs.target_scope (string)
- inputs.max_results (integer)

Rules:
- query MUST be UTF-8 encoded
- query MUST be trimmed of leading/trailing whitespace
- query length MUST be 1–4096 Unicode code points
- empty query is invalid
- target_scope MUST exactly match an allowlisted identifier
- max_results MUST be an integer in range 1–1000 (inclusive)

No defaults are permitted.

---

## 5. QUERY MATCHING RULES (GLOBAL)

Unless otherwise specified:
- Matching is case-sensitive
- Matching is literal substring matching
- No regex, fuzzy, or semantic matching
- Matching is performed on Unicode code points, not bytes

---

## 6. SCOPE MODEL

### 6.1 Scope Identifier

A scope identifier is an opaque string mapped by the host to a concrete data source.

The executor MUST NOT interpret scope identifiers.

Examples (non-normative):
- files_home
- email_inbox
- dataset_customers

### 6.2 Scope Allowlist & Configuration

- Scope allowlist MUST be provided at executor startup
- Configuration MAY be provided via constructor arguments or config file
- Runtime mutation is forbidden

---

## 7. CAPABILITY SEMANTICS

### 7.1 SEARCH_FILES

- Search filenames only
- Operate within filesystem subtree bound to target_scope
- Follow no symbolic links
- Recursion allowed within subtree
- Results sorted by Unicode code point order (U+0000 → U+10FFFF)

---

### 7.2 SEARCH_EMAILS

- Search fields:
  - From
  - To
  - Subject
  - Body (plain text only)
- Ignore attachments
- Sort by received_timestamp (ISO 8601, UTC, millisecond precision)
- Missing timestamp → record excluded

---

### 7.3 SEARCH_DATASETS

- Dataset is a finite collection of records
- Each record MUST have a stable primary key
- All string fields are searchable
- Results sorted by primary key (ascending)

---

## 8. RESULT MODEL

Each result entry MUST include:
- id: string, unique within target_scope
- match_field: string
- match_snippet: string

### match_snippet generation:
- Identify first match location
- Extract up to 100 Unicode code points before and after
- Trim to valid UTF-8
- Preserve line breaks
- Max length: 200 code points

---

## 9. EMPTY RESULT SEMANTICS

If no matches exist:
- results = []
- count = 0
- truncated = false

---

## 10. IDEMPOTENCY

- task_id is the idempotency key
- Re-execution MUST produce identical output

---

## 11. FAILURE MODES (CLOSED SET)

- INVALID_LEASE
- LEASE_EXPIRED
- UNSUPPORTED_CAPABILITY
- INVALID_QUERY
- SCOPE_NOT_ALLOWED
- SCOPE_UNAVAILABLE
- EXECUTION_FAILED
- RESOURCE_EXHAUSTED

### Error boundaries:
- SCOPE_UNAVAILABLE: allowlisted but inaccessible or missing
- EXECUTION_FAILED: runtime I/O or corruption errors

---

## 12. ACCEPTANCE CRITERIA

The Search Executor is complete when:
- Behavior is deterministic across implementations
- Sorting and truncation are explicit
- Query semantics are unambiguous
- No inference or side effects occur

---

END OF DEFINITION

