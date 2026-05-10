# Add local sandbox provider

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Add the first sandbox provider using local execution so Release 1 can run commands through the sandbox seam before Docker exists.

## Acceptance criteria

- [ ] A LocalSandboxProvider can create a sandbox handle.
- [ ] RALPH calls the sandbox seam rather than subprocess directly.
- [ ] Local commands run in the worktree path.
- [ ] Sandbox startup failures are reported clearly.
- [ ] Tests cover starting the local sandbox handle.

## Blocked by

- Blocked by `issues/014-add-worktree-preservation-and-cleanup-rules.md`

## User stories addressed

- User story 4

## Assumptions

- None

## Open questions

- None

## Notes

- None
