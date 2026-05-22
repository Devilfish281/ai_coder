# Expose final test result on RalphResult

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_4.md`

## Type

AFK

## Human decision needed

None.

## What to build

Expose the final pytest phase result through the public RALPH result object.

This slice makes the post-agent test run observable from `i_ralph_run()`. Phase 3 needs this field so tests and smoke proofs can show that final pytest ran after Codex completed and before commit/sync.

## Acceptance criteria

- [ ] `RalphResult` exposes `test_result` as an optional field.
- [ ] `test_result` defaults to `None`.
- [ ] Successful RALPH runs populate `test_result` after final tests run.
- [ ] Failed final pytest runs return a populated `test_result` with failed status information.
- [ ] Early returns before the final test phase leave `test_result` as `None`.
- [ ] Existing final test behavior does not change.

## Blocked by

- Blocked by `issues/059-expose-project-setup-result-on-ralph-result.md`

## User stories addressed

- User story 23
- User story 29
- User story 30

## Assumptions

- A final test result object already exists or equivalent test-result data is already produced by the RALPH workflow.

## Open questions

None

## Notes

Do not add a new test runner. Only expose the result the workflow already creates.
