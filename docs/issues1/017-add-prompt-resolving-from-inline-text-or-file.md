# Add prompt resolving from inline text or file

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Support resolving agent prompt text from either an inline prompt or a prompt file before the agent runs.

## Acceptance criteria

- [ ] Inline prompt text is supported.
- [ ] Prompt file text is supported when file contents are available.
- [ ] Prompt resolving lives behind i_prompt_resolve().
- [ ] Missing prompt sources produce clear errors.
- [ ] Tests cover inline prompt, file prompt, missing prompt, and large prompt text.

## Blocked by

- Blocked by `issues/016-add-normalized-command-result-contract.md`

## User stories addressed

- User story 9

## Assumptions

- None

## Open questions

- None

## Notes

- None
