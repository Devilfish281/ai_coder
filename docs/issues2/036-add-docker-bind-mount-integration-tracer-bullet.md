# Add Docker bind-mount integration tracer bullet

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Connect Docker bind-mount mode end to end so a command can run in Docker, edit the mounted worktree, return results, and preserve failed work.

## Acceptance criteria

- [ ] Docker mode can run a command through the sandbox seam.
- [ ] The command runs in /workspace.
- [ ] File changes appear in the host worktree.
- [ ] stdout, stderr, and exit code are returned.
- [ ] Secret values are redacted from logs.
- [ ] Dirty or failed worktrees are preserved.
- [ ] Integration coverage proves the Docker flow at least with patched subprocess/image checks.

## Blocked by

- Blocked by `issues/030-add-docker-bind-mount-command-execution.md`
- Blocked by `issues/031-add-windows-docker-path-conversion-utility.md`
- Blocked by `issues/032-handle-git-worktree-git-mount-behavior-for-docker.md`
- Blocked by `issues/033-add-docker-normal-env-allowlist.md`
- Blocked by `issues/034-add-docker-secret-env-allowlist-and-missing-secret-errors.md`
- Blocked by `issues/035-add-docker-command-redaction-utility.md`

## User stories addressed

- User story 4
- User story 5
- User story 6
- User story 20

## Assumptions

- None

## Open questions

- None

## Notes

- None
