# Add Windows Docker path conversion utility

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Keep Windows path conversion and mount patching behind a small utility seam so Docker bind mounts work correctly on Windows 11.

## Acceptance criteria

- [ ] Windows host paths are converted or patched for Docker bind mounts.
- [ ] Path logic is isolated in a utility seam.
- [ ] RALPH orchestration does not contain Windows path conversion logic.
- [ ] Tests cover typical Windows paths, spaces, and special characters.

## Blocked by

- Blocked by `issues/030-add-docker-bind-mount-command-execution.md`

## User stories addressed

- User story 6

## Assumptions

- None

## Open questions

- None

## Notes

- None
