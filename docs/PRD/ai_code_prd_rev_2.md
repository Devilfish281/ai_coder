# PRD: AI Code

> Publication status: Not published: issue tracker access or triage label configuration was not provided.

## Problem Statement

A solo Python developer on Windows 11 needs a safer and more repeatable way to work through GitHub issues one at a time.

Today, the developer must manually read an issue, decide whether it is actionable, create a safe working branch or worktree, prepare a prompt, run an AI coding tool, review changes, run tests, commit only safe work, and preserve failed attempts for debugging.

This workflow is valuable but repetitive. It is also risky if an AI coding agent edits the main working tree directly, hides command output, closes issues too early, or deletes dirty work after a failure.

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

4. As a solo Python developer, I want RALPH to run commands through a sandbox seam, so that local execution can later be replaced by Docker or cloud execution without rewriting the orchestrator.

5. As a solo Python developer, I want Docker bind-mount mode to run commands inside a mounted worktree, so that commands execute in a more controlled runtime while edits still appear in the host worktree.

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

23. As a future AI Code user, I want local, Docker, and later cloud sandbox providers to share a common interface, so that execution environments can evolve without rewriting RALPH.

24. As a future maintainer, I want behavior-focused tests, so that expected behavior is defined by tests rather than private implementation details.

25. As a future maintainer, I want public interfaces to follow the `i_<module_name>_<action>()` naming rule, so that module seams are easy to identify.

## Implementation Decisions

### Product Identity

1. Product/project name: AI Code.
2. Agent name: RALPH.
3. Python package name: `ai_coder`.
4. Future scaffold folder: `.ai-code/`.
5. The PRD should use AI Code-specific wording and avoid outside reference-project names.
6. Use “AI Code template scaffolding,” not “RALPH template scaffolding.”
7. Use “workflow template scaffolding,” not names tied to another project.

### Primary User

The primary user is a solo Python developer on Windows 11 who wants AI Code to safely work through GitHub issues one at a time.

### Main Product Goal

AI Code should provide RALPH, an autonomous coding agent that safely completes one GitHub issue at a time, with tests and commits required before any issue is considered complete.

### First Usable Release

Release 1 is a local single-issue tracer bullet.

It should prove the smallest useful end-to-end workflow:

1. Load configuration.
2. Receive or read one issue.
3. Create a safe worktree.
4. Start a local sandbox adapter.
5. Resolve and preprocess a prompt.
6. Run a fake/test agent through the sandbox seam.
7. Detect completion.
8. Run tests through the sandbox seam.
9. Commit successful work.
10. Preserve failed or dirty work.
11. Return a clear result status.

### Release Phases

1. Phase 1 — Local single-issue tracer bullet.
2. Phase 2 — Docker bind-mount sandbox.
3. Phase 3 — Real AI coding-agent loop.
4. Phase 4 — GitHub issue automation.
5. Phase 5 — Safe commit and PR workflow.
6. Phase 6 — Full `.ai-code/` workflow template scaffolding.
7. Phase 7 — Long-running Docker container.
8. Phase 8 — Multi-agent workflows.
9. Phase 9 — Cloud sandbox providers.

### Required Future Core Modules

AI Code should eventually include these core module responsibilities:

1. Runtime configuration.
2. CLI entrypoint.
3. RALPH orchestration.
4. GitHub issue handling.
5. Worktree management.
6. Sandbox provider.
7. Agent provider.
8. Completion detection.
9. Prompt resolving.
10. Prompt preprocessing.
11. Test running.
12. Display and logging.
13. Repository context.
14. Future template scaffolding.
15. Long-term future sync-in and sync-out for isolated or cloud sandboxes only.

Release 1 may stub some modules, but each tracer-bullet issue should move the project toward this architecture.

### Interface Naming Rule

Public module seams must use this naming pattern:

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

Private helper functions should start with `_`.

### Configuration Decisions

1. `setup_config.py` is the final runtime source of truth.
2. Defaults and `.env` values may feed into setup_config.py.
3. CLI arguments may feed into setup_config.py after validation.
4. RALPH modules should read final runtime values from setup_config.py.
5. Validate configuration before CLI overrides.
6. Validate configuration again after CLI overrides.
7. Validate Docker settings only when Docker sandbox mode is selected.
8. Validate Codex settings only when CodexProvider is selected.
9. Invalid CLI values should not mutate setup_config.py.

Expected runtime flow:

1. Load setup_config.py.
2. Validate values loaded from defaults and `.env`.
3. Parse CLI args.
4. Validate CLI values.
5. Apply CLI args into setup_config.py.
6. Validate setup_config.py again.
7. Run RALPH using setup_config.py values.

### GitHub Issue Handling Decisions

1. GitHub issues are the unit of work.
2. RALPH should read open GitHub issues.
3. RALPH should select one actionable issue at a time.
4. RALPH should skip issues that are too vague, blocked, already assigned, or unsafe.
5. RALPH should use issue number, title, body, and labels when building prompts.
6. Issue selection should stay behind `i_github_issue_select()`.
7. Issue closing is future work.
8. RALPH must never close an issue before tests pass and changes are committed.

### Worktree Decisions

1. RALPH must create a Git worktree before agent code edits.
2. Use one worktree per issue attempt.
3. Use a branch name that is traceable to the issue or run.
4. Keep worktree creation behind `i_worktree_create()`.
5. Keep worktree cleanup behind a clear worktree seam.
6. Preserve the worktree if the run fails.
7. Preserve the worktree if uncommitted changes exist.
8. Remove the worktree only when the run succeeds and the worktree is clean.
9. Show the preserved worktree path to the user.
10. Windows path behavior is a first-class requirement.

### Sandbox Decisions

1. RALPH must run project commands through `i_sandboxhandle_run()`.
2. Local execution is the first sandbox mode.
3. Docker bind-mount execution is the next major sandbox mode.
4. The first Docker version should use one `docker run --rm` per command.
5. Long-running Docker containers are future work.
6. Docker image auto-build is not part of the first Docker version.
7. The Docker image name should be configurable through setup_config.py.
8. The default Docker image should be `ai-code-ralph-test-runtime:latest`.
9. Check the configured Docker image once when creating the Docker sandbox handle.
10. Keep Docker image checks inside the Docker adapter layer.

### Docker Bind-Mount Decisions

In Docker bind-mount mode, AI Code must:

1. Create or receive a host Git worktree path.
2. Mount that worktree into the Docker container.
3. Set the container working directory to the mounted repo path.
4. Run commands inside the mounted worktree.
5. Let file edits made inside Docker appear in the host worktree.
6. Avoid a separate sync module for this mode.

### Windows Docker Mount Decisions

AI Code must:

1. Support Windows 11 as the primary development target.
2. Convert or patch host paths so Docker bind mounts work correctly from Windows.
3. Treat Git worktree `.git` mount behavior as a special case when needed.
4. Keep Windows mount patching behind a small utility seam.
5. Test Windows path conversion behavior separately from Docker command execution.
6. Avoid spreading Windows path logic across RALPH, the orchestrator, or agent providers.

### Secret and Environment Variable Decisions

1. Define normal Docker env allowlists in setup_config.py.
2. Define secret Docker env allowlists separately in setup_config.py.
3. Keep the default secret allowlist empty or very small.
4. Do not include `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GH_TOKEN` in the default secret allowlist during the early Docker tracer bullet.
5. Use normal Docker env vars first.
6. Hide env handling behind a clear seam so it can later be replaced by a stronger secret provider.
7. Pass Docker env vars as `-e NAME=value`.
8. Skip missing normal env vars, except `PYTHONUNBUFFERED`, which may default to `1`.
9. Raise a clear error when an allowlisted secret env var is missing or empty.
10. Redact only configured secret env values from logs.
11. Avoid auto-detecting secret-looking names in the first version.

### Prompt Handling Decisions

1. AI Code must accept prompt text from an inline prompt or a prompt file.
2. Prompt resolving happens before the agent runs.
3. Prompt preprocessing happens only after the sandbox is ready.
4. Safe placeholders may include issue number, issue title, issue body, branch name, and worktree path.
5. Prompt resolving stays behind `i_prompt_resolve()`.
6. Prompt preprocessing stays behind `i_prompt_preprocess()`.
7. Issue title, issue body, labels, and other external values must be treated as inert text.
8. Shell-command syntax from untrusted issue data must not be executed.
9. Command expansion should be limited, explicit, and test-covered.

### Agent Provider Decisions

1. AI coding-agent commands must stay behind an agent provider seam.
2. A fake/test agent should be supported first.
3. Codex is the first real AI coding-agent provider.
4. Other providers may be added later.
5. Each provider should define how to build its command.
6. Each provider should define how to pass prompt text.
7. Each provider should define how to parse output.
8. Provider output should be normalized into AI Code events or result objects.
9. RALPH must not hard-code one provider’s command details.
10. Provider-specific env needs should flow through setup_config.py and sandbox env seams.
11. Provider output should remain visible through display/logging.

### CodexProvider Decisions

1. CodexProvider starts with non-interactive execution.
2. Interactive support is future work for manual/debug workflows.
3. CodexProvider should prefer structured output when available.
4. Plain stdout parsing is allowed as a fallback.
5. CodexProvider should prefer stdin for large prompt text when supported.
6. If command arguments must be used for prompt text, command construction must stay isolated in the provider.
7. CodexProvider must avoid logging full raw prompts by default.
8. CodexProvider must avoid logging secret values.
9. Long prompts and special characters should be tested on Windows.

### Completion Detection Decisions

1. `<promise>COMPLETE</promise>` is the primary completion signal.
2. Max iterations reached without completion means incomplete.
3. Agent command failure means failed.
4. Sandbox command failure means failed.
5. Test failure means failed.
6. No code changes means `no_changes` unless the issue explicitly required no code change.
7. Failed, blocked, or incomplete runs must preserve logs and worktree state.

### Result Status Contract

RALPH must return one of these statuses:

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

### Repository Context Decisions

AI Code should inspect repository context before building the agent prompt.

Repository context should:

1. Detect the repository root.
2. Detect the active branch.
3. Detect whether the repo has uncommitted changes before starting.
4. Detect package manager and test command when possible.
5. Prefer configured commands from setup_config.py over guessing.
6. Include useful repo context in the agent prompt.
7. Stay behind a repository context module seam.
8. Avoid scanning huge or irrelevant folders.
9. Stay small enough to be useful in prompts.
10. Never send secret files or `.env` contents into prompts by default.

Default repository context exclusions:

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

### Display and Logging Decisions

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
11. Keep display behavior behind a display module seam.

### Future Template Scaffolding Decisions

AI Code should eventually support full workflow template scaffolding under `.ai-code/`.

Future scaffold example:

1. Dockerfile.
2. Environment example file.
3. AI Code config file.
4. Runner file.
5. Prompt file.
6. Implement prompt file.
7. Review prompt file.
8. Merge prompt file.
9. Coding standards document.

Template scaffolding is future work, not Release 1.

### Future Sync Decisions

Explicit sync behavior is not required for Release 1 or the early Docker bind-mount sandbox.

For local execution and Docker bind-mount execution, the Git worktree is the shared working directory.

Sync behavior is only needed later when AI Code supports isolated or cloud sandboxes where the sandbox filesystem is not the same as the host worktree.

Long-term future sync may include:

1. Sync in.
2. Sync out.
3. Copy-in and copy-out for isolated sandboxes.
4. Commit extraction from remote or cloud sandboxes.
5. Safe merge or pull request creation after tests pass.

## Testing Decisions

Testing is part of the product contract.

AI Code must:

1. Use pytest as the default test runner.
2. Run tests through the sandbox seam, not directly from RALPH.
3. Treat failing tests as a failed issue attempt.
4. Preserve the worktree when tests fail.
5. Only commit successful changes after required tests pass.
6. Prefer behavior tests that cross public interface seams.
7. Avoid testing private helpers unless the behavior is small and hard to reach through the public seam.
8. Keep tests as the source of truth for expected behavior.

Important behavior areas to test:

1. Configuration validation before and after CLI overrides.
2. Invalid CLI args do not mutate setup_config.py.
3. GitHub issue selection skips non-actionable issues.
4. Worktree creation uses safe branch/worktree naming.
5. Dirty or failed worktrees are preserved.
6. Local sandbox runs commands in the expected working directory.
7. Docker sandbox builds the correct bind-mount command.
8. Docker image existence is checked once when the Docker handle is created.
9. Docker env allowlist behavior.
10. Docker secret env allowlist behavior.
11. Secret value redaction.
12. Windows mount path patching.
13. Prompt resolving from inline text.
14. Prompt resolving from file.
15. Prompt preprocessing after sandbox startup.
16. Untrusted issue text is treated as inert text.
17. Fake/test agent completion behavior.
18. CodexProvider command construction.
19. CodexProvider output parsing.
20. Completion detection with `<promise>COMPLETE</promise>`.
21. Max-iteration incomplete behavior.
22. Test failure result behavior.
23. Commit-after-tests behavior.
24. No-changes result behavior.
25. Display/logging output for key phases.

Good tests should verify observable behavior through public seams whenever possible.

## Assumptions

1. The first PRD target is the AI Code project as a whole, not a single narrow issue.
2. The issue tracker target and triage label configuration were not provided, so this PRD is not published.
3. The primary development environment is Windows 11.
4. Python, Poetry, pytest, Git, GitHub, Docker, and Codex are expected parts of the long-term workflow.
5. Release 1 can use fake issue data or a manually provided issue before full GitHub automation exists.
6. Release 1 can use a fake/test agent before CodexProvider is fully implemented.
7. Docker bind-mount mode will be built before long-running Docker containers.
8. Cloud sandbox providers are far-future.
9. Pull request creation and issue closing are future workflow steps, not first-release behavior.
10. The `.ai-code/` scaffold folder is a future capability, not required for Release 1.
11. Explicit sync-in and sync-out are only needed for future isolated or cloud sandboxes.

## Open Questions

1. What exact CLI command should run Release 1?
2. What should the default fake issue look like?
3. What labels make an issue actionable or non-actionable?
4. What branch naming pattern should worktree branches use?
5. What should the first exact Docker runtime image contain?
6. What exact command should build the first Docker runtime image?
7. What default test command should setup_config.py use?
8. Should pytest be required for all projects, or configurable per repo?
9. What exact Codex CLI flags should CodexProvider start with?
10. Should CodexProvider use plain stdout first or structured output first if both are available?
11. What exact prompt template should RALPH use for Release 1?
12. How much repository context should be included by default?
13. What result object fields should RALPH return?
14. What logging format should be used for human-readable terminal output?
15. When pull request creation is added, should RALPH create draft PRs by default?
16. When issue closing is added, should closing require a merged PR or only a passing committed fix?

## Out of Scope

### Out of Scope for Release 1

1. Multiple issues at once.
2. Parallel planning.
3. Multiple AI agents working together.
4. Real Codex execution if the fake/test agent tracer bullet is not complete yet.
5. Docker bind-mount sandbox if local tracer bullet is not complete yet.
6. Long-running Docker containers.
7. Cloud sandbox providers.
8. Automatic Docker image building.
9. Automatic GitHub issue closing.
10. Pull request creation.
11. Explicit sync-in and sync-out.
12. Full `.ai-code/` template scaffolding.
13. Production deployment automation.
14. Autonomous merging into protected branches.

### Product Non-Goals

AI Code is not:

1. A general-purpose operating system automation tool.
2. A replacement for GitHub, Git, Docker, Poetry, or pytest.
3. A fully autonomous production deployment system.
4. A tool that closes GitHub issues without passing tests.
5. A tool that deletes dirty worktrees after failure.
6. A tool that hides agent decisions, commands, or logs from the user.
7. A cloud-sandbox-first product.

## Further Notes

### Release 1 Success Criteria

Release 1 is successful when AI Code can:

1. Load configuration from setup_config.py.
2. Read or receive one issue.
3. Select one actionable issue.
4. Create a Git worktree.
5. Start a local sandbox adapter.
6. Resolve prompt text from a file or inline prompt.
7. Preprocess the prompt only after the sandbox is ready.
8. Run one fake/test AI coding-agent command through the sandbox seam.
9. Detect `<promise>COMPLETE</promise>`.
10. Run pytest through the sandbox seam.
11. Commit successful changes.
12. Preserve the worktree if the run fails or leaves uncommitted changes.
13. Return a clear result object and log readable progress.

### Future Product Success Criteria

The future product is successful when AI Code can:

1. Read open GitHub issues.
2. Select actionable issues.
3. Create isolated worktrees safely.
4. Run local and Docker bind-mount sandboxes.
5. Support long-running Docker containers.
6. Support Codex as the first real agent provider.
7. Support additional agent providers later.
8. Stream or display agent output clearly.
9. Detect completion, failure, timeout, and no-progress states.
10. Run tests before committing.
11. Preserve failed worktrees.
12. Create pull requests.
13. Close GitHub issues only after tests pass and the chosen safe workflow succeeds.
14. Scaffold `.ai-code/` workflow templates.
15. Much later, support cloud sandbox providers.

### Acceptance Criteria Requirements

Each release phase should define acceptance criteria that are:

1. Specific.
2. Testable.
3. Small enough to verify with pytest, CLI output, Git state, or file existence.
4. Focused on behavior, not private implementation details.
5. Written before or alongside GitHub issues created from this PRD.

### Phase 1 Acceptance Criteria

1. Running AI Code with one fake issue creates a safe worktree.
2. AI Code starts a local sandbox adapter.
3. AI Code resolves and preprocesses a prompt.
4. AI Code runs a fake/test agent through the sandbox seam.
5. AI Code detects `<promise>COMPLETE</promise>`.
6. AI Code runs pytest through the sandbox seam.
7. AI Code commits only after tests pass.
8. AI Code preserves the worktree on failure.
9. AI Code returns a clear result status.

### Safety Requirements

AI Code must:

1. Never modify the host repo directly when a worktree is required.
2. Create a safe worktree before agent code edits.
3. Preserve the worktree if the run fails.
4. Preserve the worktree if uncommitted changes exist.
5. Run tests before committing or closing an issue.
6. Never close a GitHub issue unless tests pass and the fix is committed or merged according to the chosen workflow.
7. Log enough information for the user to understand what happened.
8. Redact configured secret values from logs.
9. Keep sandbox execution behind `i_sandboxhandle_run()`.
10. Keep final runtime configuration behind setup_config.py.

### Coding Standards

AI Code must:

1. Use Python.
2. Use Poetry.
3. Use pytest.
4. Support Windows 11 as the primary OS target.
5. Prefer small tracer-bullet slices.
6. Avoid rewriting the whole project for one issue.
7. Avoid changing unrelated files.
8. Avoid new dependencies unless clearly required.
9. Prefer clear names over clever abstractions.
10. Keep public interfaces small.
11. Hide implementation details behind module seams.
12. Write tests for behavior, not private implementation details.
13. Preserve existing public interface functions unless an issue explicitly requires a rename.

### Documentation Requirements

AI Code must include documentation that explains:

1. What AI Code does.
2. What problem AI Code solves.
3. How to install the project.
4. How to run the local tracer bullet.
5. How to run tests.
6. How setup_config.py works.
7. How the sandbox seam works.
8. How the worktree safety model works.
9. How CodexProvider works when added.
10. How to add future agent providers.
11. How to add future sandbox providers.
12. What is in scope for the current release.
13. What is intentionally future work.

### Decision Log

Locked decisions:

1. Product name is AI Code.
2. RALPH is the autonomous coding agent inside AI Code.
3. Primary user is a solo Python developer on Windows 11.
4. Release 1 is a local single-issue tracer bullet.
5. Docker bind-mount sandbox is Phase 2.
6. Cloud sandboxes are far-future.
7. Codex is the first real agent provider.
8. setup_config.py is the final runtime source of truth.
9. `.ai-code/` is the future scaffold folder.
10. Full workflow template scaffolding is a future feature.
11. Explicit sync-in and sync-out are future-only for isolated or cloud sandboxes.
12. The PRD must use AI Code-specific naming and avoid outside reference-project names.
