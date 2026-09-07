# Task 5 — Source / Obligation Closure Acceptance

## A. Final Verdict

```text
Task 5: PASS
Task 6 readiness: READY
Overall: PASS
```

Task 5 is PASS for the repository runtime and the isolated candidate bundle. The existing `sage1993` marketplace binding was not changed; its default integrity check remains stale until a separately authorized installation refresh.

## B. Baseline

```text
Task 4 base SHA: c51108c0ec7e05c6161bbc232eba37d925e8c7ec
Task 4 implementation commit: 345480a678751acf82c1c85aca95724139146444
Task 4 acceptance/docs commit: 5c0cd31ee75b54122cf37380df1b07887130a8ce
Task 4 branch: codex/task4-semantic-soundness
Task 4 final state: PASS
Task 5 implementation commit: 6ca5b06
Task 5 branch: codex/task5-source-obligation-closure
```

The Task 4 closure worktree was clean before Task 5 began. The original dirty user worktree and the `sage1993` binding were preserved.

## C. Root Cause

Task 4 separated render coverage from semantic soundness, but a candidate could still pass when a source merely existed, when a source was related but did not support the complete proposition, when the source authority or version was insufficient, or when a final answer weakened or omitted a legal obligation. The missing contract was therefore:

```text
source exists ≠ source supports the proposition
source supports the proposition ≠ authority is sufficient
authority is sufficient ≠ temporal closure is complete
coverage/soundness pass ≠ obligation and dependency closure
```

## D. Architecture

The implemented exact-turn path is:

```text
register_material_proposition
    → canonical LegalProposition / EvidenceRef
    → deterministic render contracts
    → Stop exact-turn state load
    → render coverage
    → Task 1R relation reconciliation
    → Task 4 Semantic Soundness
    → Source / Authority / Temporal Closure
    → Obligation / Dependency / Final-Conclusion Closure
    → one bounded repair
    → re-evaluation
    → PASS or fail-closed Stop
```

`coverage`, `soundness`, `source_closure`, and `obligation_closure` remain independent persisted result objects. A Task 4 soundness failure cannot be overwritten by a Task 5 source result.

Production modules:

- `scripts/proposition_source_closure.py`
- `scripts/proposition_obligation_closure.py`
- `scripts/stop_synthesis_gate.py`
- `scripts/synthesis_runtime_state.py`

The runtime bundle and repository validators include both new modules.

## E. Source Closure Contract

For each material proposition, the source evaluator checks the complete bounded relation: subject, legal action, legal object, condition, procedure, modality, polarity, and legal effect. The adopted answer must also contain the source identifier or locator. Citation markers, titles, URLs, same-topic text, rejected quotations, examples, and code blocks do not close a source by themselves.

The evaluator preserves the following positive progression independently:

```text
SOURCE_ABSENT
→ SOURCE_PRESENT
→ SOURCE_MATCHED
→ SOURCE_SUPPORTING
→ SOURCE_AUTHORITY_SATISFIED
→ SOURCE_TEMPORALLY_VALID
→ SOURCE_CLOSED
```

`SourceClosureAssessment` records the proposition ID, progression state, source ID, source span, matched span, required/actual authority, required/actual temporal status, and reason. Non-material propositions do not force a source failure.

## F. Authority / Temporal Closure

`AuthorityRequirement` and `TemporalRequirement` are typed boundary controls on the canonical proposition. They are normalized only at the registry/MCP boundary and restored as typed values from exact-turn state. Source evaluation uses the existing `EvidenceRef.authority_kind` and `EvidenceRef.temporal_status` model.

The evaluator rejects a lower or incompatible authority, including guidance where primary authority is required, and distinguishes government interpretation from precedent. A current proposition cannot close on a historical-only source or on an unresolved current source. The resulting violations are `INSUFFICIENT_AUTHORITY`, `OUTDATED_SOURCE_USED`, and `TEMPORAL_SOURCE_UNRESOLVED`.

## G. Obligation Closure

The obligation evaluator operates only on adopted answer regions and preserves:

- `MUST` as a mandatory expression; `MUST → MAY` is `MUST_DEGRADED_TO_MAY`.
- `MUST_NOT` / `MAY_NOT` as a prohibition; weakening it is `MUST_NOT_DEGRADED`.
- required conditions as conditions, not optional considerations.
- mandatory procedures as prerequisites, not descriptive background.
- exceptions and their limiting language, not an unconditional general rule.
- source-specific legal action and effect, not a generic relaxation.

An absent deterministic render contract for a material proposition is `OBLIGATION_DROPPED`, rather than an implicit pass. A final conclusion must preserve the proposition relation and polarity and may not be stronger, broader, or opposite in polarity.

## H. Dependency Closure

Base and exception dependencies are checked by proposition ID. Missing dependencies produce `DEPENDENCY_OMITTED`; `OPEN` dependencies produce `DEPENDENCY_OPEN`. A dependency effect in a rejected quotation, example, or code block does not satisfy closure. Source evaluation independently checks every material dependency for support, authority, and temporal validity.

## I. Violation Contract

The production violation set is:

```text
SOURCE_REQUIRED_BUT_MISSING
SOURCE_PRESENT_BUT_NOT_SUPPORTING
SOURCE_PROPOSITION_MISMATCH
INSUFFICIENT_AUTHORITY
OUTDATED_SOURCE_USED
TEMPORAL_SOURCE_UNRESOLVED
MATERIAL_SOURCE_OMITTED
OBLIGATION_DROPPED
MUST_DEGRADED_TO_MAY
MUST_NOT_DEGRADED
CONDITION_DROPPED
EXCEPTION_DROPPED
PROCEDURAL_PREREQUISITE_DROPPED
DEPENDENCY_OPEN
DEPENDENCY_OMITTED
FINAL_CONCLUSION_UNSUPPORTED
OPEN_PROMOTED_TO_CLOSED
```

Every source or obligation violation retains proposition ID, materiality, modality, polarity, status, required/matched condition, exception, procedure, dependency IDs, matched region/span, final-conclusion span, source evidence where applicable, and a reason.

## J. Runtime Enforcement

The Stop gate requires all of the following for completion:

```text
coverage
Task 1R relation closure
Task 4 semantic soundness
source closure
authority closure
temporal source closure
obligation closure
dependency closure
final-conclusion support
```

A first failure persists the independent results and requests at most one bounded repair. The second failed Stop event is fail-closed and does not emit the candidate answer. State is keyed by exact session and turn identity; closure results are not reused across turns.

## K. Regression Matrix

| Area | Scenario coverage | Actual result |
|---|---|---|
| Source | missing evidence; irrelevant span; citation without support; opposite polarity; rejected citation | PASS — failure cases blocked |
| Authority | lower guidance source for a primary requirement | PASS — `INSUFFICIENT_AUTHORITY` |
| Temporal | historical source; unresolved current source | PASS — `OUTDATED_SOURCE_USED` / `TEMPORAL_SOURCE_UNRESOLVED` |
| Source success | exact supporting span plus adopted source anchor; non-material proposition without source | PASS |
| Obligation | dropped `MUST`; `MUST → MAY`; weakened `MUST_NOT`; dropped condition, exception, procedure | PASS — distinct violations |
| Dependency | missing dependency; `OPEN` dependency; rejected-region dependency | PASS — `DEPENDENCY_OMITTED` / `DEPENDENCY_OPEN` |
| Conclusion | unsupported generic conclusion and polarity/modality mismatch | PASS — `FINAL_CONCLUSION_UNSUPPORTED` or modality violation |
| Runtime | source failure after coverage/soundness; independent persisted closure results; second failure | PASS — bounded repair/fail-closed |
| Cross-task | Task 1R–4 fixtures updated only where valid answers now require Task 5 source/obligation fields | PASS |

Initial TDD RED evidence: 16 negative Task 5 tests failed against the absent closure implementation. No expected failure was changed to pass by weakening its oracle. After implementation and the final rejected-dependency case, the focused Task 5 suite passed 26 tests.

## L. Verification Results

```text
Task 5 focused: 26 passed
Task 4 soundness/runtime: 31 passed
Task 3 typed semantic: 66 passed
Task 2 authority/temporal: 10 passed
Task 1R proposition/dependency: 16 passed
reconciliation/render/runtime: 21 passed
bundle/validators test group: 14 passed
full pytest: 386 passed
compileall: PASS
validate_repo.py: PASS
validate_authority_temporal_contract.py: PASS
npm ci: PASS
npm audit: PASS (0 vulnerabilities)
MCP smoke (`npm run mcp -- --help`): PASS (exit 0)
git diff --check: PASS (no content errors)
```

The Windows pytest temporary-directory ACL issue was handled by rerunning the same tests with the required elevated tool execution; it did not require a test or production fallback.

## M. Installed Candidate State

```text
repository runtime digest: generated by plugin_integrity.py
installed candidate runtime digest: exact match
candidate path: F:\2026-PJ\JDIPT\.worktrees\task5-source-obligation-closure-candidate
mismatches: []
candidate plugin integrity: PASS
```

The unqualified integrity check resolves the pre-existing `sage1993` marketplace installation and reports stale digests/missing Task 5 modules. That binding was intentionally not modified. The isolated candidate check above is the acceptance parity result.

## N. Independent Review

```text
Critical findings at acceptance: 0
Important findings at acceptance: 0
```

During review, one important false-pass path was identified: a material proposition with no deterministic render contract was skipped by the obligation evaluator. It was corrected to emit `OBLIGATION_DROPPED` and covered by a regression test before acceptance. The rejected-dependency-region case was also added before the final 386-test run.

## O. Residual Risks

- The marketplace `sage1993` binding remains stale until a separately authorized install/refresh; no marketplace mutation, push, PR, or merge was performed.
- Task 5 uses a bounded deterministic lexical relation classifier. It is intentionally not a general natural-language theorem prover; ambiguous material propositions remain failures or unresolved states.
- ASH-06 x3/x10, global live acceptance, and final release acceptance were not claimed as Task 5 gates.
- The MCP verification performed the package CLI smoke; it did not perform a live external legal-source query requiring credentials.

## P. Next Action

```text
NEXT = Task 6 — Create the Single Registry Service and Remove the Duplicate Writer
```

Acceptance/docs commit is recorded in the final Task 5 report after this document is committed.
