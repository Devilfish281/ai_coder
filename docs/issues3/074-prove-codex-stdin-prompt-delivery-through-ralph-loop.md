# Prove Codex stdin prompt delivery through RALPH loop

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_4.md`

## Type

AFK

## Human decision needed

None.

## What to build

Prove that the final preprocessed prompt reaches CodexProvider through stdin in the RALPH loop.

This must show that long issue text is prompt input, not command-line argument text.

## Acceptance criteria

- [ ] RALPH builds or receives issue data with title, body, labels, Windows paths, quotes, and shell-like text.
- [ ] The final preprocessed prompt reaches CodexProvider.
- [ ] The Codex command uses `-` or the configured stdin prompt marker.
- [ ] The fake sandbox receives the full prompt as `stdin_text` or equivalent.
- [ ] The issue body is present in stdin text.
- [ ] The issue body is not inserted into command arguments.
- [ ] Tests cross the RALPH public seam rather than testing only CodexProvider internals.

## Blocked by

- Blocked by `issues/073-prove-codex-provider-runs-through-sandbox-seam.md`

## User stories addressed

- User story 11
- User story 23
- User story 24

## Assumptions

- The sandbox command result or fake runner can capture stdin text.

## Open questions

None

## Notes

Use inert issue data. Do not execute shell-looking issue text.
