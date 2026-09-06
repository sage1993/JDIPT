# Unified Release Authority Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Bind repository, installed bundle, active runtime, static checks, Core/Full/Ansim/Stability evidence, hard gates, source correctness, host acceptance, and case identity to one versioned release manifest evaluated by one authoritative gate.

**Architecture:** Reuse the existing `scripts/run_release_gate.py`, `scripts/eval_suite.py`, `scripts/ansim_housing_oracle.py`, and `scripts/plugin_integrity.py`. Add a focused release-manifest module that validates exact snapshot identity, mandatory suite evidence, hard gates, source/host acceptance, and stable case IDs; the CLI will only publish the verdict returned by that validator.

**Tech Stack:** Python 3.13 standard library, JSON, SHA-256, pytest, existing JDIPT runners and validators.

**Spec:** User Task 2 — Unified Release Authority.

## Global Constraints

- Preserve Task 1 `registry_required`, `registry_completed`, exact-one enforcement, and range-exception relation invariants.
- Do not add typed semantic controls, semantic soundness, obligation ledger, source/obligation closure, runtime state redesign, MCP upgrades, ASH-06 x3/x10 acceptance, or final release evidence.
- Keep the existing suite manifest and Ansim oracle as the canonical case/oracle sources.
- Treat `NOT_RUN`, missing/duplicate case IDs, snapshot mismatches, hard-gate failures, critical negatives, install mismatch, and active-runtime mismatch as HOLD.
- Do not delete or rewrite existing user artifacts, marketplace worktrees, or generated host artifacts.

---

### Task 1: Freeze the Task 1 baseline

**Files:**
- Modify: existing Task 1-scoped runtime, tests, and evidence files already present in the worktree.
- Preserve: `.task14d-*`, `.task14d-schema/`, `.worktrees/`, and other generated/host-only artifacts without staging them.

**Interfaces:**
- Produces: a local Task 1 closure commit and `TASK2_BASE_SHA`.

- [ ] Step 1: Classify every tracked and untracked path as `TASK1_SCOPED`, `PRE_EXISTING_USER_CHANGE`, `GENERATED_ARTIFACT`, `HOST_ONLY_CHANGE`, or `UNKNOWN`.
- [ ] Step 2: Resolve any `UNKNOWN` path before staging; do not delete or silently include it.
- [ ] Step 3: Run `python scripts/plugin_integrity.py`, serial `python -m pytest -q`, `python -m compileall -q scripts tests`, both validators, Task 1 targeted tests, and `git diff --check` under the supported host identity when the known 0700 TEMP issue requires it.
- [ ] Step 4: Stage only Task 1 implementation/tests/evidence and commit with `fix(stabilization): close R2 correctness baseline`.
- [ ] Step 5: Record the resulting SHA as `TASK2_BASE_SHA` and verify the worktree classification again.

### Task 2: Reproduce release false-green paths

**Files:**
- Create: `tests/test_release_authority.py`
- Modify: `tests/test_release_gate.py`

**Interfaces:**
- Consumes: `evaluate_release_manifest(manifest)` from `scripts/release_manifest.py`.
- Produces: regression coverage for `REQUIRED_SUITE_NOT_RUN`, `HARD_GATE_FAILURE`, `MISSING_CASE`, `DUPLICATE_CASE`, `SNAPSHOT_MISMATCH`, `INSTALLED_PARITY_FAILURE`, `ACTIVE_RUNTIME_IDENTITY_MISMATCH`, `CRITICAL_NEGATIVE`, and one valid same-snapshot PASS fixture.

- [ ] Step 1: Add a literal fixture builder in the test module containing all mandatory manifest sections and a fixed snapshot identity; derive expected IDs from hand-written lists, not production helpers.
- [ ] Step 2: Add one test per false-green scenario and assert `verdict == "HOLD"` plus the exact structured reason code.
- [ ] Step 3: Add a valid complete fixture test asserting `verdict == "PASS"` and an empty reason list.
- [ ] Step 4: Run `python -m pytest -q tests/test_release_authority.py` and confirm the tests fail because the authority module/API is not implemented yet.

### Task 3: Implement the versioned release manifest contract

**Files:**
- Create: `scripts/release_manifest.py`
- Create: `config/release-manifest.schema.json`
- Modify: `scripts/plugin_integrity.py`
- Modify: `scripts/eval_suite.py`
- Modify: `scripts/ansim_housing_oracle.py`
- Test: `tests/test_release_authority.py`

**Interfaces:**
- Produces: `RELEASE_SCHEMA_VERSION`, `REASON_CODES`, `build_changed_file_digest_manifest(repo_root)`, `build_runtime_manifest_digest(root)`, `build_snapshot_id(identity)`, `validate_release_manifest(manifest)`, and `evaluate_release_manifest(manifest) -> ReleaseDecision`.

- [ ] Step 1: Define the JSON schema with required sections `schema_version`, `repository`, `installed`, `active_runtime`, `oracle`, `static_validation`, `suites`, `hard_gates`, `source_correctness`, `runtime_host_acceptance`, `case_inventory`, `evidence`, and `final`.
- [ ] Step 2: Implement strict shape/type checks; reject unknown schema versions, missing required sections, malformed statuses, empty identities, and non-object evidence as `INVALID_MANIFEST`.
- [ ] Step 3: Implement canonical SHA-256 hashing for changed-file manifests, installed runtime manifests, oracle bytes, and the complete snapshot identity. Include the release schema version in the identity.
- [ ] Step 4: Implement per-layer identity checks for repository, installed bundle, and active runtime. A dirty repository requires its changed-file digest manifest; SHA alone is insufficient.
- [ ] Step 5: Implement per-suite case inventory checks that calculate missing, unexpected, and duplicate IDs from observed lists and reject empty IDs and substitutions.
- [ ] Step 6: Implement fail-closed checks for all four mandatory suites (`core`, `full`, `ansim`, `stability`), static validation, hard gates, critical negatives, source correctness, and host acceptance. Never convert a pass percentage into a PASS when a hard check is absent or failed.
- [ ] Step 7: Return a structured `ReleaseDecision` with `verdict`, ordered reason codes, and human-readable details. Only this function may produce the authoritative final verdict.
- [ ] Step 8: Run the targeted release-authority tests and confirm all nine regression scenarios are green.

### Task 4: Converge existing runners on the authority

**Files:**
- Modify: `scripts/run_release_gate.py`
- Modify: `scripts/run_eval_suite.py`
- Modify: `tests/test_release_gate.py`
- Modify: `tests/test_eval_suite.py`

**Interfaces:**
- Consumes: existing `GateResult` runners, suite manifest, Ansim oracle summary, installed/runtime roots, and `evaluate_release_manifest`.
- Produces: `--full` orchestration that executes or records every mandatory suite and emits a JSON manifest plus one final machine-readable verdict.

- [ ] Step 1: Add structured result conversion from existing deterministic, Core, Full, Ansim core, and Ansim stability runners without rewriting their case execution logic.
- [ ] Step 2: Make `--full` invoke Core, Full, Ansim core, and Ansim stability; if a runner is intentionally not executed, record `NOT_RUN` and let the authority return HOLD.
- [ ] Step 3: Add explicit `--manifest`, `--manifest-output`, `--installed-root`, and `--active-runtime-root` handling. Do not infer active runtime identity from repository or installed identity.
- [ ] Step 4: Route all CLI output through `evaluate_release_manifest`; component results may be printed as evidence, but no component may print an authoritative release PASS.
- [ ] Step 5: Make exit code `0` mean only authoritative PASS; all HOLD, invalid-manifest, execution, and evidence errors return non-zero.
- [ ] Step 6: Add tests proving `--full` includes every mandatory suite and that an absent suite cannot be silently skipped.

### Task 5: Document the contract and acceptance evidence

**Files:**
- Modify: `README.md`
- Modify: `docs/evaluation-suites.md`
- Modify: `docs/plugin-packaging.md`
- Create: `docs/task2-release-evidence.md`

**Interfaces:**
- Consumes: the implemented schema, CLI flags, reason codes, and fresh verification output.
- Produces: user-facing instructions and evidence that identify the exact repository/install/runtime/oracle snapshot without claiming final release evidence.

- [ ] Step 1: Document the manifest schema version, mandatory inputs, exact-snapshot rule, case identity checks, hard-gate precedence, and CLI exit semantics.
- [ ] Step 2: Document that Core/Full/Ansim/Stability runners provide evidence only and cannot independently authorize release PASS.
- [ ] Step 3: Record the Task 2 baseline SHA, authority inventory, exact root cause, production changes, regression matrix, and residual environment/provenance risks.
- [ ] Step 4: Do not record live final release acceptance or ASH-06 x3/x10 evidence in this task.

### Task 6: Verify, review, and close Task 2

**Files:**
- Modify: `docs/task2-release-evidence.md`

- [ ] Step 1: Run targeted release-authority tests.
- [ ] Step 2: Run false-green regressions and Task 1 targeted regressions.
- [ ] Step 3: Run full pytest, compileall, validators, plugin integrity, and `git diff --check` serially; classify the known TEMP identity issue separately when necessary.
- [ ] Step 4: Run a scoped read-only code review against `TASK2_BASE_SHA..HEAD`, focusing on alternate PASS paths, snapshot mixing, case IDs, missing suites, hard-gate bypass, stale runtime, and fail-open manifest behavior.
- [ ] Step 5: Fix every Critical/Important review finding, rerun targeted tests, and re-review.
- [ ] Step 6: Commit Task 2 separately with `feat(release): add unified release authority` and record the final verdict as PASS only if every acceptance checkbox is freshly evidenced; otherwise record HOLD and `NEXT = Continue Task 2`.
