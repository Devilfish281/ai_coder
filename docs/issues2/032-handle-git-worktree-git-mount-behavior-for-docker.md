# Handle Git worktree .git mount behavior for Docker

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Treat Git worktree .git mount behavior as a special case where needed so Docker commands can inspect and modify Git state correctly.

## Acceptance criteria

- [ ] Docker bind-mount mode handles worktree .git behavior.
- [ ] Git state can be inspected after Docker commands finish.
- [ ] Dirty or failed worktrees are preserved.
- [ ] Tests cover expected .git path handling behavior where practical.

## Blocked by

- Blocked by `issues/031-add-windows-docker-path-conversion-utility.md`

## User stories addressed

- User story 3
- User story 5
- User story 6

## Assumptions

- None

## Open questions

- None

## Notes

- None
