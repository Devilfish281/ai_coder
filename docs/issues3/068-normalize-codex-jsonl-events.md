# Normalize Codex JSONL events

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_4.md`

## Type

AFK

## Human decision needed

None.

## What to build

Implement the second Codex output priority source: structured JSONL events.

When the final message file is unavailable, CodexProvider should parse supported JSONL output and normalize useful text/result/error/session information for the orchestrator.

## Acceptance criteria

- [ ] CodexProvider parses newline-delimited JSON output when present.
- [ ] Text-like events are normalized into provider events or output text.
- [ ] Result-like events are normalized into provider events or output text.
- [ ] Error-like events are surfaced as diagnostics or normalized error events.
- [ ] Session id information is preserved when available.
- [ ] Malformed lines are handled by later malformed-JSONL behavior and are not silently hidden.

## Blocked by

- Blocked by `issues/067-normalize-codex-final-message-file-output.md`

## User stories addressed

- User story 23
- User story 25

## Assumptions

- The current provider event model supports text/result/error/session-style events or equivalent normalized output.

## Open questions

None

## Notes

Keep parsing tolerant enough for provider evolution, but do not make the orchestrator depend on raw Codex event shapes.
