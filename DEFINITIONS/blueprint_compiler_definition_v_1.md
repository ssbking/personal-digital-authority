# BLUEPRINT COMPILER — DEFINITION

**STATUS:** DRAFT → FOR LOCKING  
**VERSION:** 1.0  
**SCOPE:** DETERMINISTIC KERNEL ONLY

---

## 1. PURPOSE

The Blueprint Compiler is the **second core component** of the Personal Digital Authority (PDA) Deterministic Kernel.

Its sole responsibility is to **transform a VALIDATED DSL AST** into a **Task Manifest** that describes *what must be executed*, *by whom*, and *under what constraints* — without performing any execution.

The Blueprint Compiler is a **pure, deterministic transformer**:

- Input → AST (from DSL Validator)
- Output → Task Manifest

No execution, no inference, no side effects.

---

## 2. NON-GOALS (STRICT)

The Blueprint Compiler MUST NOT:
- execute tasks
- interact with devices
- call external services
- make policy decisions
- infer missing information
- reorder intent
- use AI or heuristics

If an AST cannot be compiled deterministically, compilation **fails**.

---

## 3. INPUT CONTRACT

### 3.1 Input Type

- A VALID AST produced by the DSL Validator

### 3.2 Preconditions

- AST MUST conform exactly to `DSL_VALIDATOR_SPEC_v1.0`
- Compiler assumes AST is syntactically and structurally correct
- Compiler does NOT re-validate grammar

---

## 4. OUTPUT CONTRACT

The compiler MUST produce exactly one of:

### 4.1 SUCCESS

- A Task Manifest (JSON-serializable)

### 4.2 FAILURE

- A deterministic error
- No partial output

---

## 5. CORE RESPONSIBILITIES

The Blueprint Compiler performs the following responsibilities **in order**:

### 5.1 Capability Resolution

- Map `(VerbClass, ObjectType, Action)` → `CapabilityID`
- Mapping table is **explicit and closed-world**
- Unknown mappings result in FAILURE

No dynamic resolution is allowed.

---

### 5.2 Input Binding

- Bind AST identifiers to manifest inputs
- Preserve identifiers exactly as provided
- No normalization or mutation

---

### 5.3 Constraint Propagation

The following MUST be copied verbatim into the Task Manifest:
- reversibility
- sensitivity
- hrc_required
- scope

The compiler MUST NOT interpret these fields.

---

### 5.4 Manifest Construction

The Task Manifest MUST include:

- task_id (**DETERMINISTIC**)
- capability_id
- inputs
- constraints
- provenance metadata (source AST hash)

Rules:
- `task_id` MUST be derived deterministically from the input AST
- Allowed strategies include:
  - cryptographic hash of the canonical AST
  - UUID v5 using a fixed namespace and AST hash
- UUID v4 or any source of randomness is **FORBIDDEN**

---

## 6. DETERMINISM GUARANTEE

Given identical AST input, the compiler MUST:
- produce identical Task Manifest
- produce identical errors

No randomness, time, or external state allowed.

---

## 7. ERROR CATEGORIES

Minimum required error types:

- `UNKNOWN_CAPABILITY`
- `UNSUPPORTED_ACTION`
- `INVALID_BINDING`
- `COMPILATION_FAILURE`

Errors MUST be explicit and enumerable.

---

## 8. ACCEPTANCE CRITERIA

The Blueprint Compiler is complete when:

- Every valid AST maps to exactly one Task Manifest or a deterministic failure
- No execution occurs
- No policy logic is embedded
- Output is fully inspectable before execution

---

## 9. NEXT STEP

After this definition is locked:

→ Create `BLUEPRINT_COMPILER_SPEC_v1.0` (implementable specification)

No code may be written before that step.

---

## END OF DEFINITION

