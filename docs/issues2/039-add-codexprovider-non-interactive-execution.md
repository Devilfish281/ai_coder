# Add CodexProvider non-interactive execution

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Implement CodexProvider's first non-interactive execution path through the agent provider seam.

## Acceptance criteria

- [ ] CodexProvider starts in non-interactive mode.
- [ ] Command construction is isolated inside CodexProvider.
- [ ] RALPH does not hard-code Codex command details.
- [ ] Codex command failure returns a normalized failure.
- [ ] Tests use patched command execution.

## Blocked by

- Blocked by `issues/037-confirm-codexprovider-command-contract.md`
- Blocked by `issues/038-add-agent-provider-seam.md`

## User stories addressed

- User story 12
- User story 13

## Assumptions

- None

## Open questions

- None

## Notes

- None
