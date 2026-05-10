# Add actionable issue selection seam

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Add the issue selection seam that chooses one actionable issue and skips issues that are vague, blocked, already assigned, or unsafe.

## Acceptance criteria

- [ ] Issue selection lives behind i_github_issue_select() or the chosen Release 1 equivalent.
- [ ] Actionable issues are selected.
- [ ] Vague or blocked issues are skipped with a clear reason.
- [ ] Unsafe issues are skipped with a clear reason.
- [ ] Tests cover selected and skipped issue examples.

## Blocked by

- Blocked by `issues/010-add-provided-issue-data-model.md`

## User stories addressed

- User story 1
- User story 2

## Assumptions

- Release 1 may use fake/provided issues instead of reading GitHub directly.

## Open questions

- None

## Notes

- None
