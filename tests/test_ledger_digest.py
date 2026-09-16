import unittest

from scripts.material_obligation_ledger import (
    MaterialObligationLedger,
    canonical_material_obligation_ledger_digest,
)


class LedgerDigestTests(unittest.TestCase):
    def test_digest_is_stable_for_equivalent_typed_ledger(self):
        payload = {
            "obligations": [
                {
                    "obligation_id": "ob-1",
                    "issue_type": "source",
                    "source_status": "SOURCE_UNRESOLVED",
                    "evidence_source_ids": [],
                    "proposition_ids": ["p-1"],
                }
            ],
            "verified_source_evidence": [],
        }
        first = MaterialObligationLedger.from_mapping(payload)
        second = MaterialObligationLedger.from_mapping(dict(payload))
        self.assertEqual(
            canonical_material_obligation_ledger_digest(first),
            canonical_material_obligation_ledger_digest(second),
        )


if __name__ == "__main__":
    unittest.main()
