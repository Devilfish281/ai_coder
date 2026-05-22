# Enforce Codex non-zero exit code failure

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_4.md`

## Type

AFK

## Human decision needed

None.

## What to build

Ensure a non-zero Codex command exit code fails the agent run even if output text contains the completion token.

This protects RALPH from incorrectly trusting partial output from a crashed or failed Codex command.

## Acceptance criteria

- [ ] CodexProvider treats non-zero Codex exit code as failed.
- [ ] `<promise>COMPLETE</promise>` in final message, JSONL, or stdout does not override non-zero exit code.
- [ ] stdout and stderr are preserved for diagnostics.
- [ ] RALPH receives a failed provider/orchestrator result.
- [ ] Worktree preservation behavior is triggered when needed.
- [ ] Tests cover non-zero exit with a completion token in output.

## Blocked by

- Blocked by `issues/070-recover-from-malformed-codex-jsonl-with-diagnostics.md`

## User stories addressed

- User story 23
- User story 26

## Assumptions

- Existing result status handling can represent failed provider commands.

## Open questions

None

## Notes

Completion detection may only produce success after the Codex command exits successfully.
