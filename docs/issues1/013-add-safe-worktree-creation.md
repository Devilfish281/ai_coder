# Add safe worktree creation

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Create a Git worktree before any agent code edits so the main working tree is protected.

## Acceptance criteria

- [ ] A worktree is created before agent execution begins.
- [ ] The worktree uses the safe branch naming strategy.
- [ ] Worktree creation lives behind i_worktree_create().
- [ ] Failures return a clear blocked or failed result.
- [ ] Tests cover successful creation and creation failure.

## Blocked by

- Blocked by `issues/012-add-worktree-branch-naming.md`

## User stories addressed

- User story 3

## Assumptions

- None

## Open questions

- None

## Notes

- None
