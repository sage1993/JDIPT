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
| commands | Baseline identity/status commands; prescribed dirty-tree digest; approved-document byte comparison; baseline-phase `rg -n "runtime_registry_state|synthesis_integrity" .`; fix-round-1 exact `rg -n "runtime_registry_state|synthesis_integrity" .`; fix-round-1 scoped `rg` over `docs scripts tests` excluding inaccessible cache paths; document assertions; validators; pytest; `git diff --check`; commit | Full phase-specific command records are in `2026-09-06-baseline-git-state.txt` and the fix-round sections of `task-1-report.md`. |
| exit codes | Baseline commands `0`; digest `0`; byte comparison `0`; **baseline-phase legacy search `0`**; **fix-round-1 exact legacy search `2`** due inaccessible generated cache paths; **fix-round-1 scoped legacy search `0`**; document assertions `0`; `validate_repo.py` `0`; authority validator `0`; plugin integrity `1`; pytest `1`; final `git diff --check` `0` | The baseline `0` and fix-round exact `2` are different phases and commands/results; neither is suppressed. Nonzero results are preserved as concerns, not converted to PASS. |
| result summary | `KEEP` for verified R2 core ownership; `DELETE_AFTER_PARITY` for legacy modules; `UNKNOWN` for `registry_required`, `registry_completed`, `enforcement_count`, relation semantics, and unresolved L1 runtime extensions; Task 2 gate `BLOCKED` | Unknowns are explicit because semantic parity was not established in Task 1. |

## Baseline-only not-applicable fields

The following are explicitly `NOT_APPLICABLE` to this baseline-only artifact, with reasons rather than invented values:

- `release_verdict`: `NOT_APPLICABLE` — Task 1 establishes ownership/evidence and does not perform release acceptance.
- `active_runtime_pass`: `NOT_APPLICABLE` — no active runtime was started or attested.
- `installed_runtime_mutation`: `NOT_APPLICABLE` — the task forbids installation changes and preserves the external dirty baseline.

## Search-phase disambiguation

The search results are phase-specific and must not be read as one unqualified result:

1. **Baseline capture:** `rg -n "runtime_registry_state|synthesis_integrity" .` exited `0` in the initial baseline phase. The recorded matches did not establish semantic parity.
2. **Fix round 1 exact search:** the same exact command, `rg -n "runtime_registry_state|synthesis_integrity" .`, exited `2` because inaccessible generated pytest cache/worktree paths emitted permission warnings. This is the current exact-search warning record.
3. **Fix round 1 scoped search:** the scoped command over `docs scripts tests`, excluding the inaccessible generated paths, exited `0` and found only documentation/history/structural-validator/test references; no active R2 plugin/MCP/Stop import was observed.

The authoritative current gate is the explicit fix-round `UNKNOWN`/**BLOCKED** ruling in the convergence document and fix-round report. The baseline-phase exit `0` is historical evidence, not a replacement for the fix-round exact-search exit `2`.
