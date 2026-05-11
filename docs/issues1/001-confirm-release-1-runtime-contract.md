# Confirm Release 1 runtime contract

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

HITL

## Human decision needed

Confirm the Release 1 command, flags, config fields, fake/test agent behavior, and commit message format.

## What to build

Confirm the small set of Release 1 decisions that affect every later implementation slice: start command, CLI flags, setup_config fields, fake/test agent behavior, and commit message format.

## Confirmed Release 1 runtime contract

### Release 1 CLI command

The Release 1 command is:

```powershell
poetry run ai-coder


## Acceptance criteria

- [ ] The Release 1 CLI command is chosen and documented.
- [ ] The Release 1 CLI flags are chosen and documented.
- [ ] The minimum setup_config.py fields are listed.
- [ ] The fake/test agent behavior is defined.
- [ ] The commit message format is defined.
- [ ] Any unresolved decisions are listed as open questions.

## Blocked by

None - can start immediately.

## User stories addressed

- User story 1
- User story 7
- User story 8

## Assumptions

- None

## Open questions

- What exact CLI command should start AI Code in Release 1?
- What exact CLI flags are required in Release 1?
- What exact fake/test agent behavior should be used?
- What exact commit message format should successful runs use?

## Notes

- This is intentionally HITL because later issues depend on these choices.
```
