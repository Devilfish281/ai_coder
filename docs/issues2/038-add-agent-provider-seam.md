# Add agent provider seam

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Create the agent provider seam so RALPH does not hard-code one provider's command details.

## Acceptance criteria

- [ ] Agent provider interface supports command construction or execution.
- [ ] Fake/test provider uses the same seam.
- [ ] Provider-specific env needs can flow through setup_config.py and sandbox env seams.
- [ ] Provider output remains visible through display/logging.
- [ ] Tests prove RALPH can run with a provider without knowing provider internals.

## Blocked by

- Blocked by `issues/027-add-release-1-end-to-end-ralph-tracer-bullet.md`

## User stories addressed

- User story 12
- User story 14

## Assumptions

- None

## Open questions

- None

## Notes

- None
