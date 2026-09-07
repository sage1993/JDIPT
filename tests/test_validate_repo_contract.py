import json
from pathlib import Path

from scripts import plugin_integrity, validate_repo


def test_output_marker_matches_current_moleg_routing_contract():
    markers = validate_repo.REQUIRED_OUTPUT_SKILL_MARKERS

    assert "General legal-review mode comes first" in markers
    assert "MOLEG suitability correction applies only in explicit MOLEG request mode" not in markers
    assert "질문만 하고 그 응답에서는 중단한다" in markers


def test_agent_config_markers_are_concise_high_level_contracts():
    markers = validate_repo.REQUIRED_AGENT_CONFIG_MARKERS

    assert "allow_implicit_invocation: false" in markers
    assert "대한민국 법령의 의미·적용범위" in markers
    assert "직접 근거" in markers
    assert "material proposition" in markers
    assert "모드를 먼저 확정하세요" not in markers
    assert "URL은 검증된 것만 쓰고 빈 query 값" not in markers


def test_agents_markers_are_bootstrap_only():
    assert validate_repo.REQUIRED_AGENTS_MARKERS == {
        "$law-interpretation-request",
        "응답 모드나 정보 부족 여부를 판단하기 전에",
        "SKILL.md를 먼저 읽는다",
    }


def test_current_production_architecture_has_one_owner_per_runtime_role():
    assert validate_repo.runtime_architecture_violations() == []


def test_registry_lifecycle_has_one_service_owner():
    text = (validate_repo.ROOT / "scripts" / "proposition_registry.py").read_text(
        encoding="utf-8"
    )

    assert "class RegistryService" in text
    assert "def begin_pending" in text
    assert "def read_state" in text
    assert "def mark_enforcement" in text
    assert "def record_disposition" in text
    assert "def create_pending_runtime_state" not in text
    assert "def update_registry_enforcement_count" not in text


def test_architecture_checker_rejects_duplicate_registry_lifecycle_writer(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for relative in validate_repo.PRODUCTION_RUNTIME_MODULES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")

    (tmp_path / "scripts" / "legal_proposition.py").write_text(
        "class LegalProposition: pass\n", encoding="utf-8"
    )
    (tmp_path / "scripts" / "proposition_registry.py").write_text(
        "class RegistryService:\n"
        "    def begin_pending(self): pass\n"
        "    def register(self): pass\n"
        "    def mark_enforcement(self): pass\n"
        "    def record_disposition(self): pass\n",
        encoding="utf-8",
    )
    (tmp_path / "scripts" / "synthesis_runtime_state.py").write_text(
        "def create_pending_runtime_state(): pass\n", encoding="utf-8"
    )
    (tmp_path / ".codex-plugin").mkdir()
    (tmp_path / ".codex-plugin" / "plugin.json").write_text(
        json.dumps({"name": "jdipt", "hooks": {}, "mcpServers": {}}),
        encoding="utf-8",
    )

    violations = validate_repo.runtime_architecture_violations(tmp_path)

    assert any("lifecycle writer" in item for item in violations)


def test_required_runtime_bundle_includes_canonical_bridge_and_manifests():
    required = {path.relative_to(validate_repo.ROOT).as_posix() for path in validate_repo.REQUIRED_RUNTIME_FILES}
    for relative in plugin_integrity.PLUGIN_RUNTIME_FILES:
        assert relative in required


def test_architecture_checker_is_scoped_to_production_modules(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for relative in validate_repo.PRODUCTION_RUNTIME_MODULES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")

    (tmp_path / "scripts" / "legal_proposition.py").write_text(
        "class LegalProposition: pass\nclass LegalProposition: pass\n",
        encoding="utf-8",
    )
    (tmp_path / "scripts" / "proposition_registry.py").write_text(
        "def register_material_proposition(): pass\n"
        "def register_material_proposition_again(): pass\n"
        "def register_material_proposition(): pass\n",
        encoding="utf-8",
    )
    (tmp_path / "scripts" / "synthesis_runtime_state.py").write_text(
        "def build_render_contract(): pass\n",
        encoding="utf-8",
    )
    (tmp_path / "scripts" / "proposition_rendering.py").write_text(
        "# 안심주택 250m\n",
        encoding="utf-8",
    )
    (tmp_path / "scripts" / "runtime_registry_state.py").write_text("", encoding="utf-8")
    (tmp_path / ".codex-plugin").mkdir()
    (tmp_path / ".codex-plugin" / "plugin.json").write_text(
        json.dumps({"name": "jdipt"}), encoding="utf-8"
    )

    violations = validate_repo.runtime_architecture_violations(tmp_path)
    assert any("runtime_registry_state.py" in item for item in violations)
    assert any("LegalProposition" in item for item in violations)
    assert any("register_material_proposition" in item for item in violations)
    assert any("render builder" in item for item in violations)
    assert any("ASH-specific" in item for item in violations)
    assert any("hooks" in item for item in violations)
    assert any("MCP" in item for item in violations)


def test_architecture_checker_rejects_direct_runtime_state_reader_consumer(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for relative in validate_repo.PRODUCTION_RUNTIME_MODULES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")

    (tmp_path / "scripts" / "legal_proposition.py").write_text(
        "class LegalProposition: pass\n", encoding="utf-8"
    )
    (tmp_path / "scripts" / "proposition_registry.py").write_text(
        "class RegistryService:\n"
        "    def read_state(self): pass\n"
        "    def begin_pending(self): pass\n"
        "    def register(self): pass\n"
        "    def mark_enforcement(self): pass\n"
        "    def record_disposition(self): pass\n",
        encoding="utf-8",
    )
    (tmp_path / "scripts" / "synthesis_runtime_state.py").write_text(
        "def load_runtime_state(): pass\n", encoding="utf-8"
    )
    (tmp_path / "scripts" / "stop_synthesis_gate.py").write_text(
        "from scripts.synthesis_runtime_state import load_runtime_state\n"
        "def handle_stop_event():\n"
        "    return load_runtime_state()\n",
        encoding="utf-8",
    )
    (tmp_path / ".codex-plugin").mkdir()
    (tmp_path / ".codex-plugin" / "plugin.json").write_text(
        json.dumps({"name": "jdipt", "hooks": {}, "mcpServers": {}}),
        encoding="utf-8",
    )

    violations = validate_repo.runtime_architecture_violations(tmp_path)

    assert any("direct runtime state reader" in item for item in violations)
