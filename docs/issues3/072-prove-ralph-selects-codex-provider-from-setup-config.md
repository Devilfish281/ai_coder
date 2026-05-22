# Prove RALPH selects CodexProvider from setup_config

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_4.md`

## Type

AFK

## Human decision needed

None.

## What to build

Add a focused RALPH-loop test proving CodexProvider is selected from final runtime configuration.

This is the first full-loop Phase 3 proof slice. It should cross the public RALPH seam and show that setup_config.py drives provider selection without hard-coding Codex in the orchestrator.

## Acceptance criteria

- [ ] Test config selects `codex` as the agent provider.
- [ ] `i_ralph_run()` uses the provider creation seam.
- [ ] RALPH creates CodexProvider or the configured Codex adapter.
- [ ] Provider selection is observable through patched public seams or returned diagnostics.
- [ ] Fake/test providers still work where configured.
- [ ] Existing provider-selection behavior remains backward-compatible.

## Blocked by

- Blocked by `issues/063-document-phase-result-fields-and-early-blocked-none-behavior.md`

## User stories addressed

- User story 7
- User story 12
- User story 23

## Assumptions

- The codebase already has an agent provider seam and setup_config-driven provider selection, or this issue adds the smallest missing connection.

## Open questions

None

## Notes

Do not run real Codex in this issue. Patch at public seams.
