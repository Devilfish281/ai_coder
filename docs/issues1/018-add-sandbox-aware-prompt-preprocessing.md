# Add sandbox-aware prompt preprocessing

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Preprocess prompt placeholders only after sandbox and worktree context are ready, so placeholders can safely include issue, branch, and worktree values.

## Acceptance criteria

- [ ] Prompt preprocessing runs after sandbox/worktree context exists.
- [ ] Safe placeholders can be replaced for issue number, issue title, issue body, labels, branch name, and worktree path.
- [ ] Prompt preprocessing lives behind i_prompt_preprocess().
- [ ] Unrecognized placeholders are handled predictably.
- [ ] Tests cover placeholder replacement and missing values.

## Blocked by

- Blocked by `issues/017-add-prompt-resolving-from-inline-text-or-file.md`

## User stories addressed

- User story 10
- User story 11

## Assumptions

- None

## Open questions

- None

## Notes

- None
