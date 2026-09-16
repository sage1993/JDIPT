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

    def test_temporal_render_text_is_optional_evidence_metadata(self):
        ledger = MaterialObligationLedger.from_mapping(
            {
                "obligations": [
                    {
                        "obligation_id": "ob-1",
                        "issue_type": "source",
                        "source_status": "SOURCE_CONFIRMED",
                        "evidence_source_ids": ["src-1"],
                        "proposition_ids": ["p-1"],
                    }
                ],
                "verified_source_evidence": [
                    {
                        "source_id": "src-1",
                        "authority_kind": "statute",
                        "source_title": "Act",
                        "source_locator": "§1",
                        "evidence_span": "신청인은 신청해야 한다.",
                        "temporal_status": "CURRENT_CONFIRMED",
                    }
                ],
            }
        )
        self.assertIsNone(ledger.verified_source_evidence[0].temporal_render_text)


if __name__ == "__main__":
    unittest.main()
