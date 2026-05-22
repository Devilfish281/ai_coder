# Add Codex preflight provider and sandbox checks

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_4.md`

## Type

AFK

## Human decision needed

None.

## What to build

Add the first read-only Codex preflight checks.

Before the real Codex smoke proof can run, RALPH should verify that configuration selects CodexProvider and uses the expected local sandbox mode for the first Phase 3 proof. These checks should report blocked when the run is not configured for the intended Codex proof.

## Acceptance criteria

- [ ] Preflight verifies configured agent provider is Codex.
- [ ] Preflight verifies configured sandbox mode is local for the first Codex smoke proof.
- [ ] Provider mismatch returns a blocked result with a clear message.
- [ ] Sandbox mismatch returns a blocked result with a clear message.
- [ ] Preflight does not call the model.
- [ ] Preflight does not edit files.
- [ ] Preflight does not create commits, pull requests, or close issues.

## Blocked by

- Blocked by `issues/063-document-phase-result-fields-and-early-blocked-none-behavior.md`

## User stories addressed

- User story 23
- User story 27

## Assumptions

- The project already has setup_config.py or an equivalent final runtime configuration object.

## Open questions

None

## Notes

Keep this preflight read-only and small. Do not start Codex from this issue.
