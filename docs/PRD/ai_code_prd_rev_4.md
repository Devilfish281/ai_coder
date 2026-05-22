# PRD: AI Code

> Publication status: Not published: issue tracker access or triage label configuration was not provided.

## Problem Statement

A solo Python developer on Windows 11 needs a safer and more repeatable way to work through GitHub issues one at a time.

Today, the developer must manually read an issue, decide whether it is actionable, create a safe branch or worktree, prepare a prompt, run an AI coding tool, review changes, run tests, commit only safe work, and preserve failed attempts for debugging.

This workflow is valuable but repetitive. It is also risky if an AI coding agent edits the main working tree directly, hides command output, closes issues too early, leaks secrets in logs, or deletes dirty work after a failure.

AI Code solves this by providing a Python autonomous coding-agent system. RALPH is the agent inside AI Code. RALPH should behave like a careful junior developer: pick one issue, work in an isolated worktree, use sandboxed command execution, run tests, commit only successful work, and preserve failed work for human review.

## Solution

AI Code will provide a Python system for safely automating GitHub issue work.

RALPH, the autonomous coding agent inside AI Code, will eventually:

1. Read open GitHub issues.
2. Select one actionable issue.
3. Create a safe Git worktree.
4. Start a sandbox adapter.
5. Resolve and preprocess a prompt.
6. Run an AI coding-agent provider.
7. Let the agent edit files and run commands through sandbox seams.
8. Detect whether the work is complete.
9. Run tests.
10. Commit successful changes.
11. Preserve failed or dirty worktrees.
12. Later, create pull requests or close issues only after the safe workflow succeeds.

The first usable release should be a local single-issue tracer bullet. It should prove the end-to-end workflow with one fake or provided issue before advanced features are added.

## User Stories

1. As a solo Python developer, I want AI Code to work through one GitHub issue at a time, so that I can safely automate repetitive coding tasks.
2. As a solo Python developer, I want RALPH to select only actionable issues, so that vague or unsafe work is not attempted automatically.
3. As a solo Python developer, I want RALPH to create a Git worktree before editing code, so that my main working tree is protected.
4. As a solo Python developer, I want RALPH to run commands through a sandbox seam, so that local execution can later be replaced by Docker or future isolated execution without rewriting the orchestrator.
5. As a solo Python developer, I want Docker bind-mount mode to run commands inside a mounted worktree, so that commands execute in a controlled runtime while edits still appear in the host worktree.
6. As a solo Python developer, I want Windows 11 path and mount behavior to be a first-class concern, so that Docker and Git work reliably on my machine.
7. As a solo Python developer, I want setup_config.py to be the final runtime source of truth, so that configuration is predictable and not scattered across modules.
8. As a solo Python developer, I want CLI arguments to feed into setup_config.py only after validation, so that bad user input does not corrupt runtime configuration.
9. As a solo Python developer, I want prompt files and inline prompts to be supported, so that I can use either quick prompts or reusable prompt templates.
10. As a solo Python developer, I want prompt preprocessing to happen only after the sandbox is ready, so that placeholders can use sandbox-aware context safely.
11. As a solo Python developer, I want issue title, issue body, labels, and other external values treated as inert text, so that untrusted issue data does not become executable command text.
12. As a solo Python developer, I want Codex to be the first real AI coding-agent provider, so that AI Code can move from fake/test agents to a real automation path.
13. As a solo Python developer, I want CodexProvider to start with non-interactive execution, so that RALPH can automate issue work without relying on a human-driven terminal UI.
14. As a solo Python developer, I want CodexProvider to prefer structured output when available, so that the orchestrator can parse agent results more reliably.
15. As a solo Python developer, I want RALPH to detect `<promise>COMPLETE</promise>`, so that completion is explicit instead of guessed.
16. As a solo Python developer, I want RALPH to run pytest before committing, so that broken changes are not saved as successful work.
17. As a solo Python developer, I want RALPH to preserve the worktree when a run fails, so that I can inspect and debug the failed attempt.
18. As a solo Python developer, I want RALPH to preserve the worktree when uncommitted changes remain, so that useful partial work is not lost.
19. As a solo Python developer, I want RALPH to show command output, failures, test results, commits, and preserved worktree paths, so that I can understand what happened.
20. As a solo Python developer, I want configured secret values redacted from logs, so that sensitive values are not exposed accidentally.
21. As a solo Python developer, I want repository context to be small and useful, so that prompts contain helpful project information without sending cache folders, virtual environments, or secrets.
22. As a future AI Code user, I want template scaffolding under `.ai-code/`, so that common workflows can be generated consistently.
23. As a solo Python developer, I want Phase 3 to prove CodexProvider inside the real RALPH loop, so that Codex is not considered done just because provider-level tests pass.
24. As a solo Python developer, I want Codex prompts passed through stdin when supported, so that large issue bodies, Windows paths, quotes, and shell-like text remain inert.
25. As a solo Python developer, I want Codex output normalized before the orchestrator sees it, so that RALPH does not depend on Codex-specific output locations.
26. As a solo Python developer, I want non-zero Codex exit codes to fail the run, so that a completion token in partial output cannot hide a broken command.
27. As a solo Python developer, I want a read-only Codex preflight check, so that missing Codex CLI setup is reported as blocked before real agent work begins.
28. As a solo Python developer, I want a real-worktree Issue #49 smoke proof, so that Phase 3 proves the workflow in RALPH’s normal worktree location.
29. As a solo Python developer, I want RALPH results to expose setup, final test, sync, and cleanup phase results, so that the Phase 3 proof can assert what happened through the public result object.
30. As a solo Python developer, I want the Phase 3 proof to show baseline pytest before Codex and final pytest after Codex, so that I can tell whether Codex broke or fixed the worktree.

## Implementation Decisions

### Product Identity

1. Product/project name: AI Code.
2. Agent name: RALPH.
3. Python package name: `ai_coder`.
4. Future scaffold folder: `.ai-code/`.
5. The PRD must use AI Code-specific wording and must not name outside reference projects.
6. Use “AI Code template scaffolding,” not “RALPH template scaffolding.”
7. Use “workflow template scaffolding,” not names tied to another project.

### Core Product Goal

AI Code should help a solo Python developer safely automate the repetitive GitHub issue fixing workflow without risking the main repo.

RALPH should act like a careful junior developer that works through GitHub issues one at a time, makes code changes in an isolated worktree and sandbox, runs tests, commits successful fixes, and preserves failed work for human review.

### First Usable Release

The first usable release is a local single-issue tracer bullet.

Release 1 should prove that AI Code can:

1. Load configuration from setup_config.py.
2. Read or receive one issue.
3. Select one actionable issue.
4. Create a Git worktree.
5. Start a local sandbox adapter.
6. Resolve prompt text from a file or inline prompt.
7. Preprocess the prompt only after the sandbox is ready.
8. Run one fake/test agent command through the sandbox seam.
9. Detect completion with `<promise>COMPLETE</promise>`.
10. Run pytest through the sandbox seam.
11. Commit successful changes.
12. Preserve the worktree if the run fails or leaves uncommitted changes.
13. Return a clear result object and log readable progress.

### Release Phases

1. Phase 1: Local single-issue tracer bullet.
2. Phase 2: Docker bind-mount sandbox.
3. Phase 3: Real AI coding-agent loop with CodexProvider.
4. Phase 4: GitHub issue automation.
5. Phase 5: Safe commit and PR workflow.
6. Phase 6: Full `.ai-code/` workflow template scaffolding.
7. Phase 7: Long-running Docker container.
8. Phase 8: Multi-agent workflows.
9. Phase 9: Cloud sandbox providers.

### Phase 3 Definition

Phase 3 is not complete when CodexProvider only passes isolated provider tests.

Phase 3 is complete only when CodexProvider is proven inside the real RALPH orchestration loop.

Phase 3 must prove that:

1. RALPH selects CodexProvider from setup_config.py.
2. RALPH passes the final preprocessed prompt to CodexProvider.
3. CodexProvider runs through the sandbox seam.
4. CodexProvider uses non-interactive `codex exec`.
5. Long prompt text is passed safely, preferably through stdin.
6. Codex output becomes normalized agent events.
7. The orchestrator reads those normalized events.
8. Completion detection still depends on `<promise>COMPLETE</promise>`.
9. Baseline pytest runs before Codex starts changing the worktree.
10. Final pytest runs after Codex completes.
11. Successful changes are committed only after final tests pass.
12. Failed, incomplete, no-change, blocked, or dirty work is preserved for inspection.

### Phase 3 Smoke-Test Issue

The official simple Phase 3 smoke-test issue is Issue #49.

Issue #49 represents a tiny real coding task:

1. The startup log message currently uses mixed case.
2. The task changes the message text to all caps.
3. The expected visible code behavior is a small worktree change.
4. The issue must use the `tracer bullet` label when live GitHub issue reading is used.
5. The smoke proof must not create a pull request.
6. The smoke proof must not close a GitHub issue automatically.

The smoke proof should use RALPH’s real worktree flow under `.ai_coder/ai_coder_worktrees/`.

This proof is a real-worktree integration or manual smoke proof, not a fake repository-only proof.

### Phase 3 Prompt and Manual Acceptance Artifacts

Phase 3 should include two different artifacts:

1. `.ai-code/prompts/codex_smoke_test.md`
2. A separate manual Codex smoke-test checklist.

The prompt file tells Codex what work to do.

The checklist tells the developer how to grade the full RALPH workflow.

The checklist must verify:

1. setup_config.py selects CodexProvider.
2. Sandbox mode is local for the first Codex smoke proof.
3. Provided issue data or live GitHub issue reading represents Issue #49.
4. RALPH creates a safe worktree.
5. CodexProvider runs non-interactive `codex exec`.
6. The final prompt is passed safely, preferably through stdin.
7. The startup log text changes to all caps.
8. Codex output includes `<promise>COMPLETE</promise>`.
9. RALPH detects completion.
10. RALPH runs baseline pytest before Codex.
11. RALPH runs final pytest after Codex.
12. RALPH commits after final tests pass.
13. RALPH exposes a commit hash.
14. Pull request creation remains future/disabled or dry-run.
15. GitHub issue closing remains future/disabled or dry-run.
16. Failed, incomplete, blocked, no-change, or dirty work is preserved.

### Required Future Core Modules

AI Code should be built around small, clear Python modules. Each module should hide implementation details behind one or a few public interface seams.

Required future module areas include:

1. setup configuration
2. CLI entry point
3. RALPH orchestration
4. GitHub issue selection
5. worktree management
6. sandbox provider management
7. Docker command utilities
8. agent provider management
9. completion detection
10. prompt resolving
11. prompt preprocessing
12. test running
13. display and logging
14. repository context discovery
15. future template scaffolding
16. future isolated sandbox sync

Release 1 may stub some module areas, but every tracer-bullet issue should move the project toward the required future module structure.

### Interface Naming Rule

Public module seams must use the naming pattern:

`i_<module_name>_<action>()`

Examples:

1. `i_ralph_run()`
2. `i_sandbox_start()`
3. `i_sandboxhandle_run()`
4. `i_worktree_create()`
5. `i_prompt_resolve()`
6. `i_prompt_preprocess()`
7. `i_orchestrator_run()`
8. `i_github_issue_select()`
9. `i_test_run()`

Private helpers should start with `_`.

### Configuration Source of Truth

setup_config.py is AI Code’s final runtime source of truth.

Expected runtime flow:

1. Load setup_config.py.
2. Validate values loaded from defaults and `.env`.
3. Parse CLI arguments.
4. Apply valid CLI values into setup_config.py.
5. Validate setup_config.py again.
6. Run RALPH using only setup_config.py values.

CLI args, `.env` values, and defaults may feed into setup_config.py, but runtime modules should read final runtime values from setup_config.py.

### Configuration Validation

AI Code must:

1. Load defaults and `.env` values into setup_config.py.
2. Validate configuration once before CLI overrides.
3. Parse CLI arguments.
4. Apply valid CLI values into setup_config.py.
5. Validate configuration again after CLI overrides.
6. Validate Docker settings only when Docker sandbox mode is selected.
7. Validate Codex settings only when CodexProvider is selected.
8. Return clear user-facing errors for invalid values.
9. Avoid mutating setup_config.py with invalid CLI values.
10. Keep setup_config.py as the final runtime source of truth.

### Worktree Requirements

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

### Sandbox Provider Architecture

AI Code must not hard-code Docker behavior into the orchestrator.

RALPH must ask for a SandboxProvider. The selected provider decides whether execution is local, Docker bind-mount, or future isolated copy-in/copy-out execution.

The orchestrator should call the sandbox seam and should not know Docker command details.

The sandbox seam should make this call shape possible:

1. RALPH prepares the command.
2. RALPH calls `i_sandboxhandle_run()`.
3. The selected sandbox provider runs the command using local execution, Docker bind-mount execution, or future isolated execution.
4. The provider returns stdout, stderr, and exit code in a normalized command result.

### Sandbox Requirements

AI Code must:

1. Run project commands through `i_sandboxhandle_run()`.
2. Support local execution for the first tracer bullet.
3. Support Docker bind-mount execution as the next major sandbox mode.
4. Use one non-interactive Docker container run per command in the first Docker version.
5. Check the configured Docker image once when creating the Docker sandbox handle.
6. Make the Docker image name configurable through setup_config.py.
7. Default the Docker image to `ai-code-ralph-test-runtime:latest`.
8. Avoid auto-building the Docker image in the first Docker version.
9. Pass normal Docker env vars through a clear env seam.
10. Pass secret-like Docker env vars through a separate secret env seam.
11. Redact configured secret env values from logs.
12. Keep cloud sandbox providers as far-future work.

### Docker Bind-Mount Behavior

In Docker bind-mount mode, AI Code must:

1. Create or receive a host Git worktree path.
2. Mount that worktree into the Docker container.
3. Use `/workspace` as the container path for the mounted worktree.
4. Set the container working directory to `/workspace`.
5. Run commands inside `/workspace`.
6. Let file edits made inside Docker appear in the host worktree.
7. Let the host inspect Git state after Docker finishes.
8. Preserve dirty or failed worktrees.
9. Avoid a separate sync module for this mode.

### Windows Docker Mount Requirements

AI Code must:

1. Support Windows 11 as the primary development target.
2. Convert or patch host paths so Docker bind mounts work correctly from Windows.
3. Treat Git worktree `.git` mount behavior as a special case when needed.
4. Keep Windows mount patching behind a small utility seam.
5. Test Windows path conversion behavior separately from Docker command execution.
6. Avoid spreading Windows path logic across RALPH orchestration or agent providers.

### Docker Image Validation

Docker image validation must live inside the Docker adapter layer.

When Docker sandbox mode is selected, DockerSandboxProvider must check the configured image once when creating the Docker sandbox handle.

The Docker image name must be configurable through setup_config.py.

The default Docker image name is:

`ai-code-ralph-test-runtime:latest`

AI Code must not auto-build the Docker image in the first Docker version.

### Secret and Environment Variable Requirements

AI Code must:

1. Not pass all host environment variables into Docker.
2. Define normal Docker env allowlists in setup_config.py.
3. Define secret Docker env allowlists separately in setup_config.py.
4. Keep the default normal Docker env allowlist very small.
5. Use `PYTHONUNBUFFERED` as the default normal Docker env value.
6. Keep the default secret Docker env allowlist empty.
7. Not include `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GH_TOKEN` in the default secret allowlist during the early Docker tracer bullet.
8. Pass Docker env vars as explicit `NAME=value` runtime env args.
9. Skip missing normal env vars, except `PYTHONUNBUFFERED`, which may default to `1`.
10. Raise a clear error when an allowlisted secret env var is missing or empty.
11. Validate secret env vars when building the Docker command, not during DockerSandboxProvider construction.
12. Redact only configured secret env values from logs.
13. Avoid auto-detecting secret-looking names in the first version.
14. Keep env handling behind clear seams so runtime env vars can later be replaced by a stronger secret provider.

### Docker Command Redaction Requirements

Docker command logging must redact only configured secret env values.

Normal env values may be logged normally.

Secret env values must be redacted before logging.

Docker command redaction must support these env arg shapes:

1. short env flag followed by `NAME=value`
2. long env flag followed by `NAME=value`
3. long env flag joined directly to `NAME=value`

Docker command redaction must receive the command and secret env names as inputs. The command redaction utility should not import setup_config.py.

### Docker Module Responsibility Split

Docker command construction belongs in the sandbox provider layer.

Docker command redaction belongs in a separate Docker command utility module.

setup_config.py owns the normal env allowlist and secret env allowlist.

The sandbox provider reads the allowlists and builds Docker command args.

The Docker command utility receives a command and secret env names, returns a redacted command list, and does not own configuration.

### Prompt Handling Requirements

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

### Agent Provider Requirements

AI Code must:

1. Keep AI coding-agent commands behind an agent provider seam.
2. Support a simple fake/test agent first.
3. Support Codex as the first real AI coding-agent provider.
4. Support other providers later.
5. Let each provider define how to build its command.
6. Let each provider define how to pass prompt text to the agent.
7. Let each provider define how to parse output.
8. Return normalized stream events such as text, tool call, result, error, and session id when supported.
9. Never let RALPH hard-code one provider’s command details.
10. Allow provider-specific env needs to flow through setup_config.py and the sandbox env seams.
11. Keep provider output visible through the display/logging system.

### CodexProvider Requirements

Codex is the first real AI coding-agent provider.

CodexProvider must:

1. Start with Codex CLI non-interactive mode.
2. Prefer structured output when available.
3. Fall back to plain stdout parsing when structured output is unavailable.
4. Prefer stdin for large prompt text when supported.
5. Avoid putting full GitHub issue bodies directly into command arguments unless there is no supported alternative.
6. Keep command construction isolated inside the agent provider layer.
7. Avoid logging the raw full prompt.
8. Avoid logging secret values.
9. Treat issue title, body, and labels as inert text.
10. Add tests proving long prompts and special characters work on Windows.
11. Use command arguments only for safe provider command pieces, flags, configuration values, and the stdin prompt marker.
12. Keep untrusted GitHub issue title, body, labels, Windows paths, quotes, semicolons, pipes, ampersands, backticks, and shell-looking text in stdin prompt text.
13. Normalize Codex output into provider events before the orchestrator reads it.
14. Treat stderr as diagnostic output, not the normal completion source.
15. Treat a non-zero Codex command exit code as failed even if output text contains `<promise>COMPLETE</promise>`.

### CodexProvider Output Priority

CodexProvider must resolve completion-readable output in this priority order:

1. Final message file first, when CodexProvider uses an output-last-message path.
2. Structured JSONL events second, when available.
3. Plain stdout fallback third.
4. stderr is diagnostic output only.

The orchestrator and completion detector must not depend on Codex-specific output locations directly.

CodexProvider owns Codex output details.

RALPH receives normalized provider output.

### CodexProvider Malformed JSONL Behavior

Malformed Codex JSONL should be recoverable when another trusted completion source exists.

Rules:

1. If the final message file contains `<promise>COMPLETE</promise>`, allow completion even if some JSONL events are malformed.
2. If the final message file is missing but plain stdout contains `<promise>COMPLETE</promise>`, allow completion as a fallback.
3. Surface malformed JSONL as a warning, diagnostic message, or normalized error event.
4. Do not silently hide malformed JSONL.
5. Fail only when no trusted completion source contains the completion token, or when the Codex command exits with a failure code.

### CodexProvider Exit-Code Rule

A non-zero CodexProvider command exit code must fail the agent run even if output text contains `<promise>COMPLETE</promise>`.

Completion detection may only produce a successful result after the Codex command exits successfully.

### CodexProvider Preflight Requirement

The real Codex smoke proof must fail early with a blocked result when Codex CLI is missing, not configured, or not ready.

Preflight failures should be reported as blocked, not failed, because RALPH did not actually run the coding-agent loop.

The Codex preflight must be read-only.

It may check:

1. configured provider name
2. configured sandbox mode
3. configured Codex command
4. executable availability
5. `codex --version`
6. prompt file existence
7. dry-run GitHub automation setting
8. provided issue data availability

It must not:

1. call the model
2. edit files
3. create commits
4. create pull requests
5. close issues
6. run the real smoke task

The real Codex model call may happen only inside the official smoke-test workflow after RALPH has created the safe worktree and prepared the prompt.

### Completion Detection Requirements

AI Code must:

1. Detect `<promise>COMPLETE</promise>` as the primary completion signal.
2. Treat max-iteration reached without completion as incomplete.
3. Treat agent command failure as failed.
4. Treat sandbox command failure as failed.
5. Treat test failure as failed.
6. Treat no code changes as incomplete unless the issue explicitly required no code change.
7. Return a clear result status such as complete, incomplete, failed, blocked, or no_changes.
8. Preserve logs and worktree state for failed, blocked, or incomplete runs.

### Result Status Contract

AI Code must return one of these statuses every time RALPH runs:

1. `complete`
   - The agent signaled `<promise>COMPLETE</promise>`.
   - Required tests passed.
   - Successful changes were committed.

2. `incomplete`
   - The agent did not signal completion before max iterations.
   - The run stopped without a final successful result.

3. `failed`
   - The agent command failed.
   - The sandbox command failed.
   - Required tests failed.
   - Git commit failed.

4. `blocked`
   - RALPH could not continue because of missing configuration, missing Docker image, missing credentials, no actionable issue, or unsafe repo state.

5. `no_changes`
   - The agent completed, but no code changes were detected.
   - This may be acceptable only if the issue explicitly required no code change.

### RALPH Phase Result Visibility Requirements

RALPH must expose workflow phase results through the public RALPH result object so tests and smoke proofs can inspect observable behavior without reaching into private helpers.

The result object should expose these optional fields:

1. `project_setup_result`
2. `test_result`
3. `sync_result`
4. `cleanup_result`

These fields must default to `None`.

A field should be populated only when that workflow phase actually ran.

Expected phase-result visibility:

1. Repository-start blocked:
   - project setup result is `None`
   - final test result is `None`
   - sync result is `None`
   - cleanup result is `None`

2. GitHub issue read blocked:
   - project setup result is `None`
   - final test result is `None`
   - sync result is `None`
   - cleanup result is `None`

3. No actionable issue:
   - project setup result is `None`
   - final test result is `None`
   - sync result is `None`
   - cleanup result is `None`

4. Worktree creation blocked:
   - project setup result is `None`
   - final test result is `None`
   - sync result is `None`
   - cleanup result is `None`

5. Sandbox startup blocked:
   - project setup result is `None`
   - final test result is `None`
   - sync result is `None`
   - cleanup result is populated if cleanup or preservation ran

6. Project setup blocked:
   - project setup result is populated
   - final test result is `None`
   - sync result is `None`
   - cleanup result is populated if cleanup or preservation ran

7. Final test failure:
   - project setup result is populated
   - final test result is populated
   - sync result is `None`
   - cleanup result is populated if cleanup or preservation ran

8. Sync or commit failure:
   - project setup result is populated
   - final test result is populated
   - sync result is populated
   - cleanup result is populated if cleanup or preservation ran

9. Successful run:
   - project setup result is populated
   - final test result is populated
   - sync result is populated
   - cleanup result is populated

The result object docstring must explain the four phase-result fields.

This is a visibility requirement, not a workflow rewrite.

### GitHub Issue Handling Requirements

AI Code must:

1. Read open GitHub issues.
2. Select one actionable issue at a time.
3. Ignore or skip issues that are too vague, blocked, already assigned, or unsafe.
4. Use issue number, title, body, and labels when building the agent prompt.
5. Keep issue selection behind `i_github_issue_select()`.
6. Never close an issue before tests pass and changes are committed.
7. In a future release, create a PR or close the issue only after the safe workflow succeeds.

### Repository Context Requirements

AI Code must:

1. Detect the repository root.
2. Detect the active branch.
3. Detect whether the repo has uncommitted changes before starting.
4. Detect package manager and test command when possible.
5. Prefer configured commands from setup_config.py over guessing.
6. Include useful repo context in the agent prompt.
7. Keep repository inspection behind repository context responsibilities.
8. Avoid scanning huge folders such as `.git`, `.venv`, `node_modules`, build outputs, and cache folders.
9. Keep repository context small enough to be useful in prompts.
10. Never send secret files or `.env` contents into prompts by default.

### Repository Context Exclusion Requirements

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
13. large binary files
14. generated logs
15. generated reports unless explicitly requested

### Display and Logging Requirements

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
11. Keep display behavior behind display/logging responsibilities.

### Template Scaffolding Requirements

Full workflow template scaffolding is a future feature.

AI Code template scaffolding should generate a `.ai-code/` folder for project-specific automation files.

Future scaffolding may include:

1. Dockerfile
2. `.env.example`
3. AI Code configuration
4. runner file
5. prompt files
6. implementation prompt
7. review prompt
8. merge prompt
9. coding standards document

## Testing Decisions

### Testing Philosophy

AI Code tests should focus on observable behavior.

A good test should answer: “When the user runs AI Code or one public module seam, does the system do the right thing?”

Tests should prefer public seams. Private helper tests are acceptable when behavior is small, security-sensitive, or hard to reach through a public seam without excessive setup.

### Required Test Areas

AI Code should test:

1. setup_config.py validation behavior
2. CLI-to-setup_config flow
3. GitHub issue selection behavior
4. worktree creation and preservation behavior
5. sandbox provider selection
6. local sandbox command execution
7. Docker bind-mount command construction
8. Docker image check behavior
9. Docker env allowlist behavior
10. Docker secret env behavior
11. Docker command redaction behavior
12. prompt resolving
13. prompt preprocessing
14. completion detection
15. result statuses
16. pytest execution through the sandbox seam
17. commit behavior after tests pass
18. dirty worktree preservation
19. repository context exclusions
20. display/logging output

### Phase 3 Codex Testing Decisions

Phase 3 must test both successful and unsafe CodexProvider outcomes.

A Phase 3 implementation is not complete if it only proves the happy path.

Required Phase 3 failure-path coverage:

1. Codex CLI missing or not ready returns blocked.
2. Codex exits non-zero returns failed.
3. Codex output without `<promise>COMPLETE</promise>` returns incomplete.
4. Malformed JSONL with a valid final message recovers with diagnostics.
5. Codex outputs `<promise>COMPLETE</promise>` but makes no change returns `no_changes` unless no changes are explicitly allowed.
6. Codex makes a change but tests fail returns failed and preserves the worktree.
7. Codex makes a change, completion is detected, tests pass, and commit succeeds returns complete.

The main mocked Codex end-to-end test should patch at the sandbox seam rather than deep inside CodexProvider.

It must still exercise:

1. setup_config.py selecting CodexProvider
2. RALPH selecting CodexProvider through the provider seam
3. CodexProvider command construction
4. stdin prompt passing
5. Codex output normalization
6. orchestrator completion detection
7. test runner flow
8. sync/commit or no-change decision

### Phase 3 Prompt-Delivery Test Decisions

The main CodexProvider loop test must prove that the final preprocessed prompt is delivered through stdin when supported.

The full GitHub issue body must not be placed directly into Codex command arguments.

The command-safety proof must show:

1. Command args include safe provider pieces such as `codex`, `exec`, `--cd`, the worktree path, `--sandbox`, `--color`, `--json`, `--output-last-message`, and `-`.
2. Command args do not include the full issue title.
3. Command args do not include the full issue body.
4. Command args do not include issue labels.
5. Command args do not include shell-looking issue text.
6. Command args do not include the long prompt body.
7. stdin text includes the final preprocessed prompt.
8. stdin text includes Issue #49 content for the smoke proof.
9. Windows paths, quotes, semicolons, pipes, ampersands, and backticks from issue text remain inert prompt text.

Provider-level command-safety tests are useful but not sufficient by themselves.

Phase 3 requires the same safety proof through the full RALPH loop.

### Phase 3 Real-Worktree Smoke-Proof Testing Decisions

The Issue #49 proof should use a real RALPH worktree under `.ai_coder/ai_coder_worktrees/`.

It should not modify the main project working tree directly.

The proof should verify:

1. setup_config.py selects `codex`.
2. RALPH receives provided Issue #49 data or reads the live issue using the `tracer bullet` label.
3. RALPH creates or uses a safe worktree under `.ai_coder/ai_coder_worktrees/`.
4. RALPH starts local sandbox mode.
5. RALPH creates CodexProvider through `i_agent_provider_create()`.
6. The sandbox command captures or runs the Codex command.
7. The full final prompt is passed through stdin.
8. Issue title, body, and labels do not appear in command args.
9. Codex changes the startup log message to all caps.
10. Codex output includes `<promise>COMPLETE</promise>`.
11. RALPH detects completion.
12. RALPH runs baseline pytest before Codex changes code.
13. RALPH runs final pytest after Codex changes code.
14. RALPH commits after final tests pass.
15. RALPH returns or displays a commit hash.
16. Pull request creation remains future/disabled.
17. GitHub issue closing remains future/disabled or dry-run.
18. Dirty, failed, blocked, incomplete, or no-change worktrees are preserved.

### Near-Term Phase 3 Prerequisite Issue

Before the full Issue #49 Codex smoke proof, AI Code should implement this small prerequisite issue:

`Expose RALPH workflow phase results for Phase 3 Codex proof`

Scope:

1. Update the RALPH result object to expose `project_setup_result`.
2. Update the RALPH result object to expose `test_result`.
3. Update the RALPH result object to expose `sync_result`.
4. Update the RALPH result object to expose `cleanup_result`.
5. Make all four fields optional and default to `None`.
6. Update every RALPH result return carefully so fields are populated only when the phase actually ran.
7. Update the RALPH result docstring.
8. Add a success-path test.
9. Add an early-blocked-path test.

The success-path test name should be:

`test_ralph_result_exposes_phase_results_on_success`

The early-blocked-path test name should be:

`test_ralph_result_leaves_unreached_phase_results_none_when_blocked_early`

The success-path test should assert real phase-result values, not only non-`None`.

Expected success assertions include:

1. baseline tests ran
2. baseline tests passed
3. final tests passed
4. sync committed changes
5. sync returned the expected commit hash
6. cleanup removed the worktree when safe

The early blocked test should use repository startup blocked as the cleanest early stop case.

The early blocked test should assert:

1. status is `blocked`
2. project setup result is `None`
3. final test result is `None`
4. sync result is `None`
5. cleanup result is `None`

This prerequisite issue should only change RALPH code and existing RALPH tests unless a tiny import/export adjustment is forced by the result-field additions.

Do not update the program explanation document in this prerequisite issue.

### Docker Env and Secret Test Decisions

Docker env and secret handling must be tested before adding more Docker behavior.

Tests should cover:

1. Normal env allowlist builds Docker runtime env args.
2. Missing normal env vars are skipped.
3. `PYTHONUNBUFFERED` defaults to `1`.
4. Secret env allowlist builds Docker runtime env args.
5. Missing secret env vars raise a clear error.
6. Empty secret env vars raise a clear error.
7. Docker command logs redact configured secret values.
8. Redaction supports short env flag, long env flag, and joined long env flag forms.
9. At least one test crosses the public DockerSandboxProvider seam.

### Useful Test Techniques

1. Use pytest as the default test runner.
2. Use pytest output capture when testing printed output.
3. Use monkeypatch to safely set and delete environment variables during tests.
4. Patch Docker image inspection in unit tests that should not require real Docker.
5. Patch subprocess calls when testing command construction.
6. Keep real Docker integration tests separate from fast unit tests.

## Assumptions

1. The first implementation target is Windows 11.
2. The project uses Python, Poetry, and pytest.
3. The project package name is `ai_coder`.
4. setup_config.py already exists or will exist as the final runtime configuration source.
5. RALPH is the agent name inside AI Code.
6. The first real agent provider will be CodexProvider.
7. Docker bind-mount mode is the first Docker sandbox mode.
8. Docker image building is manual in the first Docker version.
9. Automatic GitHub issue closing is future work.
10. Pull request creation is future work.
11. Cloud sandbox providers are far-future work.
12. Explicit sync-in and sync-out are only needed for future isolated or cloud sandboxes.
13. Local and Docker bind-mount modes work directly inside the Git worktree path and do not need a separate sync layer.

## Open Questions

1. What exact CLI command should start AI Code in Release 1?
2. What exact CLI flags should be supported in Release 1?
3. What config fields should setup_config.py expose for the first tracer bullet?
4. What is the exact fake/test agent behavior for Release 1?
5. Should Release 1 support a real GitHub issue through the GitHub CLI or only a fake/provided issue object?
6. What should the exact commit message format be?
7. Should RALPH stop after creating a commit, or should it also print a suggested PR command?
8. What minimum Docker image contents are required for `ai-code-ralph-test-runtime:latest`?
9. What exact command should run the official manual Codex smoke proof?
10. Should the real Codex smoke proof be run through a dedicated CLI flag, a pytest marker, or a documented manual command?
11. What exact user-facing blocked message should Codex preflight return for missing authentication?
12. What exact scaffold templates should `.ai-code/` support after the Phase 3 proof is complete?

## Out of Scope

The following are out of scope for Release 1:

1. Multiple issues at once.
2. Parallel planning.
3. Multiple AI agents working together.
4. Long-running Docker containers.
5. Cloud sandbox providers.
6. Automatic Docker image building.
7. Automatic GitHub issue closing.
8. Pull request creation.
9. Complex sync-in/sync-out behavior.
10. Full workflow template scaffolding.
11. Production deployment automation.
12. Replacing Git, GitHub, Docker, Poetry, pytest, or Codex.
13. Deleting dirty worktrees after failure.
14. Hiding agent decisions, commands, or logs from the user.
15. Treating isolated CodexProvider unit tests as sufficient Phase 3 completion.
16. Creating pull requests automatically during the Phase 3 smoke proof.
17. Closing GitHub issues automatically during the Phase 3 smoke proof.
18. Updating the program explanation document during the small phase-result visibility prerequisite issue.

The following are out of scope for the near-term Docker bind-mount slice:

1. Passing all host environment variables into Docker.
2. Including real AI-provider secrets in the default Docker secret allowlist.
3. Switching to Docker secrets or external secret managers.
4. Long-running Docker container orchestration.
5. Remote/cloud sandbox file sync.

## Further Notes

### Non-Goals

AI Code is not:

1. A general-purpose operating system automation tool.
2. A replacement for GitHub, Git, Docker, Poetry, pytest, or Codex.
3. A fully autonomous production deployment system.
4. A tool that closes GitHub issues without passing tests.
5. A tool that deletes dirty worktrees after failure.
6. A tool that hides agent decisions, commands, or logs from the user.
7. A cloud-sandbox-first product.

### Safety Requirements

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
10. Keep final runtime configuration behind setup_config.py.

### Release 1 Acceptance Criteria

Release 1 is accepted when:

1. Running AI Code with one fake or provided issue creates a safe worktree.
2. RALPH starts a local sandbox adapter.
3. RALPH resolves and preprocesses a prompt.
4. RALPH runs a fake/test agent through the sandbox seam.
5. RALPH detects `<promise>COMPLETE</promise>`.
6. RALPH runs pytest through the sandbox seam.
7. RALPH commits only after tests pass.
8. RALPH preserves the worktree on failure.
9. RALPH returns a clear result status.
10. RALPH logs readable progress.

### Phase 2 Acceptance Criteria

The Docker bind-mount sandbox phase is accepted when:

1. Docker sandbox mode can be selected through setup_config.py.
2. Docker image validation happens inside the Docker adapter layer.
3. The configured Docker image is checked once when the Docker sandbox handle is created.
4. The host worktree is bind-mounted into the container at `/workspace`.
5. Commands run with `/workspace` as the container working directory.
6. Command results return stdout, stderr, and exit code.
7. File edits inside Docker appear in the host worktree.
8. Dirty or failed worktrees are preserved.
9. Docker env allowlists work as specified.
10. Secret env values are redacted from logs.
11. Tests cover command construction, env handling, redaction, and missing-secret behavior.

### Phase 3 Acceptance Criteria

Phase 3 is accepted when:

1. setup_config.py can select CodexProvider.
2. RALPH creates or uses a safe worktree before Codex edits code.
3. CodexProvider runs through the sandbox seam.
4. CodexProvider uses non-interactive `codex exec`.
5. The final preprocessed prompt is passed through stdin when supported.
6. GitHub issue title, body, and labels remain inert prompt text.
7. GitHub issue text does not leak into Codex command arguments.
8. Codex final message file, JSONL, and stdout are handled using the defined priority order.
9. Malformed JSONL can recover when final message or stdout has a trusted completion signal.
10. Non-zero Codex exit code fails the run even if output contains the completion token.
11. Codex output becomes normalized provider events.
12. The orchestrator reads normalized provider events.
13. Completion still depends on `<promise>COMPLETE</promise>`.
14. RALPH runs baseline pytest before Codex starts.
15. RALPH runs final pytest after Codex completes.
16. RALPH commits only after final pytest passes.
17. RALPH exposes project setup, final test, sync, and cleanup phase results through the public result object.
18. Failed, incomplete, blocked, no-change, or dirty worktrees are preserved.
19. The Issue #49 smoke proof shows a real all-caps startup-log change in a RALPH worktree.
20. Pull request creation and issue closing remain future/disabled or dry-run during the Phase 3 proof.

### Coding Standards

AI Code must:

1. Use Python.
2. Use Poetry.
3. Use pytest.
4. Support Windows 11 as the primary OS target.
5. Keep modules under the Python package.
6. Keep tests under the test suite.
7. Prefer small tracer-bullet slices.
8. Avoid rewriting the whole project for one issue.
9. Avoid changing unrelated files.
10. Avoid new dependencies unless clearly required.
11. Prefer clear names over clever abstractions.
12. Keep public interfaces small.
13. Hide implementation details behind module seams.
14. Write tests for behavior, not private implementation details.
15. Preserve existing public interface functions unless an issue explicitly requires a rename.

### Documentation Requirements

AI Code must include documentation that explains:

1. What AI Code does.
2. What problem AI Code solves.
3. What RALPH does inside AI Code.
4. How to install the project.
5. How to run the local tracer bullet.
6. How to run tests.
7. How setup_config.py works.
8. How the sandbox seam works.
9. How the worktree safety model works.
10. How Docker bind-mount mode works.
11. How Docker env allowlists and redaction work.
12. How CodexProvider works when added.
13. How to add future agent providers.
14. How to add future sandbox providers.
15. What is in scope for the current release.
16. What is intentionally future work.

### Open Questions and Decision Log

Locked decisions:

1. Product name is AI Code.
2. RALPH is the autonomous coding agent inside AI Code.
3. Primary user is a solo Python developer on Windows 11.
4. Release 1 is a local single-issue tracer bullet.
5. Docker bind-mount sandbox is Phase 2.
6. Docker should mount the worktree at `/workspace`.
7. Docker image validation belongs inside the Docker adapter layer.
8. Docker image validation happens once when creating the Docker sandbox handle.
9. The default Docker image is `ai-code-ralph-test-runtime:latest`.
10. AI Code must not auto-build the Docker image in the first Docker version.
11. setup_config.py is the final runtime source of truth.
12. Docker env allowlists are owned by setup_config.py.
13. The default normal Docker env allowlist contains `PYTHONUNBUFFERED`.
14. The default secret Docker env allowlist is empty.
15. Real AI-provider secrets are not included in the default secret allowlist.
16. Docker command redaction redacts only configured secret env values.
17. Codex is the first real agent provider.
18. CodexProvider starts with non-interactive execution.
19. CodexProvider prefers structured output when available.
20. `.ai-code/` is the future scaffold folder.
21. Full workflow template scaffolding is a future feature.
22. Explicit sync-in/sync-out is only needed for future isolated or cloud sandboxes.
23. The PRD must not use outside reference-project names.
24. Phase 3 is not done until CodexProvider is proven inside the real RALPH orchestration loop.
25. The official Phase 3 smoke-test issue is Issue #49.
26. Issue #49 changes the startup log message to all caps.
27. Live GitHub issue reading for the smoke proof uses the `tracer bullet` label.
28. The official Codex smoke-test prompt should live at `.ai-code/prompts/codex_smoke_test.md`.
29. The manual Codex smoke-test checklist is separate from the prompt file.
30. Codex output priority is final message file first, structured JSONL second, and plain stdout fallback third.
31. stderr is diagnostic output, not the normal completion source.
32. Malformed JSONL is recoverable when final message or stdout still proves completion.
33. Non-zero Codex exit code overrides any completion token and fails the run.
34. Codex preflight failures are blocked, not failed.
35. Codex preflight must be read-only and must not call the model or edit files.
36. Phase 3 requires failure-path tests, not only happy-path tests.
37. The main mocked Codex loop test should patch at the sandbox seam, not deep inside CodexProvider.
38. The Phase 3 prompt-delivery proof must show issue text goes through stdin and not command arguments.
39. The Issue #49 proof should use RALPH’s real worktree flow under `.ai_coder/ai_coder_worktrees/`.
40. RALPH must run baseline pytest before Codex and final pytest after Codex.
41. RALPH result visibility must expose project setup, final test, sync, and cleanup phase results.
42. The next prerequisite issue is `Expose RALPH workflow phase results for Phase 3 Codex proof`.

### External Technical References Considered

1. Docker bind mounts: host files or directories can be mounted into a container.
2. Docker environment variable guidance: sensitive values should be handled carefully, and stronger secret mechanisms should be considered for production.
3. Codex CLI non-interactive mode: Codex can run in script/automation mode.
4. Codex CLI output capture: Codex can write a final message file and can emit structured output for automation.
5. pytest monkeypatch: tests can safely set/delete environment variables and patch attributes.
6. Python dataclasses: result objects can expose optional fields with default values.
7. Git worktrees: multiple working trees can be attached to one repository.
