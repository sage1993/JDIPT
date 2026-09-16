import unittest

from scripts.legal_proposition import (
    EvidenceRef,
    LegalProposition,
    Materiality,
    Modality,
    Polarity,
    PropositionStatus,
)
from scripts.proposition_source_closure import source_relation_failure_code


def proposition(source_span: str, subject: str = "신청인") -> LegalProposition:
    return LegalProposition(
        proposition_id="p-1",
        status=PropositionStatus.CLOSED,
        materiality=Materiality.MATERIAL,
        subject=subject,
        condition="신청 시",
        procedure="서식을 제출",
        modality=Modality.MUST,
        legal_action="제출",
        operative_verb_lexeme="제출",
        legal_object="서식",
        legal_effect="접수",
        polarity=Polarity.POSITIVE,
        relation_type=None,
        base_proposition_id=None,
        exception_proposition_id=None,
        evidence=EvidenceRef(
            source_id="src-1",
            authority_kind="statute",
            source_title="Act",
            source_locator="§1",
            evidence_span=source_span,
            temporal_status="CURRENT_CONFIRMED",
            temporal_render_text=None,
        ),
    )


class SourceRelationGuardTests(unittest.TestCase):
    def test_rejects_source_that_does_not_preserve_relation(self):
        self.assertEqual(
            source_relation_failure_code(
                proposition("신청인은 신청 시 서식을 제출해야 한다. 서식은 접수된다.")
            ),
            None,
        )
        self.assertEqual(
            source_relation_failure_code(
                proposition("기관은 신청 시 서식을 제출해야 한다. 서식은 접수된다.")
            ),
            "SOURCE_PROPOSITION_MISMATCH",
        )


if __name__ == "__main__":
    unittest.main()
