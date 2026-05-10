# Add RALPH result status contract

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Return one clear result status every time RALPH runs: complete, incomplete, failed, blocked, or no_changes.

## Acceptance criteria

- [ ] Result status can be complete, incomplete, failed, blocked, or no_changes.
- [ ] Max-iteration without completion returns incomplete.
- [ ] Command/test/commit failures return failed.
- [ ] Missing configuration or unsafe repo state returns blocked.
- [ ] No code changes returns no_changes unless explicitly allowed.
- [ ] Tests cover every status.

## Blocked by

- Blocked by `issues/021-add-completion-detection-with-promise-tag.md`

## User stories addressed

- User story 15
- User story 16
- User story 17
- User story 18
- User story 19

## Assumptions

- None

## Open questions

- None

## Notes

- None
