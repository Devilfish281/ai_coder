# Normalize Codex final message file output

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_4.md`

## Type

AFK

## Human decision needed

None.

## What to build

Implement the first Codex output priority source: final message file output.

When CodexProvider uses an output-last-message path, it should prefer that final message as the completion-readable source and normalize it into provider output/events before the orchestrator sees it.

## Acceptance criteria

- [ ] CodexProvider can read the configured final message file after command execution.
- [ ] Final message file content is preferred over JSONL and stdout when present.
- [ ] Final message file content is normalized into provider-readable output.
- [ ] `<promise>COMPLETE</promise>` in the final message file can drive completion after a successful exit code.
- [ ] Missing final message file falls through to later output sources instead of crashing.
- [ ] Raw full prompt text is not logged.

## Blocked by

- Blocked by `issues/063-document-phase-result-fields-and-early-blocked-none-behavior.md`

## User stories addressed

- User story 23
- User story 25

## Assumptions

- CodexProvider already constructs or can be updated to construct an output-last-message path.

## Open questions

None

## Notes

CodexProvider should own this detail. The orchestrator should not read Codex-specific files directly.
