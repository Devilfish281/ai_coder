# Commit successful work and preserve failed or dirty work

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Commit successful changes only after completion is signaled and required tests pass, while preserving failed or dirty worktrees for human review.

## Acceptance criteria

- [ ] Successful changes are committed only after tests pass.
- [ ] The commit hash is shown to the user.
- [ ] Failed, blocked, incomplete, or dirty runs preserve the worktree.
- [ ] The preserved worktree path is shown.
- [ ] Commit failure returns failed and preserves work.
- [ ] Tests cover commit success, test failure, dirty worktree, and commit failure.

## Blocked by

- Blocked by `issues/023-run-pytest-through-sandbox-seam.md`

## User stories addressed

- User story 16
- User story 17
- User story 18
- User story 19

## Assumptions

- None

## Open questions

- Exact commit message format depends on Slice 1.

## Notes

- None
