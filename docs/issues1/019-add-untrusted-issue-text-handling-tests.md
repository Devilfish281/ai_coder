# Add untrusted issue text handling tests

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Add focused tests proving that issue title, issue body, labels, and other external values are treated as inert text and are never executed as shell syntax.

## Acceptance criteria

- [ ] Issue title text containing shell-like syntax is treated as text.
- [ ] Issue body text containing shell-like syntax is treated as text.
- [ ] Labels containing special characters are treated as text.
- [ ] Prompt preprocessing does not execute untrusted text.
- [ ] Tests cover long text and Windows special characters.

## Blocked by

- Blocked by `issues/018-add-sandbox-aware-prompt-preprocessing.md`

## User stories addressed

- User story 11
- User story 20

## Assumptions

- None

## Open questions

- None

## Notes

- None
