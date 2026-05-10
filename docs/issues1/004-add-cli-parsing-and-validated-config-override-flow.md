# Add CLI parsing and validated config override flow

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Add CLI parsing so command-line values feed into setup_config.py only after validation. Invalid CLI values must not corrupt runtime configuration.

## Acceptance criteria

- [ ] CLI arguments are parsed into a temporary structure before mutation.
- [ ] CLI values are validated before being applied to setup_config.py.
- [ ] Invalid CLI values leave setup_config.py unchanged.
- [ ] Validation runs again after valid CLI overrides are applied.
- [ ] Tests cover valid override and invalid override behavior.

## Blocked by

- Blocked by `issues/003-load-defaults-and-env-values-into-setup-config-py.md`

## User stories addressed

- User story 7
- User story 8

## Assumptions

- None

## Open questions

- Exact CLI flags depend on Slice 1 decisions.

## Notes

- None
