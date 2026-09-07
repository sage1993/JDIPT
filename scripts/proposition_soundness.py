"""Deterministic semantic soundness checks after render-slot coverage."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
import re
from typing import Any, Literal

from scripts.legal_proposition import (
    LegalProposition,
    Materiality,
    Modality,
    Polarity,
    PropositionStatus,
)
from scripts.proposition_reconciliation import normalize_rendered_text
from scripts.proposition_rendering import PropositionRenderContract


AnswerRegionKind = Literal[
    "affirmative",
    "quotation",
    "code_block",
    "example",
    "rejected_alternative",
    "uncertainty",
    "final_conclusion",
]


@dataclass(frozen=True)
class AnswerSpan:
    kind: AnswerRegionKind
    text: str
    start: int
    end: int
    adopted: bool


@dataclass(frozen=True)
class SoundnessViolation:
    code: str
    proposition_id: str
    proposition_status: PropositionStatus
    materiality: Materiality
    modality: Modality | None
    polarity: Polarity | None
    relation_fields: tuple[str, ...]
    matched_region: str
    matched_span: str
    final_conclusion_span: str


@dataclass(frozen=True)
class SoundnessResult:
    soundness_passed: bool
    violations: tuple[SoundnessViolation, ...]


_REGION_PRIORITY: dict[AnswerRegionKind, int] = {
    "affirmative": 0,
    "final_conclusion": 10,
    "uncertainty": 20,
    "example": 30,
    "rejected_alternative": 50,
    "quotation": 55,
    "code_block": 60,
}
_HEADING_RE = re.compile(r"(?m)^[ \t]*#\s+\d+\.\s+[^\n]*")
_CONCLUSION_HEADING_RE = re.compile(
    r"(?mi)^[ \t]*#\s*2\.\s*검토결론\s*$"
)
_CONCLUSION_LABEL_RE = re.compile(r"(?mi)^[ \t]*(?:최종\s*)?결론\s*:")
_CODE_BLOCK_RE = re.compile(
    r"(?ms)^[ \t]*```[^\n]*\n.*?^[ \t]*```[ \t]*(?:\n|$)"
)
_BLOCKQUOTE_RE = re.compile(r"(?m)^[ \t]*>[^\n]*(?:\n|$)")
_INLINE_QUOTE_RE = re.compile(r"(?s)(?P<quote>[\"'])(?P<body>.+?)(?P=quote)")
_EXAMPLE_MARKER_RE = re.compile(r"(?i)^(?:예시|example)\s*:")
_REJECTED_MARKER_RE = re.compile(
    r"(?i)(?:반대\s*견해|을설|rejected\s+alternative|배척|타당하지\s*않|"
    r"채택하지\s*않|옳지\s*않)"
)
_REJECTED_HEADING_RE = re.compile(
    r"(?i)^\s*(?:반대\s*견해|을설|rejected\s+alternative|배척)\s*:"
)
_EXPLICIT_REJECTION_RE = re.compile(
    r"(?i)(?:타당하지\s*않|채택하지\s*않|옳지\s*않)"
)
_UNCERTAINTY_RE = re.compile(
    r"(?:확인\s*필요|확정할\s*수\s*없|판단할\s*수\s*없|불확실|미확인)",
    re.IGNORECASE,
)
_POSITIVE_RE = re.compile(
    r"(?:가능(?:하다|한|함)?|허용(?:된다|될\s*수\s*있다|할\s*수\s*있다)|"
    r"할\s*수\s*있다|적용된다|인정된다|허가된다)",
    re.IGNORECASE,
)
_NEGATIVE_RE = re.compile(
    r"(?:불가능|불가|허용되지|할\s*수\s*없다|하여서는\s*안|하지\s*않아야|"
    r"금지(?:된다)?|배제된다|불허)",
    re.IGNORECASE,
)
_DEFINITIVE_RE = re.compile(
    r"(?:가능(?:하다|한|함)?|허용(?:된다|될\s*수\s*있다|할\s*수\s*있다)|"
    r"할\s*수\s*있다|적용된다|인정된다|허가된다|불가능|불가|허용되지|"
    r"할\s*수\s*없다|하여서는\s*안|하지\s*않아야|금지(?:된다)?|배제된다|불허|"
    r"하여야\s*한다|해야\s*한다)",
    re.IGNORECASE,
)
_CONDITION_BYPASS_RE = re.compile(
    r"(?:관계없이|무관하게|상관없이|조건과\s*관계없이|조건에\s*상관없이)",
    re.IGNORECASE,
)


def _line_ranges(draft: str) -> tuple[tuple[int, int, str], ...]:
    ranges: list[tuple[int, int, str]] = []
    cursor = 0
    for line in draft.splitlines(keepends=True):
        end = cursor + len(line)
        ranges.append((cursor, end, line))
        cursor = end
    if cursor < len(draft) or not ranges:
        ranges.append((cursor, len(draft), draft[cursor:]))
    return tuple(ranges)


def _add_interval(
    intervals: list[tuple[int, int, AnswerRegionKind]],
    start: int,
    end: int,
    kind: AnswerRegionKind,
) -> None:
    if start < end:
        intervals.append((start, end, kind))


def _section_intervals(draft: str) -> list[tuple[int, int, AnswerRegionKind]]:
    intervals: list[tuple[int, int, AnswerRegionKind]] = []
    headings = list(_HEADING_RE.finditer(draft))
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(draft)
        if _CONCLUSION_HEADING_RE.fullmatch(heading.group(0).rstrip("\r\n")):
            _add_interval(intervals, heading.end(), end, "final_conclusion")
    for match in _CONCLUSION_LABEL_RE.finditer(draft):
        end = draft.find("\n\n", match.end())
        if end < 0:
            end = len(draft)
        else:
            end += 2
        _add_interval(intervals, match.end(), end, "final_conclusion")
    return intervals


def _example_intervals(draft: str) -> list[tuple[int, int, AnswerRegionKind]]:
    intervals: list[tuple[int, int, AnswerRegionKind]] = []
    lines = _line_ranges(draft)
    index = 0
    while index < len(lines):
        start, _, line = lines[index]
        if not _EXAMPLE_MARKER_RE.match(line.strip()):
            index += 1
            continue
        end_index = index + 1
        body_seen = False
        blank_after_body = False
        while end_index < len(lines):
            _, _, next_line = lines[end_index]
            stripped = next_line.strip()
            if _HEADING_RE.match(next_line) or _CONCLUSION_LABEL_RE.match(next_line):
                break
            if stripped:
                body_seen = True
                blank_after_body = False
                end_index += 1
                continue
            if body_seen:
                blank_after_body = True
                end_index += 1
                if end_index < len(lines) and lines[end_index][2].strip():
                    break
                continue
            end_index += 1
        end = lines[min(end_index, len(lines) - 1)][0] if end_index < len(lines) else len(draft)
        if blank_after_body and end_index < len(lines):
            end = lines[end_index][0]
        elif end_index > index:
            end = lines[end_index - 1][1]
        _add_interval(intervals, start, end, "example")
        index = max(index + 1, end_index)
    return intervals


def _rejected_intervals(draft: str) -> list[tuple[int, int, AnswerRegionKind]]:
    intervals: list[tuple[int, int, AnswerRegionKind]] = []
    lines = _line_ranges(draft)
    for index, (start, _, line) in enumerate(lines):
        if not _REJECTED_MARKER_RE.search(line):
            continue
        if not (
            _REJECTED_HEADING_RE.match(line)
            or _EXPLICIT_REJECTION_RE.search(line)
        ):
            continue
        block_start = start
        block_end = lines[index][1]
        previous = index - 1
        while previous >= 0 and lines[previous][2].strip():
            block_start = lines[previous][0]
            previous -= 1
        following = index + 1
        while following < len(lines) and lines[following][2].strip():
            block_end = lines[following][1]
            following += 1
        _add_interval(intervals, block_start, block_end, "rejected_alternative")
    return intervals


def _raw_intervals(draft: str) -> list[tuple[int, int, AnswerRegionKind]]:
    intervals = _section_intervals(draft)
    intervals.extend(_example_intervals(draft))
    intervals.extend(_rejected_intervals(draft))
    intervals.extend(
        (match.start(), match.end(), "code_block")
        for match in _CODE_BLOCK_RE.finditer(draft)
    )
    intervals.extend(
        (match.start(), match.end(), "quotation")
        for match in _BLOCKQUOTE_RE.finditer(draft)
    )
    intervals.extend(
        (match.start(), match.end(), "quotation")
        for match in _INLINE_QUOTE_RE.finditer(draft)
    )
    intervals.extend(
        (match.start(), match.end(), "uncertainty")
        for match in _UNCERTAINTY_RE.finditer(draft)
    )
    return intervals


def classify_answer_regions(draft: str) -> tuple[AnswerSpan, ...]:
    """Classify bounded Markdown/paragraph spans before presentation normalization."""

    if not isinstance(draft, str):
        raise TypeError("draft must be a string")
    if not draft:
        return ()

    boundaries = {0, len(draft)}
    intervals = _raw_intervals(draft)
    for start, end, _ in intervals:
        boundaries.add(start)
        boundaries.add(end)
    ordered = sorted(boundaries)
    spans: list[AnswerSpan] = []
    for start, end in zip(ordered, ordered[1:]):
        if start == end:
            continue
        matching = [
            kind
            for interval_start, interval_end, kind in intervals
            if interval_start <= start and end <= interval_end
        ]
        kind = max(matching, key=lambda item: _REGION_PRIORITY[item]) if matching else "affirmative"
        spans.append(
            AnswerSpan(
                kind=kind,
                text=draft[start:end],
                start=start,
                end=end,
                adopted=kind in {"affirmative", "final_conclusion"},
            )
        )
    return tuple(spans)


def _final_conclusion_text(spans: Sequence[AnswerSpan]) -> str:
    return " ".join(
        span.text.strip()
        for span in spans
        if span.kind == "final_conclusion" and span.text.strip()
    ).strip()


def _slot_matches(
    slot_text: str,
    spans: Sequence[AnswerSpan],
) -> tuple[AnswerSpan, ...]:
    expected = normalize_rendered_text(slot_text)
    if not expected:
        return ()
    return tuple(
        span
        for span in spans
        if expected in normalize_rendered_text(span.text)
    )


def _relation_fields(proposition: LegalProposition) -> tuple[tuple[str, str | None], ...]:
    return (
        ("condition", proposition.condition),
        ("procedure", proposition.procedure),
        (
            "legal_action",
            proposition.operative_verb_lexeme or proposition.legal_action,
        ),
        ("legal_object", proposition.legal_object),
        ("legal_effect", proposition.legal_effect),
    )


def _make_violation(
    proposition: LegalProposition,
    code: str,
    *,
    matched_region: str,
    matched_span: str,
    final_conclusion_span: str,
    relation_fields: Sequence[str] = (),
) -> SoundnessViolation:
    return SoundnessViolation(
        code=code,
        proposition_id=proposition.proposition_id,
        proposition_status=proposition.status,
        materiality=proposition.materiality,
        modality=proposition.modality,
        polarity=proposition.polarity,
        relation_fields=tuple(relation_fields),
        matched_region=matched_region,
        matched_span=matched_span,
        final_conclusion_span=final_conclusion_span,
    )


def _append_once(
    violations: list[SoundnessViolation],
    violation: SoundnessViolation,
) -> None:
    if not any(
        existing.code == violation.code
        and existing.proposition_id == violation.proposition_id
        for existing in violations
    ):
        violations.append(violation)


def _output_polarity(text: str) -> tuple[bool, bool]:
    cleaned = re.sub(
        r"(?:확정|확인|판단)할\s*수\s*없(?:다|음)?",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return bool(_POSITIVE_RE.search(cleaned)), bool(_NEGATIVE_RE.search(cleaned))


def _has_definitive_conclusion(text: str) -> bool:
    cleaned = re.sub(
        r"(?:확정|확인|판단)할\s*수\s*없(?:다|음)?",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return bool(_DEFINITIVE_RE.search(cleaned))


def _relation_missing_in_conclusion(
    proposition: LegalProposition,
    conclusion: str,
) -> tuple[str, ...]:
    normalized = normalize_rendered_text(conclusion)
    return tuple(
        name
        for name, value in _relation_fields(proposition)
        if value and normalize_rendered_text(value) not in normalized
    )


def evaluate_soundness(
    propositions: Sequence[LegalProposition],
    contracts: Sequence[PropositionRenderContract],
    draft: str,
) -> SoundnessResult:
    """Evaluate adoption and typed semantic consistency after coverage."""

    spans = classify_answer_regions(draft)
    conclusion = _final_conclusion_text(spans)
    contracts_by_id = {contract.proposition_id: contract for contract in contracts}
    violations: list[SoundnessViolation] = []

    for proposition in propositions:
        if proposition.materiality is not Materiality.MATERIAL:
            continue
        contract = contracts_by_id.get(proposition.proposition_id)
        if contract is None or not contract.slots:
            continue
        matches_by_slot = {
            slot.slot_id: _slot_matches(slot.text, spans)
            for slot in contract.slots
        }
        all_matches = tuple(
            match
            for matches in matches_by_slot.values()
            for match in matches
        )
        adopted_matches = tuple(match for match in all_matches if match.adopted)

        if proposition.status is PropositionStatus.CLOSED and not adopted_matches:
            if any(match.kind == "code_block" for match in all_matches) and not any(
                match.adopted for match in all_matches
            ):
                code = "CODE_BLOCK_OR_EXAMPLE_ONLY"
                region = "code_block"
            elif any(match.kind == "example" for match in all_matches) and not any(
                match.adopted for match in all_matches
            ):
                code = "CODE_BLOCK_OR_EXAMPLE_ONLY"
                region = "example"
            elif all_matches:
                code = "REJECTED_QUOTATION_ONLY"
                region = next(
                    (
                        match.kind
                        for match in all_matches
                        if match.kind in {"quotation", "rejected_alternative"}
                    ),
                    all_matches[0].kind,
                )
            else:
                code = "REJECTED_QUOTATION_ONLY"
                region = "unresolved"
            _append_once(
                violations,
                _make_violation(
                    proposition,
                    code,
                    matched_region=region,
                    matched_span=" ".join(match.text.strip() for match in all_matches),
                    final_conclusion_span=conclusion,
                ),
            )

        if proposition.status is PropositionStatus.OPEN and conclusion:
            if _has_definitive_conclusion(conclusion):
                _append_once(
                    violations,
                    _make_violation(
                        proposition,
                        "OPEN_PROMOTED_TO_CLOSED",
                        matched_region="final_conclusion",
                        matched_span=" ".join(match.text.strip() for match in all_matches),
                        final_conclusion_span=conclusion,
                    ),
                )
            continue

        if proposition.status is not PropositionStatus.CLOSED or not conclusion:
            continue

        positive_output, negative_output = _output_polarity(conclusion)
        bypass = bool(_CONDITION_BYPASS_RE.search(conclusion))
        opposite = (
            proposition.polarity is Polarity.POSITIVE and negative_output
        ) or (proposition.polarity is Polarity.NEGATIVE and positive_output)
        if opposite:
            code = "FINAL_CONCLUSION_CONTRADICTION" if bypass else "POLARITY_CONTRADICTION"
            _append_once(
                violations,
                _make_violation(
                    proposition,
                    code,
                    matched_region="final_conclusion",
                    matched_span=" ".join(match.text.strip() for match in adopted_matches),
                    final_conclusion_span=conclusion,
                ),
            )

        missing_fields = _relation_missing_in_conclusion(proposition, conclusion)
        if missing_fields:
            _append_once(
                violations,
                _make_violation(
                    proposition,
                    "LEGAL_RELATION_DEGRADATION",
                    matched_region="final_conclusion",
                    matched_span=" ".join(match.text.strip() for match in adopted_matches),
                    final_conclusion_span=conclusion,
                    relation_fields=missing_fields,
                ),
            )

    return SoundnessResult(
        soundness_passed=not violations,
        violations=tuple(violations),
    )


def soundness_result_to_dict(result: SoundnessResult) -> dict[str, Any]:
    """Serialize a soundness result without exposing enum objects."""

    def encode(value: Any) -> Any:
        if hasattr(value, "value"):
            return value.value
        if isinstance(value, tuple):
            return [encode(item) for item in value]
        if isinstance(value, dict):
            return {key: encode(item) for key, item in value.items()}
        return value

    return encode(asdict(result))
