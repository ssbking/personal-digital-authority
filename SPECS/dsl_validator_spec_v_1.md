# DSL VALIDATOR — IMPLEMENTATION SPECIFICATION

**STATUS:** DRAFT → FOR FINAL LOCKING  
**VERSION:** 1.0  
**DERIVED FROM:** DSL_VALIDATOR_DEFINITION_v1.0

---

## 1. PURPOSE

This specification defines the **exact, implementable behavior** of the DSL Validator component in the Personal Digital Authority (PDA) system.

This document is a **single source of truth**. Any implementation MUST follow this specification verbatim.

---

## 2. EXECUTION MODEL

- Pure, synchronous function
- Input: raw DSL text (string)
- Output: ValidationResult
- No external state
- No I/O
- No randomness

---

## 3. FUNCTION SIGNATURE (REFERENCE)

```text
validate_dsl(input_text: string) -> ValidationResult
```

---

## 4. DATA STRUCTURES (SINGLE SOURCE OF TRUTH)

### 4.1 ValidationResult

```json
{
  "status": "VALID" | "INVALID",
  "ast": AST | null,
  "error": ValidationError | null
}
```

Rules:
- `ast` MUST be present iff status == VALID
- `error` MUST be present iff status == INVALID

---

### 4.2 ValidationError

```json
{
  "error_code": ErrorCode,
  "message": string,
  "location": {
    "line": number | null,
    "column": number | null
  }
}
```

---

### 4.3 Abstract Syntax Tree (AST)

```json
{
  "subject": SubjectNode,
  "verb": VerbNode,
  "object": ObjectNode,
  "metadata": MetadataNode
}
```

---

### 4.4 SubjectNode (CLOSED ENUM)

```json
{
  "type": "USER" | "SYSTEM",
  "identifier": string
}
```

---

### 4.5 ObjectNode (CLOSED ENUM)

```json
{
  "type": "FILE" | "FOLDER" | "EMAIL" | "DATASET" | "DEVICE",
  "identifier": string
}
```

---

### 4.6 VerbNode

```json
{
  "class": "MUTATE" | "TRANSFORM" | "DISSEMINATE",
  "action": string
}
```

---

### 4.7 MetadataNode (MANDATORY)

```json
{
  "scope": string,
  "reversible": boolean,
  "sensitivity": "LOW" | "MEDIUM" | "HIGH",
  "hrc_required": boolean
}
```

All fields are REQUIRED. No defaults. No inference.

---

## 5. DSL GRAMMAR & VALIDATION PIPELINE (SINGLE SOURCE OF TRUTH)

Validation proceeds in strict order. Failure at any step HALTS processing.

---

### 5.1 Grammar (Binding EBNF)

```
DSL          ::= SUBJECT VERB OBJECT META

SUBJECT      ::= "SUBJECT(" SUBJECT_TYPE "," IDENTIFIER ")"
VERB         ::= "VERB(" VERB_CLASS "," ACTION ")"
OBJECT       ::= "OBJECT(" OBJECT_TYPE "," IDENTIFIER ")"
META         ::= "META(" SCOPE "," REVERSIBLE "," SENSITIVITY "," HRC_FLAG ")"

SUBJECT_TYPE ::= "USER" | "SYSTEM"
OBJECT_TYPE  ::= "FILE" | "FOLDER" | "EMAIL" | "DATASET" | "DEVICE"
VERB_CLASS   ::= "MUTATE" | "TRANSFORM" | "DISSEMINATE"

REVERSIBLE   ::= "true" | "false"
SENSITIVITY  ::= "LOW" | "MEDIUM" | "HIGH"
HRC_FLAG     ::= "true" | "false"

IDENTIFIER   ::= 1*(ALPHA | DIGIT | "_" | "-" | "/" )
ACTION       ::= 1*(ALPHA | DIGIT | "_" | "-" )
```

Rules:
- Token order is fixed
- Whitespace outside tokens is ignored
- Newlines allowed only between top-level blocks

Failure:
- SYNTAX_ERROR

---

### 5.2 Structural Validation

Checks:
- Exactly one SUBJECT
- Exactly one VERB
- Exactly one OBJECT
- Exactly one META

Failure:
- MISSING_REQUIRED_FIELD

---

### 5.3 Verb Class Validation

Checks:
- Verb class ∈ { MUTATE, TRANSFORM, DISSEMINATE }

Failure:
- UNKNOWN_VERB_CLASS

---

### 5.4 Completeness Validation

MetadataNode MUST include:
- scope
- reversible
- sensitivity
- hrc_required

Failure:
- MISSING_REQUIRED_FIELD

---

### 5.5 Hard-No Invariant Validation

Reject if:
- irreversible deletion is attempted
- credential access is implied
- financial mutation with sensitivity HIGH and hrc_required == false

Failure:
- HARD_NO_VIOLATION

---

## 6. ERROR CATALOG (CLOSED SET)

Allowed error codes:
- SYNTAX_ERROR
- UNKNOWN_SUBJECT_TYPE
- UNKNOWN_OBJECT_TYPE
- UNKNOWN_VERB_CLASS
- MISSING_REQUIRED_FIELD
- INVALID_METADATA_VALUE
- AMBIGUOUS_SCOPE
- HARD_NO_VIOLATION

No other error codes permitted.

---

## 7. NORMALIZATION RULES

On VALID input:
- Normalize enum values
- Strip all free-form text
- Output canonical AST only

---

## 8. FORBIDDEN IMPLEMENTATION PATTERNS

- No heuristics
- No auto-correction
- No side effects
- No logging
- No network access

---

## 9. ACCEPTANCE CRITERIA

Implementation is accepted if:
- Grammar and AST are isomorphic
- All validation stages execute in order
- All Hard-No checks are enforced
- Identical input yields identical output

---

## END OF SPECIFICATION

