# Add Docker secret env allowlist and missing-secret errors

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Pass secret Docker environment variables through a separate allowlist and raise clear errors when allowlisted secrets are missing or empty.

## Acceptance criteria

- [ ] Secret env allowlist is separate from normal env allowlist.
- [ ] Default secret env allowlist is empty.
- [ ] Missing allowlisted secrets raise clear errors.
- [ ] Empty allowlisted secrets raise clear errors.
- [ ] Secret validation happens when building the Docker command, not during provider construction.
- [ ] Tests cover missing and empty secrets.

## Blocked by

- Blocked by `issues/033-add-docker-normal-env-allowlist.md`

## User stories addressed

- User story 20

## Assumptions

- None

## Open questions

- None

## Notes

- None
