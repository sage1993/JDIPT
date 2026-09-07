# Task 4 — Semantic Soundness Gate Acceptance

## A. Final Verdict

```text
Task 4: PASS
Task 5 readiness: READY
Overall: PASS
```

This task adds a deterministic post-coverage Semantic Soundness Gate. It does not implement Source/Obligation Closure, live final release acceptance, ASH-06 x3/x10, or any Task 5 authority.

## B. Baseline

```text
Task 4 base SHA: c51108c0ec7e05c6161bbc232eba37d925e8c7ec
implementation commits: eae495c, 404348b, 646b90f, 65f8462, ea3eff3, b18d574, c3e49e0, 345480a
acceptance/docs commit: this document's commit
branch: codex/task4-semantic-soundness
working tree: clean at acceptance commit
```

The implementation was performed in the isolated worktree `F:\2026-PJ\JDIPT\.worktrees\task4-semantic-soundness`. The original dirty user worktree and the existing `sage1993` binding were preserved.

## C. Existing False-Green Inventory

| Layer | Input | Output | Can currently declare success? | Can distinguish quote/example? | Can detect contradiction? |
| --- | --- | --- | --- | --- | --- |
| reconciliation | canonical render contracts and answer text | `ReconciliationResult.covered` and missing slots | Yes, for textual slot coverage | No; normalized answer text was treated as one searchable body | No |
| rendering | typed canonical proposition | deterministic slot text | No final verdict; produces required text | No region/adoption metadata | No |
| coverage | render contracts and final draft | coverage boolean plus missing-slot evidence | Yes | No, before Task 4 all regions could satisfy a slot | No |
| existing oracle | fixture/answer output | component semantic verdict | Yes for its own fixture contract | Not in the runtime coverage path | Limited to oracle-specific markers, not canonical final adoption |
| runtime gate | exact-turn state, draft, coverage and relation results | Stop allow/block response | Yes when coverage and existing relation checks passed | No | No |

The false-green reproduction on the Task 3 base was:

```text
required render slots inside a rejected quotation
→ coverage=True
→ Stop response={}
```

## D. Exact Root Cause

The former path normalized the complete draft and searched for each required slot anywhere in that text. Quotation, example, code, rejected alternative, uncertainty, affirmative answer, and final conclusion were not represented as distinct regions. Consequently, textual presence was allowed to stand in for adopted meaning:

```text
Mentioned ≠ Adopted
Coverage ≠ Soundness
```

The runtime Stop gate consumed coverage/relation success but had no independent semantic adoption, typed-polarity, status, final-conclusion, or legal-relation preservation result.

## E. Soundness Architecture

```text
canonical proposition registry
        ↓
registry closure gate
        ↓
deterministic render coverage
        ↓
semantic soundness gate
        ↓
exact-turn runtime enforcement
```

- Reconciliation calculates structural proposition-to-slot correspondence.
- Rendering emits deterministic canonical slots.
- Coverage checks textual presence in required slots.
- Soundness classifies bounded output regions, checks adoption, preserves typed status/polarity and legal relation fields, and checks the final conclusion.
- Runtime enforcement combines coverage, existing range-exception relation checks, and soundness; a soundness failure blocks or consumes the existing single bounded repair path.
- Release authority and runtime state ownership remain outside the soundness module.

Coverage and soundness are persisted independently. A valid state is therefore possible where `covered=true` and `soundness_passed=false`.

## F. Production Changes

- `scripts/proposition_soundness.py`: added the deterministic region classifier, typed soundness evaluator, structured violation evidence, and serializer.
- `scripts/stop_synthesis_gate.py`: added the post-coverage soundness call, fail-closed handling, bounded repair integration, and semantic failure reason.
- `scripts/synthesis_runtime_state.py`: preserves soundness evidence under the existing first/second reconciliation records without changing runtime ownership.
- `scripts/plugin_integrity.py`: includes the new runtime module in repository/installed parity manifests.
- `scripts/validate_repo.py`: requires the soundness module and its production markers.
- `docs/architecture.md`: records the coverage → soundness → runtime ordering.
- `tests/test_proposition_soundness.py`: locks the false-green, contradiction, relation, evidence, and non-overblocking cases.
- `tests/test_stop_synthesis_gate.py`, `tests/test_synthesis_runtime_state.py`, and `tests/test_plugin_integrity_runtime_bundle.py`: lock runtime integration, evidence persistence, and bundle parity.

No Task 2 release manifest schema or authority implementation was changed. Soundness failures are hard Stop failures and are retained as structured reconciliation evidence for downstream release evidence consumption.

## G. Violation Contract

```text
REJECTED_QUOTATION_ONLY
CODE_BLOCK_OR_EXAMPLE_ONLY
OPEN_PROMOTED_TO_CLOSED
POLARITY_CONTRADICTION
FINAL_CONCLUSION_CONTRADICTION
LEGAL_RELATION_DEGRADATION
```

Each violation carries proposition ID, typed status/materiality/modality/polarity, relevant relation-field names, matched region/span, and final-conclusion span. No LLM judge is required for the authoritative result.

## H. Regression Matrix

| Scenario | Expected | Actual | Verdict |
| --- | --- | --- | --- |
| rejected quote only | FAIL | `REJECTED_QUOTATION_ONLY` | PASS |
| code block only | FAIL | `CODE_BLOCK_OR_EXAMPLE_ONLY` | PASS |
| example only | FAIL | `CODE_BLOCK_OR_EXAMPLE_ONLY` | PASS |
| explicitly rejected alternative | FAIL | `REJECTED_QUOTATION_ONLY` | PASS |
| OPEN → definitive same-direction conclusion | FAIL | `OPEN_PROMOTED_TO_CLOSED` | PASS |
| OPEN → definitive opposite conclusion | FAIL | `OPEN_PROMOTED_TO_CLOSED` | PASS |
| POSITIVE → negative conclusion | FAIL | `POLARITY_CONTRADICTION` | PASS |
| NEGATIVE → positive conclusion | FAIL | `POLARITY_CONTRADICTION` | PASS |
| contradictory final conclusion | FAIL | `FINAL_CONCLUSION_CONTRADICTION` | PASS |
| source-specific relation degradation | FAIL | `LEGAL_RELATION_DEGRADATION` | PASS |
| quote + valid adopted proposition | PASS | PASS | PASS |
| fully consistent answer | PASS | PASS | PASS |

Quotation presence alone is not rejected: a quotation plus a separately adopted canonical proposition passes.

## I. Verification

```text
targeted soundness/runtime/bundle: PASS — 42 passed
reconciliation/render coverage: PASS — 25 passed
Task 3 typed semantics: PASS — 44 passed
Task 1R range-exception and registry parity: PASS — 12 passed
Task 2 unified authority: PASS — 34 passed
full pytest: PASS — 355 passed
compileall: PASS
validate_repo: PASS
authority/temporal: PASS
plugin_integrity: PASS — repository/installed candidate mismatches=[]
npm ci: PASS — 202 packages added, 0 vulnerabilities
npm audit: PASS — 0 vulnerabilities
MCP smoke: PASS — `npm run mcp -- --help`
diff check: PASS
```

The prohibited ASH-06 x3/x10 and global live final release acceptance were not run and are not claimed.

## J. Repository / Installed State

```text
repository SHA: acceptance commit HEAD
repository runtime digest: e1293cea40a34f27b155accfa158e7ab902f7c3e8a9b8c36147d5f379e509620
installed digest: e1293cea40a34f27b155accfa158e7ab902f7c3e8a9b8c36147d5f379e509620
candidate path: C:\Users\KSH\.codex\plugins\cache\task4-semantic-soundness\jdipt\0.2.4
plugin version: 0.2.4
```

The candidate was installed through the supported Codex marketplace/plugin installer under the isolated marketplace `task4-semantic-soundness`. The existing `sage1993` installation was not overwritten.

## K. Review Findings

- Critical findings: 0.
- Important findings: 0.
- Review focus covered quotation-only false green, code/example classification, rejected alternatives, OPEN promotion, polarity reversal, final-conclusion contradiction, legal relation flattening, coverage/soundness ownership, typed semantic preservation, fail-closed errors, and ASH-specific hardcoding.
- The scoped review confirmed that the runtime gate does not repair coverage from soundness, does not add an unbounded regeneration loop, and does not use a model judge for authoritative PASS.

## L. Residual Risks

- The region classifier intentionally supports bounded deterministic Markdown/paragraph patterns; it is not a general natural-language theorem prover.
- Source/Obligation Closure and unresolved-source policy remain Task 5 responsibilities.
- No active host runtime digest or live final release acceptance was collected.

## M. Next Action

```text
NEXT = Task 5 — Source / Obligation Closure
```
