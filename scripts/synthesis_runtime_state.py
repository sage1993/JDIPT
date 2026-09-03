"""Plugin-data state for runtime material-proposition synthesis enforcement.

The state store is deliberately independent of the repository.  It carries
only the compact proposition metadata needed by the Stop hook to reconcile a
final answer; legal source documents are never copied into the repository or
into a session transcript by this module.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Literal


STATE_DIRECTORY = "synthesis-runtime"
MAX_TEXT_LENGTH = 2048
_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
_UNSET = object()


class RuntimeStateError(ValueError):
    """Raised when runtime state cannot be safely loaded or written."""


@dataclass(frozen=True)
class MaterialProposition:
    """Compact proposition metadata registered for one Codex turn."""

    proposition_id: str
    status: Literal["OPEN", "CLOSED"]
    subject: str | None = None
    condition: str | None = None
    procedure: str | None = None
    operative_verb_lexeme: str | None = None
    legal_object: str | None = None
    legal_effect: str | None = None
    source_clause: str | None = None
    mandatory_render_clause: str | None = None
    relation_type: str | None = None
    base_proposition_id: str | None = None
    exception_proposition_id: str | None = None
    current_status: str | None = None
    modality: str | None = "may"
    legal_action: str | None = None
    polarity: str | None = "positive"
    materiality: str = "material"

    def __post_init__(self) -> None:
        _validate_identifier(self.proposition_id, "proposition_id")
        if self.status not in {"OPEN", "CLOSED"}:
            raise RuntimeStateError("status must be OPEN or CLOSED")
        if self.status == "CLOSED":
            required = {
                "subject / legal actor": self.subject,
                "condition": self.condition,
                "procedure": self.procedure,
                "legal action": self.operative_verb_lexeme or self.legal_action,
                "legal object": self.legal_object,
                "legal effect": self.legal_effect,
            }
            missing = [field for field, value in required.items() if not value]
            if missing:
                raise RuntimeStateError(
                    "CLOSED proposition is missing required legal relation fields: "
                    + ", ".join(missing)
                )
        for name in (
            "subject",
            "condition",
            "procedure",
            "operative_verb_lexeme",
            "legal_object",
            "legal_effect",
            "source_clause",
            "mandatory_render_clause",
            "relation_type",
            "base_proposition_id",
            "exception_proposition_id",
            "current_status",
            "modality",
            "legal_action",
            "polarity",
            "materiality",
        ):
            value = getattr(self, name)
            if value is not None:
                _validate_text(value, name)

    def to_integrity_proposition(self):
        """Adapt to the existing deterministic synthesis-integrity schema."""

        from scripts.synthesis_integrity import MaterialProposition as IntegrityProposition

        action = self.legal_action or _action_name(self.operative_verb_lexeme)
        relation = self.relation_type or ""
        if relation.lower() == "exception" and self.base_proposition_id:
            relation = f"exception to {self.base_proposition_id}"
        if relation.lower() == "base" and self.exception_proposition_id:
            relation = f"base for {self.exception_proposition_id}"
        return IntegrityProposition(
            proposition_id=self.proposition_id,
            materiality=self.materiality or "material",
            legal_actor=self.subject or "",
            condition=self.condition or "",
            procedure=self.procedure or "",
            modality=self.modality or "may",
            legal_action=action or "",
            legal_object=self.legal_object or "",
            resulting_status_or_effect=self.legal_effect or "",
            polarity=self.polarity or "positive",
            relation_to_base_or_exception=relation,
            source_proposition=self.source_clause or "",
            evidence_span=self.source_clause or "",
            closure_status=self.status,
            operative_verb_lexeme=self.operative_verb_lexeme or "",
            mandatory_render_clause=self.mandatory_render_clause or "",
            temporal_status=self.current_status or "",
        )


@dataclass
class RuntimeTurnState:
    """Canonical proposition ledger for one session and one turn."""

    session_id: str
    turn_id: str
    jdipt_active: bool
    repair_count: int
    propositions: list[MaterialProposition]

    def __post_init__(self) -> None:
        _validate_identifier(self.session_id, "session_id")
        _validate_identifier(self.turn_id, "turn_id")
        if not isinstance(self.jdipt_active, bool):
            raise RuntimeStateError("jdipt_active must be a boolean")
        if self.repair_count not in {0, 1}:
            raise RuntimeStateError("repair_count must be 0 or 1")
        if not isinstance(self.propositions, list):
            raise RuntimeStateError("propositions must be a list")
        if len({item.proposition_id for item in self.propositions}) != len(self.propositions):
            raise RuntimeStateError("duplicate proposition_id in runtime state")


def _validate_identifier(value: str, field: str) -> str:
    if not isinstance(value, str) or not value or not _ID_PATTERN.fullmatch(value):
        raise ValueError(f"{field} must be a safe non-empty identifier")
    return value


def _validate_text(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise RuntimeStateError(f"{field} must be a string")
    if len(value) > MAX_TEXT_LENGTH:
        raise RuntimeStateError(f"{field} exceeds the runtime metadata limit")
    if any(ord(char) < 32 and char not in "\t\r\n" for char in value):
        raise RuntimeStateError(f"{field} contains a control character")
    return value


def _plugin_data_root(plugin_data: str | os.PathLike[str] | None) -> Path:
    value = plugin_data if plugin_data is not None else os.environ.get("PLUGIN_DATA")
    if not value:
        raise RuntimeStateError("PLUGIN_DATA is required for runtime state")
    root = Path(value)
    if root.name in {"", ".", ".."}:
        raise RuntimeStateError("PLUGIN_DATA must be a concrete directory")
    return root


def runtime_state_path(
    plugin_data: str | os.PathLike[str] | None,
    session_id: str,
    turn_id: str,
) -> Path:
    """Return the exact plugin-data path for a session/turn pair."""

    _validate_identifier(session_id, "session_id")
    _validate_identifier(turn_id, "turn_id")
    return _plugin_data_root(plugin_data) / STATE_DIRECTORY / session_id / f"{turn_id}.json"


def _as_json(state: RuntimeTurnState) -> dict[str, Any]:
    return {
        "session_id": state.session_id,
        "turn_id": state.turn_id,
        "jdipt_active": state.jdipt_active,
        "repair_count": state.repair_count,
        "propositions": [asdict(item) for item in state.propositions],
    }


def _from_json(payload: Any, session_id: str, turn_id: str) -> RuntimeTurnState:
    if not isinstance(payload, dict):
        raise RuntimeStateError("runtime state must be a JSON object")
    if payload.get("session_id") != session_id or payload.get("turn_id") != turn_id:
        raise RuntimeStateError("runtime state session/turn mismatch")
    raw_propositions = payload.get("propositions")
    if not isinstance(raw_propositions, list):
        raise RuntimeStateError("runtime state propositions must be a list")
    try:
        propositions = [
            MaterialProposition(**item)
            for item in raw_propositions
            if isinstance(item, dict)
        ]
    except (TypeError, ValueError, RuntimeStateError) as exc:
        raise RuntimeStateError(f"invalid proposition metadata: {exc}") from exc
    if len(propositions) != len(raw_propositions):
        raise RuntimeStateError("runtime state contains a non-object proposition")
    try:
        return RuntimeTurnState(
            session_id=session_id,
            turn_id=turn_id,
            jdipt_active=payload["jdipt_active"],
            repair_count=payload["repair_count"],
            propositions=propositions,
        )
    except (KeyError, TypeError, ValueError, RuntimeStateError) as exc:
        raise RuntimeStateError(f"invalid runtime state: {exc}") from exc


def save_runtime_state(
    state: RuntimeTurnState,
    plugin_data: str | os.PathLike[str] | None = None,
) -> Path:
    """Atomically save state under PLUGIN_DATA and return its path."""

    path = runtime_state_path(plugin_data, state.session_id, state.turn_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(_as_json(state), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{state.turn_id}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except OSError as exc:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise RuntimeStateError(f"could not atomically save runtime state: {exc}") from exc
    return path


def load_runtime_state(
    session_id: str,
    turn_id: str,
    plugin_data: str | os.PathLike[str] | None = None,
) -> RuntimeTurnState | None:
    """Load only the exact session/turn state; missing state is not an error."""

    path = runtime_state_path(plugin_data, session_id, turn_id)
    try:
        exists = path.exists()
    except OSError as exc:
        raise RuntimeStateError(f"could not inspect runtime state: {exc}") from exc
    if not exists:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeStateError(f"could not read runtime state: {exc}") from exc
    return _from_json(payload, session_id, turn_id)


def update_repair_count(
    state: RuntimeTurnState,
    repair_count: int,
    plugin_data: str | os.PathLike[str] | None = None,
) -> RuntimeTurnState:
    """Persist the single permitted transition from zero to one repair."""

    if state.repair_count != 0 or repair_count != 1:
        raise ValueError("repair_count can only transition from 0 to 1")
    updated = replace(state, repair_count=repair_count)
    save_runtime_state(updated, plugin_data)
    return updated


def _text_arg(fields: Mapping[str, Any], *names: str) -> str | None:
    for name in names:
        if name in fields and fields[name] is not None:
            value = fields[name]
            if not isinstance(value, str):
                raise RuntimeStateError(f"{name} must be a string")
            return value.strip()
    return None


def _action_name(lexeme: str | None) -> str | None:
    if not lexeme:
        return None
    normalized = lexeme.strip().lower()
    mapping = {
        "지정": "designate",
        "designate": "designate",
        "승인": "approve",
        "approve": "approve",
        "인정": "recognize",
        "recognize": "recognize",
        "허가": "permit",
        "허용": "permit",
        "permit": "permit",
        "제외": "exclude",
        "exclude": "exclude",
        "산입": "count",
        "계상": "count",
        "count": "count",
        "적용하지 아니": "non-application",
        "non-application": "non-application",
    }
    return mapping.get(normalized, lexeme)


def build_mandatory_render_clause(proposition: MaterialProposition) -> str:
    """Build a deterministic source-specific clause from structured fields."""

    condition = proposition.condition or "관련 요건"
    procedure = proposition.procedure or "필요한 절차"
    subject = proposition.subject or "권한 있는 주체"
    legal_object = proposition.legal_object or "해당 대상"
    legal_effect = proposition.legal_effect or "정해진 법적 상태"
    action = proposition.operative_verb_lexeme or proposition.legal_action or "법적 조치"
    relation = (proposition.relation_type or "").lower()
    prefix = ""
    if relation in {"exception", "special", "예외", "특례"}:
        prefix = "다만, 예외로 "
    elif relation in {"base", "기본", "본칙"}:
        prefix = "기본 기준으로 "

    if proposition.status == "OPEN":
        return (
            f"확인 필요: {prefix}{condition} 및 {procedure}의 충족 여부에 따라 "
            f"{subject}가 {legal_object}에 {legal_effect}를 부여하는 {action}을 할 수 있는지는 "
            "현재 확정할 수 없다."
        )

    return (
        f"{prefix}{condition}을 충족하고 {procedure}를 거치면 {subject}는 "
        f"{legal_object}를 {legal_effect}로 {action}할 수 있다."
    )


def register_material_proposition(
    fields: Mapping[str, Any],
    plugin_data: str | os.PathLike[str] | None = None,
) -> RuntimeTurnState:
    """Register or replace one proposition and activate the turn."""

    if not isinstance(fields, Mapping):
        raise RuntimeStateError("registry input must be an object")
    session_id = fields.get("session_id")
    turn_id = fields.get("turn_id")
    status = fields.get("status")
    if not isinstance(session_id, str) or not isinstance(turn_id, str):
        raise RuntimeStateError("session_id and turn_id are required")
    if status not in {"OPEN", "CLOSED"}:
        raise RuntimeStateError("status must be OPEN or CLOSED")
    proposition_id = fields.get("proposition_id")
    if not isinstance(proposition_id, str) or not proposition_id:
        raise RuntimeStateError("proposition_id is required")
    proposition = MaterialProposition(
        proposition_id=proposition_id,
        status=status,
        subject=_text_arg(fields, "subject", "legal_actor"),
        condition=_text_arg(fields, "condition"),
        procedure=_text_arg(fields, "procedure"),
        operative_verb_lexeme=_text_arg(fields, "operative_verb_lexeme"),
        legal_object=_text_arg(fields, "legal_object"),
        legal_effect=_text_arg(fields, "legal_effect", "resulting_status_or_effect"),
        source_clause=_text_arg(fields, "source_clause", "source_proposition", "evidence_span"),
        mandatory_render_clause=None,
        relation_type=_text_arg(fields, "relation_type", "relation_to_base_or_exception"),
        base_proposition_id=_text_arg(fields, "base_proposition_id"),
        exception_proposition_id=_text_arg(fields, "exception_proposition_id"),
        current_status=_text_arg(fields, "current_status", "temporal_status"),
        modality=_text_arg(fields, "modality") or "may",
        legal_action=_text_arg(fields, "legal_action"),
        polarity=_text_arg(fields, "polarity") or "positive",
        materiality=_text_arg(fields, "materiality") or "material",
    )
    clause = build_mandatory_render_clause(proposition)
    proposition = replace(proposition, mandatory_render_clause=clause)
    existing = load_runtime_state(session_id, turn_id, plugin_data)
    if existing is None:
        state = RuntimeTurnState(
            session_id=session_id,
            turn_id=turn_id,
            jdipt_active=True,
            repair_count=0,
            propositions=[proposition],
        )
    else:
        propositions = list(existing.propositions)
        for index, item in enumerate(propositions):
            if item.proposition_id == proposition.proposition_id:
                propositions[index] = proposition
                break
        else:
            propositions.append(proposition)
        state = replace(existing, jdipt_active=True, propositions=propositions)
    save_runtime_state(state, plugin_data)
    return state
