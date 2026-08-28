# PR #9 Core Stability Failure Analysis and Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct the E44 deterministic oracle false negative for an actual Gate B response while preserving the existing E18 and E37 failure detection and all release-gate constraints.

**Architecture:** Treat the two latest Gate B runs as runtime evidence. Keep E18 and E37 classified as genuine model contract violations because their failed artifacts contain invalid output behavior. Change only the E44 lifecycle marker so semantically equivalent wording for the initial building permit is recognized, and pin the exact E44 runtime response in a regression test.

**Tech Stack:** Python 3.13, pytest, deterministic oracle functions in `scripts/regression_oracles.py`, UTF-8 Markdown fixtures.

**Spec:** `C:\Users\KSH\.codex\attachments\8d522aba-79d9-4a5a-96e0-0db046e0e388\pasted-text.txt`

## Global Constraints

- Do not loosen the oracle for invalid E18 H1 routing or E37 unstable/invalid URLs.
- Do not change package/plugin versions, `korean-law-mcp`, explicit-only invocation, or unrelated Skill contracts.
- Preserve the required `temporal_lifecycle` checks for the initial permit, later modification permit, effective date/transitional provision, and old/new law relationship.
- Use the exact actual E44 runtime answer as the regression fixture.
- Run targeted tests, the full pytest suite, repository validators, plugin integrity, `git diff --check`, and the requested release-gate commands where the runtime environment permits.

### Task 1: Pin the actual E44 false-negative response

**Files:**
- Modify: `tests/test_temporal_oracle_contract.py`
- Test: `tests/test_temporal_oracle_contract.py`

**Interfaces:**
- Consumes: `evaluate_case(44, answer)` and the actual response from `regression-results/core-stability/20260828-222121-114447/E44-attempt2/E44.md`.
- Produces: A regression test that fails before the oracle marker is corrected and passes afterward.

- [ ] **Step 1: Add a test containing the actual E44 attempt2 response**

  Copy the response body exactly, including its four default H1 headings and verified URLs, into a named test constant. Assert that `evaluate_case(44, actual_response)` is `PASS`.

- [ ] **Step 2: Run the targeted test to verify RED**

  Run: `py -3.13 -m pytest -q tests/test_temporal_oracle_contract.py`

  Expected: FAIL only for the new runtime-variant test with `temporal_lifecycle: initial permit reference date was not separated`; the existing neutral lifecycle test remains green.

### Task 2: Accept equivalent initial-permit wording without weakening E44

**Files:**
- Modify: `scripts/regression_oracles.py:_temporal_lifecycle`
- Test: `tests/test_temporal_oracle_contract.py`

**Interfaces:**
- Consumes: The existing `temporal_lifecycle` check and Task 1's exact runtime fixture.
- Produces: The same four-part E44 lifecycle contract, with `최초 건축허가` accepted as an equivalent initial-permit marker.

- [ ] **Step 1: Make the minimal oracle change**

  Expand only the initial-permit marker set from `("최초 허가", "허가 당시", "2024")` to include `"최초 건축허가"`. Leave all later-event, effective-date, old/new-law, neutrality, H1, hygiene, and URL checks unchanged.

- [ ] **Step 2: Run targeted oracle tests**

  Run: `py -3.13 -m pytest -q tests/test_temporal_oracle_contract.py tests/test_regression_oracles.py tests/test_e18_oracle_runtime_regression.py`

  Expected: PASS, including the existing negative E18/E37 fixtures and the new exact E44 runtime fixture.

- [ ] **Step 3: Run the complete regression and static validation set**

  Run:

  ```powershell
  py -3.13 -m pytest -q
  py -3.13 scripts/validate_repo.py
  py -3.13 scripts/validate_authority_temporal_contract.py
  py -3.13 scripts/plugin_integrity.py
  git diff --check
  git status --short
  ```

  Expected: all commands pass; only the plan, regression test, and oracle change are attributable to this task, while pre-existing untracked result reports remain untouched.

### Task 3: Re-run release acceptance checks

**Files:**
- No source files modified.

**Interfaces:**
- Consumes: The green deterministic validation from Task 2 and the corrected oracle.
- Produces: Evidence for Gate B and, only if Gate B is fully green, the full 26-case gate.

- [ ] **Step 1: Run Core stability**

  Run: `py -3.13 scripts/run_release_gate.py --critical-only`

  Expected: Gate A PASS and Gate B PASS; E37 must be 2/2, E44 3/3, and E45 3/3.

- [ ] **Step 2: Run the full gate only after Core stability passes**

  Run: `py -3.13 scripts/run_release_gate.py --full`

  Expected: Gate A PASS, Gate B PASS, Full active 26/26 PASS, and Gate D PASS. Any failed case or environment error yields `NOT_MERGE_READY`.

- [ ] **Step 3: Review the final diff and commit only the minimal fix**

  Run: `git diff --check` and `git status --short`; then commit the oracle/test/plan changes on `feat/v0.2.3-authority-temporal-evidence` with a cause-specific message such as `fix: accept equivalent E44 initial permit wording`.

## Self-Review

- E18 and E37 are documented as actual contract violations and remain rejected by existing checks.
- E44 changes only lexical recognition of an equivalent initial-permit phrase; it does not remove any required temporal or neutral-conclusion gate.
- The actual runtime response is captured before changing production code, proving the RED state.
- Full release acceptance is not declared unless the single full run reaches 26/26 with zero environment errors.
