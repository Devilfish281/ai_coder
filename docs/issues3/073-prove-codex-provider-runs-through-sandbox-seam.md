# Prove CodexProvider runs through sandbox seam

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_4.md`

## Type

AFK

## Human decision needed

None.

## What to build

Add the next RALPH-loop proof: CodexProvider must run its command through the sandbox seam.

The test should patch the sandbox command runner so the code path still exercises CodexProvider command construction while avoiding a real model call.

## Acceptance criteria

- [ ] CodexProvider command execution crosses `i_sandboxhandle_run()` or the equivalent sandbox handle seam.
- [ ] Test captures the command sent to the sandbox seam.
- [ ] Command includes non-interactive `codex exec` behavior.
- [ ] Command result from the fake sandbox is used by CodexProvider.
- [ ] The provider is not bypassed by patching too deep inside CodexProvider.
- [ ] Existing sandbox behavior remains unchanged.

## Blocked by

- Blocked by `issues/072-prove-ralph-selects-codex-provider-from-setup-config.md`

## User stories addressed

- User story 4
- User story 12
- User story 23

## Assumptions

- The sandbox handle seam can be patched in tests with monkeypatch or an equivalent test double.

## Open questions

None

## Notes

This issue proves the boundary. It does not need real GitHub, real Codex, or real Docker.
