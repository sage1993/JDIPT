"""Deterministic semantic soundness checks after render-slot coverage."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass, replace
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
from scripts.proposition_rendering import PropositionRenderContract, RenderSlot, build_render_contract


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
    proposition_status: PropositionStatus | None
    materiality: Materiality | None
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
_FENCE_LINE_RE = re.compile(r"[ \t]*(?P<fence>`{3,}|~{3,})(?P<info>[^\r\n]*)")
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


def _fence_intervals(draft: str) -> list[tuple[int, int, AnswerRegionKind]]:
    """Scan raw lines; only the same fence character of sufficient length closes."""
    intervals: list[tuple[int, int, AnswerRegionKind]] = []
    opener: tuple[int, str] | None = None
    for start, end, line in _line_ranges(draft):
        marker = _FENCE_LINE_RE.fullmatch(line.rstrip("\r\n"))
        if marker is None:
            continue
        fence, info = marker.group("fence", "info")
        if opener is None:
            if fence[0] == "`" and "`" in info:
                continue
            opener = (start, fence)
        elif fence[0] == opener[1][0] and len(fence) >= len(opener[1]) and not info.strip():
            intervals.append((opener[0], end, "code_block"))
            opener = None
    if opener is not None:
        intervals.append((opener[0], len(draft), "code_block"))
    return intervals


def _section_intervals(
    draft: str,
    fences: Sequence[tuple[int, int, AnswerRegionKind]] = (),
) -> list[tuple[int, int, AnswerRegionKind]]:
    # The caller supplies an offset-preserving view with fenced content masked.
    intervals: list[tuple[int, int, AnswerRegionKind]] = []
    headings = list(_HEADING_RE.finditer(draft))
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(draft)
        if _CONCLUSION_HEADING_RE.fullmatch(heading.group(0).rstrip("\r\n")):
            _add_interval(intervals, heading.end(), end, "final_conclusion")
    for match in _CONCLUSION_LABEL_RE.finditer(draft):
        # A label cannot swallow a later section's canonical render.
        stops = [heading.start() for heading in headings if heading.start() > match.end()]
        for blank in re.finditer(r"(?=(\r?\n[ \t]*\r?\n))", draft[match.end():]):
            start = match.end() + blank.start()
            content_start = start + (2 if draft.startswith("\r\n", start) else 1)
            # Masked code lines (including originally blank lines) are not
            # paragraph boundaries of the enclosing labelled conclusion.
            if not any(fence_start <= content_start < fence_end
                       for fence_start, fence_end, _ in fences):
                stops.append(start)
                break
        end = min(stops, default=len(draft))
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
    fences = _fence_intervals(draft)
    structural = list(draft)
    for start, end, _ in fences:
        for index in range(start, end):
            if structural[index] not in "\r\n":
                structural[index] = " "
    # Standalone CR becomes a line boundary without changing any offsets.
    visible = re.sub(r"\r(?!\n)", "\n", "".join(structural))
    intervals = _section_intervals(visible, fences)
    intervals.extend(_example_intervals(visible))
    intervals.extend(_rejected_intervals(visible))
    intervals.extend(fences)
    intervals.extend(
        (match.start(), match.end(), "quotation")
        for match in _BLOCKQUOTE_RE.finditer(visible)
    )
    intervals.extend(
        (match.start(), match.end(), "quotation")
        for match in _INLINE_QUOTE_RE.finditer(visible)
    )
    intervals.extend(
        (match.start(), match.end(), "uncertainty")
        for match in _UNCERTAINTY_RE.finditer(visible)
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
    matches: list[AnswerSpan] = []
    for span in spans:
        normalized = "\n".join(normalize_rendered_text(line) for line in span.text.splitlines())
        pattern = r"\s+".join(re.escape(token) for token in expected.split())
        for occurrence in re.finditer(pattern, normalized):
            before = _FALSE_WRAPPER_RE.search(normalized[:occurrence.start()])
            after = _FALSE_WRAPPER_SUFFIX_RE.match(normalized[occurrence.end():])
            if span.adopted and (before or after):
                start = before.start() if before else occurrence.start()
                end = occurrence.end() + after.end() if after else occurrence.end()
                matches.append(AnswerSpan(
                    "rejected_alternative", normalized[start:end],
                    span.start, span.end, False,
                ))
            else:
                matches.append(span)
    return tuple(matches)


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
    proposition: LegalProposition | None,
    code: str,
    *,
    matched_region: str,
    matched_span: str,
    final_conclusion_span: str,
    relation_fields: Sequence[str] = (),
) -> SoundnessViolation:
    return SoundnessViolation(
        code=code,
        proposition_id=getattr(proposition, "proposition_id", ""),
        proposition_status=(proposition.status if isinstance(getattr(proposition, "status", None), PropositionStatus) else None),
        materiality=(proposition.materiality if isinstance(getattr(proposition, "materiality", None), Materiality) else None),
        modality=(proposition.modality if isinstance(getattr(proposition, "modality", None), Modality) else None),
        polarity=(proposition.polarity if isinstance(getattr(proposition, "polarity", None), Polarity) else None),
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
    negative = bool(_NEGATIVE_RE.search(cleaned))
    # In particular, 불가능 must not also match the positive 가능 token.
    positive = bool(_POSITIVE_RE.search(_NEGATIVE_RE.sub("", cleaned)))
    return positive, negative


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
        if value and not _field_pattern(value).search(normalized)
    )


def _field_pattern(value: str) -> re.Pattern[str]:
    # Korean particles may follow a lexeme, but an ASCII identifier must not
    # match inside another identifier, source locator, or ordinary word.
    return re.compile(r"(?<![a-z0-9_가-힣])" + re.escape(normalize_rendered_text(value)) + r"(?![a-z0-9_])")


_WRAPPER_GAP = r"[ \t]*(?:\n[ \t]*)?"
_FALSE_WRAPPER_RE = re.compile(
    r"(?:^|(?<=[.!?:]))[ \t]*(?:다음[ \t]+)?명제는[ \t]+거짓이다[ \t]*[:.!?]+"
    + _WRAPPER_GAP + r"\Z", re.MULTILINE,
)
_FALSE_WRAPPER_SUFFIX_RE = re.compile(
    r"[ \t]*[.!?]*" + _WRAPPER_GAP
    + r"이[ \t]+명제는[ \t]+거짓이다(?:[.!?]+|$)", re.MULTILINE,
)


def _altered_relation_fields(proposition: LegalProposition, text: str) -> tuple[str, ...]:
    """Inspect only grammar immediately adjoining a canonical relation value."""
    predicates = (
        ("condition", proposition.condition, r"\s*(?:을|를|이|가|은|는)?\s*(?:충족(?:하지|되지)\s*(?:않|못|아니하)|없이|없어도)"),
        ("procedure", proposition.procedure, r"\s*(?:을|를|이|가|은|는)?\s*(?:거치지\s*(?:않|못|아니하)|생략하면|없이|없어도)"),
        ("legal_effect", proposition.legal_effect, r"\s*(?:(?:이|가)?\s*(?:아닌|아니라)|(?:으로|로)?\s*변경된|대신\s)"),
    )
    return tuple(
        name for name, value, suffix in predicates
        if value and (
            re.search(_field_pattern(value).pattern + suffix, text)
            or (name == "legal_effect" and re.search(
                r"(?<![a-z0-9_가-힣])변경된\s+" + _field_pattern(value).pattern, text
            ))
        )
    )


def _sentences(text: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in re.split(r"(?<=[.!?])|[\r\n]+", text) if part.strip())


def _normalized_sentences(text: str) -> tuple[str, ...]:
    # Split raw punctuation/newlines before presentation normalization can
    # collapse unrelated assertions into one apparent legal relation.
    return tuple(normalize_rendered_text(sentence) for sentence in _sentences(text))


def _authority_contracts(
    propositions: Sequence[LegalProposition],
    contracts: Sequence[PropositionRenderContract],
    violations: list[SoundnessViolation],
) -> tuple[tuple[LegalProposition, PropositionRenderContract], ...]:
    """Validate supplied snapshots, never resolve another registry or source.

    Rebuilding a contract checks semantic freshness against the supplied typed
    proposition. This does not compute Task 9's required set or draft coverage.
    """
    valid: list[tuple[LegalProposition, PropositionRenderContract]] = []
    for proposition in propositions:
        code = None
        try:
            if not isinstance(proposition, LegalProposition):
                raise TypeError("canonical proposition required")
            replace(proposition)  # Revalidate even a forged frozen dataclass.
            if proposition.evidence is not None:
                replace(proposition.evidence)
            if proposition.materiality is Materiality.NON_MATERIAL:
                continue
            if proposition.status is PropositionStatus.CLOSED and proposition.polarity is None:
                raise ValueError("closed polarity authority missing")
            if sum(getattr(item, "proposition_id", None) == proposition.proposition_id for item in propositions) != 1:
                code = "AMBIGUOUS_ADOPTED_IDENTITY"
            elif contracts is None:
                code = "UNAVAILABLE_SEMANTIC_AUTHORITY"
            else:
                matches = [item for item in contracts if isinstance(item, PropositionRenderContract)
                           and item.proposition_id == proposition.proposition_id]
                if not matches:
                    code = "MALFORMED_SEMANTIC_IDENTITY" if contracts else "UNAVAILABLE_SEMANTIC_AUTHORITY"
                elif len(matches) != 1:
                    code = "AMBIGUOUS_ADOPTED_IDENTITY"
                else:
                    contract = matches[0]
                    expected = build_render_contract(proposition)
                    if not isinstance(contract.slots, tuple) or not contract.slots:
                        code = "MALFORMED_SEMANTIC_IDENTITY"
                    elif any(not isinstance(slot, RenderSlot) for slot in contract.slots):
                        code = "MALFORMED_SEMANTIC_IDENTITY"
                    elif tuple((slot.slot_id, slot.proposition_id, slot.kind) for slot in contract.slots) != tuple(
                        (slot.slot_id, slot.proposition_id, slot.kind) for slot in expected.slots
                    ):
                        code = "MALFORMED_SEMANTIC_IDENTITY"
                    elif contract.semantic_identity is None:
                        code = "UNAVAILABLE_SEMANTIC_AUTHORITY"
                    elif not isinstance(contract.semantic_identity, LegalProposition):
                        code = "MALFORMED_SEMANTIC_IDENTITY"
                    elif replace(contract.semantic_identity) != proposition or contract != expected:
                        code = "STALE_SEMANTIC_AUTHORITY"
                    else:
                        valid.append((proposition, contract))
        except (AttributeError, TypeError, ValueError, KeyError):
            code = "MALFORMED_SEMANTIC_IDENTITY"
        if code:
            _append_once(violations, _make_violation(
                proposition, code, matched_region="authority", matched_span="",
                final_conclusion_span="",
            ))

    # An exact effect/open string cannot identify two different propositions.
    identities: dict[str, list[LegalProposition]] = {}
    for proposition, contract in valid:
        for slot in contract.slots:
            if slot.kind != "temporal":
                identities.setdefault(normalize_rendered_text(slot.text), []).append(proposition)
    for owners in identities.values():
        if len(owners) > 1:
            for proposition in owners:
                _append_once(violations, _make_violation(
                    proposition, "AMBIGUOUS_ADOPTED_IDENTITY", matched_region="authority",
                    matched_span="", final_conclusion_span="",
                ))
    return tuple(valid)


def _semantic_runs(spans: Sequence[AnswerSpan]) -> tuple[AnswerSpan, ...]:
    """Rejoin uncertainty fragments without crossing an adoption boundary.

    The public classifier retains its existing uncertainty/adopted contract for
    source and obligation consumers. Internally an OPEN sentence must stay whole.
    """
    runs: list[AnswerSpan] = []
    for span in spans:
        if not span.adopted and span.kind != "uncertainty":
            continue
        if runs and runs[-1].end == span.start and (
            runs[-1].kind == span.kind or span.kind == "uncertainty" or runs[-1].kind == "uncertainty"
        ):
            previous = runs.pop()
            kind = span.kind if previous.kind == "uncertainty" else previous.kind
            runs.append(AnswerSpan(kind, previous.text + span.text, previous.start, span.end, True))
        else:
            runs.append(span)
    return tuple(runs)


def _claim_owners(
    text: str,
    authorities: Sequence[tuple[LegalProposition, PropositionRenderContract]],
) -> tuple[LegalProposition, ...]:
    """Use exact relation fields; incomparable identities remain ambiguous."""
    matches = [(proposition, frozenset(
        name for name, value in _relation_fields(proposition)
        if value and _field_pattern(value).search(text)
    )) for proposition, _ in authorities]
    return tuple(proposition for proposition, fields in matches if fields and not any(
        fields < other_fields for _, other_fields in matches
    ))


def _open_uncertainty_assertion(proposition: LegalProposition, text: str) -> bool:
    """Accept an explicit relation-list/uncertainty construction, not co-occurrence."""
    values = {normalize_rendered_text(value) for _, value in _relation_fields(proposition)
              if value and _field_pattern(value).search(text)}
    if len(values) < 2:
        return False
    anchor = "(?:" + "|".join(re.escape(value) for value in sorted(values, key=len, reverse=True)) + ")"
    relation_list = anchor + r"(?:\s*(?:와|과|및|,|·)\s*" + anchor + r")+"
    # Only these explicit constructions bind uncertainty to the listed fields.
    # Other prose needs the exact OPEN slot; another subject cannot lend its
    # uncertainty merely by sharing a sentence with the relation anchors.
    return bool(re.fullmatch(
        r"(?:확인\s*필요\s*:\s*)?" + relation_list
        + r"(?:에\s*관한\s*(?:근거와\s*)?적용\s*여부|(?:의\s*)?(?:충족|이행|적용)\s*여부)?"
        + r"\s*(?:은|는|이|가)?\s*(?:현재\s*)?"
        + r"(?:확인\s*필요(?:하다)?|(?:확정|판단)할\s*수\s*없(?:다|음)|불확실하다|미확인이다)[.!?]*",
        text,
    ))


def _is_bounded_legal_claim(proposition: LegalProposition, text: str) -> bool:
    fields = {name for name, value in _relation_fields(proposition)
              if value and _field_pattern(value).search(text)}
    if len(fields) < 2:
        return False
    # An object/field list cannot borrow another clause's predicate. Bind an
    # action conjugation or effect-role particle to the canonical field itself.
    # The effect role also retains claims whose original action was removed.
    suffixes = {
        "legal_action": r"\s*(?:할|하여|하지|해야|해서는|된다|될|되지)",
        "legal_effect": r"\s*(?:으로|로)(?=\s|$)",
    }
    return any(value and name in suffixes and re.search(
        _field_pattern(value).pattern + suffixes[name], text,
    ) for name, value in _relation_fields(proposition))


_LEGAL_ANAPHORA_RE = re.compile(
    r"^(?:결론\s*:\s*)?(?:따라서\s*)?"
    r"(?:(?:이|본|해당)\s*(?:행위|사안)(?:는|은|에는|에)\s*"
    r"(?:허용된다|허용되지\s*않는다|금지된다|적용된다|적용되지\s*않는다)|"
    r"(?:일부\s*)?완화(?:가|는)\s*(?:가능하다|불가능하다))[.!?]*$"
)


_MODALITY_MARKERS = (
    (Modality.MAY_NOT, re.compile(r"(?:하지\s*않아도\s*된다|하지\s*않을\s*수\s*있다)")),
    (Modality.MUST_NOT, re.compile(r"(?:하여서는\s*안|해서는\s*안|하지\s*않아야)")),
    (Modality.MUST, re.compile(r"(?:하여야|해야)\s*(?:한다|하고|함)")),
    (Modality.MAY, re.compile(r"(?:할\s*수\s*있|허용된다|가능하다)")),
)


def _claim_semantics(
    proposition: LegalProposition,
    contract: PropositionRenderContract,
    claim: AnswerSpan,
    violations: list[SoundnessViolation],
) -> None:
    text = claim.text
    missing = list(_relation_missing_in_conclusion(proposition, text))
    missing.extend(name for name in _altered_relation_fields(proposition, text) if name not in missing)

    def reject(code: str, fields: Sequence[str] = ()) -> None:
        _append_once(violations, _make_violation(
            proposition, code, matched_region=claim.kind, matched_span=text,
            final_conclusion_span=text if claim.kind == "final_conclusion" else "",
            relation_fields=fields,
        ))

    # Field words are authority, not predicate markers (e.g. a condition may
    # contain '금지'). Inspect only the surrounding relation grammar.
    predicate = text
    values = [value for _, value in _relation_fields(proposition) if value]
    for value in sorted(values, key=len, reverse=True):
        predicate = _field_pattern(value).sub(" ", predicate)
    observed: set[Modality] = set()
    remainder = predicate
    for modality, marker in _MODALITY_MARKERS:
        if marker.search(remainder):
            observed.add(modality)
            remainder = marker.sub("", remainder)
    if proposition.status is PropositionStatus.OPEN:
        # MAY_NOT is a definitive modality too; uncertainty cannot cancel it.
        if observed or _has_definitive_conclusion(predicate):
            reject("OPEN_PROMOTED_TO_CLOSED")
        return
    if proposition.modality is Modality.MUST and observed != {Modality.MUST}:
        reject("MUST_DEGRADED_TO_MAY", missing)
        return
    if proposition.modality is Modality.MUST_NOT and observed != {Modality.MUST_NOT}:
        reject("MUST_NOT_DEGRADED", missing)
        return

    positive, negative = _output_polarity(predicate)
    opposite = (proposition.polarity is Polarity.POSITIVE and negative) or (
        proposition.polarity is Polarity.NEGATIVE and positive
    )
    if opposite:
        reject("POLARITY_CONTRADICTION")
        if claim.kind == "final_conclusion":
            reject("FINAL_CONCLUSION_CONTRADICTION")
    elif observed and observed != {proposition.modality}:
        reject("MODALITY_CONTRADICTION", ("modality",))
    elif not observed and not missing:
        reject("UNAVAILABLE_SEMANTIC_AUTHORITY", ("modality",))

    if _CONDITION_BYPASS_RE.search(predicate):
        missing.extend(name for name in ("condition", "procedure") if name not in missing)
        if claim.kind == "final_conclusion":
            reject("FINAL_CONCLUSION_CONTRADICTION")
    effect = next(slot.text for slot in contract.slots if slot.kind == "effect")
    # The renderer owns how an exception relation is expressed.
    if effect.startswith("다만, 예외로 ") and not re.search(
        r"(?:다만,\s*예외로|예외\s*:|예외\s*기준은)", text
    ):
        missing.append("relation_type")
    if missing:
        reject("LEGAL_RELATION_DEGRADATION", missing)


def _evaluate_claims(
    authorities: Sequence[tuple[LegalProposition, PropositionRenderContract]],
    spans: Sequence[AnswerSpan],
    violations: list[SoundnessViolation],
) -> None:
    """Inspect every residual adopted sentence, never a document-wide union.

    Exact canonical slots are consumed as typed assertions. Remaining clauses
    cannot borrow their fields or predicate from those assertions or duplicates.
    """
    slots = sorted({normalize_rendered_text(slot.text) for _, contract in authorities
                    for slot in contract.slots}, key=len, reverse=True)
    contracts = {proposition.proposition_id: contract for proposition, contract in authorities}
    for run in _semantic_runs(spans):
        text = "\n".join(normalize_rendered_text(line) for line in run.text.splitlines())
        # Classify each exact occurrence's enclosing assertion BEFORE consuming
        # its text. A correct earlier occurrence cannot adopt a false wrapper.
        for proposition, contract in authorities:
            for slot in contract.slots:
                for match in _slot_matches(slot.text, (run,)):
                    if match.kind == "rejected_alternative":
                        _append_once(violations, _make_violation(
                            proposition,
                            "FINAL_CONCLUSION_CONTRADICTION" if run.kind == "final_conclusion"
                            else "POLARITY_CONTRADICTION",
                            matched_region=run.kind, matched_span=match.text,
                            final_conclusion_span=match.text if run.kind == "final_conclusion" else "",
                        ))
        for slot in slots:
            # Exact normalized slots may themselves wrap across source lines.
            pattern = r"\s+".join(re.escape(token) for token in slot.split())
            text = re.sub(pattern, "\n", text)
        for sentence in _sentences(text):
            sentence = sentence.strip()
            if not sentence:
                continue
            owners = _claim_owners(sentence, authorities)
            definitive = _has_definitive_conclusion(sentence) or any(
                marker.search(sentence) for _, marker in _MODALITY_MARKERS
            )
            if not definitive:
                continue  # A field mention alone does not assert a legal effect.
            owners = tuple(proposition for proposition in owners
                           if _is_bounded_legal_claim(proposition, sentence))
            if (not owners and run.kind == "final_conclusion" and len(authorities) == 1
                    and _LEGAL_ANAPHORA_RE.fullmatch(sentence)):
                # Explicit legal anaphora has one possible antecedent here.
                # Ordinary ownerless predicates (e.g. document operations) do not.
                owners = (authorities[0][0],)
            if not owners:
                continue  # unrelated explanatory prose has no legal identity
            if len(owners) > 1:
                for proposition in owners:
                    _append_once(violations, _make_violation(
                        proposition, "AMBIGUOUS_ADOPTED_IDENTITY", matched_region=run.kind,
                        matched_span=sentence,
                        final_conclusion_span=sentence if run.kind == "final_conclusion" else "",
                    ))
                continue
            proposition = owners[0]
            _claim_semantics(proposition, contracts[proposition.proposition_id],
                             AnswerSpan(run.kind, sentence, run.start, run.end, True), violations)


def evaluate_soundness(
    propositions: Sequence[LegalProposition],
    contracts: Sequence[PropositionRenderContract],
    draft: str,
) -> SoundnessResult:
    """Evaluate adoption and typed semantic consistency after coverage."""

    spans = classify_answer_regions(draft)
    conclusion = _final_conclusion_text(spans)
    violations: list[SoundnessViolation] = []
    if propositions is None:
        return SoundnessResult(False, (_make_violation(
            None, "UNAVAILABLE_SEMANTIC_AUTHORITY", matched_region="authority",
            matched_span="", final_conclusion_span="",
        ),))
    authorities = _authority_contracts(propositions, contracts, violations)

    for proposition, contract in authorities:
        # Supplemental linked-rule metadata may be rendered in its own
        # relation sentence, rather than repeated in every effect sentence.
        rules = [(name, getattr(proposition, name)) for name in ("base_rule", "exception_rule")
                 if getattr(proposition, name)]
        if rules and not any(
            all(_field_pattern(value).search(sentence) for _, value in rules)
            for run in _semantic_runs(spans)
            for sentence in _normalized_sentences(run.text)
        ):
            _append_once(violations, _make_violation(
                proposition, "LEGAL_RELATION_DEGRADATION", matched_region="unresolved",
                matched_span="", final_conclusion_span=conclusion,
                relation_fields=[name for name, _ in rules],
            ))
        matches_by_slot = {
            slot.slot_id: _slot_matches(slot.text, spans)
            for slot in contract.slots
        }
        all_matches = tuple(
            match
            for matches in matches_by_slot.values()
            for match in matches
        )
        unadopted_required_matches = tuple(
            match
            for matches in matches_by_slot.values()
            if not any(match.adopted for match in matches)
            for match in matches
        )
        required_slots_adopted = all(
            any(match.adopted for match in matches_by_slot[slot.slot_id])
            for slot in contract.slots
        )

        if proposition.status is PropositionStatus.OPEN:
            # Neutral paraphrases are allowed; excluded regions cannot adopt.
            open_runs = _semantic_runs(spans)
            exact_adoption = any(
                match.adopted
                for slot in contract.slots
                for match in _slot_matches(slot.text, open_runs)
            )
            neutral_adoption = exact_adoption or any(
                _open_uncertainty_assertion(proposition, sentence)
                and proposition in _claim_owners(sentence, authorities)
                for run in open_runs
                for sentence in _normalized_sentences(run.text)
            )
            if not neutral_adoption:
                _append_once(violations, _make_violation(
                    proposition, "UNAVAILABLE_SEMANTIC_AUTHORITY",
                    matched_region="unresolved", matched_span="",
                    final_conclusion_span=conclusion,
                ))

        if proposition.status is PropositionStatus.CLOSED and not required_slots_adopted:
            evidence_matches = unadopted_required_matches or all_matches
            if any(match.kind == "code_block" for match in evidence_matches):
                code = "CODE_BLOCK_OR_EXAMPLE_ONLY"
                region = "code_block"
            elif any(match.kind == "example" for match in evidence_matches):
                code = "CODE_BLOCK_OR_EXAMPLE_ONLY"
                region = "example"
            elif evidence_matches:
                code = "REJECTED_QUOTATION_ONLY"
                region = next(
                    (
                        match.kind
                        for match in evidence_matches
                        if match.kind in {"quotation", "rejected_alternative"}
                    ),
                    evidence_matches[0].kind,
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
                    matched_span=" ".join(
                        match.text.strip() for match in evidence_matches
                    ),
                    final_conclusion_span=conclusion,
                ),
            )

    _evaluate_claims(authorities, spans, violations)
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
