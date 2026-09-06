# Task 4 — Semantic Soundness Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic post-coverage Semantic Soundness Gate that rejects mentioned-but-not-adopted propositions and semantic contradictions while preserving the Task 1–3 contracts.

**Architecture:** Keep `LegalProposition`, render contracts, and textual coverage unchanged as upstream inputs. Add `scripts/proposition_soundness.py` to classify bounded answer regions and compare adopted output with typed canonical propositions, then invoke it from the existing Stop gate after coverage/relation reconciliation and persist independent structured evidence in the existing reconciliation record.

**Tech Stack:** Python 3, dataclasses, `StrEnum`/typed enums already owned by `scripts.legal_proposition`, deterministic regular expressions and Markdown span scanning, pytest, existing runtime JSON evidence persistence.

**Spec:** `docs/superpowers/specs/2026-09-07-task4-semantic-soundness-design.md`

## Global Constraints

- `TASK4_BASE_SHA=c51108c0ec7e05c6161bbc232eba37d925e8c7ec`; work only on branch `codex/task4-semantic-soundness` in the isolated worktree.
- Keep the Task 3 typed contract exactly: `MATERIAL/NON_MATERIAL`, `MAY/MUST/MUST_NOT/MAY_NOT`, `POSITIVE/NEGATIVE`, `OPEN/CLOSED`.
- Preserve `coverage` and `soundness` as independent results; never make Soundness repair Coverage or make Coverage imply Soundness.
- Keep the runtime order `reconcile → deterministic render coverage → semantic soundness → runtime completion/enforcement`.
- Do not implement Material Obligation Ledger, source closure, source evidence-link redesign, transactional writers, locking redesign, MCP upgrade, host negative matrix, ASH-06 x3/x10, live final release acceptance, PR, push, merge, rebase, reset, or cleanup of user changes.
- Do not weaken existing oracles/fixtures and do not add ASH-06-specific literals to production soundness logic.
- Use `apply_patch` for source/test/document edits and run each new test RED before writing its production implementation.

---

### Task 1: Lock the deterministic false-green regressions

**Files:**
- Create: `tests/test_proposition_soundness.py`
- Read-only references: `scripts/legal_proposition.py`, `scripts/proposition_rendering.py`, `scripts/proposition_reconciliation.py`

**Interfaces:**
- Consumes: Task 3 `LegalProposition`, `EvidenceRef`, `Materiality`, `Modality`, `Polarity`, `PropositionStatus`, and `build_render_contract`.
- Produces: failing examples that define `evaluate_soundness(propositions, contracts, draft)` and the six structured violation codes before any production implementation exists.

- [ ] **Step 1: Write the failing unit-test fixture and assertions.**

Create typed proposition helpers that use `EvidenceRef` for `CLOSED` propositions and no raw strings for semantic controls. Add one test per behavior:

```python
def test_rejected_quotation_only_has_coverage_but_fails_soundness():
    proposition = _closed_proposition()
    contract = build_render_contract(proposition)
    draft = (
        "다음 견해가 제시될 수 있다: "
        f"'{contract.slots[0].text} {contract.slots[1].text}' "
        "그러나 이 견해는 타당하지 않다."
    )

    coverage = reconcile_render_contracts([contract], draft)
    soundness = evaluate_soundness([proposition], [contract], draft)

    assert coverage.covered
    assert not soundness.soundness_passed
    assert _codes(soundness) == {"REJECTED_QUOTATION_ONLY"}
```

Add equivalent tests for an exact slot only inside a fenced code block, an exact slot only inside an `예시:` block, and a proposition in a bounded rejected-alternative paragraph. Add OPEN same-direction and opposite-direction definitive conclusion tests, both polarity directions, a condition-bypassing contradictory conclusion, and a generic-relaxation conclusion. Add positive tests for a quotation plus an independently adopted proposition and a fully consistent answer. Every failure assertion must inspect `SoundnessViolation.code` and at least one evidence field rather than a log string.

- [ ] **Step 2: Run the new tests and verify the failure is the missing production layer.**

Run:

```powershell
python -m pytest -q tests/test_proposition_soundness.py
```

Expected: collection fails because `scripts.proposition_soundness` and `evaluate_soundness` do not exist. If the failure is a fixture typo or an unrelated import problem, correct the test and rerun until the missing-layer failure is observed.

- [ ] **Step 3: Commit the RED regression contract.**

```powershell
git add -- tests/test_proposition_soundness.py
git commit -m "test(soundness): lock semantic false-green regressions"
```

---

### Task 2: Implement the standalone deterministic Soundness Gate

**Files:**
- Create: `scripts/proposition_soundness.py`
- Test: `tests/test_proposition_soundness.py`

**Interfaces:**
- Consumes: typed `LegalProposition` values and `PropositionRenderContract` slots from Task 3.
- Produces: `AnswerSpan`, `SoundnessViolation`, `SoundnessResult`, `classify_answer_regions`, `evaluate_soundness`, and `soundness_result_to_dict`.

Use these exact public shapes:

```python
AnswerRegionKind = Literal[
    "affirmative",
    "quotation",
    "code_block",
    "example",
    "rejected_alternative",
    "uncertainty",
    "final_conclusion",
]

@dataclass(frozen=True)
class AnswerSpan:
    kind: AnswerRegionKind
    text: str
    start: int
    end: int
    adopted: bool

@dataclass(frozen=True)
class SoundnessViolation:
    code: str
    proposition_id: str
    proposition_status: PropositionStatus
    materiality: Materiality
    modality: Modality | None
    polarity: Polarity | None
    relation_fields: tuple[str, ...]
    matched_region: str
    matched_span: str
    final_conclusion_span: str

@dataclass(frozen=True)
class SoundnessResult:
    soundness_passed: bool
    violations: tuple[SoundnessViolation, ...]

def classify_answer_regions(draft: str) -> tuple[AnswerSpan, ...]: ...
def evaluate_soundness(
    propositions: Sequence[LegalProposition],
    contracts: Sequence[PropositionRenderContract],
    draft: str,
) -> SoundnessResult: ...
def soundness_result_to_dict(result: SoundnessResult) -> dict[str, Any]: ...
```

- [ ] **Step 1: Implement raw-span classification without changing coverage.**

Scan the original draft before calling `normalize_rendered_text`. Preserve half-open character offsets. Recognize fenced code blocks using a bounded multiline fence match; recognize Markdown blockquotes and clearly delimited single/double quoted spans; recognize `예시:`/`example:` labelled blocks until the next blank or heading boundary; recognize `반대 견해`, `을설`, `배척`, `타당하지 않다`, `채택하지 않다`, and equivalent bounded rejection markers in the same paragraph/section; recognize `# 2. 검토결론`, `최종 결론:`, and `결론:` as final-conclusion regions; recognize the canonical OPEN uncertainty phrase as `uncertainty`. Mark code, example, quotation, rejected-alternative, and uncertainty regions as non-adopted. Mark ordinary prose and final-conclusion text as adopted. Keep the classifier structural and generic; do not add ASH-specific terms.

- [ ] **Step 2: Implement canonical slot matching and the six violation rules.**

Normalize only presentation differences using the existing `normalize_rendered_text` behavior, but match each required slot against classified spans. For `CLOSED` material propositions, accept a required slot only when it is present in an adopted span. If all matches are in quotation/rejected spans, emit `REJECTED_QUOTATION_ONLY`; if all matches are in code/example spans, emit `CODE_BLOCK_OR_EXAMPLE_ONLY`. If an adopted match exists alongside a quotation, do not emit either violation.

For `OPEN`, accept its uncertainty representation but emit `OPEN_PROMOTED_TO_CLOSED` when the final-conclusion span contains a definitive legal result marker rather than unresolved language. Compare final-conclusion markers against the canonical typed `Polarity`; never recalculate the canonical polarity from text. Emit `POLARITY_CONTRADICTION` for positive→negative and negative→positive reversals. Emit `FINAL_CONCLUSION_CONTRADICTION` for a bounded condition-bypass/opposite-effect statement even if the generic polarity marker is insufficient. When an explicit final conclusion exists, require the proposition's actual `condition`, `procedure`, legal action/operative verb, `legal_object`, and `legal_effect` fields to remain represented; otherwise emit `LEGAL_RELATION_DEGRADATION`.

- [ ] **Step 3: Serialize evidence without string-log parsing.**

Implement `soundness_result_to_dict` so enum fields are stored as their canonical `.value` strings and each violation includes `proposition_id`, `status`, `materiality`, `modality`, `polarity`, `relation_fields`, `matched_region`, `matched_span`, `final_conclusion_span`, and `code`. Keep `SoundnessResult` immutable and deterministic in proposition/violation order.

- [ ] **Step 4: Run the standalone tests and verify GREEN.**

Run:

```powershell
python -m pytest -q tests/test_proposition_soundness.py
```

Expected: all standalone soundness tests pass, including `coverage.covered is True` with `soundness_passed is False` for false-green fixtures and both positive non-overblocking cases.

- [ ] **Step 5: Commit the standalone implementation.**

```powershell
git add -- scripts/proposition_soundness.py tests/test_proposition_soundness.py
git commit -m "feat(soundness): add deterministic semantic gate"
```

---

### Task 3: Integrate Soundness after coverage and preserve runtime evidence

**Files:**
- Modify: `scripts/stop_synthesis_gate.py`
- Modify: `scripts/synthesis_runtime_state.py`
- Test: `tests/test_stop_synthesis_gate.py`
- Test: `tests/test_synthesis_runtime_state.py`

**Interfaces:**
- Consumes: `evaluate_soundness`, `SoundnessResult`, existing `DraftReconciliationResult`, existing `RelationReconciliationResult`, and existing bounded `repair_count` transitions.
- Produces: Stop responses that fail closed on soundness violations and first/second reconciliation records containing independent coverage and soundness evidence.

- [ ] **Step 1: Add Stop integration tests that fail before wiring.**

Add tests that save an active exact-turn state, build a draft with full render-slot coverage but a rejected quote or contradictory `결론:` section, call `handle_stop_event`, and assert:

```python
result = handle_stop_event(_event(draft), tmp_path)
stored = load_runtime_state("session-a", "turn-1", tmp_path)

assert result["decision"] == "block"
assert stored.first_reconciliation["covered"] is True
assert stored.first_reconciliation["soundness"]["soundness_passed"] is False
assert stored.first_reconciliation["soundness"]["violations"][0]["code"] == expected_code
```

Add a second-stop test proving the same soundness failure reaches the existing fail-closed exhausted path without a second repair. Add a positive test proving a valid quotation plus adopted proposition still returns `{}`. Add a runtime-state round-trip assertion that the structured soundness evidence remains JSON-safe and preserves canonical enum values.

- [ ] **Step 2: Run integration tests to verify the missing wiring failure.**

Run:

```powershell
python -m pytest -q tests/test_stop_synthesis_gate.py tests/test_synthesis_runtime_state.py
```

Expected: the new assertions fail because the Stop gate does not yet call Soundness and reconciliation evidence has no soundness object. Existing Task 3 tests must remain otherwise green.

- [ ] **Step 3: Wire Soundness after coverage/relation reconciliation.**

In `handle_stop_event`, keep these assignments independent:

```python
result = reconcile_render_contracts(contracts, draft)
relation_result = reconcile_range_exception_relation(state.propositions, draft)
soundness_result = evaluate_soundness(state.propositions, contracts, draft)
overall_covered = result.covered and (
    relation_result is None or relation_result.covered
)
overall_sound = soundness_result.soundness_passed
```

Use `overall_covered and overall_sound` only for completion. Do not mutate `result.covered` or relation coverage. If either gate fails, retain the existing one bounded repair and second-attempt fail-closed behavior. Extend failure details with violation codes/evidence without replacing the structured result with a parsed message.

- [ ] **Step 4: Persist compact soundness evidence.**

Extend `_reconciliation_summary` with:

```python
summary["soundness"] = soundness_result_to_dict(soundness_result)
```

Pass `soundness_result` through `record_reconciliation` as an optional keyword argument, preserving compatibility for existing callers. Keep first/second coverage summaries and existing range-exception evidence unchanged. Do not change `RUNTIME_STATE_SCHEMA_VERSION`, the registry fields, or the Task 3 enum normalization.

- [ ] **Step 5: Run integration tests and verify GREEN.**

Run:

```powershell
python -m pytest -q tests/test_stop_synthesis_gate.py tests/test_synthesis_runtime_state.py tests/test_proposition_soundness.py
```

Expected: all tests pass; a coverage-PASS/soundness-FAIL result is persisted and causes bounded repair/fail-closed enforcement, while a consistent answer returns `{}`.

- [ ] **Step 6: Commit the runtime integration.**

```powershell
git add -- scripts/stop_synthesis_gate.py scripts/synthesis_runtime_state.py tests/test_stop_synthesis_gate.py tests/test_synthesis_runtime_state.py
git commit -m "feat(soundness): enforce post-coverage runtime gate"
```

---

### Task 4: Verify responsibility boundaries and existing relation behavior

**Files:**
- Modify: `tests/test_proposition_runtime_policy_contract.py` only if a focused static contract assertion is needed.
- Test: `tests/test_proposition_reconciliation.py`
- Test: `tests/test_proposition_rendering.py`
- Test: `tests/test_synthesis_relation_regressions.py`
- Test: `tests/test_task1r_registry_parity.py`

**Interfaces:**
- Consumes: existing Task 1R range-exception relation and Task 3 typed semantic tests.
- Produces: regression evidence that Soundness is an additional consumer and does not change render coverage, relation reconciliation, or free-form semantic acceptance.

- [ ] **Step 1: Add a narrow responsibility-order assertion.**

Assert in the policy test that `stop_synthesis_gate.py` contains the ordered calls `reconcile_render_contracts`, `reconcile_range_exception_relation`, and `evaluate_soundness`, and that the completion condition includes independent soundness state. Do not assert implementation-private regex details in the policy test.

- [ ] **Step 2: Run the targeted upstream regression groups.**

Run:

```powershell
python -m pytest -q tests/test_proposition_reconciliation.py tests/test_proposition_rendering.py tests/test_proposition_runtime_contract.py tests/test_proposition_runtime_behavior.py tests/test_synthesis_relation_regressions.py tests/test_task1r_registry_parity.py tests/test_typed_semantic_controls.py
```

Expected: all existing coverage, render, relation, registry-parity, and Task 3 typed-control tests pass without fixture weakening. In particular, the deterministic range-exception relation remains unchanged and generic-relaxation coverage remains blocked.

- [ ] **Step 3: Commit only if the focused boundary test changed.**

```powershell
git add -- tests/test_proposition_runtime_policy_contract.py
git commit -m "test(soundness): lock post-coverage ownership"
```

If no policy-test change was required, keep the earlier implementation commits intact and record that no additional commit was needed.

---

### Task 5: Record acceptance evidence and run the complete verification sequence

**Files:**
- Create: `docs/task4-semantic-soundness-acceptance.md`
- Modify: `docs/architecture.md` to show the post-coverage Soundness Gate only if the existing architecture diagram still omits it.

**Interfaces:**
- Consumes: verified test outputs, repository/installed runtime digests, branch/base/implementation SHAs, and scoped review findings.
- Produces: the Task 4 final report with no claim of live final acceptance or ASH-06 x3/x10.

- [ ] **Step 1: Run the required deterministic and package checks.**

Run each command freshly from the Task 4 worktree:

```powershell
python -m pytest -q tests/test_proposition_soundness.py tests/test_stop_synthesis_gate.py tests/test_synthesis_runtime_state.py
python -m pytest -q tests/test_proposition_reconciliation.py tests/test_proposition_rendering.py tests/test_synthesis_relation_regressions.py tests/test_task1r_registry_parity.py tests/test_typed_semantic_controls.py
python -m pytest -q tests/test_release_gate.py tests/test_release_authority.py
python -m pytest -q
python -m compileall -q scripts tests
python scripts/validate_repo.py
python scripts/validate_authority_temporal_contract.py
python scripts/plugin_integrity.py --repo-root .
npm ci
npm audit --omit=dev
npm run mcp -- --help
git diff --check
```

Do not run ASH-06 x3, ASH-06 x10, or global live final release acceptance. If a command fails, use the systematic debugging workflow, add a regression before changing production code, and rerun the failed command.

- [ ] **Step 2: Check installed parity only with a separate Task 4 candidate.**

Inspect the supported installer/parity path, create a separate Task 4 candidate only if the repository tooling supports it, and record:

```text
repository runtime digest
installed runtime digest
candidate path
plugin version
```

Do not alter the existing `sage1993` binding or the Task 3 installation. If no supported candidate installation is available, report installed parity as not applicable rather than inventing a path.

- [ ] **Step 3: Perform scoped review against the required focus.**

Review the final diff and tests for quote-only, code/example, rejected alternative, OPEN promotion, both polarity reversals, conclusion contradiction, relation flattening, coverage/soundness mixing, free-form semantic regression, fail-open errors, and ASH-specific hardcoding. Any Critical/Important finding must be fixed, regression-tested, and reviewed again. No unresolved Critical/Important findings may remain.

- [ ] **Step 4: Write the acceptance report only from fresh evidence.**

Use the requested sections: Final Verdict, Baseline, Existing False-Green Inventory, Exact Root Cause, Soundness Architecture, Production Changes, Violation Contract, Regression Matrix, Verification, Repository/Installed State, Review Findings, Residual Risks, and Next Action. Report `Task 4: PASS` and `Task 5 readiness: READY` only if every acceptance checkbox is supported by fresh output; otherwise report `Task 4: HOLD` and `NEXT = Continue Task 4`.

- [ ] **Step 5: Commit acceptance documentation and verify the final diff.**

```powershell
git add -- docs/task4-semantic-soundness-acceptance.md docs/architecture.md
git commit -m "docs(soundness): record task 4 acceptance"
git diff HEAD~1 --check
git status --short --branch
```

