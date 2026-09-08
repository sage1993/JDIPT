# Task 11R-3 Phase V — Final Regression

Local, non-active checks after the evidence-only change:

| Check | Result |
| --- | --- |
| `python -m pytest -q -p no:cacheprovider` | PASS — 688 passed (approved-permission rerun) |
| `python scripts/validate_repo.py` | PASS |
| `python scripts/validate_authority_temporal_contract.py` | PASS |
| `python -m compileall -q scripts tests` | PASS (approved-permission rerun) |
| `python scripts/plugin_integrity.py ...` | PASS — scoped runtime manifest, 0 mismatches |
| `npm ci` | PASS — 202 packages added, 203 audited, 0 vulnerabilities |
| `npm audit --audit-level=high` | PASS — 0 vulnerabilities |
| `npm run mcp -- --help` | PASS |
| `MCP_LOCAL` | PASS by inherited/local smoke evidence; no active post-install claim |
| `MCP_ACTIVE` | NOT_RUN after failed official installation |
| `git diff --check` | PASS |

The initial unapproved-permission pytest/compileall attempt was retained as an
environment ACL failure; the approved-permission rerun passed. Final runtime
acceptance remains HOLD because the official installation and active gates did
not pass.

