# Add worktree preservation and cleanup rules

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Implement worktree cleanup and preservation rules so failed or dirty work is never deleted unexpectedly.

## Acceptance criteria

- [ ] Failed runs preserve the worktree.
- [ ] Runs with uncommitted changes preserve the worktree.
- [ ] Successful clean runs may remove the worktree.
- [ ] Worktree cleanup lives behind i_worktree_cleanup().
- [ ] The preserved worktree path is shown to the user.
- [ ] Tests cover success, failure, dirty state, and preserved path reporting.

## Blocked by

- Blocked by `issues/013-add-safe-worktree-creation.md`

## User stories addressed

- User story 17
- User story 18
- User story 19

## Assumptions

- None

## Open questions

- None

## Notes

- None
