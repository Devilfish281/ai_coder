# Add CodexProvider stream event normalization

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Normalize provider output into stream events such as text, tool call, result, error, and session id when supported.

## Acceptance criteria

- [ ] Text events are represented.
- [ ] Tool-call-like events are represented when available.
- [ ] Result and error events are represented.
- [ ] Session id is preserved when available.
- [ ] Display/logging can consume normalized events.

## Blocked by

- Blocked by `issues/041-add-codexprovider-structured-output-parsing.md`
- Blocked by `issues/042-add-codexprovider-plain-stdout-fallback-parsing.md`

## User stories addressed

- User story 14
- User story 19

## Assumptions

- None

## Open questions

- None

## Notes

- None
