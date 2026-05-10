# Add display and logging phases

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Add readable progress output for setup, worktree, sandbox, prompt, agent, tests, commit, and cleanup phases.

## Acceptance criteria

- [ ] Each major RALPH phase is displayed.
- [ ] Command failures show stdout, stderr, and exit code.
- [ ] Test pass/fail is visible.
- [ ] Commit hash is visible after success.
- [ ] Preserved worktree path is visible after preservation.
- [ ] Tests cover expected display messages.

## Blocked by

- Blocked by `issues/024-commit-successful-work-and-preserve-failed-or-dirty-work.md`

## User stories addressed

- User story 19

## Assumptions

- None

## Open questions

- None

## Notes

- None
