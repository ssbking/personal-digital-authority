# DSL VALIDATOR — DEFINITION

**STATUS:** DRAFT → FOR LOCKING  
**VERSION:** 1.0  
**SCOPE:** DETERMINISTIC KERNEL ONLY

---

## 1. PURPOSE

The DSL Validator is the **first executable component** of the Personal Digital Authority (PDA).

Its sole responsibility is to **deterministically accept or reject** DSL statements according to the frozen DSL v1.1 grammar and the Hard-No invariants defined in `PDA_MASTER_CONTEXT_v1.0.md`.

The validator is a **pure function**:

- Input → DSL text
- Output → VALID or INVALID (+ structured error)

No side effects. No execution. No inference.

---

## 2. NON-GOALS (STRICT)

The DSL Validator MUST NOT:
- execute any action
- infer missing intent
- auto-correct user input
- interact with devices
- call external services
- use machine learning or LLMs
- mutate system state

If input is ambiguous or incomplete, the validator **rejects** it.

---

## 3. INPUT CONTRACT

### 3.1 Input Type

- UTF-8 text
- One DSL statement per invocation

### 3.2 Assumptions

- DSL text may be produced by an AI or a human
- DSL text may be malformed or malicious
- Validator assumes **zero trust** in input

---

## 4. OUTPUT CONTRACT

The validator MUST return **one of two outcomes**:

### 4.1 VALID

- A parsed Abstract Syntax Tree (AST)
- Normalized (canonical) representation

### 4.2 INVALID

- A machine-readable error code
- A human-readable error message
- Exact location (line/column) if applicable

No partial success is allowed.

---

## 5. CORE VALIDATION RESPONSIBILITIES

The validator performs validation in **strict order**. Failure at any stage halts processing.

### 5.1 Structural Validation

- Exactly one Subject
- Exactly one Verb
- Exactly one Object
- No free-form text outside grammar

### 5.2 Verb Class Validation

- Verb MUST belong to an allowed Verb Class
- Verb Class MUST be explicitly declared

Examples (non-exhaustive):
- MUTATE
- TRANSFORM
- DISSEMINATE

Unknown verb classes are rejected.

---

### 5.3 Completeness Validation

The following MUST be explicitly present:
- target scope
- reversibility flag
- sensitivity level

Implicit defaults are **not allowed**.

---

### 5.4 Hard-No Invariant Validation

The validator MUST reject any DSL that:
- attempts silent deletion
- attempts credential access or exfiltration
- attempts financial mutation without HRC flag
- violates any invariant defined in the Master Context

This check is **absolute** and ignores trust levels.

---

## 6. ERROR TAXONOMY

Errors MUST be deterministic and enumerable.

Minimum required categories:

- `SYNTAX_ERROR`
- `UNKNOWN_VERB_CLASS`
- `MISSING_REQUIRED_FIELD`
- `AMBIGUOUS_SCOPE`
- `HARD_NO_VIOLATION`

Each error MUST include:
- error_code
- error_message
- location (if applicable)

---

## 7. AST REQUIREMENTS

The AST produced on VALID input MUST:
- be fully typed
- contain no raw text
- be serializable (JSON-safe)
- be stable across executions

The AST is the **only** artifact passed to downstream components.

---

## 8. DETERMINISM GUARANTEE

Given identical input DSL text, the validator MUST:
- produce identical output
- produce identical errors
- never rely on external state

No randomness is permitted.

---

## 9. ACCEPTANCE CRITERIA

The DSL Validator is considered **complete** when:

- Valid DSL inputs always produce a stable AST
- Invalid inputs always fail fast with the correct error
- No input can bypass Hard-No checks
- Unit tests cover:
  - valid examples
  - malformed inputs
  - boundary cases
  - explicit invariant violations

---

## 10. DEPENDENCIES

Allowed:
- Standard parsing libraries
- Deterministic data structures

Forbidden:
- LLMs
- Network access
- OS-level execution

---

## 11. NEXT STEP

After this definition is locked:

→ Create `DSL_VALIDATOR_SPEC.md` (implementable specification)

No code may be written before that step.

---

## END OF DEFINITION

