# Task 1 Evidence Snapshot

**Snapshot timestamp:** `2026-09-06T21:37:22.367+09:00`
**Purpose:** Documentation/evidence-only fix round for Task 1; no production or external-baseline writes.

| Approved evidence field | Value | Basis / limitation |
|---|---|---|
| timestamp | `2026-09-06T21:37:22.367+09:00` | Captured from the isolated worktree host clock. |
| repository SHA | R2 `afa4003ca700f15794dc346e8239c6dda79492e2`; fix-round base commit `05b2cb63734f4c2cff414606a6a59c06010709a7` | The convergence comparison is against R2; the fix round is based on the prior local documentation commit. |
| working-tree state | L1 `DIRTY`; 601 manifest entries, including one `missing_or_nonfile`; isolated worktree documentation-only fix round pending commit | L1 was intentionally preserved and never cleaned or switched. |
| installed runtime digest | `NOT_OBSERVABLE` | `scripts/plugin_integrity.py` emitted per-file repository/installed digests and mismatches, but no accepted single installed-candidate digest or stable active install identity. No installation mutation was authorized. |
| active runtime identity | `NOT_OBSERVABLE` | Task 1 did not start an active plugin/MCP/Stop process or collect runtime attestation; no process identity may be invented. |
| oracle version | `v0.2.4-candidate` | Reported by `scripts/validate_authority_temporal_contract.py`. |
| oracle digest | `NOT_OBSERVABLE` | The Task 1 commands reported the oracle version but did not emit an oracle artifact/content digest; no digest is inferred. |
| commands | Baseline identity/status commands; prescribed dirty-tree digest; approved-document byte comparison; `rg -n "runtime_registry_state|synthesis_integrity" .`; document assertions; validators; pytest; `git diff --check`; commit | Full command records are in `2026-09-06-baseline-git-state.txt` and the fix-round section of `task-1-report.md`. |
| exit codes | Baseline commands `0`; digest `0`; byte comparison `0`; legacy search `0`; document assertions `0`; `validate_repo.py` `0`; authority validator `0`; plugin integrity `1`; pytest `1`; final `git diff --check` `0` | Nonzero results are preserved as concerns, not converted to PASS. |
| result summary | `KEEP` for verified R2 core ownership; `DELETE_AFTER_PARITY` for legacy modules; `UNKNOWN` for `registry_required`, `registry_completed`, `enforcement_count`, relation semantics, and unresolved L1 runtime extensions; Task 2 gate `BLOCKED` | Unknowns are explicit because semantic parity was not established in Task 1. |

## Baseline-only not-applicable fields

The following are explicitly `NOT_APPLICABLE` to this baseline-only artifact, with reasons rather than invented values:

- `release_verdict`: `NOT_APPLICABLE` — Task 1 establishes ownership/evidence and does not perform release acceptance.
- `active_runtime_pass`: `NOT_APPLICABLE` — no active runtime was started or attested.
- `installed_runtime_mutation`: `NOT_APPLICABLE` — the task forbids installation changes and preserves the external dirty baseline.
