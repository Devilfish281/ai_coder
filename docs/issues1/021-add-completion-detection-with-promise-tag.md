# Add completion detection with promise tag

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Add completion detection using the explicit <promise>COMPLETE</promise> signal instead of guessing whether the agent is done.

## Acceptance criteria

- [ ] The completion detector recognizes <promise>COMPLETE</promise>.
- [ ] Missing completion before max iterations is treated as incomplete.
- [ ] Agent command failure is treated as failed.
- [ ] Sandbox command failure is treated as failed.
- [ ] Tests cover completion, no completion, command failure, and malformed output.

## Blocked by

- Blocked by `issues/020-add-fake-test-agent-provider.md`

## User stories addressed

- User story 15

## Assumptions

- None

## Open questions

- None

## Notes

- None
