# JDIPT Correctness Stabilization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Converge JDIPT on the R2 canonical legal-proposition core, eliminate the confirmed false-green/runtime-state/release-authority defects, and prove source-to-final-answer correctness on one exact runtime snapshot before release.

**Architecture:** Keep the existing Skill-first / external Korean Law MCP architecture and use the R2 canonical `LegalProposition → Registry → Render Contract → Reconciliation → Runtime State` path as the domain core. Port only verified L1 runtime-enforcement invariants into that core, add a separate semantic-soundness layer and a source/obligation closure only if an independently observable source boundary is proven, then make one release authority own every required gate.

**Tech Stack:** Python 3.13, pytest, stdlib dataclasses/enum/json/pathlib/tempfile, cross-platform stdlib file locking (`fcntl` on POSIX, `msvcrt` on Windows), Node.js 20.19.0, npm, `korean-law-mcp`, Codex Plugin hooks/MCP, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-06-jdipt-correctness-stabilization-design.md`

## Global Constraints

- R2 `refactor/legal-proposition-core-working2` is the canonical domain-core baseline unless Task 1 evidence disproves that assumption.
- Preserve the user's existing R1/L1 dirty working tree. Do not `reset`, `clean`, `restore`, `stash`, `rebase`, or switch that dirty worktree.
- Execute implementation in an isolated worktree created at execution time with `superpowers:using-git-worktrees`.
- Never copy L1 dirty files wholesale over R2. Port invariants/functionality after a file-by-file convergence review.
- Do not weaken any existing oracle, required marker, hard gate, run count, temporal/evidence requirement, or fail-closed rule.
- Do not add ASH-06-specific numeric or legal-answer literals to production runtime code.
- Do not invent a general legal NLP extractor.
- `Coverage` and `Soundness` are separate acceptance dimensions.
- A missing/unsupported source-observation boundary is a hard architectural blocker; do not substitute model-declared metadata and call it independent source completeness.
- Repository parity, installed-bundle completeness/parity, and active-runtime identity are separate gates.
- Runtime state updates must be exact-session/exact-turn and must not use "latest state" fallback.
- `npm audit` and MCP `--help` are package/smoke checks only; they do not prove legal-source correctness.
- All PASS claims must identify the repository SHA or dirty-tree content manifest, installed runtime digest, active runtime identity, oracle version/digest, commands, and exit codes.
- Commit steps below are **commit boundaries**. Execute the actual `git commit`, `push`, PR creation, or merge only when the user has separately authorized those actions. Otherwise record the proposed commit message and continue in the isolated worktree without publishing changes.

---

## File / Responsibility Map

The implementation should converge on the following responsibilities.

| File | Responsibility after stabilization |
|---|---|
| `scripts/legal_proposition.py` | Canonical proposition/evidence/typed semantic domain model |
| `scripts/proposition_registry.py` | Single domain writer for canonical propositions |
| `scripts/proposition_rendering.py` | Deterministic coverage slots only |
| `scripts/proposition_reconciliation.py` | Exact render-slot coverage only |
| `scripts/proposition_soundness.py` | **New:** proposition adoption/contradiction/OPEN-promotion checks |
| `scripts/material_obligation.py` | **Conditional new file:** source-observed obligation model; create only after Task 6 source-observation gate passes |
| `scripts/obligation_closure.py` | **Conditional new file:** obligation ↔ evidence ↔ proposition closure; create only after Task 6 passes |
| `scripts/synthesis_runtime_state.py` | Exact-turn state schema, revision, transactional mutation |
| `scripts/runtime_state_lock.py` | **New:** cross-platform per-turn lock |
| `scripts/jdipt_runtime_mcp.py` | Runtime MCP transport; typed arguments; registry-completion tool if L1 convergence requires it |
| `scripts/inject_registry_runtime.py` | Authoritative session/turn/plugin-data binding and optional diagnostic attestation |
| `scripts/stop_synthesis_gate.py` | Coverage → soundness → closure → bounded enforcement orchestration |
| `scripts/release_contract.py` | **New:** one versioned release contract loader/validator |
| `skills/law-interpretation-request/evals/release-contract.json` | **New:** final release requirements |
| `scripts/ansim_housing_oracle.py` | Case oracle + strict result-set validation |
| `scripts/run_release_gate.py` | Sole release PASS authority |
| `scripts/plugin_integrity.py` | Required bundle completeness + repo/install parity |
| `scripts/runtime_attestation.py` | **New:** active plugin/runtime attestation schema/validator |
| `run_jdipt_full_regression_v4.py` | Native runner lifecycle/fresh-artifact hardening |
| `scripts/run_eval_suite.py` | Core/Full/Ansim execution; no independent release PASS authority |
| `.github/workflows/ci.yml` | Deterministic cross-platform-independent gates only |
| `docs/stabilization/2026-09-06-baseline-convergence.md` | R1/R2/L1 ownership/parity record |
| `docs/stabilization/2026-09-06-acceptance-contract.md` | Human-readable gate semantics |
| `docs/task14-stabilization-evidence/` | Final evidence bundles; create during acceptance tasks |

The plan keeps one master sequence because these workstreams are not independent features: each later task consumes invariants established by earlier tasks.

---

# PR-A — Baseline Convergence / Ownership

### Task 1: Preserve the Dirty Tree and Establish the Exact Integration Baseline

**Files:**
- Create in isolated worktree: `docs/stabilization/2026-09-06-baseline-convergence.md`
- Copy approved spec into repository: `docs/superpowers/specs/2026-09-06-jdipt-correctness-stabilization-design.md`
- No production file changes in this task.

**Interfaces:**
- Consumes: R1 `69dda97106cf094d93d7abb26753a76ed33ea773`, R2 `afa4003ca700f15794dc346e8239c6dda79492e2`, current L1 dirty working tree.
- Produces: a reviewed `KEEP | PORT_TO_R2 | DELETE_AFTER_PARITY | UNKNOWN` ownership decision for every runtime file and L1-only invariant.

- [ ] **Step 1: Read and record the dirty-tree state without modifying it**

Run from the user's existing JDIPT worktree:

```powershell
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main
git status --short
git diff --name-status
git diff --cached --name-status
git ls-files --others --exclude-standard
```

Expected:
- commands are read-only;
- no branch switch occurs;
- all existing modified/untracked files are recorded verbatim.

- [ ] **Step 2: Create a content digest manifest for dirty tracked and untracked files**

Run:

```powershell
@'
import hashlib
import json
import subprocess
from pathlib import Path

root = Path.cwd()
paths = set()

for cmd in (
    ["git", "diff", "--name-only"],
    ["git", "diff", "--cached", "--name-only"],
    ["git", "ls-files", "--others", "--exclude-standard"],
):
    out = subprocess.check_output(cmd, text=True, encoding="utf-8")
    paths.update(line.strip() for line in out.splitlines() if line.strip())

items = []
for rel in sorted(paths):
    path = root / rel
    if path.is_file():
        items.append({
            "path": rel.replace("\\", "/"),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size": path.stat().st_size,
        })
    else:
        items.append({"path": rel.replace("\\", "/"), "missing_or_nonfile": True})

print(json.dumps(items, ensure_ascii=False, indent=2))
'@ | py -3.13 -
```

Save the output in the Task 1 evidence directory, not by editing the user's dirty files.

- [ ] **Step 3: At execution time, create an isolated R2 worktree**

Use the `superpowers:using-git-worktrees` skill. The target ref is:

```text
refactor/legal-proposition-core-working2
afa4003ca700f15794dc346e8239c6dda79492e2
```

Do **not** switch the dirty worktree.

- [ ] **Step 4: Build the convergence matrix**

The document must contain at least these rows:

```markdown
| Capability | R1 | R2 | L1 | Decision | Evidence |
|---|---|---|---|---|---|
| canonical proposition | duplicate schemas | LegalProposition | inspect | KEEP R2 | file/symbol |
| evidence metadata | source_clause/current_status | EvidenceRef | inspect | KEEP R2 | file/symbol |
| registry writer | runtime_registry_state.py | proposition_registry.py | inspect | KEEP R2 / PORT invariant | file/symbol |
| exact-turn state | yes | yes | inspect | KEEP + verify | test |
| registry_required | absent | absent | inspect | PORT_TO_R2 if verified | L1 diff |
| registry_completed | absent | absent | inspect | PORT_TO_R2 if verified | L1 diff |
| enforcement_count | absent | absent | inspect | PORT_TO_R2 if verified | L1 diff |
| relation model | synthesis_integrity | exact render slots | inspect | compare semantics | tests |
| CI | absent | present | inspect | KEEP R2 | ci.yml |
| legacy runtime_registry_state | present | removed | inspect | DELETE_AFTER_PARITY | import graph |
| legacy synthesis_integrity | present | removed | inspect | DELETE_AFTER_PARITY | import graph |
```

For every L1 production file, include exact symbol names and whether the behavior already exists in R2.

- [ ] **Step 5: Prove there is no hidden production import of R1 legacy modules in R2**

Run in the isolated worktree:

```powershell
rg -n "runtime_registry_state|synthesis_integrity" .
```

Expected:
- only documentation/history/tests explicitly meant to reference the old implementation;
- no active plugin/MCP/Stop path imports them.

If an active import exists, mark that file `UNKNOWN` and stop before deleting anything.

- [ ] **Step 6: Add the approved design spec and convergence document**

Copy the approved design text exactly into:

```text
docs/superpowers/specs/2026-09-06-jdipt-correctness-stabilization-design.md
```

Write the completed matrix to:

```text
docs/stabilization/2026-09-06-baseline-convergence.md
```

- [ ] **Step 7: Validate the documentation-only task**

Run:

```powershell
git diff --check
git status --short
```

Expected:
- only the intended docs are new/modified in the isolated worktree;
- the original dirty worktree remains byte-for-byte unchanged according to the Task 1 digest manifest.

- [ ] **Step 8: Record the commit boundary**

Proposed commit message:

```text
docs: define JDIPT correctness stabilization baseline
```

If commits are not authorized, do not commit; record this boundary in the evidence log.

**Task 1 Gate:** Do not start Task 2 until every runtime capability is classified. Any `UNKNOWN` that affects registry/state/Stop behavior is a blocker.

---

# PR-B — Unified Release Authority + Typed Semantic Controls

### Task 2: Create One Versioned Release Contract

**Files:**
- Create: `skills/law-interpretation-request/evals/release-contract.json`
- Create: `scripts/release_contract.py`
- Create: `tests/test_release_contract.py`
- Modify later in Task 3: `scripts/run_release_gate.py`
- Modify: `scripts/validate_repo.py` to require the release contract file and schema marker.

**Interfaces:**
- Consumes: existing suite manifest from `scripts.eval_suite`.
- Produces:
  - `load_release_contract(path: Path | None = None) -> ReleaseContract`
  - `validate_release_contract(data: Mapping[str, Any]) -> None`
  - `RELEASE_CONTRACT_PATH`

Use this exact JSON shape:

```json
{
  "schema_version": 1,
  "contract": "jdipt_release_contract=v0.2.4-stabilization",
  "required_gates": [
    "deterministic",
    "core_stability",
    "full_active",
    "ansim_core",
    "ansim_stability",
    "package",
    "installed_bundle",
    "active_runtime",
    "source_correctness"
  ],
  "ansim": {
    "case_ids": ["ASH-01", "ASH-02", "ASH-03", "ASH-04", "ASH-05", "ASH-06", "ASH-07", "ASH-08", "ASH-09"],
    "core_repetitions": 1,
    "core_min_pass": 9,
    "stability_repetitions": 3,
    "stability_min_pass": 26,
    "max_global_hard_gate_violations": 0,
    "max_critical_negative_markers": 0,
    "require_exact_case_attempts": true
  }
}
```

This preserves the existing stochastic 26/27 tolerance **only for non-hard-gate semantic instability**. A hard-gate violation can never be offset by the 26/27 threshold.

- [ ] **Step 1: Write failing schema tests**

Create `tests/test_release_contract.py`:

```python
from copy import deepcopy

import pytest

from scripts.release_contract import (
    RELEASE_CONTRACT_PATH,
    load_release_contract,
    validate_release_contract,
)


def test_repository_release_contract_is_valid():
    contract = load_release_contract()
    assert contract["schema_version"] == 1
    assert contract["contract"] == "jdipt_release_contract=v0.2.4-stabilization"


def test_release_contract_requires_every_release_gate():
    contract = load_release_contract()
    assert contract["required_gates"] == [
        "deterministic",
        "core_stability",
        "full_active",
        "ansim_core",
        "ansim_stability",
        "package",
        "installed_bundle",
        "active_runtime",
        "source_correctness",
    ]


def test_release_contract_rejects_missing_required_gate():
    contract = deepcopy(load_release_contract())
    contract["required_gates"].remove("ansim_stability")

    with pytest.raises(ValueError, match="required_gates"):
        validate_release_contract(contract)


def test_release_contract_rejects_hard_gate_tolerance():
    contract = deepcopy(load_release_contract())
    contract["ansim"]["max_global_hard_gate_violations"] = 1

    with pytest.raises(ValueError, match="hard gate"):
        validate_release_contract(contract)


def test_release_contract_requires_exact_ash_case_identity():
    contract = deepcopy(load_release_contract())
    contract["ansim"]["case_ids"][-1] = "ASH-01"

    with pytest.raises(ValueError, match="ASH-01 through ASH-09"):
        validate_release_contract(contract)
```

- [ ] **Step 2: Run the tests and verify RED**

Run:

```powershell
py -3.13 -m pytest -q tests/test_release_contract.py
```

Expected:
- collection/import failure because `scripts.release_contract` does not exist.

- [ ] **Step 3: Implement the minimal contract loader/validator**

Create `scripts/release_contract.py`:

```python
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RELEASE_CONTRACT_PATH = (
    ROOT
    / "skills"
    / "law-interpretation-request"
    / "evals"
    / "release-contract.json"
)

EXPECTED_GATES = [
    "deterministic",
    "core_stability",
    "full_active",
    "ansim_core",
    "ansim_stability",
    "package",
    "installed_bundle",
    "active_runtime",
    "source_correctness",
]
EXPECTED_ASH_CASES = [f"ASH-{number:02d}" for number in range(1, 10)]


def validate_release_contract(data: Mapping[str, Any]) -> None:
    if data.get("schema_version") != 1:
        raise ValueError("release contract schema_version must be 1")
    if data.get("contract") != "jdipt_release_contract=v0.2.4-stabilization":
        raise ValueError("invalid release contract identifier")
    if data.get("required_gates") != EXPECTED_GATES:
        raise ValueError("required_gates do not match the release contract")

    ansim = data.get("ansim")
    if not isinstance(ansim, Mapping):
        raise ValueError("ansim release contract must be an object")
    if ansim.get("case_ids") != EXPECTED_ASH_CASES:
        raise ValueError("ansim case_ids must be exactly ASH-01 through ASH-09")
    if ansim.get("core_repetitions") != 1 or ansim.get("core_min_pass") != 9:
        raise ValueError("invalid Ansim core acceptance")
    if ansim.get("stability_repetitions") != 3:
        raise ValueError("invalid Ansim stability repetitions")
    if ansim.get("stability_min_pass") != 26:
        raise ValueError("invalid Ansim stability pass threshold")
    if ansim.get("max_global_hard_gate_violations") != 0:
        raise ValueError("hard gate violations must be zero")
    if ansim.get("max_critical_negative_markers") != 0:
        raise ValueError("critical negative markers must be zero")
    if ansim.get("require_exact_case_attempts") is not True:
        raise ValueError("exact Ansim case attempts are required")


def load_release_contract(path: Path | None = None) -> dict[str, Any]:
    source = path or RELEASE_CONTRACT_PATH
    data = json.loads(source.read_text(encoding="utf-8"))
    validate_release_contract(data)
    return data
```

Add the JSON file with the exact payload specified above.

- [ ] **Step 4: Run the focused tests**

Run:

```powershell
py -3.13 -m pytest -q tests/test_release_contract.py
```

Expected: PASS.

- [ ] **Step 5: Wire static validation**

Modify `scripts/validate_repo.py` to:
- require `release-contract.json`;
- import/load `release_contract`;
- fail if validation fails;
- print exactly:

```text
release_contract=jdipt_release_contract=v0.2.4-stabilization
```

Add a test to `tests/test_validate_repo_contract.py` that asserts the marker exists and invalid/missing release contracts fail.

- [ ] **Step 6: Run regression around the validator**

Run:

```powershell
py -3.13 -m pytest -q tests/test_release_contract.py tests/test_validate_repo_contract.py
py -3.13 scripts/validate_repo.py
```

Expected: PASS.

- [ ] **Step 7: Record the commit boundary**

Proposed message:

```text
feat: define one JDIPT release contract
```

---

### Task 3: Make Ansim Result Aggregation and `--full` Release Orchestration Fail Closed

**Files:**
- Modify: `scripts/ansim_housing_oracle.py` (`build_ansim_summary`)
- Modify: `scripts/run_release_gate.py` (`orchestrate`, `ansim_regression_gate`, CLI)
- Modify: `tests/test_ansim_housing_oracle.py`
- Modify: `tests/test_release_gate.py`

**Interfaces:**
- Consumes: `load_release_contract()`.
- Produces:
  - `validate_ansim_result_set(results: Sequence[Mapping[str, Any]], repetitions: int) -> tuple[bool, tuple[str, ...]]`
  - release orchestration that runs `A → B → C → Ansim core → Ansim stability → package → external attestation gates`.

- [ ] **Step 1: Replace the known false-green test with fail-closed expectations**

In `tests/test_release_gate.py`, replace the existing permissive test:

```python
def test_ansim_stability_gate_allows_one_noncritical_failure():
    ...
```

with both:

```python
def test_ansim_stability_gate_allows_one_noncritical_failure_only_when_summary_has_no_hard_gate_violation():
    def runner(command):
        return CommandResult(
            0,
            "process_ok: 27/27\n"
            "contract_oracle_pass: 26/27\n"
            "global_hard_gate_violations: 0\n"
            "critical_negative_markers: 0\n"
            "case_attempts_complete: true\n"
            "release_verdict: PASS\n",
        )

    assert ansim_regression_gate(repetitions=3, command_runner=runner).passed


def test_ansim_stability_gate_rejects_hard_gate_failure_even_at_26_of_27():
    def runner(command):
        return CommandResult(
            0,
            "process_ok: 27/27\n"
            "contract_oracle_pass: 26/27\n"
            "global_hard_gate_violations: 1\n"
            "critical_negative_markers: 0\n"
            "case_attempts_complete: true\n"
            "release_verdict: FAIL\n",
        )

    assert not ansim_regression_gate(repetitions=3, command_runner=runner).passed
```

Add:

```python
def test_ansim_stability_gate_rejects_incomplete_case_identity():
    def runner(command):
        return CommandResult(
            0,
            "process_ok: 27/27\n"
            "contract_oracle_pass: 27/27\n"
            "global_hard_gate_violations: 0\n"
            "critical_negative_markers: 0\n"
            "case_attempts_complete: false\n"
            "release_verdict: FAIL\n",
        )

    assert not ansim_regression_gate(repetitions=3, command_runner=runner).passed
```

- [ ] **Step 2: Add result-set identity tests**

In `tests/test_ansim_housing_oracle.py` add:

```python
from copy import deepcopy

from scripts.ansim_housing_oracle import (
    build_ansim_summary,
    validate_ansim_result_set,
)


def _passing_result(case_id: str, attempt: int) -> dict:
    return {
        "case_id": case_id,
        "attempt": attempt,
        "process_ok": True,
        "verdict": "PASS",
        "findings": [],
        "critical_negative_markers": [],
    }


def test_ansim_result_set_requires_each_case_exactly_three_times():
    results = [
        _passing_result(f"ASH-{case:02d}", attempt)
        for case in range(1, 10)
        for attempt in range(1, 4)
    ]
    ok, failures = validate_ansim_result_set(results, repetitions=3)
    assert ok
    assert failures == ()


def test_ansim_result_set_rejects_27_results_from_one_case():
    results = [_passing_result("ASH-01", attempt) for attempt in range(1, 28)]
    ok, failures = validate_ansim_result_set(results, repetitions=3)
    assert not ok
    assert "case attempt identity mismatch" in failures


def test_ansim_summary_rejects_one_hard_gate_failure():
    results = [
        _passing_result(f"ASH-{case:02d}", attempt)
        for case in range(1, 10)
        for attempt in range(1, 4)
    ]
    results[0] = deepcopy(results[0])
    results[0]["verdict"] = "FAIL"
    results[0]["findings"] = [{
        "gate": "AUTHORITY_PRIORITY",
        "passed": False,
        "marker": "STALE_POLICY_CONTROLS",
        "case_id": "ASH-01",
        "reason": "test",
    }]
    summary = build_ansim_summary(
        results,
        model="test",
        plugin_version="0.2.4",
        repetitions=3,
    )
    assert summary["release_verdict"] == "FAIL"
```

- [ ] **Step 3: Run the focused tests and verify RED**

Run:

```powershell
py -3.13 -m pytest -q tests/test_release_gate.py tests/test_ansim_housing_oracle.py
```

Expected: FAIL on missing stricter result-set semantics/output markers.

- [ ] **Step 4: Implement `validate_ansim_result_set`**

Add to `scripts/ansim_housing_oracle.py`:

```python
from collections import Counter
from collections.abc import Mapping, Sequence


def validate_ansim_result_set(
    results: Sequence[Mapping[str, Any]],
    *,
    repetitions: int,
) -> tuple[bool, tuple[str, ...]]:
    expected = Counter(
        case_id
        for case_id in EXPECTED_CASE_IDS
        for _ in range(repetitions)
    )
    actual = Counter(
        result.get("case_id")
        for result in results
        if isinstance(result.get("case_id"), str)
    )
    failures: list[str] = []
    if actual != expected:
        failures.append("case attempt identity mismatch")
    for case_id in EXPECTED_CASE_IDS:
        attempts = sorted(
            result.get("attempt")
            for result in results
            if result.get("case_id") == case_id
            and isinstance(result.get("attempt"), int)
        )
        if attempts != list(range(1, repetitions + 1)):
            failures.append(f"{case_id} attempt numbers mismatch")
    return (not failures, tuple(failures))
```

Update `build_ansim_summary()`:

```python
identity_ok, identity_failures = validate_ansim_result_set(
    results,
    repetitions=repetitions,
)

accepted = (
    identity_ok
    and len(results) == expected_total
    and process_success == expected_total
    and pass_count >= minimum_pass
    and not gate_violations
    and not critical
)
```

Add these summary fields:

```python
"case_attempts_complete": identity_ok,
"case_attempt_failures": list(identity_failures),
"global_hard_gate_violation_count": len(gate_violations),
```

Update CLI summary output to print:

```text
global_hard_gate_violations: <count>
case_attempts_complete: true|false
```

- [ ] **Step 5: Make `ansim_regression_gate()` require those fields**

Required regexes must include:

```python
r"global_hard_gate_violations:\s*0",
r"case_attempts_complete:\s*true",
```

- [ ] **Step 6: Extend release orchestration**

Change `orchestrate()` to accept:

```python
ansim_core_fn: Callable[[], GateResult] | None = None
ansim_stability_fn: Callable[[], GateResult] | None = None
```

For `mode="full"`, order must be:

```text
A deterministic
B core stability
C full active
E ansim core
F ansim stability
D package/static
```

Do not label the result PASS if either Ansim gate is missing/not run.

Update the test:

```python
def test_full_mode_runs_every_required_behavior_gate_before_package():
    calls = []
    results = orchestrate(
        mode="full",
        deterministic_fn=lambda: (calls.append("A") or passing("A")),
        critical_fn=lambda: (calls.append("B") or passing("B")),
        full_fn=lambda: (calls.append("C") or passing("C")),
        ansim_core_fn=lambda: (calls.append("E") or passing("E")),
        ansim_stability_fn=lambda: (calls.append("F") or passing("F")),
        package_fn=lambda: (calls.append("D") or passing("D")),
    )
    assert calls == ["A", "B", "C", "E", "F", "D"]
```

Add stop-after-failure tests for both Ansim gates.

- [ ] **Step 7: Run focused and full deterministic tests**

Run:

```powershell
py -3.13 -m pytest -q tests/test_release_gate.py tests/test_ansim_housing_oracle.py
py -3.13 -m pytest -q
```

Expected: PASS.

- [ ] **Step 8: Record the commit boundary**

Proposed message:

```text
fix: make release aggregation fail closed
```

---

### Task 4: Replace Free-Form Semantic Control Strings with Canonical Enums

**Files:**
- Modify: `scripts/legal_proposition.py`
- Modify: `scripts/proposition_registry.py`
- Modify: `scripts/proposition_rendering.py`
- Modify: `scripts/jdipt_runtime_mcp.py`
- Modify: `tests/test_legal_proposition.py`
- Modify: `tests/test_proposition_registry.py`
- Modify: `tests/test_proposition_rendering.py`
- Modify: `tests/test_jdipt_runtime_mcp.py`

**Interfaces:**
- Produces:
  - `Materiality(StrEnum)`
  - `Modality(StrEnum)`
  - `Polarity(StrEnum)`
  - strict adapter functions in `proposition_registry.py`.
- Canonical in-memory values are enums; external legacy aliases are accepted only from a fixed allowlist.

- [ ] **Step 1: Write enum rejection tests**

Add to `tests/test_legal_proposition.py`:

```python
@pytest.mark.parametrize("materiality", ["critical", "important", "material-ish"])
def test_proposition_rejects_unknown_materiality(materiality):
    with pytest.raises(PropositionValidationError, match="materiality"):
        _closed_proposition(materiality=materiality)


@pytest.mark.parametrize("modality", ["not required", "maybe required", "shall-ish"])
def test_proposition_rejects_unknown_modality(modality):
    with pytest.raises(PropositionValidationError, match="modality"):
        _closed_proposition(modality=modality)


def test_proposition_rejects_unknown_polarity():
    with pytest.raises(PropositionValidationError, match="polarity"):
        _closed_proposition(polarity="mixed")
```

Add a rendering regression to `tests/test_proposition_rendering.py` that proves `MUST_NOT` renders prohibited and `MAY` renders discretionary.

- [ ] **Step 2: Run focused tests and verify RED**

```powershell
py -3.13 -m pytest -q tests/test_legal_proposition.py tests/test_proposition_rendering.py
```

Expected: current free-form strings are accepted; RED.

- [ ] **Step 3: Add canonical enum types**

In `scripts/legal_proposition.py`:

```python
from enum import StrEnum


class Materiality(StrEnum):
    MATERIAL = "MATERIAL"
    NON_MATERIAL = "NON_MATERIAL"


class Modality(StrEnum):
    MAY = "MAY"
    MUST = "MUST"
    MUST_NOT = "MUST_NOT"
    MAY_NOT = "MAY_NOT"


class Polarity(StrEnum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
```

Change `LegalProposition` fields:

```python
materiality: Materiality
modality: Modality | None
polarity: Polarity | None
```

In `__post_init__`, reject non-enum values rather than searching arbitrary strings.

- [ ] **Step 4: Add explicit legacy input normalization at the registry boundary**

In `scripts/proposition_registry.py` define exact maps:

```python
_MATERIALITY_ALIASES = {
    "MATERIAL": Materiality.MATERIAL,
    "material": Materiality.MATERIAL,
    "NON_MATERIAL": Materiality.NON_MATERIAL,
    "non_material": Materiality.NON_MATERIAL,
    "non-material": Materiality.NON_MATERIAL,
}

_MODALITY_ALIASES = {
    "MAY": Modality.MAY,
    "may": Modality.MAY,
    "MUST": Modality.MUST,
    "must": Modality.MUST,
    "MUST_NOT": Modality.MUST_NOT,
    "must not": Modality.MUST_NOT,
    "MAY_NOT": Modality.MAY_NOT,
    "may not": Modality.MAY_NOT,
}

_POLARITY_ALIASES = {
    "POSITIVE": Polarity.POSITIVE,
    "positive": Polarity.POSITIVE,
    "NEGATIVE": Polarity.NEGATIVE,
    "negative": Polarity.NEGATIVE,
}
```

Use a helper:

```python
def _enum_arg(fields, name, aliases, *, default=None):
    raw = _text_arg(fields, name)
    if raw is None:
        return default
    try:
        return aliases[raw]
    except KeyError as exc:
        raise PropositionValidationError(f"unsupported {name}: {raw}") from exc
```

Do not add aliases for `critical`, `important`, or `not required`.

- [ ] **Step 5: Make rendering compare enum identity only**

Replace substring modality detection with:

```python
if proposition.modality is Modality.MUST:
    ...
elif proposition.modality in {Modality.MUST_NOT, Modality.MAY_NOT}:
    ...
else:
    ...
```

Materiality:

```python
return proposition.materiality is Materiality.MATERIAL
```

Polarity comparisons also use enum identity.

- [ ] **Step 6: Tighten the MCP schema**

In `tool_definitions()`, set:

```python
"materiality": {
    "type": "string",
    "enum": ["MATERIAL", "NON_MATERIAL", "material", "non_material", "non-material"],
},
"modality": {
    "type": "string",
    "enum": ["MAY", "MUST", "MUST_NOT", "MAY_NOT", "may", "must", "must not", "may not"],
},
"polarity": {
    "type": "string",
    "enum": ["POSITIVE", "NEGATIVE", "positive", "negative"],
},
```

The canonical values should be first so model-generated calls prefer them.

- [ ] **Step 7: Run all proposition/MCP tests**

```powershell
py -3.13 -m pytest -q `
  tests/test_legal_proposition.py `
  tests/test_proposition_registry.py `
  tests/test_proposition_rendering.py `
  tests/test_jdipt_runtime_mcp.py
```

Expected: PASS.

- [ ] **Step 8: Run full tests**

```powershell
py -3.13 -m pytest -q
```

Expected: PASS.

- [ ] **Step 9: Record the commit boundary**

Proposed message:

```text
fix: type legal proposition semantic controls
```

---

# PR-C — Semantic Soundness Gate

### Task 5: Separate Render Coverage from Final-Answer Soundness

**Files:**
- Create: `scripts/proposition_soundness.py`
- Create: `tests/test_proposition_soundness.py`
- Modify: `scripts/stop_synthesis_gate.py`
- Modify: `tests/test_stop_synthesis_gate.py`
- Keep `scripts/proposition_reconciliation.py` focused on exact coverage.

**Interfaces:**
- Consumes: `Sequence[LegalProposition]`, `Sequence[PropositionRenderContract]`, final draft.
- Produces:
  - `SoundnessFinding`
  - `SoundnessResult`
  - `evaluate_proposition_soundness(propositions, contracts, draft) -> SoundnessResult`

The first implementation is deliberately deterministic and narrow. It must cover the confirmed false-green families without pretending to understand arbitrary legal prose.

- [ ] **Step 1: Write the four confirmed false-green tests**

Create `tests/test_proposition_soundness.py` with helpers matching existing R2 proposition fixtures, then:

```python
def test_exact_slot_inside_fenced_code_is_not_adopted():
    proposition = _closed_proposition()
    contract = build_render_contract(proposition)
    draft = "```text\n" + "\n".join(slot.text for slot in contract.slots) + "\n```"
    result = evaluate_proposition_soundness([proposition], [contract], draft)
    assert not result.sound
    assert "NON_ASSERTIVE_ONLY" in {f.kind for f in result.findings}


def test_exact_slot_inside_rejected_quote_is_not_adopted():
    proposition = _closed_proposition()
    contract = build_render_contract(proposition)
    slots = " ".join(slot.text for slot in contract.slots)
    draft = f"다음 해석은 잘못된 해석이며 채택하지 않는다: {slots}"
    result = evaluate_proposition_soundness([proposition], [contract], draft)
    assert not result.sound
    assert "REJECTED_ONLY" in {f.kind for f in result.findings}


def test_open_uncertainty_plus_definitive_opposite_conclusion_fails():
    proposition = _open_proposition(
        legal_action="approve",
        operative_verb_lexeme="승인",
        legal_object="사업계획",
    )
    contract = build_render_contract(proposition)
    draft = contract.slots[0].text + "\n결론: 사업계획을 승인할 수 있음이 확정되었다."
    result = evaluate_proposition_soundness([proposition], [contract], draft)
    assert not result.sound
    assert "OPEN_PROMOTED" in {f.kind for f in result.findings}


def test_positive_proposition_with_same_relation_negated_in_conclusion_fails():
    proposition = _closed_proposition(
        legal_action="designate",
        operative_verb_lexeme="지정",
        legal_object="사업대상지",
    )
    contract = build_render_contract(proposition)
    draft = (
        " ".join(slot.text for slot in contract.slots)
        + "\n결론: 해당 사업대상지는 지정할 수 없다."
    )
    result = evaluate_proposition_soundness([proposition], [contract], draft)
    assert not result.sound
    assert "POLARITY_CONTRADICTION" in {f.kind for f in result.findings}
```

Also add positive controls:
- exact slots as normal paragraphs are sound;
- unrelated negation of another object is sound.

- [ ] **Step 2: Run and verify RED**

```powershell
py -3.13 -m pytest -q tests/test_proposition_soundness.py
```

Expected: import failure.

- [ ] **Step 3: Implement non-assertive-region stripping**

Create `scripts/proposition_soundness.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
import re
from collections.abc import Sequence

from scripts.legal_proposition import LegalProposition, Polarity
from scripts.proposition_reconciliation import normalize_rendered_text
from scripts.proposition_rendering import PropositionRenderContract


@dataclass(frozen=True)
class SoundnessFinding:
    proposition_id: str
    kind: str
    detail: str


@dataclass(frozen=True)
class SoundnessResult:
    sound: bool
    findings: tuple[SoundnessFinding, ...]


_FENCED = re.compile(r"```.*?```", re.DOTALL)
_BLOCKQUOTE_LINE = re.compile(r"(?m)^\s*>\s?.*$")
_REJECTION_MARKERS = (
    "잘못된 해석",
    "틀린 해석",
    "채택하지 않는다",
    "채택할 수 없다",
    "반대견해",
    "오답",
)
_UNCERTAINTY_MARKERS = (
    "확인 필요",
    "확정할 수 없다",
    "판단할 수 없다",
    "미확인",
)


def _assertive_text(draft: str) -> str:
    without_fences = _FENCED.sub(" ", draft)
    return _BLOCKQUOTE_LINE.sub(" ", without_fences)


def _occurrence_is_rejected(text: str, start: int) -> bool:
    prefix = text[max(0, start - 120):start]
    return any(marker in prefix for marker in _REJECTION_MARKERS)
```

Implement required-slot adoption:
- normalize `_assertive_text`;
- for each slot, require at least one occurrence not preceded by a rejection marker;
- emit `NON_ASSERTIVE_ONLY` if slot exists only in code/blockquote;
- emit `REJECTED_ONLY` if all assertive occurrences are in rejection context.

- [ ] **Step 4: Implement proposition-scoped contradiction detection**

Split the assertive text into sentence-like spans:

```python
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?。！？])\s+|\n+")
```

For an OPEN proposition, only inspect a sentence if it contains both:
- `legal_object` if available;
- `operative_verb_lexeme` or `legal_action` if available.

Flag `OPEN_PROMOTED` when that sentence contains one of:

```text
할 수 있다
가능하다
확정되었다
인정된다
적용된다
```

and no `_UNCERTAINTY_MARKERS`.

For a POSITIVE CLOSED proposition, on the same object/action relation, flag:

```text
할 수 없다
불가
금지
아니다
적용되지 않는다
```

For NEGATIVE, flag the corresponding affirmative forms.

Do not search answer-wide for a generic `없다` token.

- [ ] **Step 5: Run soundness tests**

```powershell
py -3.13 -m pytest -q tests/test_proposition_soundness.py
```

Expected: PASS.

- [ ] **Step 6: Integrate soundness after coverage in Stop**

In `scripts/stop_synthesis_gate.py`:

```python
coverage = reconcile_render_contracts(contracts, draft)
if not coverage.covered:
    return _handle_mismatch(...)

soundness = evaluate_proposition_soundness(
    state.propositions,
    contracts,
    draft,
)
if not soundness.sound:
    return _handle_mismatch(...)
```

Refactor the current one-repair logic into one helper so coverage and soundness consume the **same** repair budget.

The block reason must include proposition id and soundness kind, but must not invent a replacement legal proposition.

- [ ] **Step 7: Add Stop-level regressions**

Add to `tests/test_stop_synthesis_gate.py`:
- rejected quote → first block;
- OPEN + definitive conclusion → first block;
- second identical soundness mismatch with `repair_count=1` → `continue:false`;
- valid exact slots + unrelated negation → `{}`.

- [ ] **Step 8: Run Stop + soundness tests**

```powershell
py -3.13 -m pytest -q tests/test_proposition_soundness.py tests/test_stop_synthesis_gate.py
```

Expected: PASS.

- [ ] **Step 9: Full regression**

```powershell
py -3.13 -m pytest -q
```

Expected: PASS.

- [ ] **Step 10: Record the commit boundary**

Proposed message:

```text
feat: separate proposition coverage from soundness
```

---

# PR-D — Source / Obligation Closure

### Task 6: Prove an Independent Source-Observation Boundary Before Building Closure

**Files:**
- No permanent production file is created until the capability gate passes.
- Evidence only: `docs/task14-stabilization-evidence/source-observation-capability.md`
- If a repository diagnostic helper is required, create it under `scripts/diagnostics/` and remove it from the proposed production file list after the capability decision; do not make correctness depend on it.

**Interfaces:**
- Consumes: actual Codex host events for Korean Law MCP calls.
- Produces one of exactly two verdicts:
  - `SOURCE_OBSERVATION_CAPABILITY=PASS`
  - `SOURCE_OBSERVATION_CAPABILITY=BLOCKED`

This task exists because the approved architecture requires that the model not be the sole authority for both discovered evidence and the complete set of propositions to be checked.

- [ ] **Step 1: Inspect the installed/runtime hook contract read-only**

Record:
- Codex CLI version;
- app-server binary/path if observable;
- active JDIPT plugin root;
- existing hook event names;
- whether the host exposes a post-tool event that contains the actual tool result or a stable result reference.

Use read-only host/config inspection only. Do not infer support from a guessed event name.

- [ ] **Step 2: Run a one-call capability probe**

Use a known harmless Korean Law MCP lookup in a fresh JDIPT test turn.

The probe is PASS only if JDIPT can capture, without relying on model-authored re-description:
- exact session id;
- exact turn id;
- tool identity;
- tool result or stable content/result reference;
- enough source identity to bind later evidence (`law id/MST/article/decision id` or equivalent).

Do not capture secrets or full unrelated conversation content.

- [ ] **Step 3: Write the verdict**

`source-observation-capability.md` must contain:

```text
Codex version:
JDIPT active plugin root:
Observed event:
Observed fields:
Tool result available: YES/NO
Stable result reference available: YES/NO
Source identity observable: YES/NO
Verdict: PASS/BLOCKED
```

- [ ] **Step 4A: PASS branch**

Continue to Task 7 only if the result is independently observable.

- [ ] **Step 4B: BLOCKED branch**

If the actual tool result/stable reference is not observable, stop the implementation program here with:

```text
BLOCKED — independent source observation unavailable in the current Codex/plugin boundary.
Do not implement a fake source-completeness gate from model-declared evidence metadata.
Architecture choice required: host post-tool observation or a JDIPT-owned source broker.
```

Do **not** proceed to Task 7, ASH-06 closure, or release acceptance.

This is a mandatory design-protection gate, not an optional diagnostic.

---

### Task 7: Add a Source-Observed Material Obligation Ledger

**Precondition:** Task 6 PASS.

**Files:**
- Create: `scripts/material_obligation.py`
- Create: `scripts/obligation_closure.py`
- Create: `tests/test_material_obligation.py`
- Create: `tests/test_obligation_closure.py`
- Modify: `scripts/synthesis_runtime_state.py`
- Modify: source-observation hook/adapter identified in Task 6.
- Modify: `scripts/plugin_integrity.py` required runtime files.

**Interfaces:**
- Produces:
  - `SourceResolution(StrEnum)`
  - `MaterialObligation`
  - `ObligationClosureResult`
  - `evaluate_obligation_closure(obligations, propositions)`

Use exact statuses:

```python
class SourceResolution(StrEnum):
    SOURCE_CONFIRMED = "SOURCE_CONFIRMED"
    SOURCE_UNRESOLVED = "SOURCE_UNRESOLVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
```

Use this model:

```python
@dataclass(frozen=True)
class MaterialObligation:
    obligation_id: str
    materiality: Materiality
    issue_key: str
    description: str
    source_resolution: SourceResolution
    source_ids: tuple[str, ...]
    proposition_ids: tuple[str, ...]
```

The observer, not the final-answer model, must be able to create/update the `source_ids` relation from an observed source result.

- [ ] **Step 1: Write model validation tests**

`tests/test_material_obligation.py`:

```python
def test_confirmed_material_obligation_requires_source_identity():
    with pytest.raises(ObligationValidationError):
        MaterialObligation(
            obligation_id="O1",
            materiality=Materiality.MATERIAL,
            issue_key="RANGE_EXCEPTION",
            description="예외범위와 법적 효과",
            source_resolution=SourceResolution.SOURCE_CONFIRMED,
            source_ids=(),
            proposition_ids=(),
        )


def test_unresolved_obligation_cannot_claim_source_ids():
    with pytest.raises(ObligationValidationError):
        MaterialObligation(
            obligation_id="O1",
            materiality=Materiality.MATERIAL,
            issue_key="RANGE_EXCEPTION",
            description="예외범위와 법적 효과",
            source_resolution=SourceResolution.SOURCE_UNRESOLVED,
            source_ids=("law-1",),
            proposition_ids=(),
        )
```

- [ ] **Step 2: Write closure tests**

`tests/test_obligation_closure.py`:

```python
def test_confirmed_material_obligation_without_proposition_fails():
    obligation = _confirmed_obligation(
        obligation_id="O_EXCEPTION",
        source_ids=("law-1",),
        proposition_ids=(),
    )
    result = evaluate_obligation_closure([obligation], [])
    assert not result.closed
    assert result.failures[0].kind == "MISSING_PROPOSITION"


def test_unresolved_material_obligation_requires_open_proposition():
    obligation = _unresolved_obligation(
        obligation_id="O_EXCEPTION",
        proposition_ids=("P_EXCEPTION",),
    )
    closed = _closed_proposition(proposition_id="P_EXCEPTION")
    result = evaluate_obligation_closure([obligation], [closed])
    assert not result.closed
    assert result.failures[0].kind == "UNRESOLVED_PROMOTED_TO_CLOSED"


def test_confirmed_obligation_proposition_must_reference_observed_source():
    obligation = _confirmed_obligation(
        source_ids=("law-1",),
        proposition_ids=("P1",),
    )
    proposition = _closed_proposition(
        proposition_id="P1",
        evidence=replace(_evidence(), source_id="law-2"),
    )
    result = evaluate_obligation_closure([obligation], [proposition])
    assert not result.closed
    assert result.failures[0].kind == "SOURCE_BINDING_MISMATCH"
```

Positive control:
- confirmed obligation + CLOSED proposition with matching `source_id` passes.

- [ ] **Step 3: Run and verify RED**

```powershell
py -3.13 -m pytest -q tests/test_material_obligation.py tests/test_obligation_closure.py
```

Expected: import failure.

- [ ] **Step 4: Implement the two pure domain modules**

`material_obligation.py` validates identifiers/text in the same style as `legal_proposition.py`.

`obligation_closure.py` must:
- index propositions by id;
- for every `MATERIAL` obligation:
  - `NOT_APPLICABLE`: require no CLOSED proposition bound to it;
  - `SOURCE_UNRESOLVED`: require every bound proposition to be OPEN;
  - `SOURCE_CONFIRMED`: require at least one bound CLOSED proposition;
  - require the proposition evidence `source_id` to belong to `source_ids`.

Do not infer a proposition from keywords.

- [ ] **Step 5: Persist obligations in RuntimeTurnState**

Bump runtime schema version from 2 to 3.

Add:

```python
obligations: list[MaterialObligation]
```

Schema v2 must fail closed exactly as schema v1 does now. Do not migrate silently.

Update JSON serialization/deserialization.

- [ ] **Step 6: Connect the Task 6 observed-source boundary**

The exact adapter identified in Task 6 must create/update obligation source bindings from the observed tool result/reference.

Do not let the final-answer text itself set `SOURCE_CONFIRMED`.

- [ ] **Step 7: Run focused tests**

```powershell
py -3.13 -m pytest -q `
  tests/test_material_obligation.py `
  tests/test_obligation_closure.py `
  tests/test_synthesis_runtime_state.py
```

Expected: PASS.

- [ ] **Step 8: Record the commit boundary**

Proposed message:

```text
feat: bind material obligations to observed sources
```

---

### Task 8: Enforce Registry Closure and Explicit Registry Completion

**Files:**
- Modify: `scripts/synthesis_runtime_state.py`
- Modify: `scripts/proposition_registry.py`
- Modify: `scripts/jdipt_runtime_mcp.py`
- Modify: `scripts/stop_synthesis_gate.py`
- Modify: `tests/test_proposition_registry.py`
- Modify: `tests/test_jdipt_runtime_mcp.py`
- Modify: `tests/test_stop_synthesis_gate.py`
- Add/port verified L1 test cases after Task 1 convergence.

**Interfaces:**
- Produces RuntimeTurnState fields:
  - `registry_required: bool`
  - `registry_completed: bool`
  - `enforcement_count: int`
- Produces MCP tool:
  - `complete_material_registry`
- Closure before completion:
  - `evaluate_obligation_closure(...)`

Use exact invariant:

```text
registry_completed == True
⇒ obligation closure == True
```

- [ ] **Step 1: Add runtime-state contract tests**

Extend `tests/test_synthesis_runtime_state.py` with:

```python
def test_registry_required_turn_cannot_start_completed():
    with pytest.raises(RuntimeStateError):
        RuntimeTurnState(
            schema_version=3,
            session_id="session-a",
            turn_id="turn-1",
            registry_active=True,
            registry_required=True,
            registry_completed=True,
            enforcement_count=0,
            repair_count=0,
            obligations=[],
            propositions=[],
        )


def test_enforcement_count_is_bounded_to_zero_or_one():
    with pytest.raises(RuntimeStateError):
        _state(enforcement_count=2)
```

The exact initial activation state may be adapted from L1 after Task 1, but it must preserve:
- required before completion;
- one enforcement only;
- no `PENDING + active` invalid combination if L1 has an activation-state enum.

- [ ] **Step 2: Add MCP completion tests**

In `tests/test_jdipt_runtime_mcp.py`:

```python
def test_complete_registry_fails_when_material_obligation_is_unclosed(tmp_path):
    # create exact-turn state with a confirmed obligation and no proposition
    response = dispatch_json_rpc(
        _tool_call("complete_material_registry", {
            "session_id": "model-controlled",
            "turn_id": "model-controlled",
            "_runtime_plugin_data": str(tmp_path),
        }),
        plugin_data=tmp_path,
    )
    assert response["error"]["code"] == -32602
    assert "closure" in response["error"]["message"].lower()
```

Add positive completion test after a matching proposition is registered.

- [ ] **Step 3: Run and verify RED**

```powershell
py -3.13 -m pytest -q `
  tests/test_synthesis_runtime_state.py `
  tests/test_jdipt_runtime_mcp.py `
  tests/test_stop_synthesis_gate.py
```

Expected: RED until state and tool are implemented.

- [ ] **Step 4: Add explicit completion tool**

In `jdipt_runtime_mcp.py` expose two tools:

```text
register_material_proposition
complete_material_registry
```

The PreToolUse hook must bind authoritative session/turn/plugin-data for both tool names.

`complete_material_registry`:
1. loads exact-turn state;
2. validates obligation closure;
3. atomically marks `registry_completed=True`;
4. returns closure summary, not invented content.

- [ ] **Step 5: Stop must fail before semantic coverage when registry is incomplete**

Order in `handle_stop_event`:

```text
exact state
→ active/required check
→ registry completion/closure
→ render coverage
→ soundness
→ accept
```

If registry is required but incomplete:
- first Stop: one `decision:block` directing completion of the registry/closure;
- increment `enforcement_count` only;
- do **not** spend `repair_count`;
- second occurrence: `continue:false`.

If registry is complete but the rendered answer fails coverage/soundness:
- use the independent one-repair budget.

This keeps "registry enforcement" and "answer repair" observable as separate counters.

- [ ] **Step 6: Add two-budget tests**

```python
def test_first_registry_incomplete_stop_consumes_enforcement_not_repair(...):
    ...
    assert stored.enforcement_count == 1
    assert stored.repair_count == 0


def test_render_mismatch_after_completed_registry_consumes_repair_not_enforcement(...):
    ...
    assert stored.enforcement_count == 0
    assert stored.repair_count == 1
```

- [ ] **Step 7: Run focused tests**

```powershell
py -3.13 -m pytest -q `
  tests/test_proposition_registry.py `
  tests/test_jdipt_runtime_mcp.py `
  tests/test_synthesis_runtime_state.py `
  tests/test_stop_synthesis_gate.py
```

Expected: PASS.

- [ ] **Step 8: Record the commit boundary**

Proposed message:

```text
feat: enforce exact-turn registry closure
```

---

# PR-E — Transactional Runtime State

### Task 9: Replace Stale Read-Modify-Write with Locked Revisioned Mutation

**Files:**
- Create: `scripts/runtime_state_lock.py`
- Modify: `scripts/synthesis_runtime_state.py`
- Modify: `scripts/proposition_registry.py`
- Modify: `scripts/jdipt_runtime_mcp.py`
- Modify: `scripts/stop_synthesis_gate.py`
- Create: `tests/test_runtime_state_concurrency.py`
- Modify: `tests/test_synthesis_runtime_state.py`

**Interfaces:**
- Produces:
  - `turn_state_lock(plugin_data, session_id, turn_id)`
  - `mutate_runtime_state(session_id, turn_id, mutator, plugin_data, *, create=None) -> RuntimeTurnState`
  - `increment_repair_count(session_id, turn_id, plugin_data=None) -> RuntimeTurnState`
  - `increment_enforcement_count(session_id, turn_id, plugin_data=None) -> RuntimeTurnState`
- RuntimeTurnState adds `revision: int`.
- Production mutation APIs no longer accept stale `RuntimeTurnState` objects as authority.

- [ ] **Step 1: Write stale-write regression**

Add:

```python
def test_repair_mutation_cannot_erase_a_newly_registered_proposition(tmp_path):
    register_material_proposition(_fields(proposition_id="P1"), tmp_path)
    stale = load_runtime_state("session-a", "turn-1", tmp_path)

    register_material_proposition(_fields(proposition_id="P2"), tmp_path)

    # The production API must reload latest state under lock.
    increment_repair_count("session-a", "turn-1", tmp_path)

    loaded = load_runtime_state("session-a", "turn-1", tmp_path)
    assert [p.proposition_id for p in loaded.propositions] == ["P1", "P2"]
    assert loaded.repair_count == 1
    assert loaded.revision > stale.revision
```

- [ ] **Step 2: Write two-process race tests**

Create `tests/test_runtime_state_concurrency.py` using `multiprocessing` with a start `Event`.

Test A:
- process 1 registers P1;
- process 2 registers P2;
- after join, both are present.

Test B:
- one process registers P2 while another increments repair;
- final state has P1/P2 and `repair_count == 1`.

Use a bounded join:

```python
proc.join(timeout=10)
assert not proc.is_alive()
assert proc.exitcode == 0
```

- [ ] **Step 3: Run and verify RED**

```powershell
py -3.13 -m pytest -q tests/test_runtime_state_concurrency.py tests/test_synthesis_runtime_state.py
```

Expected: at least the stale-state/race regression fails before locking is introduced.

- [ ] **Step 4: Implement cross-platform lock**

Create `scripts/runtime_state_lock.py`.

Use a sibling lock file:

```text
PLUGIN_DATA/synthesis-runtime/<session>/<turn>.lock
```

On POSIX use `fcntl.flock(handle.fileno(), LOCK_EX)`.

On Windows use `msvcrt.locking()` on one byte after ensuring the lock file contains at least one byte.

Expose only a context manager; keep OS details private.

Do not use a lock-file existence protocol (`O_EXCL`) that can be left permanently stale after a crash.

- [ ] **Step 5: Add revision to schema**

Bump schema version once only for the combined state format used after Task 8/9. If Task 8 already moved to schema 3, Task 9 extends that same schema before the branch is accepted; do not create schema 4 solely for an unshipped intermediate state.

Add:

```python
revision: int
```

Validation:
- integer;
- `>= 0`.

Every committed mutation increments revision exactly once.

- [ ] **Step 6: Implement one mutation primitive**

In `synthesis_runtime_state.py`:

```python
def mutate_runtime_state(
    session_id: str,
    turn_id: str,
    mutator,
    plugin_data=None,
    *,
    create=None,
) -> RuntimeTurnState:
    with turn_state_lock(plugin_data, session_id, turn_id):
        current = load_runtime_state(session_id, turn_id, plugin_data)
        if current is None:
            if create is None:
                raise RuntimeStateError("runtime state is required")
            current = create()
        updated = mutator(current)
        if updated.session_id != session_id or updated.turn_id != turn_id:
            raise RuntimeStateError("runtime mutation changed identity")
        updated = replace(updated, revision=current.revision + 1)
        save_runtime_state(updated, plugin_data)
        return updated
```

`save_runtime_state()` remains a low-level atomic serializer for tests/bootstrap, but all production writes after initialization use `mutate_runtime_state`.

- [ ] **Step 7: Refactor registry/repair/completion writers**

- `proposition_registry._merge_state()` becomes a mutation callback.
- `increment_repair_count(session_id, turn_id, ...)` reloads latest state under lock.
- registry completion/enforcement mutation does the same.
- no production caller passes a stale state object to a write API.

- [ ] **Step 8: Run focused concurrency tests repeatedly**

Run at least 20 loops:

```powershell
1..20 | ForEach-Object {
  py -3.13 -m pytest -q tests/test_runtime_state_concurrency.py
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
```

Expected: 20/20 PASS.

- [ ] **Step 9: Run full pytest**

```powershell
py -3.13 -m pytest -q
```

Expected: PASS.

- [ ] **Step 10: Record the commit boundary**

Proposed message:

```text
fix: make exact-turn state mutations transactional
```

---

# PR-F — Source Provider Correctness

### Task 10: Upgrade `korean-law-mcp` to 4.12.2 Only After Functional Acceptance

**Files:**
- Modify: `package.json`
- Modify: `package-lock.json`
- Create: `docs/task14-stabilization-evidence/upstream-mcp-4.12.2-acceptance.md`
- If a reusable stdio acceptance client is needed and can be implemented without vendoring upstream logic:
  - Create: `scripts/validate_upstream_mcp_acceptance.py`
  - Create: `tests/test_validate_upstream_mcp_acceptance.py`
- Update docs that state the pinned upstream version after acceptance.

**Interfaces:**
- Produces: `SOURCE_CORRECTNESS=PASS|FAIL`.
- This gate is separate from `npm audit`.

- [ ] **Step 1: Capture the 4.12.1 baseline**

Run:

```powershell
node --version
npm --version
npm ci
npm ls korean-law-mcp
npm audit --omit=dev
npm run mcp -- --help
```

Record exact versions and exit codes.

- [ ] **Step 2: Update only the dependency pin**

Change:

```json
"korean-law-mcp": "4.12.1"
```

to:

```json
"korean-law-mcp": "4.12.2"
```

Regenerate the lockfile with the repository's normal npm workflow.

- [ ] **Step 3: Run package checks**

```powershell
npm ci
npm ls korean-law-mcp
npm audit --omit=dev
npm run mcp -- --help
```

Expected:
- resolved version exactly 4.12.2;
- audit gate meets repository policy;
- MCP process starts.

These checks are not yet SOURCE_CORRECTNESS PASS.

- [ ] **Step 4: Run functional source acceptance**

Using the current MCP interface, execute and preserve raw results for:

1. `get_law_text` on a known valid law/article path that exercises the MST single-law retrieval path.
2. citation verification through `legal_analysis(mode=verify_citations)` or the exposed equivalent.
3. `get_historical_law` on a known historical law with multiple articles.
4. one branch article such as `제75조의2` or another verified 가지번호 fixture.
5. one article whose operative text is in paragraph/item children rather than title text only.

The fixture identity must be recorded before the run:
- law name/id/MST;
- article;
- effective date if historical;
- expected non-empty structural fields.

Do not assert exact prose beyond the stable structural facts needed to detect the 4.12.1 failure class.

- [ ] **Step 5: Declare source correctness**

PASS only if all five functional probes return usable, structurally correct source data and no probe falls back to "자료 없음" solely because of transport/parser failure.

Otherwise:

```text
SOURCE_CORRECTNESS=FAIL
Overall=HOLD
```

and do not continue to live ASH acceptance.

- [ ] **Step 6: Run JDIPT deterministic regressions after the dependency bump**

```powershell
py -3.13 -m pytest -q
py -3.13 scripts/validate_repo.py
py -3.13 scripts/validate_authority_temporal_contract.py
npm ci
npm audit --omit=dev
npm run mcp -- --help
git diff --check
```

Expected: PASS.

- [ ] **Step 7: Record the commit boundary**

Proposed message:

```text
chore: validate korean-law-mcp 4.12.2
```

---

# PR-G — Installed / Active Runtime Attestation + Runner Lifecycle

### Task 11: Make Runtime-Bundle Completeness Independent of Repo/Install Equality

**Files:**
- Modify: `scripts/plugin_integrity.py`
- Modify: `tests/test_plugin_integrity_runtime_bundle.py`
- Modify: `tests/test_plugin_integrity.py`

**Interfaces:**
- Produces:
  - `required_runtime_logical_paths(root) -> tuple[str, ...]`
  - `validate_runtime_bundle_completeness(root) -> list[str]`
- `resolve_installed_skill_root(explicit=...)` becomes strict when explicit is supplied.

- [ ] **Step 1: Write the "both sides missing" false-green test**

Add:

```python
def test_compare_fails_when_required_runtime_file_is_missing_from_both_sides(tmp_path):
    repo = tmp_path / "repo"
    installed = tmp_path / "installed"
    _write_bundle(repo, omit="scripts/stop_synthesis_gate.py")
    _write_bundle(installed, omit="scripts/stop_synthesis_gate.py")

    mismatches = compare_runtime_manifests(
        repo,
        installed / "skills" / "law-interpretation-request",
    )

    assert "repository required file missing: plugin/scripts/stop_synthesis_gate.py" in mismatches
    assert "installed required file missing: plugin/scripts/stop_synthesis_gate.py" in mismatches
```

Add a strict explicit target test:

```python
def test_explicit_missing_install_root_does_not_fallback_to_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    explicit = tmp_path / "does-not-exist"
    assert resolve_installed_skill_root(explicit) is None
```

- [ ] **Step 2: Run and verify RED**

```powershell
py -3.13 -m pytest -q tests/test_plugin_integrity.py tests/test_plugin_integrity_runtime_bundle.py
```

Expected: false-green test fails.

- [ ] **Step 3: Implement required-path completeness**

Maintain a fixed required logical-path list from `SKILL_RUNTIME_FILES`, required reference files, and `PLUGIN_RUNTIME_FILES`.

`compare_runtime_manifests()` order:
1. validate repository completeness;
2. validate installed completeness;
3. compare digests only after both completeness reports are produced.

Never omit a required path merely because it is absent.

- [ ] **Step 4: Make explicit installed root authoritative**

If `explicit` is not `None`:
- inspect only that target;
- return `None` if invalid;
- do not search env/cache fallback.

Fallback resolution is used only when no explicit root was supplied.

- [ ] **Step 5: Run focused and full tests**

```powershell
py -3.13 -m pytest -q tests/test_plugin_integrity.py tests/test_plugin_integrity_runtime_bundle.py
py -3.13 -m pytest -q
```

Expected: PASS.

- [ ] **Step 6: Record the commit boundary**

Proposed message:

```text
fix: validate runtime bundle completeness before parity
```

---

### Task 12: Add Exact-Turn Active Runtime Attestation

**Files:**
- Create: `scripts/runtime_attestation.py`
- Create: `tests/test_runtime_attestation.py`
- Modify: `scripts/inject_registry_runtime.py`
- Modify: `scripts/stop_synthesis_gate.py`
- Modify: `scripts/plugin_integrity.py` runtime file list
- Modify: `tests/test_registry_runtime_bridge.py`
- Modify: `tests/test_stop_synthesis_gate.py`

**Interfaces:**
- Produces:
  - `RuntimeAttestation`
  - `write_runtime_attestation(...)`
  - `load_runtime_attestation(...)`
  - `verify_active_runtime_attestation(...)`
- Attestation is diagnostic/acceptance evidence; correctness must not silently fall back to a different cache.

Schema:

```python
@dataclass(frozen=True)
class RuntimeAttestation:
    session_id: str
    turn_id: str
    plugin_root: str
    plugin_data: str
    runtime_manifest_sha256: str
    hook_name: str
```

- [ ] **Step 1: Write mismatch tests**

```python
def test_active_attestation_rejects_wrong_plugin_root(tmp_path):
    attestation = _attestation(plugin_root=str(tmp_path / "old-plugin"))
    result = verify_active_runtime_attestation(
        attestation,
        expected_plugin_root=tmp_path / "current-plugin",
        expected_manifest_sha256="abc",
    )
    assert not result.passed
    assert "plugin_root" in result.failures


def test_active_attestation_rejects_manifest_mismatch(tmp_path):
    ...
```

- [ ] **Step 2: Run and verify RED**

```powershell
py -3.13 -m pytest -q tests/test_runtime_attestation.py
```

Expected: import failure.

- [ ] **Step 3: Implement attestation utilities**

Write attestation under:

```text
PLUGIN_DATA/runtime-attestation/<session>/<turn>.json
```

Use atomic temp-write + replace.

`runtime_manifest_sha256` is a hash over the canonical JSON form of the runtime manifest, not a hash of a display string.

- [ ] **Step 4: Emit attestation from actual hook execution**

`inject_registry_runtime.py` must record `PLUGIN_ROOT`, `PLUGIN_DATA`, session, turn, and hook name when the registry/completion tool is invoked.

`stop_synthesis_gate.py` entrypoint must update/confirm a Stop attestation for the same exact session/turn.

Any diagnostic write failure must:
- be visible in acceptance evidence;
- not corrupt proposition state;
- not be misreported as file parity PASS.

- [ ] **Step 5: Add bridge tests**

Test:
- PreToolUse attestation root;
- Stop attestation same exact turn;
- wrong turn cannot satisfy acceptance;
- old cache root is rejected.

- [ ] **Step 6: Run tests**

```powershell
py -3.13 -m pytest -q `
  tests/test_runtime_attestation.py `
  tests/test_registry_runtime_bridge.py `
  tests/test_stop_synthesis_gate.py
```

Expected: PASS.

- [ ] **Step 7: Record the commit boundary**

Proposed message:

```text
feat: attest the active JDIPT runtime
```

---

### Task 13: Harden Regression Process Cleanup and Fresh-Artifact Ownership

**Files:**
- Modify: `run_jdipt_full_regression_v4.py`
- Modify: `tests/test_runner_diagnostics.py`
- Add if needed: `tests/fixtures/runner/child_holds_pipe.py`

**Interfaces:**
- `run_case()` must never score an answer file that existed before the attempt.
- timeout cleanup must have a second bounded wait.
- `resolve_codex_command()` must support native POSIX `codex`.

- [ ] **Step 1: Add stale-answer test**

Use a temporary output directory with a pre-existing expected answer file.

Expected behavior:
- `run_case()` returns `process_ok=False`;
- error contains `pre-existing answer artifact`;
- no old answer is scored.

- [ ] **Step 2: Add native POSIX resolver test**

Monkeypatch `shutil.which` so:
- `codex.exe` is absent;
- `codex` resolves `/usr/local/bin/codex`.

Expected:

```python
assert resolve_codex_command() == ["/usr/local/bin/codex"]
```

- [ ] **Step 3: Add bounded second-wait cleanup test**

Use a fixture child process that spawns a descendant holding a pipe open.

The test must complete within a bounded outer pytest timeout implemented by process join/time measurement; do not let the suite hang.

- [ ] **Step 4: Run and verify RED**

```powershell
py -3.13 -m pytest -q tests/test_runner_diagnostics.py
```

- [ ] **Step 5: Harden `run_case()`**

Before spawning:

```python
if answer_path.exists():
    return Result(
        ...,
        process_ok=False,
        error="pre-existing answer artifact",
        ...
    )
```

Do not delete it silently.

After timeout:
1. terminate process tree;
2. call `communicate(timeout=10)`;
3. on a second timeout, `proc.kill()` and one final `communicate(timeout=5)`;
4. if still not reaped, return a lifecycle failure and never score the answer.

- [ ] **Step 6: Add POSIX `codex` resolution**

Check native executables in this order:
- `codex.exe`
- `codex`

Then npm shims.

- [ ] **Step 7: Run runner tests repeatedly**

```powershell
1..10 | ForEach-Object {
  py -3.13 -m pytest -q tests/test_runner_diagnostics.py
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
```

Expected: 10/10 PASS.

- [ ] **Step 8: Full pytest**

```powershell
py -3.13 -m pytest -q
```

Expected: PASS.

- [ ] **Step 9: Record the commit boundary**

Proposed message:

```text
fix: harden regression process and artifact lifecycle
```

---

# PR-H — Targeted and Global Acceptance

### Task 14: Add a First-Class ASH-06 3-Run / 10-Run Acceptance Harness

**Files:**
- Create: `scripts/run_targeted_ansim_acceptance.py`
- Create: `tests/test_targeted_ansim_acceptance.py`
- Modify: `scripts/run_eval_suite.py` only to reuse stable helpers if necessary; do not duplicate process execution.
- Evidence output: `docs/task14-stabilization-evidence/ash06/`

**Interfaces:**
- Produces:
  - `build_targeted_ansim_summary(case_id, results, repetitions) -> dict`
  - CLI accepts `--case-id ASH-06 --repetitions 3|10`
- This targeted harness does not redefine the oracle; it calls `evaluate_ansim_case`.

- [ ] **Step 1: Write summary tests**

```python
def test_ash06_three_run_requires_three_semantic_passes():
    results = [_result("ASH-06", attempt, "PASS") for attempt in (1, 2, 3)]
    summary = build_targeted_ansim_summary("ASH-06", results, repetitions=3)
    assert summary["release_verdict"] == "PASS"


def test_ash06_three_run_fails_on_one_semantic_failure():
    results = [
        _result("ASH-06", 1, "PASS"),
        _result("ASH-06", 2, "FAIL"),
        _result("ASH-06", 3, "PASS"),
    ]
    summary = build_targeted_ansim_summary("ASH-06", results, repetitions=3)
    assert summary["release_verdict"] == "FAIL"


def test_ash06_ten_run_requires_exact_attempt_numbers():
    results = [_result("ASH-06", n, "PASS") for n in range(1, 11)]
    summary = build_targeted_ansim_summary("ASH-06", results, repetitions=10)
    assert summary["release_verdict"] == "PASS"
```

Also fail on:
- wrong case id;
- duplicate attempt;
- critical marker;
- process failure.

- [ ] **Step 2: Run and verify RED**

```powershell
py -3.13 -m pytest -q tests/test_targeted_ansim_acceptance.py
```

- [ ] **Step 3: Implement the targeted summary**

Requirements:
- exactly one requested case id;
- attempts exactly `1..N`;
- process success N/N;
- semantic PASS N/N;
- zero critical negative markers;
- zero global hard-gate findings.

For targeted ASH-06, **no 26/27-style tolerance exists**.

- [ ] **Step 4: Reuse the existing run-case path**

Do not write another subprocess runner. Call the same hardened `legacy.run_case()`/shared helper used by `run_eval_suite.py`.

Each attempt gets a unique directory:

```text
docs/task14-stabilization-evidence/ash06/3run/run-01
...
docs/task14-stabilization-evidence/ash06/10run/run-10
```

For each attempt save:
- prompt;
- raw answer;
- process log;
- oracle result;
- exact-turn runtime attestation;
- registry/closure summary where observable.

- [ ] **Step 5: Add early-halt behavior**

For the live 3-run gate:
- run sequentially;
- if any attempt fails runtime activation/registry closure/semantic oracle/critical marker, stop immediately;
- summary records remaining attempts `NOT_RUN`.

For 10-run:
- command must refuse to start unless the provided 3-run evidence summary has PASS and matches the same repository/install/runtime/oracle snapshot.

- [ ] **Step 6: Run static tests**

```powershell
py -3.13 -m pytest -q tests/test_targeted_ansim_acceptance.py
```

Expected: PASS.

- [ ] **Step 7: Record the commit boundary**

Proposed message:

```text
test: add gated ASH-06 acceptance runner
```

---

### Task 15: Execute the Fresh Static and Host Acceptance Gates

**Files:**
- Evidence only under `docs/task14-stabilization-evidence/`.
- No production edits after this task begins. Any failure returns to the owning task.

**Interfaces:**
- Consumes the exact integrated snapshot.
- Produces immutable evidence for later live runs.

- [ ] **Step 1: Freeze the candidate identity**

Record:

```powershell
git branch --show-current
git rev-parse HEAD
git status --short
git diff --check
```

If dirty, generate SHA-256 for every changed/untracked file and bind that manifest to all evidence.

- [ ] **Step 2: Run deterministic Python gates**

```powershell
py -3.13 -m pytest -q
py -3.13 scripts/validate_repo.py
py -3.13 scripts/validate_authority_temporal_contract.py
py -3.13 -m compileall -q scripts tests
git diff --check
```

All must PASS.

- [ ] **Step 3: Run Node/source-provider package gates**

```powershell
npm ci
npm audit --omit=dev
npm run mcp -- --help
```

All repository policy gates must PASS.

- [ ] **Step 4: Run source correctness acceptance**

Use Task 10 evidence script/procedure.

Required:

```text
SOURCE_CORRECTNESS=PASS
```

- [ ] **Step 5: Install/refresh only the candidate intended for host acceptance**

Record exact installed root and version.

Do not rely on "newest cache" resolution.

- [ ] **Step 6: Run repository completeness and installed parity**

Required:

```text
repository_bundle_complete=true
installed_bundle_complete=true
mismatches=[]
```

- [ ] **Step 7: Run active-runtime identity probe in a fresh turn**

Required exact-turn evidence:

```text
active_plugin_root == expected installed/plugin root
active_runtime_manifest == candidate runtime manifest
session/turn exact
PreToolUse/Stop attestation valid
```

- [ ] **Step 8: Run negative host probes**

At minimum:
- missing PLUGIN_DATA;
- wrong session;
- wrong turn;
- incomplete registry;
- unclosed obligation;
- corrupted state;
- exhausted enforcement;
- exhausted answer repair;
- stale alternate cache.

Expected behavior is explicit fail-closed or documented unrelated-turn no-op; none may silently pass as a valid JDIPT final answer.

- [ ] **Step 9: Gate**

If any step fails:

```text
STATIC_OR_HOST_ACCEPTANCE=FAIL
ASH06_3RUN=NOT_RUN
ASH06_10RUN=NOT_RUN
Overall=HOLD
```

Do not patch code inside the acceptance task.

---

### Task 16: Run ASH-06 Fresh 3-Run then 10-Run

**Files:**
- Evidence only:
  - `docs/task14-stabilization-evidence/ash06/3run/`
  - `docs/task14-stabilization-evidence/ash06/10run/`

**Interfaces:**
- Consumes Task 15 PASS snapshot.
- Produces targeted stability evidence.

- [ ] **Step 1: Run fresh ASH-06 3-run**

Use:

```powershell
py -3.13 scripts/run_targeted_ansim_acceptance.py `
  --case-id ASH-06 `
  --repetitions 3 `
  --output-dir docs/task14-stabilization-evidence/ash06/3run
```

Required:

```text
process            3/3
runtime activation 3/3
registry closure   3/3
semantic oracle    3/3
critical negatives 0
repair exhausted   0
release_verdict    PASS
```

If any run fails, stop. Do not run 10-run.

- [ ] **Step 2: Review each 3-run raw answer manually against the observed propositions**

This review is independent of the machine oracle. Record:
- base proposition;
- exception proposition;
- current-status proposition;
- legal act/object/effect;
- evidence source id/locator;
- whether any required sentence is merely quoted/rejected.

Any discrepancy = HOLD.

- [ ] **Step 3: Run fresh ASH-06 10-run only after 3-run PASS**

```powershell
py -3.13 scripts/run_targeted_ansim_acceptance.py `
  --case-id ASH-06 `
  --repetitions 10 `
  --require-passing-prerequisite docs/task14-stabilization-evidence/ash06/3run/summary.json `
  --output-dir docs/task14-stabilization-evidence/ash06/10run
```

Required:

```text
process             10/10
runtime activation  10/10
registry closure    10/10
semantic oracle     10/10
activation bypass        0
registry missing         0
critical missing         0
critical negative        0
repair exhausted         0
release_verdict       PASS
```

- [ ] **Step 4: Bind evidence to snapshot**

Both summaries must include:
- repository SHA / dirty manifest digest;
- installed runtime manifest digest;
- active runtime manifest digest;
- oracle contract id/hash;
- model;
- Codex version.

- [ ] **Step 5: Gate**

Only 3/3 + 10/10 PASS allows Task 17.

---

### Task 17: Run the Unified Global Release Gate

**Files:**
- Evidence:
  - `docs/task14-stabilization-evidence/global-release/`
- Update only after PASS:
  - `docs/validation/v0.2.4-ansim-housing-regression.md`
  - relevant README/roadmap status text.

**Interfaces:**
- Consumes exact Task 16 snapshot.
- Produces final project candidate verdict.

- [ ] **Step 1: Run the one release authority**

Use the final CLI form implemented in Task 3:

```powershell
py -3.13 scripts/run_release_gate.py --full --codex <exact-codex-path>
```

It must run:
1. deterministic;
2. Core stability;
3. Full active;
4. Ansim core;
5. Ansim stability;
6. package/static;
7. installed bundle gate;
8. active runtime attestation gate;
9. source correctness gate.

If installed/active/source gates are supplied as verified evidence inputs rather than rerun inside the process, the release runner must verify their snapshot digest before accepting them.

- [ ] **Step 2: Required global result**

```text
deterministic                   PASS
Core14 stability               PASS
Full26                         PASS
Ansim9 core                    PASS
Ansim stability                PASS
global hard-gate violations       0
critical negative markers         0
package/static                 PASS
installed bundle               PASS
active runtime                 PASS
source correctness             PASS
```

- [ ] **Step 3: Run final repository hygiene**

```powershell
py -3.13 -m pytest -q
py -3.13 scripts/validate_repo.py
py -3.13 scripts/validate_authority_temporal_contract.py
py -3.13 -m compileall -q scripts tests
npm ci
npm audit --omit=dev
npm run mcp -- --help
git diff --check
git status --short
```

- [ ] **Step 4: Update validation documentation only if all gates PASS**

Document actual counts and exact snapshot identifiers.

Never reuse v0.2.3 PASS text as proof for the current candidate.

- [ ] **Step 5: Final verdict**

Only if everything above passes:

```text
Correctness stabilization: PASS
Release candidate: CONDITIONAL_PASS
```

`CONDITIONAL_PASS` becomes `PASS` only after any separately required user-approved merge/release procedure is completed and post-merge verification is run on the merge commit.

Any failure:

```text
Overall: HOLD
```

- [ ] **Step 6: Record the commit boundary**

Proposed message:

```text
docs: record JDIPT stabilization acceptance
```

No push/PR/merge without explicit user authorization.

---

# Post-Acceptance Cleanup

### Task 18: Remove Legacy Runtime Code Only After Canonical Parity Is Proven

**Files:**
- Candidate removals only if still present after Task 1:
  - `scripts/runtime_registry_state.py`
  - `scripts/synthesis_integrity.py`
  - corresponding legacy-only tests/imports
- Modify:
  - `scripts/plugin_integrity.py`
  - architecture/docs as required

**Interfaces:**
- Consumes Task 17 PASS evidence.
- Produces one canonical runtime implementation.

- [ ] **Step 1: Re-run import/call-site search**

```powershell
rg -n "runtime_registry_state|synthesis_integrity" .
```

Classify every occurrence.

- [ ] **Step 2: Prove every old public behavior is covered by canonical tests**

Build a checklist mapping each old test/invariant to:
- `legal_proposition`;
- registry;
- render coverage;
- soundness;
- obligation closure;
- exact-turn enforcement;
- transactional state.

If any old invariant has no canonical equivalent, do not delete that code yet.

- [ ] **Step 3: Remove only proven-dead implementation**

Deletion must not include historical evidence/docs that are intentionally retained.

- [ ] **Step 4: Run full deterministic + targeted tests**

```powershell
py -3.13 -m pytest -q
py -3.13 scripts/validate_repo.py
py -3.13 scripts/validate_authority_temporal_contract.py
py -3.13 -m compileall -q scripts tests
git diff --check
```

Expected: PASS.

- [ ] **Step 5: Re-run plugin completeness/parity after removal**

Required:
- repository required runtime list matches the canonical architecture;
- installed refresh has no extra legacy runtime file that can still be loaded.

- [ ] **Step 6: Do not reuse pre-cleanup live evidence as post-cleanup release evidence**

Because runtime bytes changed, any release claim after cleanup requires at least:
- active runtime identity re-attestation;
- targeted smoke;
- the release gate required by policy for a changed runtime snapshot.

- [ ] **Step 7: Record the commit boundary**

Proposed message:

```text
refactor: remove superseded JDIPT runtime paths
```

---

# Required Review Checkpoints

The executor must stop for review at these boundaries even in inline execution:

1. **After Task 1** — convergence matrix approved; no UNKNOWN runtime ownership.
2. **After Task 5** — soundness design passes confirmed false-green regressions.
3. **After Task 6** — source-observation capability PASS. A BLOCKED result requires architecture review; do not continue.
4. **After Task 9** — concurrency tests pass repeatedly.
5. **After Task 10** — source-provider correctness PASS.
6. **After Task 15** — static + host acceptance PASS.
7. **After Task 16** — ASH-06 3/3 then 10/10 PASS.
8. **After Task 17** — global release decision.

---

# Definition of Done

The stabilization program is complete only when all are true:

```text
[ ] R1/R2/L1 convergence reviewed
[ ] R2 canonical proposition model is the single production domain model
[ ] semantic controls are typed and unknown values fail closed
[ ] render coverage and semantic soundness are separate
[ ] independent source-observation boundary is proven
[ ] material obligation closure is source-bound
[ ] registry completion requires obligation closure
[ ] runtime enforcement is exact-session/exact-turn and bounded
[ ] state mutation is locked/revisioned with no lost-update regression
[ ] korean-law-mcp 4.12.2 functional source acceptance passes
[ ] repository bundle completeness passes
[ ] installed bundle completeness/parity passes
[ ] active runtime attestation matches the candidate
[ ] regression runner cannot reuse stale artifacts and cleans timeout trees boundedly
[ ] ASH-06 fresh 3/3 passes
[ ] ASH-06 fresh 10/10 passes
[ ] Core14 passes
[ ] Full26 passes
[ ] Ansim9 core passes
[ ] Ansim stability policy passes with zero hard-gate violations
[ ] critical negative markers = 0
[ ] source correctness = PASS
[ ] one exact snapshot owns all evidence
```

If any checkbox is false:

```text
Overall: HOLD
```

The key implementation rule remains:

> **The model may propose legal propositions, but it must not be the sole authority for what evidence was actually observed or whether the complete required obligation set was closed. Coverage is not soundness, and only one release authority may declare PASS for one exact runtime snapshot.**
