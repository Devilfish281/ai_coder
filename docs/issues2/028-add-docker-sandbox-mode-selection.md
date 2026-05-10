# Add Docker sandbox mode selection

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Allow Docker sandbox mode to be selected through setup_config.py while keeping Docker behavior out of the RALPH orchestrator.

## Acceptance criteria

- [ ] setup_config.py can select local or Docker sandbox mode.
- [ ] RALPH asks for a SandboxProvider rather than hard-coding Docker.
- [ ] Docker mode has clear validation errors when selected but unavailable.
- [ ] Local mode still works without Docker settings.
- [ ] Tests cover provider selection.

## Blocked by

- Blocked by `issues/027-add-release-1-end-to-end-ralph-tracer-bullet.md`

## User stories addressed

- User story 4
- User story 5

## Assumptions

- None

## Open questions

- None

## Notes

- None
