# Expose cleanup result on RalphResult

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_4.md`

## Type

AFK

## Human decision needed

None.

## What to build

Expose the cleanup or preservation phase result through the public RALPH result object.

Phase 3 needs this field so success, failure, blocked, dirty, and preserved-worktree outcomes can be verified through `i_ralph_run()` without inspecting private helpers.

## Acceptance criteria

- [ ] `RalphResult` exposes `cleanup_result` as an optional field.
- [ ] `cleanup_result` defaults to `None`.
- [ ] Successful runs populate `cleanup_result` when cleanup ran.
- [ ] Cleanup result shows whether the worktree was removed when safe.
- [ ] Failure or dirty-worktree paths populate `cleanup_result` when cleanup/preservation ran.
- [ ] Early returns before a worktree or cleanup phase leave `cleanup_result` as `None`.

## Blocked by

- Blocked by `issues/061-expose-sync-result-on-ralph-result.md`

## User stories addressed

- User story 17
- User story 18
- User story 23
- User story 29
- User story 30

## Assumptions

- A cleanup result object already exists or equivalent cleanup/preservation data is already produced by the RALPH workflow.

## Open questions

None

## Notes

This slice supports later failure-path proof because preservation decisions become visible through the public result.
