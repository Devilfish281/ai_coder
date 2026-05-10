# Add Docker command redaction utility

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Add a Docker command redaction utility that redacts only configured secret env values and does not import setup_config.py.

## Acceptance criteria

- [ ] Redaction receives the command and secret env names as inputs.
- [ ] Short env flag followed by NAME=value is redacted.
- [ ] Long env flag followed by NAME=value is redacted.
- [ ] Joined long env flag form is redacted.
- [ ] Normal env values are not redacted.
- [ ] Tests cover every supported env arg shape.

## Blocked by

- Blocked by `issues/034-add-docker-secret-env-allowlist-and-missing-secret-errors.md`

## User stories addressed

- User story 20

## Assumptions

- None

## Open questions

- None

## Notes

- None
