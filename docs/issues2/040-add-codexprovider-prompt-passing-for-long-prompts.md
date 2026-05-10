# Add CodexProvider prompt passing for long prompts

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Pass prompt text to Codex in a way that supports large issue bodies and avoids putting full issue bodies directly into command arguments when possible.

## Acceptance criteria

- [ ] CodexProvider prefers stdin for large prompt text when supported.
- [ ] Full GitHub issue bodies are not placed in command args unless no supported alternative exists.
- [ ] Raw full prompts are not logged by default.
- [ ] Tests cover large prompt text and special characters.

## Blocked by

- Blocked by `issues/039-add-codexprovider-non-interactive-execution.md`

## User stories addressed

- User story 9
- User story 12
- User story 13

## Assumptions

- None

## Open questions

- None

## Notes

- None
