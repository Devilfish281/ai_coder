# Add normalized command result contract

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Normalize command results from sandbox execution into stdout, stderr, exit code, and failure state so all providers return the same shape.

## Acceptance criteria

- [ ] i_sandboxhandle_run() returns a normalized command result.
- [ ] stdout is captured.
- [ ] stderr is captured.
- [ ] exit code is captured.
- [ ] Command failure is represented consistently.
- [ ] Tests cover successful and failed commands.

## Blocked by

- Blocked by `issues/015-add-local-sandbox-provider.md`

## User stories addressed

- User story 4
- User story 19

## Assumptions

- None

## Open questions

- None

## Notes

- None
