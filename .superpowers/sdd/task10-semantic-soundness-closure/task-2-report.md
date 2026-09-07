# Task 2 Report — Task 10 RED-suite Fix Round 4

This report supersedes the earlier fix-run notes and their stale counts.

## Scope and reviewed inputs

- Worktree: `F:\2026-PJ\JDIPT\.worktrees\task10-semantic-soundness-closure`
- Starting commit: `007a74e`; production remains at Task 9 baseline `02156e9`.
- Read the Task 10 plan, Task 2 brief, current test module, and round-3 independent review verdict (Task 2 NOT DONE).
- Changed paths only:
  - `tests/test_task10_semantic_soundness.py`
  - `.superpowers/sdd/task10-semantic-soundness-closure/task-2-report.md`
- No production, installed plugin binding, source/obligation tests, or unrelated tests changed.

## Four review fixes

1. Legal-action degradation now uses `처리할 수 있다` in place of canonical `지정`. Fixture assertions prove both canonical action fields are absent and condition, procedure, object, and effect are retained. The conclusion retains positive MAY; the exact expected code is `LEGAL_RELATION_DEGRADATION` with `relation_fields == ("legal_action",)`.
2. Both OPEN-promotion tests use their own OPEN contract and the same evaluated draft for coverage. Each draft contains the exact OPEN render as the author's ordinary review-reason prose, outside quotation/code/example regions, plus a separate definitive positive or negative conclusion. No unrelated CLOSED fixture remains.
3. MUST_NOT weakening uses typed `Polarity.NEGATIVE` and the canonical action `지정`; condition, procedure, object, and effect all remain in the final relation, which says only `지정하지 않아도 된다`. It still requires exactly `MUST_NOT_DEGRADED` and verifies typed modality/polarity metadata. No unrelated violation code is accepted. Baseline returns a passing result with no violations, so the test is genuinely RED for missing modality enforcement.
4. Exception-effect degradation retains the exception wording, condition, procedure, canonical action, object, and positive MAY while changing only `예외 효과` to `변경 효과`. Fixture assertions check preservation; the expected relation fields are exactly `("legal_effect",)`.

For these final-relation tests, a blank paragraph terminates the `결론:` label before the canonical review-reason render. Otherwise baseline region classification includes the later canonical render in the final conclusion and masks missing fields.

## Matrix and layer boundaries

Exactly 24 cases remain: 7 expected-allow cases and 17 expected-reject cases. These are specification categories, not the observed pytest pass/fail counts.

All seven expected-allow cases pass. Of the 17 expected-reject cases, 9 already pass their rejection assertions against baseline and 8 remain RED. Action and exception-effect isolation now pass against existing baseline checks; no test was weakened to force a particular RED count.

Coverage and soundness remain separate result objects. Required layer-boundary cases assert coverage PASS before soundness FAIL. Canonical fixtures still use validated constructors, typed enums, and `build_render_contract`; no `object.__new__` or untyped bypass was introduced.

## Focused verification

Working directory is the worktree above. UTF-8 output was selected with `$env:PYTHONIOENCODING='utf-8'`.

Initial command:

```powershell
python -m pytest -q -p no:cacheprovider tests/test_task10_semantic_soundness.py
```

Observed summary: `8 failed, 16 passed in 0.16s`, exit code 1. No collection or fixture errors.

A compact traceback run captured the complete output below:

```powershell
python -m pytest -q -p no:cacheprovider --tb=short tests/test_task10_semantic_soundness.py
```

Exit code: 1.

```text
..............FFFF.F.FFF                                                 [100%]
================================== FAILURES ===================================
__________ test_must_weakened_to_may_fails_with_structured_violation __________
tests\test_task10_semantic_soundness.py:328: in test_must_weakened_to_may_fails_with_structured_violation
    assert soundness.soundness_passed is False
E   assert True is False
E    +  where True = SoundnessResult(soundness_passed=True, violations=()).soundness_passed
______ test_must_not_weakened_to_may_not_fails_with_structured_violation ______
tests\test_task10_semantic_soundness.py:351: in test_must_not_weakened_to_may_not_fails_with_structured_violation
    assert soundness.soundness_passed is False
E   assert True is False
E    +  where True = SoundnessResult(soundness_passed=True, violations=()).soundness_passed
_ test_correct_intermediate_render_plus_contradictory_final_conclusion_fails __
tests\test_task10_semantic_soundness.py:373: in test_correct_intermediate_render_plus_contradictory_final_conclusion_fails
    assert "FINAL_CONCLUSION_CONTRADICTION" in _codes(soundness)
E   AssertionError: assert 'FINAL_CONCLUSION_CONTRADICTION' in {'POLARITY_CONTRADICTION'}
E    +  where {'POLARITY_CONTRADICTION'} = _codes(SoundnessResult(soundness_passed=False, violations=(SoundnessViolation(code='POLARITY_CONTRADICTION', proposition_id='...행정청은 대상 O를 지위 Z로 지정할 수 없으므로 불가능하다. # 3. 검토이유\n기본 기준으로 요건 C을 충족하고 절차 P를 거치면 행정청는 대상 O를 지위 Z로 지정할 수 있다.\n현행 기준에 따른다.'),)))
______ test_one_correct_duplicate_plus_one_contradictory_duplicate_fails ______
tests\test_task10_semantic_soundness.py:394: in test_one_correct_duplicate_plus_one_contradictory_duplicate_fails
    assert "FINAL_CONCLUSION_CONTRADICTION" in _codes(soundness)
E   AssertionError: assert 'FINAL_CONCLUSION_CONTRADICTION' in {'POLARITY_CONTRADICTION'}
E    +  where {'POLARITY_CONTRADICTION'} = _codes(SoundnessResult(soundness_passed=False, violations=(SoundnessViolation(code='POLARITY_CONTRADICTION', proposition_id='... 거치면 행정청는 대상 O를 지위 Z로 지정할 수 있다.\n현행 기준에 따른다.\n기본 기준으로 요건 C을 충족하고 절차 P를 거치면 행정청는 대상 O를 지위 Z로 지정할 수 있다.\n현행 기준에 따른다.'),)))
_ test_source_specific_legal_effect_removed_while_other_keywords_remain_fails _
tests\test_task10_semantic_soundness.py:445: in test_source_specific_legal_effect_removed_while_other_keywords_remain_fails
    assert soundness.soundness_passed is False
E   assert True is False
E    +  where True = SoundnessResult(soundness_passed=True, violations=()).soundness_passed
___________________ test_malformed_semantic_identity_fails ____________________
tests\test_task10_semantic_soundness.py:504: in test_malformed_semantic_identity_fails
    assert soundness.soundness_passed is False
E   assert True is False
E    +  where True = SoundnessResult(soundness_passed=True, violations=()).soundness_passed
____________________ test_ambiguous_adopted_identity_fails ____________________
tests\test_task10_semantic_soundness.py:527: in test_ambiguous_adopted_identity_fails
    assert "AMBIGUOUS_ADOPTED_IDENTITY" in _codes(soundness)
E   AssertionError: assert 'AMBIGUOUS_ADOPTED_IDENTITY' in {'LEGAL_RELATION_DEGRADATION'}
E    +  where {'LEGAL_RELATION_DEGRADATION'} = _codes(SoundnessResult(soundness_passed=False, violations=(SoundnessViolation(code='LEGAL_RELATION_DEGRADATION', proposition_... 충족하고 절차 P를 거치면 행정청는 대상 O를 지위 Z로 지정할 수 있다.\n현행 기준에 따른다.\n# 2. 검토결론', final_conclusion_span='위 결론은 두 제안을 함께 언급할 뿐이다.'))))
__________________ test_unavailable_semantic_authority_fails __________________
tests\test_task10_semantic_soundness.py:547: in test_unavailable_semantic_authority_fails
    assert soundness.soundness_passed is False
E   assert True is False
E    +  where True = SoundnessResult(soundness_passed=True, violations=()).soundness_passed
=========================== short test summary info ===========================
FAILED tests/test_task10_semantic_soundness.py::test_must_weakened_to_may_fails_with_structured_violation
FAILED tests/test_task10_semantic_soundness.py::test_must_not_weakened_to_may_not_fails_with_structured_violation
FAILED tests/test_task10_semantic_soundness.py::test_correct_intermediate_render_plus_contradictory_final_conclusion_fails
FAILED tests/test_task10_semantic_soundness.py::test_one_correct_duplicate_plus_one_contradictory_duplicate_fails
FAILED tests/test_task10_semantic_soundness.py::test_source_specific_legal_effect_removed_while_other_keywords_remain_fails
FAILED tests/test_task10_semantic_soundness.py::test_malformed_semantic_identity_fails
FAILED tests/test_task10_semantic_soundness.py::test_ambiguous_adopted_identity_fails
FAILED tests/test_task10_semantic_soundness.py::test_unavailable_semantic_authority_fails
8 failed, 16 passed in 0.16s
```

## Additional required repository checks

- `python scripts/validate_repo.py`: PASS, exit 0.
- `python scripts/validate_authority_temporal_contract.py`: PASS, exit 0.
- `python scripts/plugin_integrity.py`: `INSTALLATION_INTEGRITY: FAIL`, exit 1; 18 installed-file/digest mismatches. No installed files were changed. These local regression results do not establish installed-runtime behavioral parity.
- `python -m pytest -q`: `8 failed, 331 passed, 2 warnings, 155 errors in 25.81s`, exit 1. This is not a clean full-suite result. A focused reproduction of the first setup error confirmed pytest could not create a numbered temporary directory under `C:\Users\KSH\AppData\Local\Temp\pytest-of-KSH` after 10 tries; no unrelated environment repair was attempted.
- `git diff --check`: clean (Git emitted only LF-to-CRLF notices).
- `git diff 02156e9 --name-only -- scripts skills`: empty; production and skill files remain at baseline.

## Result

Round-4 test/report changes are complete within the four requested findings. The focused suite remains genuinely RED for baseline behavior gaps; no Task 10 production behavior has been implemented.
