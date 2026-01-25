# PERSONAL DIGITAL AUTHORITY (PDA)
## Master Context & Architectural Constitution

**STATUS:** ACTIVE • LOCKED FOR IMPLEMENTATION  
**VERSION:** 1.0  
**CHANGE POLICY:** EXPLICIT VERSIONING ONLY

---

## 1. PURPOSE (WHY THIS EXISTS)

This project builds a **Personal Digital Authority (PDA)** — a local-first system that allows a human to delegate digital tasks **without surrendering authority, safety, or long-term intelligibility**.

This is **not**:
- an AI assistant
- a chatbot
- an OS replacement
- a smart home controller
- an autonomous agent system

This **is**:
- a deterministic execution substrate
- a grammar-driven intent system
- a human-in-the-loop automation platform
- infrastructure for boring, trustworthy delegation

The system must be **predictable when wrong**, not impressive when right.

---

## 2. CORE PHILOSOPHY (FIXED)

These principles are non-negotiable.

1. **Deterministic Inversion**  
   AI interprets intent. The system decides and executes.

2. **Grammar over Semantics**  
   All actions flow through a typed DSL. If intent cannot be expressed, it is rejected.

3. **Human Authority is Absolute**  
   No autonomous execution without explicit, bounded permission.

4. **Wrongness is Expected**  
   The system must fail visibly, reversibly, and auditably.

5. **Invisibility is Success**  
   If a user “sets up a system”, the product has failed.

---

## 3. ARCHITECTURE (LOCKED)

### 3.1 Deterministic Kernel (NON-AI)

The kernel is strictly mechanical and includes:

- **DSL Validator** – Enforces grammar, completeness, and invariants.
- **Blueprint Compiler** – Maps DSL → Task Manifest → Capability invocation.
- **Lease Manager** – Manages executor permissions, revocation, and checkpoints.
- **Trust Matrix Store** – CRDT-based store tracking trust for `(VerbClass, Context, Sensitivity)`.

No LLM may execute code or bypass this layer.

---

### 3.2 AI Role (STRICTLY LIMITED)

AI is a **compiler frontend**, not an agent.

AI may:
- parse human language into DSL
- generate plans (not actions)
- assist via UI helpers (guided clicks, explanations)

AI may NOT:
- execute tools
- modify files directly
- invent new capabilities
- bypass the kernel
- operate without human checkpoints

---

### 3.3 Deterministic Separation

```
Human → AI (Parser) → DSL → Kernel → Executor
```

If DSL generation fails, execution stops.

---

## 4. DSL (v1.1 — FROZEN)

The DSL is the **only language of action**.

Characteristics:
- Subject / Verb / Object
- Typed Verb Classes (e.g., MUTATE, TRANSFORM, DISSEMINATE)
- Explicit scope and reversibility
- Rejects ambiguity

If a task cannot be expressed in DSL, it **must not run**.

---

## 5. SAFETY & TRUST (FIXED)

### 5.1 Hard-No Invariants
Certain actions are **never allowed**, regardless of trust.

Examples:
- silent deletion
- credential exfiltration
- financial transactions without physical confirmation

### 5.2 Trust Decay
Autonomy decays over time. The system *forgets* trust deliberately.

### 5.3 Hardware-Rooted Confirmation (HRC)
High-impact actions require physical confirmation on a trusted device.

---

## 6. DEVICE & EXECUTION MODEL

- No “central brain” with absolute authority
- Authority state is CRDT-replicated
- Executors are **preemptible**, not disposable
- Tasks operate under **leases**, not permanent permission

Users never manage nodes, roles, or infrastructure.

---

## 7. USER EXPERIENCE (THE ELECTRICITY TEST)

**Input:**
> “File my email receipts into the tax folder.”

**System behavior:**
- Parses intent
- Generates DSL
- Executes silently
- Logs outcome

**User experience:**
- No setup
- No explanation
- No celebration

Just done.

---

## 8. ABSOLUTE PROHIBITIONS

- No persistent chat personalities
- No autonomous agents
- No background retries
- No silent learning
- No feature invention
- No scope expansion without version bump

Violation = rejection.

---

## 9. CONTRIBUTION & AI USAGE RULES

Roles:
- **Human Architect** – defines meaning and boundaries
- **GPT-class AI** – reasoning, acceptance criteria, scope enforcement
- **Code-Gen AI (DeepSeek, etc.)** – mechanical implementation only
- **Review AI (Gemini, etc.)** – critique and edge cases only

No AI may change architecture.

---

## 10. CHANGE CONTROL

Any change to:
- DSL
- Kernel boundaries
- Trust model

Requires:
1. Written justification
2. Explicit approval
3. Version increment

No silent evolution.

---

## 11. CURRENT STATE

- Architecture: LOCKED
- DSL v1.1: LOCKED
- Implementation: NOT STARTED
- Next step: **DSL Validator (Deterministic Kernel)**

---

## END OF CONTEXT

