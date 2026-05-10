# Add CodexProvider plain stdout fallback parsing

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Fall back to plain stdout parsing when structured Codex output is unavailable.

## Acceptance criteria

- [ ] Plain stdout fallback can detect useful text output.
- [ ] Completion detection can still find <promise>COMPLETE</promise>.
- [ ] Fallback parsing errors are visible.
- [ ] Tests cover stdout-only provider output.

## Blocked by

- Blocked by `issues/041-add-codexprovider-structured-output-parsing.md`

## User stories addressed

- User story 14
- User story 15

## Assumptions

- None

## Open questions

- None

## Notes

- None
