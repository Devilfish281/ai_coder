# Add Docker bind-mount command execution

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Run sandbox commands inside a Docker container with the host worktree bind-mounted to /workspace.

## Acceptance criteria

- [ ] The host worktree is mounted into the container.
- [ ] The container path is /workspace.
- [ ] The container working directory is /workspace.
- [ ] Commands run in /workspace.
- [ ] File edits inside Docker appear in the host worktree.
- [ ] Command results return stdout, stderr, and exit code.

## Blocked by

- Blocked by `issues/029-add-docker-image-validation-inside-adapter-layer.md`

## User stories addressed

- User story 5
- User story 6

## Assumptions

- None

## Open questions

- None

## Notes

- None
