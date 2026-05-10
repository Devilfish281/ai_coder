# Add configured secret redaction

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Redact configured secret values from logs while avoiding broad auto-detection that hides useful normal values.

## Acceptance criteria

- [ ] Configured secret values are redacted from logs.
- [ ] Normal env values may be logged normally.
- [ ] Huge prompt bodies are not logged by default.
- [ ] Raw secret values are never printed in expected log paths.
- [ ] Tests cover redaction and non-redaction of normal values.

## Blocked by

- Blocked by `issues/025-add-display-and-logging-phases.md`

## User stories addressed

- User story 20

## Assumptions

- None

## Open questions

- None

## Notes

- None
