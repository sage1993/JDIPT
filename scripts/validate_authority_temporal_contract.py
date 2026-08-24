"""Validate JDIPT authority, temporal, claim-evidence, and active-suite contracts."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "law-interpretation-request"
REFERENCES = SKILL_ROOT / "references"
EVALS = SKILL_ROOT / "evals"

CONTRACTS: dict[Path, tuple[str, ...]] = {
    REFERENCES / "legal-issue-mapping.md": (
        "적용 기준시점",
        "허가일",
        "신청일",
        "처분일",
        "경과조치",
        "확인 필요",
        "현행 요건을 과거 사실에 자동 대입하지 않는다",
    ),
    REFERENCES / "interpretation-principles.md": (
        "적용 법령 버전",
        "공포일과 시행일",
        "경과조치",
        "법제처 해석례",
        "법적 구속력",
        "소관 중앙행정기관의 질의회신",
        "핵심 문언이 개정되었으면",
    ),
    REFERENCES / "source-policy.md": (
        "적용 기준시점·현행성 Gate",
        "Authority / Legal Effect Gate",
        "검색 우선순위와 법적 효력을 구분",
        "법제처 정부유권해석",
        "소관부처",
        "Claim-level Evidence Gate",
        "Source Claim",
        "Analytical Inference",
        "material legal proposition",
        "Referenced Source Resolution Hard Gate",
        "Source Completeness / Counterevidence Gate",
        "URL provenance Gate",
    ),
    EVALS / "v0.2.3-authority-temporal-evidence.md": tuple(
        f"E{i}." for i in range(43, 47)
    ),
    EVALS / "suite-manifest.json": (
        '"core_cases"',
        '"full_cases"',
        '"legacy_cases"',
        '"E42": "E41"',
    ),
    EVALS / "v0.2.3-machine-oracles.json": (
        '"E43"',
        '"E44"',
        '"E45"',
        '"E46"',
        '"temporal_lifecycle"',
        '"no_directional_abstract_conclusion"',
        '"authority_versioning"',
        '"claim_inference_separation"',
    ),
}


def validate() -> list[str]:
    failures: list[str] = []
    for path, markers in CONTRACTS.items():
        if not path.is_file():
            failures.append(f"missing file: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        missing = [marker for marker in markers if marker not in text]
        if missing:
            failures.append(
                f"{path.relative_to(ROOT)} missing markers: {missing}"
            )
    return failures


def main() -> int:
    failures = validate()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS")
    print("authority_temporal_evidence_contract=v0.2.3-candidate")
    print("behavior_spec=E43-E46")
    print("live_suites=core14/full26")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
