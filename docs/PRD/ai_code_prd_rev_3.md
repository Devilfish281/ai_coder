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
9. What Codex CLI flags should be used for the first CodexProvider slice?
10. Should CodexProvider initially parse structured output, plain stdout, or both?
11. What exact scaffold templates should `.ai-code/` support first?

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

### External Technical References Considered

1. Docker bind mounts: host files or directories can be mounted into a container.
2. Docker environment variable guidance: sensitive values should be handled carefully, and stronger secret mechanisms should be considered for production.
3. Codex CLI non-interactive mode: Codex can run in script/automation mode.
4. pytest monkeypatch: tests can safely set/delete environment variables and patch attributes.
5. Git worktrees: multiple working trees can be attached to one repository.
