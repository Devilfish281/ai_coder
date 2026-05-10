# Add worktree branch naming

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Create a branch-name strategy that makes worktrees traceable to the issue or run while staying safe for Git and Windows path behavior.

## Acceptance criteria

- [ ] A branch name can be derived from issue/run data.
- [ ] Unsafe characters are sanitized.
- [ ] Branch names are short enough to be usable.
- [ ] Branch names are traceable to the source issue or run.
- [ ] Tests cover normal titles, long titles, and special characters.

## Blocked by

- Blocked by `issues/011-add-actionable-issue-selection-seam.md`

## User stories addressed

- User story 3
- User story 19

## Assumptions

- None

## Open questions

- Exact naming pattern may depend on Slice 1 decisions.

## Notes

- None
