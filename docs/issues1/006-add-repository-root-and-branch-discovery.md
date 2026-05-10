# Add repository root and branch discovery

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Add repository inspection that detects the repository root and active branch so RALPH can report context and prepare safe worktrees.

## Acceptance criteria

- [ ] Repository root can be detected from the current working directory.
- [ ] Active branch can be detected.
- [ ] Failures return clear blocked-style errors.
- [ ] Repository inspection is behind a clear responsibility.
- [ ] Tests cover normal repo, nested path, and non-repo behavior.

## Blocked by

- Blocked by `issues/002-define-setup-config-py-runtime-model.md`

## User stories addressed

- User story 21

## Assumptions

- None

## Open questions

- None

## Notes

- None
