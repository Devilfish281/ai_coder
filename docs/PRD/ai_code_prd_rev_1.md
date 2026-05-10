# AI Code PRD

## 1. Product Summary

AI Code is a Python autonomous coding-agent system that helps a solo Python developer on Windows 11 safely work through GitHub issues one at a time.

RALPH is the autonomous coding agent inside AI Code. RALPH selects one actionable issue, creates a safe Git worktree, runs commands through a sandbox seam, uses Codex as the first real AI coding-agent provider, runs tests, commits successful work, and preserves failed work for review.

AI Code must be built in small tracer-bullet slices. Each slice should prove useful behavior end to end before adding more advanced features.

## 2. Primary User

The primary user is a solo Python developer on Windows 11 who wants AI Code to safely work through GitHub issues one at a time.

## 3. Problem Statement

A solo developer has many GitHub issues, but fixing them safely is slow and repetitive. AI Code solves this by giving the developer a careful automation loop that isolates work, runs through clear seams, tests results, and preserves failed work.

## 4. Product Goal

AI Code should behave like a careful junior developer that safely completes one GitHub issue at a time.

RALPH should:

1. Select one actionable issue.
2. Work inside a safe Git worktree.
3. Run commands through a sandbox seam.
4. Use Codex as the first real AI coding-agent provider.
5. Detect completion.
6. Run tests.
7. Commit successful work.
8. Preserve failed or dirty worktrees.
9. Never close an issue until the safe workflow succeeds.

## 5. First Usable Release

The first usable release is a local single-issue tracer bullet.

Release 1 should prove that AI Code can move through the full safe workflow with one issue, even if some modules are still simple, fake, or stubbed.

## 6. Release 1 Success Criteria

Release 1 is successful when AI Code can:

1. Load configuration from `setup_config.py`.
2. Read or receive one GitHub issue.
3. Select one actionable issue.
4. Create a Git worktree.
5. Start a local sandbox adapter.
6. Resolve prompt text from a file or inline prompt.
7. Preprocess the prompt only after the sandbox is ready.
8. Run one fake or test AI coding-agent command through the sandbox seam.
9. Detect `<promise>COMPLETE</promise>`.
10. Run `pytest` through the sandbox seam.
11. Commit successful changes.
12. Preserve the worktree if the run fails or leaves uncommitted changes.
13. Return a clear result object.
14. Log readable progress.

## 7. Future Product Success Criteria

Future AI Code is successful when it can:

1. Read open GitHub issues.
2. Select one or more actionable issues.
3. Create isolated worktrees safely.
4. Run local and Docker bind-mount sandboxes.
5. Support long-running Docker containers.
6. Support multiple AI coding-agent providers.
7. Stream agent output clearly.
8. Detect completion, failure, timeout, and no-progress states.
9. Run tests before commit or issue closure.
10. Preserve failed worktrees.
11. Create pull requests.
12. Close GitHub issues only after tests pass and changes are committed.
13. Scaffold `.ai-code/` workflow templates.
14. Much later, support isolated or cloud sandbox providers.

## 8. Release Phases

### Phase 1 — Local Single-Issue Tracer Bullet

Prove AI Code can complete one safe local issue workflow end to end.

### Phase 2 — Docker Bind-Mount Sandbox

Move command execution from local Windows execution into Docker using a bind-mounted worktree.

### Phase 3 — Real AI Coding-Agent Loop

Run a real agent provider through the sandbox seam and parse output or events.

### Phase 4 — GitHub Issue Automation

Read open GitHub issues, select one actionable issue, and prepare issue-specific prompts.

### Phase 5 — Safe Commit and PR Workflow

Run tests, commit passing changes, preserve dirty worktrees, and later create pull requests.

### Phase 6 — Full `.ai-code/` Workflow Template Scaffolding

Generate workflow templates for common AI Code automation patterns.

### Phase 7 — Long-Running Docker Container

Replace one `docker run --rm` per command with a long-running Docker execution environment.

### Phase 8 — Multi-Agent Workflows

Support planner, implementer, reviewer, and merger-style workflows.

### Phase 9 — Cloud Sandbox Providers

Much later, support isolated or cloud sandbox providers.

## 9. Non-Goals

AI Code is not:

1. A general-purpose operating system automation tool.
2. A replacement for GitHub, Git, Docker, Poetry, or pytest.
3. A fully autonomous production deployment system.
4. A tool that closes GitHub issues without passing tests.
5. A tool that deletes dirty worktrees after failure.
6. A tool that hides agent decisions, commands, or logs from the user.
7. A full autonomous coding platform in Release 1.
8. A cloud-sandbox-first product.

## 10. Final Naming Rules

1. Product/project name: AI Code.
2. Agent name: RALPH.
3. Python package name: `ai_coder`.
4. Future scaffold folder: `.ai-code/`.
5. Do not use outside reference-project names in this PRD.
6. Use “AI Code template scaffolding,” not “RALPH template scaffolding.”
7. Use “workflow template scaffolding,” not names tied to another project.

## 11. Product Identity

AI Code is the software project and product.

RALPH is the autonomous coding agent inside AI Code.

Recommended wording:

> AI Code is a Python autonomous coding-agent system that helps a solo Python developer on Windows 11 safely work through GitHub issues one at a time.
>
> RALPH is the autonomous coding agent inside AI Code.

## 12. Architecture Rules

AI Code must use small, clear Python modules. Each module should hide implementation details behind one or a few public interface seams.

Release 1 may stub some modules, but every tracer-bullet issue should move the project toward the future module structure.

## 13. Design Vocabulary

### Module

Anything with an interface and an implementation.

### Interface

Everything a caller must know to use the module correctly.

### Implementation

The internal code hidden behind the interface.

### Seam

The place where callers cross into the module through the interface.

### Adapter

A concrete thing that satisfies an interface at a seam.

### Depth

How much useful behavior is hidden behind a small interface.

### Leverage

What callers get from depth.

### Locality

What maintainers get from depth.

## 14. Public Interface Naming Rule

Every public module seam must use this naming pattern:

```text
i_<module_name>_<action>()
```

Examples:

```text
i_ralph_run()
i_sandbox_start()
i_sandboxhandle_run()
i_worktree_create()
i_prompt_resolve()
i_prompt_preprocess()
i_orchestrator_run()
i_github_issue_select()
i_test_run()
```

Private helper functions must start with `_`.

Do not expose many public functions.

Prefer a small interface with useful behavior hidden behind it.

## 15. Required Future Core Modules

AI Code should eventually include these core modules:

1. `setup_config.py`
2. `main.py`
3. `ralph.py`
4. `github_issues.py`
5. `worktree_manager.py`
6. `sandbox_provider.py`
7. `agent_provider.py`
8. `orchestrator.py`
9. `completion_detector.py`
10. `prompt_resolver.py`
11. `prompt_preprocessor.py`
12. `test_runner.py`
13. `display.py`
14. `repository_context.py`
15. `template_scaffolder.py`

Long-term isolated/cloud sandbox sync modules may be added later, but they are not near-term requirements.

## 16. Configuration Source of Truth

AI Code must use `setup_config.py` as the final runtime source of truth.

CLI args, `.env` values, and defaults may feed into `setup_config.py`, but AI Code modules should read final runtime values only from `setup_config.py`.

Expected runtime flow:

1. Load `setup_config.py`.
2. Validate values loaded from `.env` and defaults.
3. Parse CLI args.
4. Apply valid CLI args into `setup_config.py`.
5. Validate `setup_config.py` again.
6. Run RALPH using only `setup_config.py` values.

## 17. Configuration Validation Requirements

AI Code must:

1. Load defaults and `.env` values into `setup_config.py`.
2. Validate configuration once before CLI overrides.
3. Parse CLI arguments.
4. Apply valid CLI values into `setup_config.py`.
5. Validate configuration again after CLI overrides.
6. Validate Docker settings only when Docker sandbox mode is selected.
7. Validate Codex settings only when `CodexProvider` is selected.
8. Return clear user-facing errors for invalid values.
9. Avoid mutating `setup_config.py` with invalid CLI values.
10. Keep `setup_config.py` as the final runtime source of truth.

## 18. Safety Requirements

AI Code must:

1. Never modify the host repo directly when a worktree is required.
2. Create a safe worktree before agent code edits.
3. Preserve the worktree if the run fails.
4. Preserve the worktree if uncommitted changes exist.
5. Run tests before committing or closing an issue.
6. Never close a GitHub issue unless tests pass and a fix is committed.
7. Log enough information for the user to understand what happened.
8. Redact configured secret values from logs.
9. Keep sandbox execution behind `i_sandboxhandle_run()`.
10. Keep final runtime configuration behind `setup_config.py`.

## 19. Testing Requirements

AI Code must:

1. Use `pytest` as the default test runner.
2. Run tests through the sandbox seam, not directly from `ralph.py`.
3. Treat failing tests as a failed issue attempt.
4. Preserve the worktree when tests fail.
5. Only commit successful changes after required tests pass.
6. Prefer behavior tests that cross public interface seams.
7. Avoid testing private helpers unless the behavior is small and hard to reach through the public seam.
8. Keep tests as the source of truth for expected behavior.

## 20. Completion Detection Requirements

AI Code must:

1. Detect `<promise>COMPLETE</promise>` as the primary completion signal.
2. Treat max-iteration reached without completion as incomplete.
3. Treat agent command failure as failed.
4. Treat test failure as failed.
5. Treat no code changes as incomplete unless the issue explicitly required no code change.
6. Return a clear result status such as `complete`, `incomplete`, `failed`, `blocked`, or `no_changes`.
7. Preserve logs and worktree state for failed, blocked, or incomplete runs.

## 21. Result Status Contract

AI Code must return one of these statuses every time it runs.

### `complete`

The run is complete when:

1. The agent signaled `<promise>COMPLETE</promise>`.
2. Required tests passed.
3. Successful changes were committed.

### `incomplete`

The run is incomplete when:

1. The agent did not signal completion before max iterations.
2. The run stopped without a final successful result.

### `failed`

The run failed when:

1. The agent command failed.
2. The sandbox command failed.
3. Required tests failed.
4. Git commit failed.

### `blocked`

The run is blocked when RALPH cannot continue because of:

1. Missing configuration.
2. Missing Docker image.
3. Missing credentials.
4. No actionable issue.
5. Unsafe repository state.

### `no_changes`

The run produced no changes when:

1. The agent completed.
2. No code changes were detected.

This may be acceptable only if the issue explicitly required no code change.

## 22. GitHub Issue Handling Requirements

AI Code must:

1. Read open GitHub issues.
2. Select one actionable issue at a time.
3. Ignore or skip issues that are too vague, blocked, already assigned, or unsafe.
4. Use issue number, title, body, and labels when building the agent prompt.
5. Keep issue selection behind `i_github_issue_select()`.
6. Never close an issue before tests pass and changes are committed.
7. In a future release, create a PR or close the issue only after the safe workflow succeeds.

## 23. Prompt Handling Requirements

AI Code must:

1. Accept prompt text from an inline prompt or a prompt file.
2. Resolve prompt text before running the agent.
3. Preprocess the prompt only after the sandbox is ready.
4. Replace safe placeholders such as issue number, issue title, issue body, branch name, and worktree path.
5. Keep prompt resolving behind `i_prompt_resolve()`.
6. Keep prompt preprocessing behind `i_prompt_preprocess()`.
7. Treat issue title, issue body, labels, and other external values as inert text.
8. Never execute shell-command syntax that came from untrusted issue data.
9. Keep command expansion limited, explicit, and test-covered.

## 24. Worktree Requirements

AI Code must:

1. Create a Git worktree before agent code edits.
2. Use one worktree per issue attempt.
3. Use a branch name that is traceable to the issue or run.
4. Keep worktree creation behind `i_worktree_create()`.
5. Keep worktree cleanup behind `i_worktree_cleanup()`.
6. Preserve the worktree if the run fails.
7. Preserve the worktree if uncommitted changes exist.
8. Remove the worktree only when the run succeeds and the worktree is clean.
9. Show the preserved worktree path to the user.
10. Support Windows path behavior as a first-class requirement.

## 25. Sandbox Requirements

AI Code must:

1. Run project commands through `i_sandboxhandle_run()`.
2. Support local execution for the first tracer bullet.
3. Support Docker bind-mount execution as the next major sandbox mode.
4. Use one `docker run --rm` per command in the first Docker version.
5. Check the configured Docker image once when creating the Docker sandbox handle.
6. Make the Docker image name configurable through `setup_config.py`.
7. Default the Docker image to `ai-code-ralph-test-runtime:latest`.
8. Avoid auto-building the Docker image in the first Docker version.
9. Pass normal Docker env vars through a clear env seam.
10. Pass secret-like Docker env vars through a separate secret env seam.
11. Redact configured secret env values from logs.
12. Keep cloud sandbox providers as far-future work.

## 26. Docker Bind-Mount Behavior

In Docker bind-mount mode, AI Code must:

1. Create or receive a host Git worktree path.
2. Mount that worktree into the Docker container.
3. Set the container working directory to the mounted repo path.
4. Run commands inside the mounted worktree.
5. Let file edits made inside Docker appear in the host worktree.
6. Avoid a separate sync module for this mode.

## 27. Windows Docker Mount Requirements

AI Code must:

1. Support Windows 11 as the primary development target.
2. Convert or patch host paths so Docker bind mounts work correctly from Windows.
3. Treat Git worktree `.git` mount behavior as a special case when needed.
4. Keep Windows mount patching behind a small utility seam.
5. Test Windows path conversion behavior separately from Docker command execution.
6. Avoid spreading Windows path logic across `ralph.py`, `orchestrator.py`, or agent providers.

## 28. Secret and Environment Variable Requirements

AI Code must:

1. Define normal Docker env allowlists in `setup_config.py`.
2. Define secret Docker env allowlists separately in `setup_config.py`.
3. Keep the default secret allowlist empty or very small.
4. Not include `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GH_TOKEN` in the default secret allowlist during the early Docker tracer bullet.
5. Pass Docker env vars as `-e NAME=value`.
6. Skip missing normal env vars, except `PYTHONUNBUFFERED`, which may default to `1`.
7. Raise a clear error when an allowlisted secret env var is missing or empty.
8. Redact only configured secret env values from logs.
9. Avoid auto-detecting secret-looking names in the first version.
10. Keep env handling behind clear seams so Docker env vars can later be replaced by a stronger secret provider.

## 29. Agent Provider Requirements

AI Code must:

1. Keep AI coding-agent commands behind an agent provider seam.
2. Support a simple fake/test agent first.
3. Support Codex as the first real AI coding-agent provider.
4. Support other providers later, such as Claude Code, OpenCode, or additional command-line coding agents.
5. Let each provider define how to build its command.
6. Let each provider define how to pass prompt text to the agent.
7. Let each provider define how to parse output.
8. Return normalized stream events such as `text`, `tool_call`, `result`, `error`, and `session_id` when supported.
9. Never let `ralph.py` hard-code one provider’s command details.
10. Allow provider-specific env needs to flow through `setup_config.py` and the sandbox env seams.
11. Keep provider output visible through the display/logging system.

## 30. CodexProvider Requirements

Codex is the first real AI coding-agent provider for AI Code.

CodexProvider must:

1. Start with non-interactive `codex exec`.
2. Build the Codex command inside the agent provider seam.
3. Run Codex through `i_sandboxhandle_run()`.
4. Capture stdout, stderr, and exit code.
5. Prefer structured output such as JSONL when available.
6. Fall back to plain stdout parsing when structured output is unavailable.
7. Return normalized RALPH result events.
8. Keep interactive Codex support as a future feature.

## 31. CodexProvider Prompt Delivery Requirement

CodexProvider should pass large prompt text through stdin when supported.

If Codex CLI requires prompt text as a command argument for a specific mode, CodexProvider must:

1. Keep command construction isolated inside `agent_provider.py`.
2. Avoid logging the raw full prompt.
3. Avoid logging secret values.
4. Keep issue title, issue body, and labels treated as inert text.
5. Add tests proving long prompts and special characters work on Windows.

## 32. CodexProvider Output Requirement

CodexProvider should prefer Codex CLI structured output such as JSONL when available.

If JSONL is unavailable or disabled, CodexProvider may fall back to plain stdout parsing, but the provider must still return a normalized result object.

## 33. Display and Logging Requirements

AI Code must:

1. Show the selected issue number and title.
2. Show the current phase: setup, worktree, sandbox, prompt, agent, tests, commit, cleanup.
3. Show agent output in a readable way.
4. Show command failures with stdout, stderr, and exit code.
5. Show when tests pass or fail.
6. Show the commit hash when changes are committed.
7. Show the preserved worktree path when work is preserved.
8. Redact configured secret values from logs.
9. Avoid logging full secret env values.
10. Avoid logging huge prompt bodies by default.
11. Keep display behavior behind `display.py`.

## 34. Repository Context Requirements

AI Code must:

1. Detect the repository root.
2. Detect the active branch.
3. Detect whether the repo has uncommitted changes before starting.
4. Detect package manager and test command when possible.
5. Prefer configured commands from `setup_config.py` over guessing.
6. Include useful repo context in the agent prompt.
7. Keep repository inspection behind `repository_context.py`.
8. Avoid scanning huge folders such as `.git`, `.venv`, `node_modules`, build outputs, and cache folders.
9. Keep repository context small enough to be useful in prompts.
10. Never send secret files or `.env` contents into prompts by default.

## 35. Repository Context Exclusion Requirements

When building repository context, AI Code should exclude by default:

1. `.git/`
2. `.venv/`
3. `venv/`
4. `__pycache__/`
5. `.pytest_cache/`
6. `.mypy_cache/`
7. `.ruff_cache/`
8. `node_modules/`
9. `dist/`
10. `build/`
11. `.env`
12. `.env.*`
13. Large binary files
14. Generated logs
15. Generated reports unless explicitly requested

## 36. Future / Long-Term Sync Capabilities

Explicit sync behavior is not required for Release 1 or the early Docker bind-mount sandbox.

For local execution and Docker bind-mount execution, the Git worktree is the shared working directory.

Explicit sync behavior is only needed later when AI Code supports isolated or cloud sandboxes where the sandbox filesystem is not the same as the host worktree.

Future sync may include:

1. `i_sync_in()`
2. `i_sync_out()`
3. Copy-in and copy-out for isolated sandboxes.
4. Commit extraction from remote or cloud sandboxes.
5. Safe merge or PR creation after tests pass.

## 37. AI Code Template Scaffolding

AI Code template scaffolding is a future feature.

AI Code template scaffolding should generate a `.ai-code/` folder for project-specific automation files.

Reason:

AI Code is the product name. RALPH is the agent inside AI Code, so the scaffold folder should use the product name instead of the agent name.

Example future scaffold:

```text
.ai-code/
  Dockerfile
  .env.example
  ai_code_config.toml
  run.py
  prompt.md
  implement_prompt.md
  review_prompt.md
  merge_prompt.md
  CODING_STANDARDS.md
```

Future template types may include:

1. Simple one-agent loop.
2. Sequential implementation and review loop.
3. Planning plus implementation loop.
4. Planning, implementation, review, and merge loop.

These templates should generate Python files and AI Code configuration files.

## 38. Coding Standards

AI Code must:

1. Use Python.
2. Use Poetry.
3. Use pytest.
4. Support Windows 11 as the primary OS target.
5. Keep modules under `src/ai_coder/`.
6. Keep tests under `tests/`.
7. Prefer small tracer-bullet slices.
8. Avoid rewriting the whole project for one issue.
9. Avoid changing unrelated files.
10. Avoid new dependencies unless clearly required.
11. Prefer clear names over clever abstractions.
12. Keep public interfaces small.
13. Hide implementation details behind module seams.
14. Write tests for behavior, not private implementation details.
15. Preserve existing public interface functions unless an issue explicitly requires a rename.

## 39. Documentation Requirements

AI Code must include documentation that explains:

1. What AI Code does.
2. What problem AI Code solves.
3. How to install the project.
4. How to run the local tracer bullet.
5. How to run tests.
6. How `setup_config.py` works.
7. How the sandbox seam works.
8. How the worktree safety model works.
9. How CodexProvider works when added.
10. How to add future agent providers.
11. How to add future sandbox providers.
12. What is in scope for the current release.
13. What is intentionally future work.

## 40. Acceptance Criteria Requirements

Each release phase must define acceptance criteria that are:

1. Specific.
2. Testable.
3. Small enough to verify with pytest, CLI output, Git state, or file existence.
4. Focused on behavior, not internal implementation details.
5. Written before or alongside GitHub issues created from this PRD.

## 41. Phase 1 Acceptance Criteria

Phase 1 is accepted when:

1. Running AI Code with one fake issue creates a safe worktree.
2. RALPH starts a local sandbox adapter.
3. RALPH resolves and preprocesses a prompt.
4. RALPH runs a fake or test agent through the sandbox seam.
5. RALPH detects `<promise>COMPLETE</promise>`.
6. RALPH runs `pytest` through the sandbox seam.
7. RALPH commits only after tests pass.
8. RALPH preserves the worktree on failure.
9. RALPH returns a clear result status.

## 42. Open Questions and Decision Log

### Locked Decisions

1. Product name is AI Code.
2. RALPH is the autonomous coding agent inside AI Code.
3. Primary user is a solo Python developer on Windows 11.
4. Release 1 is a local single-issue tracer bullet.
5. Docker bind-mount sandbox is Phase 2.
6. Cloud sandboxes are far-future.
7. Codex is the first real agent provider.
8. CodexProvider starts with non-interactive `codex exec`.
9. CodexProvider prefers JSONL or structured output when available.
10. CodexProvider should prefer stdin for large prompt text when supported.
11. `setup_config.py` is the final runtime source of truth.
12. `.ai-code/` is the future scaffold folder.
13. Full workflow template scaffolding is a future feature.
14. Explicit sync behavior is only needed later for isolated or cloud sandboxes.
15. The PRD must not use outside reference-project names.

### Open Questions

1. What exact Codex CLI flags should be used for the first CodexProvider implementation?
2. Should the first real CodexProvider run outside Docker first, or only inside Docker bind-mount mode?
3. What is the first exact GitHub issue that should implement CodexProvider?
4. What result event schema should CodexProvider return?
5. What should the first `.ai-code/` template include?
6. When should pull request creation become part of the workflow?
7. When should automatic GitHub issue closure be allowed?

### Deferred Decisions

1. Cloud sandbox provider choice.
2. Long-running Docker container design.
3. Multi-agent workflow design.
4. Explicit sync-in and sync-out implementation.
5. Template scaffolding format and command names.

## 43. Near-Term Implementation Order

Recommended near-term order:

1. Finish the local single-issue tracer bullet.
2. Strengthen worktree safety.
3. Strengthen sandbox seams.
4. Add Docker bind-mount sandbox.
5. Add Docker image validation.
6. Add normal and secret env seams.
7. Add command redaction.
8. Add CodexProvider with fake-output tests first.
9. Add CodexProvider non-interactive execution.
10. Add completion detection and result statuses.
11. Add safe commit behavior.
12. Add GitHub issue read/select behavior.

## 44. Release 1 Out of Scope

Release 1 does not include:

1. Multiple issues at once.
2. Multiple real AI agents.
3. Long-running Docker containers.
4. Cloud sandbox providers.
5. Automatic Docker image building.
6. Automatic GitHub issue closing.
7. Pull request creation.
8. Explicit sync-in and sync-out.
9. Full workflow template scaffolding.
10. Multi-agent workflows.

## 45. Summary

AI Code is a Python autonomous coding-agent system for safely working through GitHub issues one at a time.

RALPH is the agent inside AI Code.

The product must prioritize safety, clarity, small module seams, Windows 11 support, tests, worktree preservation, and readable logs.

The first release should be a small local tracer bullet.

The future product should grow gradually into Docker execution, CodexProvider, GitHub automation, safe commits, workflow templates, long-running containers, multi-agent workflows, and much later isolated or cloud sandbox providers.
