# AI Code scaffold

This folder contains project-specific AI Code workflow scaffolding.

RALPH is the coding agent inside AI Code. These files are safe text templates for human review before future automation uses them.

## Files

- `prompts/implementation.md` describes how implementation work should be guided.
- `prompts/review.md` describes how review work should be guided.
- `prompts/merge.md` describes how merge preparation should be guided.
- `prompts/codex_smoke_test.md` tells Codex what tiny Issue #49 smoke-test change to make.
- `checklists/codex_smoke_test_checklist.md` tells the developer how to grade the real-worktree Codex smoke proof.
- `standards/coding-standards.md` records local coding expectations.
- `.env.example` documents safe example settings only.
- `Dockerfile` is a starter Docker runtime template for project-specific experiments.

## Safe extension points

Use this folder for safe extension points that are specific to one project.

Good scaffold extensions include:

- new prompt templates,
- project coding standards,
- project review checklists,
- local Docker runtime notes,
- safe example configuration values.

Keep scaffold files small, readable, and reviewable.

## Safety rules

- Do not store real secrets in this folder.
- Do not store real API keys in `.env.example`.
- Do not copy `.env` contents into scaffold files.
- Treat generated prompt templates as text for human review.
- Keep issue title, issue body, and labels inert when they are inserted into prompts.
- Do not claim future automation is available until tests prove it.

## Prompt templates

`prompts/implementation.md` is for implementation work.

`prompts/review.md` is for review work.

`prompts/merge.md` is for merge preparation.

`prompts/codex_smoke_test.md` is for the Phase 3 Codex smoke proof only.

The Codex smoke prompt tells Codex what tiny Issue #49 startup-log change to make.

The Codex smoke checklist tells the developer how to grade the real RALPH worktree flow under `.ai_coder/ai_coder_worktrees/`.

The smoke proof must not create a pull request.

The smoke proof must not close a GitHub issue.

When adding a new prompt template, also add or update scaffold tests so the generated file is covered.

## Codex smoke proof

Use `prompts/codex_smoke_test.md` when manually running the Phase 3 Codex smoke proof.

Use `checklists/codex_smoke_test_checklist.md` to grade the real-worktree smoke proof after the run.

The prompt tells Codex what to do.

The checklist tells the developer how to grade the real-worktree smoke proof.

The smoke proof should use a RALPH worktree under `.ai_coder/ai_coder_worktrees/`.

The smoke proof must not create a PR.

The smoke proof must not close a GitHub issue.

This scaffold documents the manual proof artifacts. It does not claim the future smoke proof is fully automated.

## Docker template

`Dockerfile` is a starter runtime template.

Docker bind-mount mode should mount the host worktree at `/workspace`.

The Docker runtime template should not include real secrets.

## Coding standards

`standards/coding-standards.md` records local project rules.

Use this file for project-specific guidance that RALPH should follow during future implementation, review, or merge workflows.

## Secrets

Do not store real secrets in scaffold files.

Use `.env.example` only for safe placeholder names and example values.

## Overwrite behavior

Existing files are skipped by default.

Use overwrite only when you intentionally want to replace existing scaffold files.

Run scaffold with overwrite only after reviewing the existing files:

```powershell
poetry run ai-coder scaffold --repo-path . --overwrite
```
