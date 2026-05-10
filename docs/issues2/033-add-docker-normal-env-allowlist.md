# Add Docker normal env allowlist

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Pass normal Docker environment variables through an explicit allowlist owned by setup_config.py.

## Acceptance criteria

- [ ] Normal env allowlist is defined in setup_config.py.
- [ ] Default normal env allowlist is small.
- [ ] PYTHONUNBUFFERED defaults to 1 when appropriate.
- [ ] Missing normal env vars are skipped except supported defaults.
- [ ] Tests cover normal env arg construction.

## Blocked by

- Blocked by `issues/030-add-docker-bind-mount-command-execution.md`

## User stories addressed

- User story 20

## Assumptions

- None

## Open questions

- None

## Notes

- None
