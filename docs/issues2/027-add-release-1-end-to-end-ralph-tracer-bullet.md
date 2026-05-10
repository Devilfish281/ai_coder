# Add Release 1 end-to-end RALPH tracer bullet

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Connect the Release 1 pieces into one end-to-end local single-issue tracer bullet that proves RALPH can run from issue input to safe result.

## Acceptance criteria

- [ ] Running AI Code with one fake/provided issue creates a safe worktree.
- [ ] RALPH starts a local sandbox adapter.
- [ ] RALPH resolves and preprocesses a prompt.
- [ ] RALPH runs a fake/test agent.
- [ ] RALPH detects <promise>COMPLETE</promise>.
- [ ] RALPH runs pytest.
- [ ] RALPH commits only after tests pass.
- [ ] RALPH preserves worktree on failure.
- [ ] RALPH returns a clear result status.

## Blocked by

- Blocked by `issues/024-commit-successful-work-and-preserve-failed-or-dirty-work.md`
- Blocked by `issues/025-add-display-and-logging-phases.md`
- Blocked by `issues/026-add-configured-secret-redaction.md`

## User stories addressed

- User story 1
- User story 3
- User story 4
- User story 9
- User story 10
- User story 15
- User story 16
- User story 17
- User story 18
- User story 19

## Assumptions

- None

## Open questions

- None

## Notes

- None
