# Task 8 Material Obligation Registry Closure Design

## Goal

Close the gap between an independently supplied set of required material
obligations, verified source evidence, and the existing canonical
`LegalProposition` registry.

## Design

`MaterialObligation` identifies one required material issue, its typed source
resolution state, the source IDs that resolve it, and the canonical proposition
IDs that express it. `MaterialObligationLedger` groups those obligations with
the verified `EvidenceRef` objects used to resolve them. The ledger is a
domain boundary, not a second proposition store.

`evaluate_registry_closure` compares the ledger obligations, the explicitly
provided verified evidence set, and the canonical propositions. It fails closed
for missing links, unverified proposition evidence, unresolved-to-CLOSED
promotion, invalid applicability state, temporal conflicts, and malformed
inputs. It does not infer required obligations from the proposition list.

The existing `EvidenceRef`, `LegalProposition`, authority requirements, and
temporal requirements remain canonical. The source-closure module exposes its
existing authority/temporal semantics for reuse rather than duplicating a
second temporal truth system.

`RuntimeTurnState` stores an optional ledger field for backward-compatible
legacy snapshots. When present, the ledger is serialized in the same exact-turn
state and participates in the existing registry fingerprint. Only
`RegistryService.record_material_obligation_ledger` may persist ledger updates.
No direct runtime reader, writer, shadow state, fallback, or synthetic repair
is introduced.

The Stop gate evaluates registry closure before accepting a final answer when
the Task 8 ledger is present. Existing states without the optional ledger keep
the accepted Task 1R–7 behavior; Task 8-enabled states cannot pass without
closing their independently supplied obligations.

## Non-goals

- No arbitrary text obligation extractor or NLP/orchestration framework.
- No ASH-06-specific identifiers, values, or markers.
- No change to the installed `sage1993` binding.
- No change to the existing proposition render/source/answer closure contracts.
