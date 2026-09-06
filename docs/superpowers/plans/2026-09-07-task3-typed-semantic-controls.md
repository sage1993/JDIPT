# Task 3 — Typed Semantic Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace free-form materiality, modality, polarity, and proposition-status values with validated canonical typed values while preserving the Task 1/Task 2 runtime contracts.

**Architecture:** `proposition_registry` is the single external-input adapter. It accepts only an explicit, finite legacy-alias allowlist, converts values to enums owned by `legal_proposition`, and constructs `LegalProposition` only with typed values. Persistence serializes enum values through their canonical strings; rendering and relation checks branch on enum identity and never infer semantics from raw text.

**Tech Stack:** Python 3.11+ `enum.StrEnum`, frozen dataclasses, JSON runtime-state persistence, pytest, MCP tool JSON schema.

**Spec:** User-provided Task 3 — Typed Semantic Controls.

## Global Constraints

- Task 3 base is `8fcf3fdc726887ee3871a1772c1946150966521f`.
- Do not change Unified Release Authority, mandatory suite enforcement, hard-gate authority, case identity, snapshot identity, or repository/installed/active-runtime separation.
- Do not implement Task 4 semantic soundness, source-resolution closure, final-answer contradiction detection, ASH-06 x3/x10, or live final release acceptance.
- Unknown semantic values fail closed; no fuzzy matching, substring inference, truthiness coercion, or silent defaults.
- Normalization occurs once in `proposition_registry.py`, before `LegalProposition` construction.
- Existing user changes in the original worktree remain untouched; this worktree is the exact-base implementation candidate.

---

### Task 1: Lock the semantic domain and adapter regressions

**Files:**
- Modify: `tests/test_legal_proposition.py`
- Modify: `tests/test_proposition_registry.py`
- Modify: `tests/test_proposition_rendering.py`
- Modify: `tests/test_jdipt_runtime_mcp.py`
- Modify: `tests/test_synthesis_runtime_state.py`
- Create: `tests/test_typed_semantic_controls.py`

**Interfaces:**
- Tests will import `Materiality`, `Modality`, `Polarity`, `PropositionStatus`, and `PropositionValidationError` from `scripts.legal_proposition`.
- Tests will exercise `register_material_proposition` as the only supported legacy-input adapter.

- [ ] **Step 1: Add failing direct-domain rejection tests**

Add tests that construct a complete proposition with each unknown value and assert `PropositionValidationError`: `criticality`, `critical`, `important`, `not required`, `SHOULD`, `REQUIRED`, `PROHIBITED`, `NEUTRAL`, `UNKNOWN`, `PENDING`, `DONE`, and empty strings. Add a direct-construction test proving an unknown value cannot enter the domain without the registry.

- [ ] **Step 2: Add failing adapter and canonicalization tests**

Add tests for the explicit supported aliases currently used by fixtures: `material`, `non_material`, `non-material`, `may`, `must`, `mandatory`, `must not`, `prohibited`, `forbidden`, `may not`, `positive`, `negative`, and canonical uppercase values. Assert `not required`, `critical`, and `important` are rejected and that omission does not default materiality to `MATERIAL`.

- [ ] **Step 3: Add failing distinction, schema, rendering, and round-trip tests**

Assert `MUST`/`MUST_NOT` and `MAY`/`MAY_NOT` remain distinct after persistence round-trip; assert MCP schemas expose finite enums; assert typed render output remains equivalent without raw-string heuristics; assert persisted JSON contains canonical uppercase values only.

- [ ] **Step 4: Run the new tests and record the RED failure**

Run:

```powershell
py -3.13 -m pytest -q tests/test_typed_semantic_controls.py tests/test_legal_proposition.py tests/test_proposition_registry.py tests/test_proposition_rendering.py tests/test_jdipt_runtime_mcp.py
```

Expected: FAIL because the domain fields are currently unrestricted strings and registry materiality currently defaults silently.

---

### Task 2: Implement canonical typed values and the single normalization boundary

**Files:**
- Modify: `scripts/legal_proposition.py`
- Modify: `scripts/proposition_registry.py`
- Modify: `scripts/jdipt_runtime_mcp.py`
- Modify: `scripts/synthesis_runtime_state.py`

**Interfaces:**
- `Materiality`, `Modality`, `Polarity`, and `PropositionStatus` are `StrEnum` types with exactly the canonical values from the Task 3 contract.
- `proposition_registry` owns `normalize_materiality`, `normalize_modality`, `normalize_polarity`, and `normalize_status` (or one equivalent shared helper) and no other module normalizes semantic input.
- Unknown and missing required semantic values raise `PropositionValidationError` with a field-specific message.

- [ ] **Step 1: Implement the minimum enum types and strict domain invariant**

Define the four enums in `legal_proposition.py`. Change `LegalProposition` annotations to those enums, require `PropositionStatus`/`Materiality`, and validate optional modality/polarity as enum instances. Do not coerce strings in `__post_init__`; direct domain construction with strings is invalid.

- [ ] **Step 2: Implement exact alias maps at the registry boundary**

Use exact dictionary lookup after the existing whitespace trim. Preserve only aliases observed in the current fixtures or explicit contract: `material`, `non_material`, `non-material`; `may`, `must`, `mandatory`, `must not`, `may not`; `positive`, `negative`; and uppercase canonical strings. Do not promote renderer-only heuristic tokens such as `required`, `shall`, `prohibited`, or `forbidden`; do not add `critical`, `important`, `not required`, fuzzy variants, hyphenated `must-not`, or polarity aliases derived from modality.

- [ ] **Step 3: Remove silent defaults and build typed propositions**

Make registry materiality explicit and required. Normalize status, materiality, modality, and polarity before calling `LegalProposition`; pass enum instances into the constructor. Preserve status `OPEN`/`CLOSED` closure checks and all existing evidence/registry enforcement behavior.

- [ ] **Step 4: Make JSON persistence canonical and fail closed**

Ensure `asdict`/JSON serialization emits enum `.value` strings and `_from_json` normalizes only canonical stored values before constructing the domain object. Legacy persisted lowercase values may be read through the same explicit adapter only if needed by existing fixtures, but every subsequent write must contain canonical uppercase values. Unknown persisted values raise `RuntimeStateError`.

- [ ] **Step 5: Tighten MCP input schemas**

Expose canonical values first and the finite supported legacy aliases second in `tool_definitions()` for the four semantic properties. Keep `status` required and ensure schema-level rejection does not replace domain validation.

- [ ] **Step 6: Run targeted tests and refactor only after GREEN**

Run the tests from Task 1. Fix production code, not weakened expectations, until they pass; then remove duplicated normalizers and keep the single registry owner.

---

### Task 3: Convert consumers to typed comparisons without semantic re-inference

**Files:**
- Modify: `scripts/proposition_rendering.py`
- Modify: `scripts/proposition_relations.py`
- Modify: `tests/test_proposition_rendering.py`
- Modify: `tests/test_task1r_range_exception_relation.py`
- Modify: `tests/test_synthesis_relation_regressions.py`

**Interfaces:**
- Rendering uses `Materiality.MATERIAL`, `Modality`, `Polarity`, and `PropositionStatus` identity/equality only.
- Relation checks use typed materiality/status/polarity values; relation text matching remains limited to legal content and is not reused for semantic-control normalization.

- [ ] **Step 1: Replace renderer semantic heuristics**

Make materiality check enum identity. Map `MUST` to mandatory text, `MUST_NOT` to prohibition text, `MAY_NOT` to prohibition text with its distinct typed value preserved, and `MAY` to discretionary text. Do not inspect `"not" in modality`, action text, or polarity strings.

- [ ] **Step 2: Replace relation semantic-control checks**

Use typed materiality/status/polarity comparisons in range-exception logic. Preserve existing relation matching and Task 1R range-exception behavior; do not add new semantic soundness rules.

- [ ] **Step 3: Run rendering and relation regressions**

Run:

```powershell
py -3.13 -m pytest -q tests/test_proposition_rendering.py tests/test_task1r_range_exception_relation.py tests/test_synthesis_relation_regressions.py
```

Expected: PASS with canonical fixtures and explicit legacy registry aliases.

---

### Task 4: Documentation, scoped review, and repository verification

**Files:**
- Create: `docs/superpowers/plans/2026-09-07-task3-typed-semantic-controls.md`
- Create: `docs/task3-typed-semantic-controls-acceptance.md`

**Interfaces:**
- Acceptance documentation records inventory, exact alias policy, changes, regression matrix, verification results, installed/runtime scope, and residual Task 4 risks.

- [ ] **Step 1: Run the required regression groups**

Run targeted semantic, registry, rendering, serialization, Task 1R, and Task 2 authority tests, then full pytest and compileall.

- [ ] **Step 2: Run static/package checks**

Run `python scripts/validate_repo.py`, `python scripts/validate_authority_temporal_contract.py`, `python scripts/plugin_integrity.py`, `npm ci`, `npm audit`, and `git diff --check`. Do not run live final release acceptance, ASH-06 x3, or ASH-06 x10.

- [ ] **Step 3: Perform scoped review**

Search changed production files for `.lower()`/substring semantic classification, defaults, fuzzy aliases, schema/domain mismatch, and renderer re-inference. Fix any Critical/Important finding and rerun affected tests.

- [ ] **Step 4: Record the acceptance report and commit Task 3 separately**

Commit only Task 3 files with a semantic typing message. Report `Task 3: PASS` only if every acceptance checkbox has fresh evidence; otherwise report `HOLD` and the exact blocker.

---

## Verification Checklist

- [ ] `TASK3_BASE_SHA` is exact and preserved.
- [ ] Four semantic controls are typed and canonical in memory.
- [ ] Unknown values and missing materiality fail closed.
- [ ] Supported aliases are explicit and finite.
- [ ] Direct domain construction cannot bypass validation.
- [ ] Persistence round-trip preserves typed values and writes canonical strings.
- [ ] Renderer and relation consumers do not re-infer semantic controls.
- [ ] Task 1R and Task 2 release-authority tests remain green.
- [ ] Full pytest, compileall, static validation, package checks, and diff check are fresh and recorded.
- [ ] No live acceptance, ASH-06 x3, or ASH-06 x10 is claimed.
