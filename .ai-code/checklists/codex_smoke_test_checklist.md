# AI Code manual Codex smoke-test checklist

## Purpose

Use this checklist to grade the Phase 3 real-worktree Codex smoke proof.

The prompt tells Codex what tiny code change to make.

This checklist tells the developer how to verify that the full RALPH workflow behaved safely.

This checklist is not a Codex prompt.

## Prerequisites

- [ ] `.ai-code/prompts/codex_smoke_test.md` exists.
- [ ] `.ai-code/checklists/codex_smoke_test_checklist.md` exists.
- [ ] The prompt and checklist are separate files.
- [ ] `codex --version` works in PowerShell.
- [ ] `poetry run pytest` passes before starting the smoke proof.
- [ ] The main repository working tree is clean before starting.
- [ ] Pull request creation is disabled or dry-run.
- [ ] GitHub issue closing is disabled or dry-run.

## Setup configuration checks

- [ ] `.env` sets `RALPH_AGENT=codex`.
- [ ] `.env` sets `RALPH_SANDBOX_MODE=local`.
- [ ] `.env` sets `CODEX_COMMAND=codex`.
- [ ] `.env` sets `PROMPT_PATH=.ai-code/prompts/codex_smoke_test.md`.
- [ ] `.env` sets `DRY_RUN=true`.
- [ ] `.env` sets `RALPH_GITHUB_ISSUE_CLOSE_ENABLED=false`.
- [ ] `setup_config.py` reads the configured agent provider from `RALPH_AGENT`.
- [ ] `setup_config.py` reads the configured sandbox mode from `RALPH_SANDBOX_MODE`.
- [ ] `setup_config.py` reads the configured Codex command from `CODEX_COMMAND`.
- [ ] `setup_config.py` reads the prompt path from `PROMPT_PATH`.
- [ ] `setup_config.py` selects `CodexProvider`.

## Issue input checks

- [ ] The smoke issue data is available through `.env` or live GitHub issue reading.
- [ ] If using `.env` issue input, `ISSUE_NUMBER` is set.
- [ ] If using `.env` issue input, `ISSUE_TITLE` is set.
- [ ] If using `.env` issue input, `ISSUE_BODY` is set.
- [ ] If using `.env` issue input, `LABEL` is set.
- [ ] If using live GitHub issue reading, `GITHUB_REPO` is set.
- [ ] If using live GitHub issue reading, `LABEL` selects the intended smoke issue.
- [ ] The selected issue is small enough for a safe Codex smoke proof.

## Official invocation style

The official Issue 078 smoke-proof invocation style is a documented manual run using the existing RALPH entry point and setup configuration values.

For this project, prefer `.env` configuration instead of command-line variables.

Do not add a new CLI flag for this issue.

Do not add a pytest marker for this issue.

Run RALPH with:

```powershell
poetry run ai-coder
```
