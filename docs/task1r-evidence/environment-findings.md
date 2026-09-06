# Task 1R Phase C — Environment Findings

All findings below were freshly observed in the isolated R2 worktree before production edits.

| Finding | Fresh evidence | Classification | Acceptance impact |
|---|---|---|---|
| `plugin_integrity.py` | Exit `1`; auto-resolved candidate was `C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4`; R2 canonical files were missing from installed manifest and existing files had digest mismatches | **A — directly affects R2 parity** when installed/runtime is used | Installed/runtime PASS is unavailable. Repository-only tests cannot be reported as live installed parity. No installation mutation was performed. |
| `python scripts/validate_repo.py` | Exit `0`, `PASS`, `structural_synthesis_contract=PASS` | No blocker | Static repository contract passed at the pre-change snapshot. |
| `python scripts/validate_authority_temporal_contract.py` | Exit `0`, `PASS`, `authority_temporal_evidence_contract=v0.2.4-candidate` | No blocker | Authority/temporal contract passed at the pre-change snapshot. |
| `python -m pytest -q` | Exit `1`; collection reported permission denied for `pytest-cache-files-d_ie3gmn` and `pytest-cache-files-wmok1bp6` under the isolated worktree, with cache warnings | **C — host/environment-only deviation** | If the approved full-suite gate requires zero setup errors, the same finding is also a **B — repository acceptance blocker** until the suite is rerun with a permitted fresh basetemp or the ACL issue is remediated. It is not a product assertion failure. |
| focused pytest without a permitted basetemp | Exit `1`; 13 passed and 26 setup errors because `C:\Users\KSH\AppData\Local\Temp\pytest-of-KSH` could not create another numbered directory after 10 attempts | **C — host/environment-only deviation** | Same B impact if zero setup errors is required. The test command is not replaced; later verification uses the same tests with an explicit writable `--basetemp`. |

The previously recorded `213 passed / 47 setup errors` is retained as historical evidence. The fresh isolated reproduction produced a different count because the accessible cache/temp state changed; both failures have the same observed permission/ACL root cause and neither is silently converted to PASS.

The installed mismatch is not repaired in this closure because no installation mutation was authorized. Any R2 live acceptance that uses the installed bundle remains `NOT_PROVEN` until a separately authorized refresh and digest comparison.
