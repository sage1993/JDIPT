# Task 2 Unified Release Authority Evidence

이 문서는 release authority 계약과 회귀 검증을 기록한다. 이 Task에서는 live 최종 release acceptance evidence와 ASH-06 x3/x10 evidence를 생성하지 않는다.

## Baseline

- Task 1 closure commit: `b5a55ecbbbb378418fdc5eeb4ef004729ff0c57f`
- Task 2 base SHA: `b5a55ecbbbb378418fdc5eeb4ef004729ff0c57f`
- Branch: `codex-jdipt-correctness-stabilization`
- Installed reference: `C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4`

Task 1 baseline은 먼저 독립 커밋으로 고정했다. `.task1r-*` 디렉터리는 테스트 실행 중 생성된 artifact로 분류하여 커밋하지 않는다.

## Existing Authority Inventory

| Component | Can declare final PASS? | Inputs | Snapshot-bound? | Hard-gate aware? | Action |
| --- | --- | --- | --- | --- | --- |
| `scripts/run_release_gate.py` (기존) | Yes, via aggregate exit code | deterministic/core/full/package `GateResult` | No | No | ROUTE to unified authority |
| `scripts/run_eval_suite.py` | Component result only | suite runner output | No | Ansim oracle only | KEEP as evidence producer |
| Ansim oracle summary | Component result only | Ansim case results | No | Yes, within Ansim suite | KEEP; rename to `suite_verdict` |
| `scripts/plugin_integrity.py` | Component integrity result | repository/installed runtime manifests | Partially | No | KEEP; consume in manifest |
| `.github/workflows/ci.yml` | CI job status, not release PASS | pytest, validators, Node checks | No | No | KEEP as component validation; release CLI is authoritative |

### Exact root cause

The former release script returned success when the `GateResult` objects that happened to run were successful. Its `--full` path did not require every mandatory suite, did not bind evidence to repository/install/active-runtime/oracle identity, and did not validate stable case IDs or a separate hard-gate result. Consequently, a partial or mixed set of component PASS values could be interpreted as release PASS.

## Production Changes

- `config/release-manifest.schema.json`: versioned manifest shape with required identity, suite, static, hard-gate, source, host, case-inventory, evidence, and final sections.
- `scripts/release_manifest.py`: canonical SHA-256 identity, strict fail-closed validation, case identity checks, mandatory-suite checks, and structured `ReleaseDecision`.
- `scripts/run_release_gate.py`: existing runners are retained as evidence producers; `--full` runs Core, Stability, Full, and Ansim; `--manifest` evaluates an existing manifest; only the unified authority controls exit code 0.
- `scripts/run_eval_suite.py` and `scripts/ansim_housing_oracle.py`: Ansim output is a suite-level `suite_verdict`, not an alternate release verdict.
- `tests/test_release_authority.py` and `tests/test_release_gate.py`: false-green and orchestration regressions.

## Release Contract

`schema_version` is `1.0`. A release PASS requires all of the following in one manifest:

- repository SHA and, when dirty, the changed-file digest manifest;
- installed plugin version, manifest digest, and parity PASS;
- independently recorded active runtime plugin ID, source path, digest, and identity PASS;
- oracle version and raw-byte digest;
- PASS for all static validation fields;
- PASS for `core`, `full`, `ansim`, and `stability` with exact expected/observed case IDs;
- no hard-gate violations and no critical-negative markers;
- source correctness and runtime-host acceptance PASS;
- evidence snapshot ID equal to the canonical hash of the complete release identity.

`NOT_RUN`, missing/duplicate/unexpected IDs, hard-gate failures, identity mismatches, or critical negatives produce `HOLD` regardless of any percentage score.

## False-Green Regression Matrix

| Scenario | Expected | Actual | Verdict |
| --- | --- | --- | --- |
| required suite `NOT_RUN` | HOLD | HOLD | PASS |
| hard gate failure | HOLD | HOLD | PASS |
| missing case | HOLD | HOLD | PASS |
| duplicate case | HOLD | HOLD | PASS |
| mixed snapshot | HOLD | HOLD | PASS |
| installed mismatch | HOLD | HOLD | PASS |
| stale/active runtime mismatch | HOLD | HOLD | PASS |
| critical negative | HOLD | HOLD | PASS |
| valid full evidence | PASS | PASS | PASS |

The positive row is a deterministic fixture only; it is not live release acceptance evidence.

## Verification Evidence

The targeted release-authority and release-gate tests were green during implementation. The final verification commands and their fresh results are recorded in the task completion response after the complete sequence is rerun.

## Residual Risks

- The known un-escalated sandbox TEMP/0700 identity issue remains an environment risk and must not be reclassified as a product defect without evidence.
- Marketplace provenance continues to use the retained isolated worktree. It must not be deleted, moved, or rebound to the main worktree during release validation.
- Active runtime identity is intentionally a separate input. Omitting `--active-runtime-root` cannot produce release PASS.

## Review Scope

The scoped review targets alternate PASS paths, mixed snapshots, missing suites, duplicate identities, hard-gate bypass, stale runtime identity, and fail-open manifest behavior. No live final release acceptance is claimed by this document.
