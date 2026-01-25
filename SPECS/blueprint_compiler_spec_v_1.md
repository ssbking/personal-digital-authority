# BLUEPRINT COMPILER — IMPLEMENTATION SPECIFICATION

**STATUS:** DRAFT → FOR REVIEW & LOCKING  
**VERSION:** 1.0  
**DERIVED FROM:** BLUEPRINT_COMPILER_DEFINITION_v1.0

---

## 1. PURPOSE

This specification defines the **exact, implementable behavior** of the Blueprint Compiler in the Personal Digital Authority (PDA) Deterministic Kernel.

The Blueprint Compiler converts a **VALID DSL AST** into a **deterministic Task Manifest**. It performs *no execution* and makes *no policy decisions*.

This document is a **single source of truth**. Implementations MUST follow it verbatim.

---

## 2. EXECUTION MODEL

- Pure, synchronous function
- Input: AST (validated)
- Output: `CompilationResult`
- No I/O
- No external state
- No randomness

---

## 3. FUNCTION SIGNATURE (REFERENCE)

```text
compile_ast(ast: AST) -> CompilationResult
```

---

## 4. DATA STRUCTURES (CLOSED WORLD)

### 4.1 CompilationResult

```json
{
  "status": "SUCCESS" | "FAILURE",
  "manifest": TaskManifest | null,
  "error": CompilationError | null
}
```

Rules:
- `manifest` MUST be present iff status == SUCCESS
- `error` MUST be present iff status == FAILURE

---

### 4.2 CompilationError

```json
{
  "error_code": ErrorCode,
  "message": string
}
```

---

### 4.3 TaskManifest

```json
{
  "task_id": string,
  "capability_id": string,
  "inputs": object,
  "constraints": {
    "scope": string,
    "reversible": boolean,
    "sensitivity": "LOW" | "MEDIUM" | "HIGH",
    "hrc_required": boolean
  },
  "provenance": {
    "ast_hash": string
  }
}
```

---

## 5. DETERMINISTIC TASK ID GENERATION

The `task_id` MUST be generated deterministically.

### 5.1 Canonical AST Serialization

Before hashing, the AST MUST be serialized in a canonical form:

Rules:
- Keys sorted lexicographically
- No whitespace
- No derived or transient fields

---

### 5.2 Task ID Algorithm

Allowed algorithms:

- `SHA-256(canonical_ast_json)`
- `UUID v5(namespace, canonical_ast_json)`

UUID v4 or any random source is **FORBIDDEN**.

---

## 6. CAPABILITY RESOLUTION

### 6.1 Capability Mapping Table

Capability resolution MUST use a **static mapping table**.

Example (illustrative, not exhaustive):

```json
{
  "MUTATE:FILE:MOVE": "FILE_MOVE",
  "TRANSFORM:EMAIL:EXTRACT": "EMAIL_EXTRACT",
  "DISSEMINATE:FILE:COPY": "FILE_COPY"
}
```

Rules:
- Key format: `VerbClass:ObjectType:Action`
- Table is closed-world
- Missing key → FAILURE

---

## 7. INPUT BINDING RULES

- Inputs MUST be derived directly from AST identifiers
- No transformation or inference
- Identifiers are passed verbatim

---

## 8. CONSTRAINT PROPAGATION

The following MUST be copied verbatim from AST metadata into the manifest:

- scope
- reversible
- sensitivity
- hrc_required

The compiler MUST NOT interpret or modify these values.

---

## 9. FAILURE MODES

The compiler MUST fail deterministically with one of:

- `UNKNOWN_CAPABILITY`
- `UNSUPPORTED_ACTION`
- `INVALID_BINDING`
- `COMPILATION_FAILURE`

No partial manifests are allowed.

---

## 10. FORBIDDEN BEHAVIOR

- No execution
- No policy enforcement
- No retries
- No logging
- No network access
- No dynamic capability discovery

---

## 11. ACCEPTANCE CRITERIA

Implementation is accepted if:

- Identical AST input produces identical Task Manifest
- Capability resolution is deterministic and closed-world
- All constraints are propagated without interpretation
- Failure modes are explicit and enumerable

---

## 12. NEXT STEP

Once this spec is locked:

→ DeepSeek may generate the Blueprint Compiler implementation.

---

## END OF SPECIFICATION

