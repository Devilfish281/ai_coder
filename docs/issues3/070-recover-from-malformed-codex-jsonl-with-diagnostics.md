# Recover from malformed Codex JSONL with diagnostics

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_4.md`

## Type

AFK

## Human decision needed

None.

## What to build

Make malformed Codex JSONL recoverable when another trusted completion source exists.

A bad JSONL line should not automatically fail the run if the final message file or stdout clearly proves completion. It must still be visible as a warning, diagnostic, or normalized error event.

## Acceptance criteria

- [ ] Malformed JSONL plus valid final message can still complete.
- [ ] Malformed JSONL plus valid stdout fallback can still complete.
- [ ] Malformed JSONL is surfaced as a warning, diagnostic, or normalized error event.
- [ ] Malformed JSONL is not silently hidden.
- [ ] Malformed JSONL without any trusted completion source does not produce success.
- [ ] Tests cover at least one malformed JSONL line.

## Blocked by

- Blocked by `issues/069-add-codex-stdout-fallback-and-stderr-diagnostics.md`

## User stories addressed

- User story 23
- User story 25

## Assumptions

- Diagnostics can be represented by existing provider result fields or normalized events.

## Open questions

None

## Notes

This is a resilience slice. Do not weaken the non-zero exit-code rule.
