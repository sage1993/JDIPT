# Task 3 — Typed Semantic Controls Acceptance

## A. Final Verdict

```text
Task 3: PASS
Task 4 readiness: READY
Overall: PASS
```

This report covers the typed semantic-control boundary only. Semantic Soundness, quotation/example rejection, final-answer contradiction detection, source-resolution closure, live final release acceptance, ASH-06 x3, and ASH-06 x10 remain outside this task.

## B. Baseline

```text
Task 3 base SHA: 8fcf3fdc726887ee3871a1772c1946150966521f
Task 3 commit: 090e43723e8e9b22a7c67db708e594853a808ef8
branch: codex/task3-typed-semantic-controls
working tree: clean at implementation commit before this report commit
```

The implementation was performed in an isolated worktree because the original shared worktree contained unrelated user changes and was not descended from the requested Task 3 base. No reset, rebase, push, merge, or cleanup of the original worktree was performed.

## C. Existing Semantic Inventory

| Field | Producer | Raw representation | Normalizer | Validator | Consumer | Risk closed |
| --- | --- | --- | --- | --- | --- | --- |
| materiality | registry request and `LegalProposition` construction | legacy `material`, `non_material`, `non-material`; canonical uppercase | `normalize_materiality` before construction | `Materiality` invariant in `LegalProposition`; registry required field | rendering and range-exception relation selection | silent material default, `critical`/`important` guessing, non-material downgrade |
| modality | registry request and proposition fixtures | canonical values plus explicit `may`, `must`, `mandatory`, `must not`, `may not` | `normalize_modality` before construction | `Modality` invariant in `LegalProposition` | deterministic renderer and relation payload | substring matching and MUST/MUST_NOT or MAY/MAY_NOT collapse |
| polarity | registry request and proposition fixtures | canonical values plus exact lowercase `positive`/`negative` | `normalize_polarity` before construction | `Polarity` invariant in `LegalProposition` | typed relation polarity preservation | unknown/empty/truthy polarity default |
| status | registry request and runtime JSON | canonical `OPEN`/`CLOSED` | `normalize_status` before construction/deserialization | `PropositionStatus` invariant in `LegalProposition` | rendering lifecycle and runtime persistence | unknown/missing status defaulting to `CLOSED` |

The canonical domain owner is `scripts/legal_proposition.py`; `scripts/proposition_registry.py` is the external registry adapter and calls the shared normalizers exactly once before domain construction. Runtime deserialization uses the same explicit boundary normalizers before reconstructing the domain object.

## D. Exact Root Cause

`LegalProposition` previously stored all four controls as unrestricted strings. The registry also used `materiality=_text_arg(...) or "material"`, so missing/empty materiality could silently become material. Rendering then called `.lower()` and searched substrings such as `"required"`, `"must not"`, and `"prohibited"` in modality, polarity, and legal-action text. This permitted false classification, collapsed negative modalities, and made unknown values indistinguishable from valid semantic values.

## E. Canonical Semantic Contract

```text
Materiality:
  MATERIAL
  NON_MATERIAL

Modality:
  MAY
  MUST
  MUST_NOT
  MAY_NOT

Polarity:
  POSITIVE
  NEGATIVE

Status:
  OPEN
  CLOSED
```

The dataclass stores enum instances, not raw strings. `None` remains permitted only for the existing optional `modality`/`polarity` fields on partial `OPEN` propositions; `status` and `materiality` are required.

## F. Adapter Policy

Supported aliases are exact dictionary entries only:

| Control | Supported legacy aliases | Rejected examples |
| --- | --- | --- |
| materiality | `material`, `non_material`, `non-material` | `criticality`, `critical`, `important`, `not required`, empty, missing |
| modality | `may`, `must`, `mandatory`, `must not`, `may not` | `SHOULD`, `REQUIRED`, `PROHIBITED`, `required`, `shall`, `must-not`, `not required` |
| polarity | `positive`, `negative` | `NEUTRAL`, `UNKNOWN`, empty, modality-derived values |
| status | no lowercase or synonym aliases; canonical `OPEN`/`CLOSED` | `PENDING`, `DONE`, empty, missing |

Canonical uppercase values are also accepted at the external boundary and are the only values written to persistence. Renderer-only heuristic tokens were not promoted to aliases.

## G. Production Changes

- `scripts/legal_proposition.py`: added `Materiality`, `Modality`, `Polarity`, and `PropositionStatus` `StrEnum`s; added shared strict normalizers; made domain fields typed and rejected raw strings/unknown values.
- `scripts/proposition_registry.py`: removed silent materiality default; normalized all four controls before constructing `LegalProposition`.
- `scripts/synthesis_runtime_state.py`: serializes enum `.value` strings, normalizes persisted values before deserialization, and fails closed on unknown persisted controls.
- `scripts/proposition_rendering.py`: replaced materiality/modality/status substring heuristics with enum comparisons.
- `scripts/proposition_relations.py`: uses typed materiality/status/polarity values while preserving existing range-exception relation behavior.
- `scripts/jdipt_runtime_mcp.py`: restricted semantic properties to explicit finite schema enums and made materiality required.
- Related fixtures/regressions now construct domain propositions with typed values while registry/MCP fixtures continue to exercise supported legacy aliases.

## H. Regression Matrix

| Scenario | Expected | Actual | Verdict |
| --- | --- | --- | --- |
| unknown materiality | REJECT | `PropositionValidationError` | PASS |
| silent downgrade | REJECT | missing materiality rejected; no default | PASS |
| `not required` | REJECT | rejected as modality/materiality alias | PASS |
| `critical` | REJECT | rejected | PASS |
| `important` | REJECT | rejected | PASS |
| unknown modality | REJECT | `SHOULD`/`REQUIRED`/`PROHIBITED` rejected | PASS |
| MUST vs MUST_NOT | distinct | distinct enum values and render branches | PASS |
| MAY vs MAY_NOT | distinct | distinct enum values and render branches | PASS |
| unknown polarity | REJECT | `NEUTRAL`/`UNKNOWN`/empty rejected | PASS |
| unknown status | REJECT | `PENDING`/`DONE`/empty rejected | PASS |
| direct domain bypass | REJECT | raw unknown and raw noncanonical domain values rejected | PASS |
| serialization | exact round-trip | canonical uppercase JSON and enum equality preserved | PASS |

## I. Verification

```text
targeted semantics: PASS — 86 passed
registry: PASS — included in targeted suite and full suite
rendering: PASS — 41 passed in rendering/relation/Task 1R group
serialization round-trip: PASS — typed semantic controls round-trip exactly
Task 1R: PASS — 41 passed in rendering/relation/Task 1R group
Task 2 authority: PASS — 34 passed
full pytest: PASS — 335 passed
compileall: PASS
validate_repo: PASS
authority/temporal: PASS
plugin_integrity: PASS — repository/installed candidate mismatches=[]
npm ci: PASS — 202 packages added, 0 vulnerabilities
npm audit: PASS — 0 vulnerabilities
MCP smoke: PASS — package help and stdio initialize
diff check: PASS
```

The pytest TEMP 0700 ACL fingerprint appeared during the first un-escalated RED attempt and was resolved by running filesystem-dependent verification with normal temporary-directory access. It was not attributed to Task 3 code.

## J. Repository / Installed State

```text
repository SHA: 090e43723e8e9b22a7c67db708e594853a808ef8
repository runtime digest: 449fbe4e2feaaefa0425d625635ddbead2642d8683889e41e54b5b44df8f66a9
installed candidate: C:\Users\KSH\.codex\plugins\cache\task3-typed-semantic-controls\jdipt\0.2.4
installed digest: 449fbe4e2feaaefa0425d625635ddbead2642d8683889e41e54b5b44df8f66a9
runtime digest if checked: not checked in a live host thread; repository/installed candidate parity checked
approved sage1993 binding: preserved; original stabilization worktree remained unchanged
```

## K. Review Findings

- Critical findings: 0.
- Important findings: 0.
- The review specifically checked unknown-value fail-open paths, materiality defaults, substring classification, alias over-acceptance, schema/domain mismatch, persistence drift, renderer re-inference, direct construction bypass, Task 1R regressions, and Task 2 release bypass.
- The final review narrowed legacy modality aliases to values supported by the explicit contract/current fixture (`mandatory`) plus canonical/explicit negative forms; heuristic-only tokens were rejected.

## L. Residual Risks

- Semantic Soundness remains Task 4 and is intentionally not implemented here.
- No live final release acceptance, ASH-06 x3, or ASH-06 x10 was run or claimed.
- The installed parity check covers the isolated Task 3 candidate; no fresh active host runtime digest was claimed.

## M. Next Action

```text
NEXT = Task 4 — Semantic Soundness
```
