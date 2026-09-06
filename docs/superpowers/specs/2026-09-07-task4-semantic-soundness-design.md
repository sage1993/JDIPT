# Task 4 — Semantic Soundness Gate Design

## Goal

Add a deterministic post-coverage Semantic Soundness Gate that distinguishes a
canonical legal proposition being mentioned from being adopted in the answer's
meaning and final conclusion.

The Task 3 typed semantic contract remains unchanged:

```text
Materiality: MATERIAL / NON_MATERIAL
Modality: MAY / MUST / MUST_NOT / MAY_NOT
Polarity: POSITIVE / NEGATIVE
Status: OPEN / CLOSED
```

## Scope and invariants

The runtime order is fixed:

```text
Canonical LegalProposition Registry
        ↓
Registry Closure Gate
        ↓
Deterministic Render Coverage
        ↓
Semantic Soundness Gate
        ↓
Exact-turn Runtime Enforcement
```

Coverage and soundness are independent results. Coverage does not repair or
upgrade soundness, and soundness does not rewrite coverage. The following
states are valid and must remain observable:

```text
coverage = PASS
soundness = FAIL
```

The authoritative gate is deterministic. No LLM judge is required for a
PASS. Task 4 does not add material-obligation/source-closure ownership,
transactional state writing, concurrency changes, MCP upgrades, live release
acceptance, or ASH-specific production logic.

## Existing false-green inventory

| Layer | Input | Output | Can currently declare success? | Can distinguish quote/example? | Can detect contradiction? |
| --- | --- | --- | --- | --- | --- |
| Reconciliation | `PropositionRenderContract[]`, draft text | `DraftReconciliationResult(covered, missing_slots)` | No release authority, but it declares textual coverage | No; normalized draft is answer-wide | No |
| Rendering | typed `LegalProposition` | deterministic effect/temporal/open slots | No; it supplies required slots | No; it emits plain slot text | No |
| Coverage | normalized render slots and answer-wide draft | `covered=True` when every slot is a contiguous normalized substring | Yes, for textual slot coverage | No; Markdown/code/quotation markers are normalized away | No |
| Existing oracle | case fixture and final answer | case-specific PASS/FAIL/INVALID markers | Yes for its case contract | Only where an individual oracle happens to encode it | Not as a general runtime contract |
| Runtime gate | exact-turn state and `last_assistant_message` | `{}`, bounded block, or fail-closed response | Yes when render/relation coverage is true | No; it currently calls coverage after answer-wide normalization | No |

The direct false-green path is:

```text
required slot exists somewhere in the draft
→ normalize_rendered_text removes presentation markers
→ reconcile_render_contracts returns covered=True
→ Stop gate returns {}
```

The path cannot tell whether the match is a quotation, code block, example,
rejected alternative, uncertainty-only statement, or adopted conclusion.

## Design

### 1. Semantic Soundness module

Create `scripts/proposition_soundness.py` with one focused deterministic
interface:

```python
def evaluate_soundness(
    propositions: Sequence[LegalProposition],
    contracts: Sequence[PropositionRenderContract],
    draft: str,
) -> SoundnessResult:
    ...
```

The module owns only answer-region classification, canonical-slot adoption,
typed semantic consistency, final-conclusion contradiction checks, and legal
relation preservation. It does not own registry state, repair counters,
release aggregation, or source closure.

The result is structured and serializable:

```python
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
```

The violation codes are:

```text
REJECTED_QUOTATION_ONLY
CODE_BLOCK_OR_EXAMPLE_ONLY
OPEN_PROMOTED_TO_CLOSED
POLARITY_CONTRADICTION
FINAL_CONCLUSION_CONTRADICTION
LEGAL_RELATION_DEGRADATION
```

### 2. Answer-region classification

Use a small deterministic Markdown/paragraph classifier, not a general NLP
parser. It preserves raw spans before presentation normalization and recognizes:

- fenced code blocks;
- Markdown block quotations and clearly delimited inline quotations;
- example-labelled blocks;
- rejected-alternative markers in the same bounded paragraph/section;
- the existing `# 2. 검토결론` or explicit conclusion-labelled region;
- uncertainty markers used by the canonical OPEN render slot.

All other non-excluded prose is an adopted/affirmative candidate region. A
quotation is not itself a failure: a required slot is accepted when a separate
adopted region also contains the required canonical representation.

The classifier returns region and span metadata sufficient for reproducible
evidence. It must not infer a canonical proposition's polarity from raw text;
the canonical `Polarity` enum remains authoritative. Output marker matching is
only used to observe whether the final conclusion contradicts that typed value.

### 3. Soundness rules

For each material proposition:

1. `CLOSED` required effect/temporal slots must be matched in an adopted
   region. A quotation, rejected alternative, code block, or example-only
   match fails soundness while leaving coverage unchanged.
2. `OPEN` propositions may be represented by their uncertainty slot, but a
   definitive final conclusion that promotes the proposition to a closed
   legal result fails with `OPEN_PROMOTED_TO_CLOSED`.
3. Final-conclusion polarity is compared with the canonical typed polarity.
   Both positive→negative and negative→positive reversals fail with
   `POLARITY_CONTRADICTION`.
4. Structured contradiction patterns that negate or bypass the canonical
   condition/action/effect relationship fail with
   `FINAL_CONCLUSION_CONTRADICTION`, even when polarity markers alone are not
   sufficient.
5. When a final-conclusion region is present, it must preserve the canonical
   legal relation fields required by the proposition. A source-specific legal
   action/effect cannot be reduced to an unqualified generic relaxation. A
   missing condition, procedure, legal action, object, or effect is reported as
   `LEGAL_RELATION_DEGRADATION` using the proposition's actual fields, never
   ASH-specific literals.

The classifier and rules are deliberately conservative. They only classify
bounded structural and semantic markers; they do not attempt theorem proving
or unrestricted paraphrase understanding.

### 4. Runtime integration and evidence

In `scripts/stop_synthesis_gate.py`, after render coverage and existing range
relation reconciliation:

```text
reconcile_render_contracts
→ reconcile_range_exception_relation
→ evaluate_soundness
→ persist coverage + soundness evidence
→ bounded repair or completion response
```

The existing coverage and range-relation results remain unchanged. A soundness
failure follows the existing one-repair/fail-closed path and never causes an
unbounded regeneration loop.

In `scripts/synthesis_runtime_state.py`, extend the compact first/second
reconciliation evidence with a `soundness` object containing
`soundness_passed` and structured violation evidence. Do not change the
Task 3 enum contract or introduce a new state owner/schema writer.

## Testing strategy

Add deterministic unit tests for the soundness module and Stop integration for:

- rejected quotation only;
- fenced code-block only;
- example only;
- explicitly rejected alternative;
- OPEN with same-direction definitive conclusion;
- OPEN with opposite definitive conclusion;
- positive canonical polarity with negative final conclusion;
- negative canonical polarity with positive final conclusion;
- final-conclusion contradiction beyond polarity;
- source-specific relation reduced to generic relaxation;
- valid adopted proposition with a quotation also present;
- fully consistent answer.

Retain and rerun existing reconciliation, render, range-exception relation,
Task 1 registry, Task 2 release authority, and Task 3 typed semantic tests.
No existing oracle or expected fixture may be weakened to make a new test pass.

## Acceptance boundary

Task 4 is PASS only when the standalone soundness layer is demonstrably after
coverage, both results are independent, all required negative regressions fail
closed with structured evidence, both positive cases pass, and the existing
Task 1–3 contracts remain green. ASH-06 x3/x10 and global live final
acceptance are outside this task and must not be claimed here.
