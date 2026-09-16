# TASK11R9A FIX4 — Proposition MCP Contract Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the canonical `LegalProposition` contract authoritative across the registry validator, MCP JSON schema, Native-facing Skill instructions, and acceptance tests without changing capability issuance or validation.

**Architecture:** `scripts/legal_proposition.py` owns the flattened model-facing proposition field contract and schema metadata. The registry validator and MCP tool definitions consume that authority. The Skill describes only those canonical input names; legacy names from the failed Native call remain rejected and are covered by actual JSON-RPC acceptance tests.

**Tech Stack:** Python 3, dataclasses/enums, stdio JSON-RPC MCP server, pytest, Markdown Skill contract.

**Spec:** `docs/task11-evidence/task11r9a-change-allowlist.md` plus the TASK11R9A FIX4 request in the user message.

## Global Constraints

- Do not modify capability issuance, lookup, digest, validation, transaction identity, root, epoch, or anchor semantics.
- Do not add `closure_status`, `direct_source`, `relation_to_base_or_exception`, or `resulting_status_or_effect` to the MCP contract.
- Keep `RegistryService` as the canonical legal-state writer.
- Unsupported, missing, and malformed proposition input must fail closed before registry mutation.
- Do not run Native R01 or ASH-06 3/10-run campaigns in this task.
- Preserve unrelated existing worktree changes and do not reset or commit the dirty worktree.

---

### Task 1: Establish one canonical typed proposition input authority

**Files:**
- Modify: `scripts/legal_proposition.py`
- Modify: `scripts/proposition_registry.py`
- Modify: `scripts/jdipt_runtime_mcp.py`

**Interfaces:**
- Produces `CANONICAL_PROPOSITION_FIELDS`, `CANONICAL_PROPOSITION_REQUIRED_FIELDS`, and `canonical_proposition_schema()` from the `LegalProposition` module.
- The registry typed validator and MCP proposition schema use the same field set.
- Compatibility/legacy registry paths remain separate and are not exposed through the capability MCP schema.

- [ ] **Step 1: Add canonical contract metadata and schema generation.**

  Define the flattened model-facing names corresponding to `LegalProposition` plus its flattened `EvidenceRef`: `proposition_id`, `status`, `materiality`, `subject`, `condition`, `procedure`, `modality`, `legal_action`, `operative_verb_lexeme`, `legal_object`, `legal_effect`, `polarity`, `relation_type`, `base_proposition_id`, `exception_proposition_id`, `base_rule`, `exception_rule`, `required_authority`, `required_temporal_status`, `required_source_type`, `source_id`, `authority_kind`, `source_title`, `source_locator`, `evidence_span`, `temporal_status`, and `temporal_render_text`. The schema must require `proposition_id`, `status`, and `materiality`, reject additional properties, and express the existing CLOSED relation/evidence requirements.

- [ ] **Step 2: Make the registry typed validator consume the canonical field set.**

  Replace the independent `_TYPED_FIELDS` copy with the canonical authority. Keep legacy aliases only in the non-typed compatibility path. A typed payload containing any of the four failed Native names must raise `RuntimeStateError` before `RegistryService` writes.

- [ ] **Step 3: Make MCP definitions and dispatch consume the same authority.**

  Remove the independent MCP proposition field set and duplicated property construction. Use `canonical_proposition_schema()` for both prepared and lifecycle proposition schemas, while retaining only transport-level `turn_capability` and `proposition` fields outside the canonical proposition object.

---

### Task 2: Add red-green native-equivalent acceptance coverage

**Files:**
- Create: `tests/test_task11r9a_proposition_contract.py`
- Modify: `tests/test_jdipt_runtime_mcp.py`

**Interfaces:**
- Tests call `dispatch_json_rpc()` with the real `register_material_proposition` JSON-RPC path after beginning a real transaction and recording a real ledger.
- Tests inspect the canonical registry after failures to prove no proposition mutation occurred.

- [ ] **Step 1: Write the failing parity test.**

  Assert that the MCP proposition property names equal `CANONICAL_PROPOSITION_FIELDS`, that the registry typed acceptance set equals the same set, and that none of `closure_status`, `direct_source`, `relation_to_base_or_exception`, or `resulting_status_or_effect` is exposed.

- [ ] **Step 2: Run the focused test and observe the expected failure.**

  Run: `python -m pytest -q tests/test_task11r9a_proposition_contract.py`

  Expected: FAIL because the current MCP and registry maintain independent field definitions and/or expose transitional aliases.

- [ ] **Step 3: Write the native-equivalent lifecycle test.**

  Use one canonical CLOSED payload with exact ledger evidence, call the actual MCP dispatch, and assert `register_material_proposition` returns `state == "ACTIVE"` and a generated `mandatory_render_clause`; then finalize and assert `state == "CLOSED"`.

- [ ] **Step 4: Add fail-closed regression tests.**

  For each failed Native field, assert JSON-RPC `-32602`, `INVALID_TOOL_ARGUMENTS`, and an unchanged registry. Add missing-required and malformed-enum cases with the same no-mutation assertion.

- [ ] **Step 5: Run the focused tests in red/green order.**

  Run the single new parity test before implementation, then run: `python -m pytest -q tests/test_task11r9a_proposition_contract.py tests/test_jdipt_runtime_mcp.py tests/test_jdipt_runtime_mcp_v2.py tests/test_jdipt_runtime_orchestration.py`.

---

### Task 3: Close the Native-facing contract and repository marker drift

**Files:**
- Modify: `skills/law-interpretation-request/SKILL.md`
- Modify: `scripts/validate_repo.py`
- Modify: `tests/test_validate_repo_contract.py`

**Interfaces:**
- The Skill’s Material Proposition Schema uses the canonical names and explicitly excludes generated/internal fields.
- Repository validation checks the canonical contract markers rather than requiring the obsolete four names.

- [ ] **Step 1: Replace obsolete Skill field names.**

  Use `status`, `subject`, `legal_effect`, `relation_type`, and the complete evidence reference fields. State that `mandatory_render_clause` is output-only, `status` is the closure state, `direct_source` is not an input field, and `source_id`/`source_locator`/`evidence_span` carry evidence provenance.

- [ ] **Step 2: Add an explicit fail-closed contract note.**

  Document that `closure_status`, `direct_source`, `relation_to_base_or_exception`, and `resulting_status_or_effect` are obsolete/invalid MCP input names and must not be translated or added to the MCP schema.

- [ ] **Step 3: Update validator markers and tests.**

  Require the canonical Skill markers and assert the obsolete four names are absent from the Material Proposition Schema section while preserving unrelated policy checks.

- [ ] **Step 4: Run the Skill/repository contract tests.**

  Run: `python -m pytest -q tests/test_validate_repo_contract.py tests/test_agents_runtime_precedence.py` and `python scripts/validate_repo.py`.

---

### Task 4: Full local qualification and evidence report

**Files:**
- No additional production files unless a failing focused test identifies a contract defect.

- [ ] **Step 1: Run compile and focused runtime checks.**

  Run: `python -m compileall -q scripts tests` and `python -m pytest -q tests/test_task11r9a_proposition_contract.py tests/test_task11r9_runtime_contracts.py tests/test_registry_runtime_bridge.py tests/test_runtime_transaction_registry.py`.

- [ ] **Step 2: Run the required repository gates.**

  Run: `python scripts/validate_repo.py`, `python scripts/validate_authority_temporal_contract.py`, `python -m pytest -q`, and `python scripts/plugin_integrity.py`.

- [ ] **Step 3: Inspect the final diff.**

  Run: `git diff --check` and `git status --short`; report only Fix4 files changed by this run and distinguish pre-existing dirty files.

- [ ] **Step 4: Report the acceptance matrix.**

  Explicitly report `PROPOSITION_CANONICAL_MODEL`, `PROPOSITION_MCP_SCHEMA_PARITY`, `NATIVE_EQUIVALENT_PAYLOAD_ACCEPTANCE`, `UNSUPPORTED_FIELD_REGRESSION`, `MALFORMED_PROPOSITION_FAIL_CLOSED`, `FULL_PYTEST`, `VALIDATE_REPO`, `COMPILEALL`, `PLUGIN_INTEGRITY`, `REPOSITORY_CACHE_PARITY`, and `ALLOW_NATIVE_RERUN`. Keep Native rerun and ASH-06 campaigns blocked unless all listed local gates pass.
