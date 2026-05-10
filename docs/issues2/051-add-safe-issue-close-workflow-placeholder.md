# Add safe issue close workflow placeholder

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Add a future-safe issue close workflow placeholder that never closes an issue before tests pass and changes are committed.

## Acceptance criteria

- [ ] Issue close behavior is disabled unless explicitly configured.
- [ ] Close workflow checks completion, tests, and commit success.
- [ ] Failed or incomplete runs never close issues.
- [ ] The user sees what would happen in dry-run/placeholder mode.
- [ ] Tests cover allowed and blocked close paths.

## Blocked by

- Blocked by `issues/049-confirm-safe-pr-and-close-policy.md`

## User stories addressed

- User story 1
- User story 16

## Assumptions

- None

## Open questions

- None

## Notes

- None
