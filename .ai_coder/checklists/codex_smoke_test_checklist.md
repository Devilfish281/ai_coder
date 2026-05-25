# AI Code manual Codex smoke-test checklist

## Purpose

Use this checklist to grade the Phase 3 real-worktree Codex smoke proof.

The prompt tells Codex what tiny code change to make. This checklist tells the developer how to verify that the full RALPH workflow behaved safely.

## Prerequisites

- [ ] Issue #77 is complete.
- [ ] `poetry run pytest` passed before this smoke proof.
- [ ] Issue #49 is the selected smoke-test issue.
- [ ] Issue #49 uses the `tracer bullet` label when live GitHub issue reading is used.
- [ ] Pull request creation is disabled or dry-run.
- [ ] GitHub issue closing is disabled or dry-run.

## Setup configuration checks

- [ ] `setup_config.py` selects `CodexProvider`.
- [ ] `RALPH_AGENT` is `codex` or the CLI passes `--agent codex`.
- [ ] `RALPH_SANDBOX_MODE` is `local` or the CLI passes `--sandbox local`.
- [ ] `CODEX_COMMAND` points to the local Codex executable command.
- [ ] `PROMPT_PATH` or `--prompt-path` uses `.ai-code/prompts/codex_smoke_test.md`.
- [ ] `DRY_RUN` is enabled or the CLI passes `--dry-run`.

## Manual invocation command shape

The official Issue 078 smoke-proof invocation style is a documented manual command using the existing CLI and setup configuration values.

Do not add a dedicated CLI flag or pytest marker for this slice.

Example Windows PowerShell shape:

```powershell
$env:RALPH_AGENT = "codex"
$env:RALPH_SANDBOX_MODE = "local"
$env:CODEX_COMMAND = "codex"
$env:DRY_RUN = "true"

poetry run ai-coder --agent codex --sandbox local --dry-run --issue-number 49 --issue-title "Change startup log message to all caps" --issue-body "Tiny Phase 3 Codex smoke proof." --label "tracer bullet" --prompt-path .ai-code/prompts/codex_smoke_test.md
```
