# Add repository clean-state guard

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Detect whether the main repository has uncommitted changes before starting work so RALPH does not proceed from an unsafe repo state.

## Acceptance criteria

- [ ] Dirty main repo state is detected before worktree creation.
- [ ] Clean main repo state allows work to proceed.
- [ ] Unsafe repo state returns a clear blocked result.
- [ ] The user sees enough information to understand the blocked state.
- [ ] Tests cover clean, dirty, and detection-failure cases.

## Blocked by

- Blocked by `issues/006-add-repository-root-and-branch-discovery.md`

## User stories addressed

- User story 3
- User story 17
- User story 18

## Assumptions

- None

## Open questions

- None

## Notes

- None
