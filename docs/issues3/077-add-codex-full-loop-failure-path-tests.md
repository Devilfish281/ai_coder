# Add Codex full-loop failure path tests

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_4.md`

## Type

AFK

## Human decision needed

None.

## What to build

Add the required unsafe-outcome tests for Phase 3.

Phase 3 is not complete if it only proves the happy path. This issue should add full-loop or seam-crossing tests for blocked, incomplete, no-change, failed-test, and preservation behavior.

## Acceptance criteria

- [ ] Codex CLI missing or not ready returns `blocked`.
- [ ] Codex output without `<promise>COMPLETE</promise>` returns `incomplete`.
- [ ] Codex completes but makes no changes returns `no_changes` unless no changes are explicitly allowed.
- [ ] Codex changes code but final pytest fails returns `failed`.
- [ ] Non-zero Codex command failure returns `failed`.
- [ ] Failed, blocked, incomplete, no-change, or dirty worktrees are preserved when required.
- [ ] Result statuses match the PRD result-status contract.

## Blocked by

- Blocked by `issues/076-add-mocked-codex-full-loop-success-proof.md`

## User stories addressed

- User story 17
- User story 18
- User story 23
- User story 26
- User story 27
- User story 30

## Assumptions

- Some tests may use patched seams instead of a real Codex process.

## Open questions

None

## Notes

Prefer a few focused tests over one giant failure test. Keep assertions observable through public results, display output, or sandbox/worktree seams.
