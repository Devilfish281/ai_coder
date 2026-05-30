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

## Safe Codex command check

Before running RALPH, verify Codex can execute a harmless project inspection command from the project root.

```powershell
codex exec --sandbox workspace-write --color never "Run git status --short and poetry --version. Do not edit files."
```

- [ ] The command runs from the real project root.
- [ ] The command completes without `spawn setup refresh`.
- [ ] `git status --short` output is visible.
- [ ] `poetry --version` output is visible.
- [ ] No files are edited.

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

- [ ] The command uses the existing CLI.
- [ ] The command uses setup configuration values.
- [ ] The command does not create a pull request.
- [ ] The command does not close a GitHub issue.
- [ ] Future automation is left for a later issue.

## Real worktree checks

- [ ] RALPH creates or uses a real worktree.
- [ ] The worktree is under `.ai_coder/ai_coder_worktrees/`.
- [ ] The main project working tree is not edited directly.
- [ ] The preserved or removed worktree path is visible in output.
- [ ] The worktree is under `.ai_coder/ai_coder_worktrees/`.

## Codex command-safety checks

- [ ] CodexProvider runs non-interactive `codex exec`.
- [ ] The Codex command runs through the sandbox seam.
- [ ] The final prompt is passed through stdin.
- [ ] Command args include only safe provider command pieces, flags, config values, paths, and the stdin marker.
- [ ] Command args do not include the full issue title.
- [ ] Command args do not include the full issue body.
- [ ] Command args do not include issue labels.
- [ ] Command args do not include shell-looking issue text.
- [ ] Windows paths, quotes, semicolons, pipes, ampersands, and backticks stay inert in stdin prompt text.

## Baseline pytest checks

- [ ] Baseline pytest runs before Codex changes code.
- [ ] Baseline pytest result is visible through the RALPH result or output.
- [ ] A baseline pytest failure blocks the smoke proof before Codex work is trusted.

## Codex execution checks

- [ ] Codex changes the startup log text to all caps.
- [ ] Codex output includes `<promise>COMPLETE</promise>`.
- [ ] RALPH detects `<promise>COMPLETE</promise>`.
- [ ] Stderr is preserved as diagnostics, not treated as the normal completion source.
- [ ] A non-zero Codex exit code fails the run even if output contains the completion token.

## Final pytest checks

- [ ] Final pytest runs after Codex changes code.
- [ ] Final pytest passes before sync or commit is treated as successful.
- [ ] Final pytest failure returns `failed`.
- [ ] Failed-test worktrees are preserved.

## Sync and commit checks

- [ ] RALPH detects that the worktree changed.
- [ ] RALPH commits only after final tests pass.
- [ ] The result or output exposes the commit hash.
- [ ] No-change completion returns `no_changes` unless no changes were explicitly allowed.

## Cleanup and preservation checks

- [ ] Clean successful worktrees can be removed.
- [ ] Failed worktrees are preserved.
- [ ] Incomplete worktrees are preserved.
- [ ] Blocked worktrees are preserved when a worktree was created.
- [ ] Dirty worktrees are preserved.
- [ ] Preserved worktree paths are visible.

## PR and issue-close safety checks

- [ ] Pull request creation remains disabled or dry-run.
- [ ] No pull request is created by this smoke proof.
- [ ] GitHub issue closing remains disabled or dry-run.
- [ ] No GitHub issue is closed by this smoke proof.
- [ ] Human review is still required before PR creation or issue closing.

## Pass/fail summary

- [ ] PASS: CodexProvider is proven through the real RALPH worktree loop.
- [ ] PASS: Prompt delivery uses stdin and command args stay safe.
- [ ] PASS: Baseline pytest and final pytest are both visible.
- [ ] PASS: The startup log text changed to all caps.
- [ ] PASS: Commit hash visibility is confirmed.
- [ ] PASS: PR creation and issue closing stayed disabled or dry-run.
- [ ] PASS: Failed or dirty worktrees are preserved.
