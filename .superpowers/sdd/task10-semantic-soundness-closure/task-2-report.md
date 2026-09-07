# Task 2 Report — Task 10 Semantic Soundness RED Regressions

## Scope

- Worktree: `F:\2026-PJ\JDIPT\.worktrees\task10-semantic-soundness-closure`
- Constraint followed: test-only change, no production edits
- Requested output file: `F:\2026-PJ\JDIPT\.worktrees\task10-semantic-soundness-closure\.superpowers\sdd\task10-semantic-soundness-closure\task-2-report.md`

## Changed Files

- `tests/test_task10_semantic_soundness.py`
- `.superpowers/sdd/task10-semantic-soundness-closure/task-2-report.md`

## Focused Test Command

```powershell
python -m pytest -q -p no:cacheprovider 'F:\2026-PJ\JDIPT\.worktrees\task10-semantic-soundness-closure\tests\test_task10_semantic_soundness.py'
```

## RED Output

```text
17 failed, 19 passed in 0.27s
```

## Failing Cases

- `test_closed_negative_with_matching_final_adoption_passes`
- `test_must_weakened_to_may_fails_with_structured_violation`
- `test_must_not_weakened_to_may_not_fails_with_structured_violation`
- `test_correct_intermediate_render_plus_contradictory_final_conclusion_fails`
- `test_one_correct_duplicate_plus_one_contradictory_duplicate_fails`
- `test_malformed_semantic_identity_fails`
- `test_ambiguous_adopted_identity_fails`
- `test_unavailable_semantic_authority_fails`
- `test_missing_source_citation_fails_with_task10_code`
- `test_irrelevant_evidence_span_fails_with_task10_code`
- `test_lower_authority_fails_with_task10_code`
- `test_historical_source_for_current_requirement_fails_with_task10_code`
- `test_unresolved_temporal_source_fails_with_task10_code`
- `test_must_dropped_fails_with_task10_code`
- `test_condition_dropped_fails_with_task10_code`
- `test_procedure_dropped_fails_with_task10_code`
- `test_final_conclusion_unsupported_fails_with_task10_code`

## Notes

- The new file uses the existing `scripts.legal_proposition`, `scripts.proposition_rendering`, `scripts.proposition_reconciliation`, and `scripts.proposition_soundness` APIs.
- The seven required PASS cases are present and currently pass.
- The 17 required FAIL regressions are present and currently fail on missing Task 10 behavior, which is the intended RED state for this task.

## Fix Run

Focused command:

```powershell
python -m pytest -q -p no:cacheprovider 'F:\2026-PJ\JDIPT\.worktrees\task10-semantic-soundness-closure\tests\test_task10_semantic_soundness.py'
```

Exact output:

```text
.F............FFFFFFFFFF                                                 [100%]
================================== FAILURES ===================================
__________ test_closed_negative_with_matching_final_adoption_passes ___________

    def test_closed_negative_with_matching_final_adoption_passes():
        proposition = _proposition(
            polarity=Polarity.NEGATIVE,
            legal_action="����",
            operative_verb_lexeme="����",
        )
        draft = _draft_with_contract(
            proposition,
            prefix="# 2. ������\n",
            suffix="\n���: ��� C�� ���� P�� �����ϴ��� ����û�� ��� O�� ���� Z�� �����ȴ�.",
        )

        coverage = _coverage(build_render_contract(proposition), draft)
        soundness = _soundness(proposition, draft)

        assert coverage.covered is True
        assert soundness.soundness_passed is True
E       AssertionError: assert False is True
E        +  where False = SoundnessResult(soundness_passed=False, violations=(SoundnessViolation(code='POLARITY_CONTRADICTION', proposition_id='...�� �������� ��� C�� �����ϰ� ���� P�� ��ġ�� ����û�� ��� O�� ���� Z�� ������ �� �ִ�.\n���� ���ؿ� ������.\n���: ��� C�� ���� P�� �����ϴ��� ����û�� ��� O�� ���� Z�� �����ȴ�.'),)).soundness_passed

tests\test_task10_semantic_soundness.py:131: AssertionError
__________ test_must_weakened_to_may_fails_with_structured_violation __________

    def test_must_weakened_to_may_fails_with_structured_violation():
        proposition = _proposition(modality=Modality.MUST)
        draft = "\n".join(
            (
                "# 2. ������",
                "���: ��� C�� ���� P�� ������ ����û�� ��� O�� ���� Z�� �ȴ�.",
                "# 3. ��������",
                _rendered(proposition),
            )
        )

        coverage = _coverage(build_render_contract(proposition), draft)
        soundness = _soundness(proposition, draft)

        assert coverage.covered is True
        assert soundness.soundness_passed is False
E       assert True is False
E        +  where True = SoundnessResult(soundness_passed=True, violations=()).soundness_passed

tests\test_task10_semantic_soundness.py:311: AssertionError
... (remaining failure output unchanged)
```

The focused run remained red on the current Task 10 evaluator boundary, while the test-only review fixes stayed in the test module and report only.
