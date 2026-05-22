# Add Codex stdout fallback and stderr diagnostics

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_4.md`

## Type

AFK

## Human decision needed

None.

## What to build

Implement the third Codex output priority source and stderr handling rule.

If no final message file or usable JSONL source exists, CodexProvider should fall back to plain stdout. stderr should be preserved for diagnostics but should not be treated as the normal completion source.

## Acceptance criteria

- [ ] CodexProvider falls back to stdout when final message and structured output are unavailable.
- [ ] `<promise>COMPLETE</promise>` in stdout can drive completion after a successful exit code.
- [ ] stderr is preserved in diagnostics.
- [ ] stderr is not treated as the normal completion source.
- [ ] Command result stdout, stderr, and exit code remain visible through provider result data.
- [ ] Tests cover final-message missing, JSONL missing, and stdout fallback behavior.

## Blocked by

- Blocked by `issues/068-normalize-codex-jsonl-events.md`

## User stories addressed

- User story 23
- User story 25

## Assumptions

- Command results already include stdout, stderr, and exit code.

## Open questions

None

## Notes

This finishes the output priority chain: final message file, JSONL, stdout, stderr diagnostics.
