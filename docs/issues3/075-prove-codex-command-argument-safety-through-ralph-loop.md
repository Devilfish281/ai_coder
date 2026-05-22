# Prove Codex command argument safety through RALPH loop

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_4.md`

## Type

AFK

## Human decision needed

None.

## What to build

Add the stricter command-safety proof through the full RALPH path.

Provider-level command-safety tests are useful but not sufficient. This test proves that the issue title, body, labels, Windows paths, and shell-looking text do not leak into Codex command arguments when the full RALPH loop is used.

## Acceptance criteria

- [ ] Command args include only safe provider command pieces, flags, config values, paths, and the stdin marker.
- [ ] Command args do not include the full issue title.
- [ ] Command args do not include the full issue body.
- [ ] Command args do not include issue labels.
- [ ] Command args do not include shell-looking issue text.
- [ ] stdin text contains the final preprocessed prompt.
- [ ] stdin text contains the issue content as inert text.

## Blocked by

- Blocked by `issues/074-prove-codex-stdin-prompt-delivery-through-ralph-loop.md`

## User stories addressed

- User story 11
- User story 23
- User story 24

## Assumptions

- The fake sandbox can capture the command args and stdin text for assertions.

## Open questions

None

## Notes

This issue focuses on safety. Do not combine it with success commit assertions.
