# Expose project setup result on RalphResult

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_4.md`

## Type

AFK

## Human decision needed

None.

## What to build

Expose the project setup phase result through the public RALPH result object.

This is the first small slice of the Phase 3 result-visibility prerequisite. The goal is to make the baseline setup/test phase observable through `i_ralph_run()` without changing the RALPH workflow. The project setup result should be populated only when project setup actually ran and should remain `None` on early blocked paths that stop before project setup.

## Acceptance criteria

- [ ] `RalphResult` exposes `project_setup_result` as an optional field.
- [ ] `project_setup_result` defaults to `None`.
- [ ] Successful RALPH runs populate `project_setup_result`.
- [ ] The populated result exposes whether baseline tests ran.
- [ ] The populated result exposes whether baseline tests passed.
- [ ] Early returns before project setup leave `project_setup_result` as `None`.
- [ ] Existing RALPH behavior does not change.

## Blocked by

None - can start immediately.

## User stories addressed

- User story 23
- User story 29
- User story 30

## Assumptions

- `ProjectSetupResult` already exists in the codebase or equivalent setup result data is already produced by the RALPH workflow.

## Open questions

None

## Notes

Keep this as a visibility-only change. Do not change CodexProvider, worktree behavior, or sync behavior.
