# ai_coder Program Explanation

## 1. Purpose

`ai_coder` is a Python project that is building **AI Code**.

Inside AI Code, the main coding agent is named **RALPH**.

RALPH means:

```text
R = Repository
A = Autonomous
L = Local
P = Patch
H = Helper
```

In plain English:

> RALPH is a careful coding helper that works on one GitHub issue at a time.

The goal is not to create a giant fully automatic system all at once. The goal is to build the system in small, safe slices. Each slice proves one part of the workflow before the next part is added.

That is why the project uses a **tracer-bullet** style.

A tracer bullet is a thin working path through the whole system. It does not do every advanced feature yet, but it proves the main idea can work from start to finish.

For `ai_coder`, the big idea is:

```text
Pick one issue.
Create a safe worktree.
Run an agent in a sandbox.
Run tests.
Commit only safe work.
Preserve failed work.
Do not close GitHub issues too early.
```

---

## 2. The simple mental model

Think of RALPH like a careful student working on a class assignment.

```text
GitHub issue        = assignment instructions
Repository          = class project folder
Git worktree        = safe copy of the project
Sandbox             = safe place to run commands
Prompt              = instruction sheet for the AI agent
Agent provider      = the worker that tries to solve the task
Orchestrator        = the supervisor that asks, "Are you done yet?"
Completion detector = the done checker
Test runner         = the grader
Sync out            = commit the finished work
PR draft            = write a future pull request plan
Issue close         = future ticket close plan
Cleanup             = remove or preserve the work area
```

The most important safety idea is:

> RALPH should not directly risk the main project folder.

Instead, RALPH should work in a separate Git worktree. If something goes wrong, the worktree is preserved so a human can inspect it.

---

## 3. What AI Code is trying to solve

Before AI Code, the developer has to do many steps manually:

1. Read GitHub issues.
2. Decide which issue is safe and actionable.
3. Create a branch or worktree.
4. Prepare a prompt for an AI coding tool.
5. Run the AI tool.
6. Watch command output.
7. Run tests.
8. Commit changes only if tests pass.
9. Open a pull request later.
10. Close the issue only after everything is safe.

That process is useful, but repetitive.

AI Code is trying to make that workflow safer and more repeatable.

The PRD describes RALPH as a careful junior developer. That is a good way to understand the project: RALPH should help, but it should not secretly take dangerous actions.

---

## 4. Current high-level runtime flow

The current `i_ralph_run()` workflow is more complete than the old explanation described.

The current flow is:

```text
User runs ai-coder
        |
        v
main.py parses command-line arguments
        |
        v
setup_config.py becomes the final runtime source of truth
        |
        v
ralph.py starts the RALPH workflow
        |
        v
repository_context validates the Git repository
        |
        v
github_issues reads or receives issues
        |
        v
github_issues selects one actionable issue
        |
        v
worktree_manager creates a real Git worktree
        |
        v
sandbox_provider starts local or Docker sandbox mode
        |
        v
project_setup optionally runs poetry install and baseline pytest
        |
        v
repository_context discovers prompt-safe repo context
        |
        v
prompt_resolver loads prompt text
        |
        v
prompt_preprocessor fills placeholders
        |
        v
agent_provider creates mock or Codex provider
        |
        v
orchestrator runs the agent loop
        |
        v
completion_detector checks for <promise>COMPLETE</promise>
        |
        v
test_runner runs tests through the sandbox seam
        |
        v
sync_out commits successful work
        |
        v
pull_request_draft builds future PR metadata
        |
        v
github_issues builds future issue-close metadata
        |
        v
display shows a dry-run GitHub automation summary
        |
        v
worktree_manager removes clean completed worktrees or preserves unsafe ones
```

---

## 5. The 12-step RALPH workflow

Your current `ralph.py` still follows the original 12-step roadmap, but several steps now have real behavior.

### Step 1 — Start with a Git repository

RALPH calls:

```python
i_repository_start()
```

This checks whether the path is inside a Git repository.

It runs Git commands such as:

```text
git rev-parse --show-toplevel
git rev-parse --abbrev-ref HEAD
git status --porcelain
```

It blocks RALPH if:

- Git cannot find the repository root,
- the repo is in detached `HEAD` state,
- the host repo has uncommitted changes,
- clean-state detection fails.

High-school explanation:

> Before RALPH starts working, it checks whether the main project folder is clean. This is like making sure your desk is clear before starting a new assignment.

### Step 2 — Read open GitHub issues

RALPH resolves issue data using this priority:

1. Issues passed directly into `i_ralph_run()`.
2. A testing issue when `TESTING_FLAG=true`.
3. User issue values from config or command-line input.
4. A local GitHub issue markdown file.
5. Real GitHub CLI issue reading through `gh issue list`.

The GitHub issue reader is safer than a raw shell string because it builds a command list and parses JSON.

### Step 3 — Pick one actionable issue

RALPH calls:

```python
i_github_issue_select_actionable()
```

This function picks one issue and skips unsafe or inappropriate ones.

It can skip issues for reasons like:

- closed,
- blocked,
- unsafe,
- already assigned,
- outside configured workflow labels,
- too vague.

The priority order is:

```text
1. bug
2. tracer
3. feature / enhancement
4. polish
5. refactor
6. anything else
```

High-school explanation:

> If several assignments are available, RALPH chooses the most important safe one first.

### Step 4 — Create a safe Git worktree

RALPH calls:

```python
i_worktree_create()
```

This is now real behavior, not only a stub.

The worktree manager:

1. Builds a safe branch name.
2. Creates a worktree path under `.ai_coder/ai_coder_worktrees/`.
3. Builds the command:

```text
git -C <repo_path> worktree add -b <branch_name> <worktree_path>
```

4. Runs the Git command.
5. Returns a `WorktreeCreateResult`.

Example branch shape:

```text
ralph-issue-58-add-provider-and-sandbox-extension-documentation
```

High-school explanation:

> A worktree is like making a safe copy of your project where RALPH can work without messing up the main folder.

### Step 5 — Start a sandbox

RALPH calls:

```python
i_sandbox_start()
```

The sandbox mode comes from `setup_config.py`.

Current supported modes:

```text
local
docker
```

#### Local sandbox

The local sandbox runs commands on the host machine inside the worktree folder.

It uses:

```python
LocalSandboxProvider.i_sandboxhandle_run()
```

That returns a normalized `CommandResult` with:

- `stdout`,
- `stderr`,
- `exit_code`,
- `succeeded`,
- `failed`.

#### Docker sandbox

The Docker sandbox runs commands inside a Docker container.

The current Docker mode is **bind-mount mode**.

That means:

```text
host worktree path  ->  /workspace inside Docker
```

So if the agent edits a file inside Docker, the change appears in the host worktree too.

The current Docker implementation uses one short-lived command container:

```text
docker run --rm ...
```

High-school explanation:

> Local sandbox means "run it on this computer." Docker sandbox means "run it inside a controlled container, but still let edits appear in the worktree."

### Step 5a — Run project setup

RALPH calls:

```python
i_project_setup_run()
```

This checks whether the worktree has:

```text
pyproject.toml
```

If yes, it treats the project as a Poetry project and runs:

```text
poetry install
poetry run pytest
```

Both commands run through the sandbox seam.

This is important because RALPH should know whether the project was already broken before the agent starts making changes.

High-school explanation:

> This is like checking that the project builds and passes tests before RALPH changes anything.

### Step 5b — Discover prompt-safe repository context

RALPH calls:

```python
i_repository_context_discover()
```

This collects safe, high-level facts for the prompt.

It can detect things like:

- package manager,
- test command,
- useful project files,
- safe project signals.

It intentionally excludes sensitive or noisy folders and files such as:

```text
.git/
.venv/
venv/
__pycache__/
.pytest_cache/
node_modules/
dist/
build/
.env
.env.*
*.log
large binary files
```

High-school explanation:

> RALPH gives the agent a small map of the project, not the entire messy backpack.

### Step 6 — Give an AI coding agent a prompt

This step is split into two smaller jobs.

#### Step 6a — Resolve prompt text

RALPH calls:

```python
i_prompt_resolve()
```

This can load:

- an inline prompt, or
- a prompt file.

It raises helpful errors if:

- both inline prompt and prompt file are provided,
- neither is provided,
- the prompt file does not exist,
- the path is not a file.

#### Step 6b — Preprocess prompt text

RALPH calls:

```python
i_prompt_preprocess()
```

This replaces placeholders like:

```text
{{ISSUE_NUMBER}}
{{ISSUE_TITLE}}
{{ISSUE_BODY}}
{{ISSUE_LABELS}}
{{BRANCH_NAME}}
{{WORKTREE_PATH}}
{{REPOSITORY_CONTEXT}}
{{COMPLETE_TOKEN}}
```

Important safety rule:

> Issue title, issue body, and labels are treated as inert text.

That means issue text should be copied into the prompt as text, not executed like a command.

High-school explanation:

> If an issue body says `delete everything`, RALPH should not treat that as a real command. It should treat it like words written on paper.

### Step 7 — Run the agent loop

RALPH chooses or builds an agent provider.

Current provider seam:

```python
i_agent_provider_create()
```

Supported provider names:

```text
mock
codex
```

#### Fake test agent

The fake test agent runs a small Python command through the sandbox and returns the completion token.

It is safe because it does not call a real AI service.

#### CodexProvider

`CodexProvider` is the first real agent-provider path.

It builds a non-interactive command shaped like:

```text
codex exec --cd <worktree> --sandbox workspace-write --color never --json --output-last-message <path> -
```

The `-` means the prompt is passed through stdin instead of being placed directly into command arguments.

That is safer for long issue bodies and special characters.

CodexProvider also tries to parse structured JSONL output and normalize events into categories like:

```text
text
tool_call
result
error
session
```

High-school explanation:

> The agent provider is the adapter that knows how to talk to a specific AI coding tool. RALPH should not know all the details of every tool.

### Step 8 — Detect completion

RALPH calls:

```python
i_completion_detector_detect()
```

The completion token is:

```text
<promise>COMPLETE</promise>
```

This is intentionally simple.

RALPH does not guess completion based on vibes. It looks for the exact token.

High-school explanation:

> RALPH waits for the agent to say the exact magic phrase that means "I am done."

### Step 9 — Run tests

RALPH calls:

```python
i_test_runner_run()
```

The test runner uses the sandbox handle when available.

The default configured test command is:

```text
poetry run pytest
```

The test runner returns:

- whether tests passed,
- the command used,
- stdout,
- stderr,
- exit code,
- whether testing was blocked.

High-school explanation:

> The test runner is the grader. RALPH should not call the work successful unless the grader passes it.

### Step 10 — Sync or commit finished work

RALPH calls:

```python
i_sync_out_merge()
```

In the current code, this is mainly a Git commit workflow.

If RALPH completed and tests passed, `sync_out`:

1. Checks worktree status.
2. Skips commit if no changes exist.
3. Runs:

```text
git add -A
git commit -m "<message>"
git rev-parse HEAD
```

4. Checks final worktree status.
5. Returns commit metadata.

If there are no changes, RALPH can return the `no_changes` status unless `allow_no_changes=True`.

High-school explanation:

> If the agent did useful work and tests passed, RALPH saves that work as a Git commit.

### Step 11 — Prepare GitHub automation metadata

This step is split into safe placeholder pieces.

#### Step 11a — Pull request draft metadata

RALPH calls:

```python
i_pull_request_draft_build()
```

This does **not** create a real pull request.

It builds future-safe metadata such as:

- PR title,
- PR body,
- suggested `gh pr create` command.

The workflow stays future/disabled by default.

#### Step 11b — Issue close metadata

RALPH calls:

```python
i_github_issue_close()
```

This does **not** close a real issue yet.

It only prepares close metadata when all safety conditions are true:

- completion was confirmed,
- final status is complete,
- tests passed,
- work was committed,
- commit hash exists.

Even when enabled, the current implementation is still a placeholder and does not actually close GitHub issues.

#### Step 11c — Dry-run summary

RALPH displays a summary showing:

- selected issue,
- final status,
- no PR was created,
- no GitHub issue was closed,
- next action for the human.

High-school explanation:

> RALPH writes the paperwork for a future PR or issue close, but it does not submit the paperwork automatically yet.

### Step 12 — Preserve or clean up the worktree

RALPH calls:

```python
i_worktree_cleanup()
```

The cleanup rules are safety-first:

```text
Incomplete run                 -> preserve worktree
Known uncommitted changes       -> preserve worktree
Cannot verify clean state       -> preserve worktree
Clean completed worktree        -> remove worktree
Failed cleanup                  -> preserve worktree
```

High-school explanation:

> If there is any chance useful work could be lost, RALPH keeps the worktree.

---

## 6. Current result statuses

`RalphResult.status` can be one of:

```text
complete
incomplete
failed
blocked
no_changes
```

### `complete`

The best result.

It means:

- the agent signaled completion,
- tests passed,
- work was committed,
- cleanup rules allowed success.

### `incomplete`

The agent did not finish before the allowed number of iterations.

### `failed`

Something important failed, such as:

- agent command failed,
- tests failed,
- commit failed.

### `blocked`

RALPH stopped before it could safely continue.

Examples:

- Git repository is dirty,
- no actionable issue was found,
- GitHub issues could not be read,
- worktree creation failed,
- sandbox startup failed,
- project setup failed.

### `no_changes`

The agent completed and tests passed, but there were no code changes to commit.

That can be okay for documentation or no-code issues only if the caller explicitly allows it.

---

## 7. Project layout

Your current project uses a `src/` layout.

Simplified layout:

```text
ai_coder/
├── pyproject.toml
├── README.md
├── .ai-code/
│   ├── .env.example
│   ├── Dockerfile
│   ├── README.md
│   ├── prompts/
│   │   ├── implementation.md
│   │   ├── review.md
│   │   └── merge.md
│   └── standards/
│       └── coding-standards.md
├── .ai_coder/
│   ├── Dockerfile
│   ├── prompt.md
│   ├── ai_coder_worktrees/
│   └── logs/
├── docker/
│   └── ralph-test-runtime/
│       └── Dockerfile
├── src/
│   └── ai_coder/
│       ├── __main__.py
│       ├── setup_config.py
│       ├── agent_provider/
│       ├── completion_detector/
│       ├── display/
│       ├── github_issues/
│       ├── main/
│       ├── orchestrator/
│       ├── project_setup/
│       ├── prompt_preprocessor/
│       ├── prompt_resolver/
│       ├── pull_request_draft/
│       ├── ralph/
│       ├── repository_context/
│       ├── sandbox_provider/
│       ├── scaffold/
│       ├── sync_in/
│       ├── sync_out/
│       ├── test_runner/
│       └── worktree_manager/
└── tests/
    ├── agent_provider/
    ├── completion_detector/
    ├── display/
    ├── github_issues/
    ├── main/
    ├── orchestrator/
    ├── project_setup/
    ├── prompt_preprocessor/
    ├── prompt_resolver/
    ├── pull_request_draft/
    ├── ralph/
    ├── repository_context/
    ├── sandbox_provider/
    ├── scaffold/
    ├── setup_config/
    ├── sync_in/
    ├── sync_out/
    ├── test_docs/
    ├── test_runner/
    └── worktree_manager/
```

The main idea:

```text
src/ai_coder/ = application code
tests/        = pytest tests
.ai-code/     = project-specific AI Code scaffolding
.ai_coder/    = runtime files, worktrees, logs, prompt files
```

---

## 8. Main configuration file: `setup_config.py`

`setup_config.py` is the final runtime source of truth.

That means `.env` values and CLI arguments may feed into it, but once RALPH runs, modules should trust `setup_config.py`.

Important default values include:

```text
DEFAULT_PROJECT_NAME = "AI Code"
DEFAULT_GITHUB_REPO = "Devilfish281/ai_coder"
DEFAULT_DOCKER_IMAGE_NAME = "ai-code-ralph-test-runtime:latest"
DEFAULT_AGENT_NAME = "mock"
DEFAULT_TEST_COMMAND = "poetry run pytest"
DEFAULT_COMMIT_MESSAGE_TEMPLATE = "RALPH: issue #{issue_number} - {issue_title}"
```

Important supported modes:

```text
SUPPORTED_AGENT_NAMES = {"mock", "codex"}
SUPPORTED_SANDBOX_MODES = {"local", "docker"}
```

Important config areas:

| Area                   | Examples                                                                        |
| ---------------------- | ------------------------------------------------------------------------------- |
| Project identity       | `project_name`, `repo_path`, `github_repo`                                      |
| Agent                  | `default_agent`, `codex_command`                                                |
| Sandbox                | `sandbox_mode`, `docker_image_name`, `ralph_dockerfile_path`                    |
| Docker env             | `docker_env_allowlist`, `docker_secret_env_allowlist`                           |
| Provider env           | `provider_env_allowlist`, `provider_secret_env_allowlist`                       |
| GitHub issue filtering | actionable labels, blocked labels, unsafe labels, assignee rules                |
| Safety                 | `dry_run`, `github_issue_close_enabled`                                         |
| Testing and commits    | `test_command`, `commit_message_template`                                       |
| Prompt and issue input | `prompt_path`, `github_issue_path`, `issue_number`, `issue_title`, `issue_body` |

High-school explanation:

> `setup_config.py` is like the clipboard the coach uses. Everyone should read the same clipboard instead of making up their own rules.

---

## 9. Command-line entry point

The project has a script entry in `pyproject.toml`:

```toml
[project.scripts]
ai-coder = "ai_coder.main.main:main"
```

That means the program can be run as:

```powershell
poetry run ai-coder
```

It can also run as a Python module:

```powershell
poetry run python -m ai_coder
```

The CLI supports important flags such as:

```text
--issue-number
--issue-title
--issue-body
--label
--max-iterations
--prompt-path
--github-issue-path
--repo-path
--agent
--dry-run / --no-dry-run
--sandbox
```

There is also a scaffold command:

```powershell
poetry run ai-coder scaffold --repo-path .
```

That creates the `.ai-code/` scaffold folder.

---

## 10. Module-by-module explanation

### `src/ai_coder/__main__.py`

This lets Python run the project with:

```powershell
python -m ai_coder
```

It:

1. Loads `.env` once.
2. Creates setup config.
3. Creates the logger.
4. Calls `main()`.
5. Handles `KeyboardInterrupt`.

### `src/ai_coder/main/main.py`

This is the CLI controller.

It:

1. Parses command-line arguments.
2. Validates CLI input before applying it.
3. Applies valid values into `setup_config.py`.
4. Runs `setup_config.validate_initialization()`.
5. Builds a provided issue when the user passes issue values.
6. Calls:

```python
i_ralph_run()
```

It also supports:

```text
ai-coder scaffold
```

### `src/ai_coder/ralph/ralph.py`

This is the heart of the system.

Main public seam:

```python
i_ralph_run()
```

This function coordinates almost every other module.

It returns:

```python
RalphResult
```

Important fields:

```text
selected_issue
prompt
orchestrator_result
completed
message
status
pull_request_draft_result
issue_close_result
```

High-school explanation:

> `ralph.py` is the project manager. It does not do every job itself. It calls the right worker module at the right time.

### `src/ai_coder/repository_context/repository_context.py`

This module checks the repository before RALPH starts.

Main seams:

```python
i_repository_start()
i_repository_context_discover()
```

`i_repository_start()` blocks unsafe starts.

`i_repository_context_discover()` builds safe context for the prompt.

This is important because the agent should receive helpful project facts but should not receive secrets, huge cache folders, logs, or binary files.

### `src/ai_coder/github_issues/github_issues.py`

This module handles issue data.

Important data classes:

```python
GitHubIssue
ProvidedIssueData
GitHubIssueSkipReason
GitHubIssueSelectionResult
GitHubIssueCloseResult
GitHubIssuePrClosePolicy
```

Important seams:

```python
i_github_issue_from_file()
i_github_issue_from_provided()
i_github_issue_list()
i_github_issue_select_actionable()
i_github_issue_select()
i_github_issue_close()
i_github_issue_get_safe_pr_close_policy()
```

The key safety behavior is:

> RALPH can select issues, but real issue closing is still protected and placeholder-only.

### `src/ai_coder/worktree_manager/worktree_manager.py`

This module handles worktree creation and cleanup.

Important seams:

```python
i_worktree_sanitize_branch_name()
i_worktree_branch_name()
i_worktree_create_command()
i_worktree_create()
i_worktree_preserve()
i_worktree_cleanup()
```

Current important behavior:

- `i_worktree_create()` runs real Git worktree creation.
- `i_worktree_cleanup()` preserves unsafe worktrees and removes only clean completed worktrees.

### `src/ai_coder/sandbox_provider/sandbox_provider.py`

This module is the sandbox seam.

Important data classes:

```python
CommandResult
MountConfig
SandboxStartResult
```

Important classes:

```python
LocalSandboxProvider
DockerSandboxProvider
```

Important seam:

```python
i_sandbox_start()
```

The key design rule:

> RALPH should call `i_sandboxhandle_run()`, not `subprocess.run()` directly.

That gives you depth and leverage:

- RALPH does not need to know Docker command details.
- Docker bugs stay inside the sandbox provider.
- Future sandbox providers can be added without rewriting the orchestrator.

### `src/ai_coder/sandbox_provider/mount_utils.py`

This module handles Docker mount path helpers.

Important seams include:

```python
i_mountutils_to_docker_host_path()
i_mountutils_patch_git_mounts_for_windows()
i_mountutils_build_docker_volume_args()
```

This keeps Windows path behavior out of `ralph.py`.

That is good design because Windows path logic can become tricky.

### `src/ai_coder/sandbox_provider/docker_command_utils.py`

This module handles Docker command redaction.

Important seam:

```python
i_dockercommand_redact()
```

It redacts configured secret environment values from Docker commands.

This is separate from the sandbox provider so the redaction logic is small and testable.

### `src/ai_coder/project_setup/project_setup.py`

This module runs setup checks after the worktree and sandbox are ready.

Main seam:

```python
i_project_setup_run()
```

If the project has `pyproject.toml`, it runs:

```text
poetry install
poetry run pytest
```

through the sandbox seam.

This catches broken baseline setup before the agent changes code.

### `src/ai_coder/prompt_resolver/prompt_resolver.py`

This module loads raw prompt text.

Main seam:

```python
i_prompt_resolve()
```

It supports:

- inline prompt,
- prompt file.

It prevents ambiguous input.

### `src/ai_coder/prompt_preprocessor/prompt_preprocessor.py`

This module replaces prompt placeholders.

Main seam:

```python
i_prompt_preprocess()
```

It replaces placeholders matching:

```text
{{PLACEHOLDER_NAME}}
```

It does not execute shell commands.

That is correct for the current safe tracer-bullet design.

### `src/ai_coder/agent_provider/agent_provider.py`

This module connects RALPH to an agent.

Important data classes:

```python
AgentProviderEvent
AgentResponse
CodexCommandContract
```

Important providers:

```python
MockAgentProvider
FakeTestAgentProvider
CodexProvider
```

Important seam:

```python
i_agent_provider_create()
```

Current supported providers:

```text
mock
codex
```

The fake provider is safe for tests.

The Codex provider is the first real agent-provider path and keeps Codex command construction inside the provider layer.

### `src/ai_coder/orchestrator/orchestrator.py`

This module runs the agent loop.

Main seam:

```python
i_orchestrator_run()
```

The orchestrator keeps asking the agent for output until:

- completion token is found,
- max iterations are reached,
- an agent error happens.

High-school explanation:

> The orchestrator is the supervisor. It gives the agent a task and checks whether it finished.

### `src/ai_coder/completion_detector/completion_detector.py`

This module checks for:

```text
<promise>COMPLETE</promise>
```

Main seam:

```python
i_completion_detector_detect()
```

It does a simple substring check.

That is good because the completion rule is easy to understand and test.

### `src/ai_coder/test_runner/test_runner.py`

This module runs the configured tests.

Main seam:

```python
i_test_runner_run()
```

If a sandbox handle exists, tests run through:

```python
sandbox_handle.i_sandboxhandle_run()
```

If no sandbox handle exists, the old stub behavior remains.

Current RALPH passes a sandbox handle, so the main workflow uses real command execution through the sandbox seam.

### `src/ai_coder/sync_out/sync_out.py`

This module handles commit/sync behavior.

Main seams:

```python
i_sync_out_run()
i_sync_out_merge()
```

`i_sync_out_merge()` now performs real Git commit behavior when there are changes:

```text
git status --porcelain
git add -A
git commit -m ...
git rev-parse HEAD
git status --porcelain
```

It returns a `SyncMergeResult`.

### `src/ai_coder/pull_request_draft/pull_request_draft.py`

This module builds future pull request metadata.

Main seam:

```python
i_pull_request_draft_build()
```

It does not create a PR.

It prepares:

- a draft PR title,
- a draft PR body,
- a suggested command.

This keeps the workflow safe for early releases.

### `src/ai_coder/display/display.py`

This module controls what the user sees.

Important classes:

```python
SilentDisplay
ConsoleDisplay
```

Important seams include:

```python
i_display_phase()
i_display_selected_issue()
i_display_issue_skip_reasons()
i_display_agent_events()
i_display_command_failure()
i_display_test_result()
i_display_commit_result()
i_display_cleanup_result()
i_display_pull_request_draft()
i_display_issue_close_result()
i_display_github_automation_dry_run_summary()
i_display_redact_text()
```

This is good design because output formatting stays in one module instead of being scattered everywhere.

### `src/ai_coder/scaffold/scaffold.py`

This module creates the `.ai-code/` folder.

Main seam:

```python
i_scaffold_create()
```

It creates project-specific automation scaffolding such as:

```text
.ai-code/README.md
.ai-code/.env.example
.ai-code/Dockerfile
.ai-code/prompts/implementation.md
.ai-code/prompts/review.md
.ai-code/prompts/merge.md
.ai-code/standards/coding-standards.md
```

It skips existing files by default and overwrites only when explicitly requested.

High-school explanation:

> The scaffold command gives each project a starter kit for future AI Code automation files.

### `src/ai_coder/sync_in/sync_in.py`

This is still a small placeholder area.

It will matter more for future isolated or cloud sandboxes.

For local mode and Docker bind-mount mode, separate sync-in is less important because work happens directly in the worktree.

### `src/ai_coder/my_utils/env_loader.py`

This module loads `.env` once per process.

Main seam:

```python
load_dotenv_once()
```

It uses a thread lock so multiple parts of the program do not load `.env` at the same time.

### `src/ai_coder/my_utils/logger_setup.py`

This module configures logging.

It includes:

- console logging,
- rotating file logging,
- async file handling,
- secret redaction filter.

It is useful, but it is larger than most tracer-bullet modules.

### `src/ai_coder/my_utils/llm_loader.py`

This lazily creates a `ChatOpenAI` object.

Current RALPH does not need this for the fake agent path.

It may matter later when real LangChain or LangGraph flows are used.

### `src/ai_coder/my_utils/configuration.py`

This looks like a LangGraph runtime configuration helper.

It is not central to the current RALPH workflow.

### `src/ai_coder/my_utils/postgres_store_loader.py` and `redis_saver_loader.py`

These look like future or copied utility modules for LangGraph memory/checkpointing.

They are not central to the current RALPH workflow.

If they introduce missing dependency problems, they should stay isolated from the core RALPH imports.

---

## 11. Current implementation status

| Area                        |            Current Status | Explanation                                                                                                  |
| --------------------------- | ------------------------: | ------------------------------------------------------------------------------------------------------------ |
| CLI entry                   |                   Working | `main.py` parses args, validates overrides, and calls RALPH.                                                 |
| Config                      |                   Working | `setup_config.py` owns defaults, `.env`, validation, Docker, agent, GitHub, prompt, test, and commit config. |
| Repository startup          |                   Working | Detects Git root, active branch, and dirty host repo state.                                                  |
| Repository prompt context   |                   Working | Builds prompt-safe project context and excludes unsafe/noisy paths.                                          |
| GitHub issue model          |                   Working | `GitHubIssue` and related result objects exist.                                                              |
| GitHub issue reading        |   Working with GitHub CLI | Uses `gh issue list` and parses JSON.                                                                        |
| Issue selection             |                   Working | Skips unsafe/blocked/assigned/vague/out-of-workflow issues and selects by priority.                          |
| Worktree creation           |                   Working | Runs real `git worktree add -b`.                                                                             |
| Worktree cleanup            |                   Working | Preserves unsafe worktrees and removes only clean completed worktrees.                                       |
| Local sandbox               |                   Working | Runs commands locally through the sandbox seam.                                                              |
| Docker bind-mount sandbox   |               Implemented | Mounts worktree at `/workspace`, checks image, supports env allowlists and secrets.                          |
| Docker image auto-build     | Not implemented by design | The first Docker version tells the user how to build the image manually.                                     |
| Docker env allowlist        |               Implemented | Normal env vars are allowlisted. `PYTHONUNBUFFERED` can default to `1`.                                      |
| Docker secret env allowlist |               Implemented | Secret env vars are separate and must exist if configured.                                                   |
| Docker command redaction    |               Implemented | Redacts configured secret env values.                                                                        |
| Project setup               |                   Working | Runs `poetry install` and baseline `poetry run pytest` through sandbox when Poetry project detected.         |
| Prompt resolving            |                   Working | Supports inline or prompt file.                                                                              |
| Prompt preprocessing        |                   Working | Replaces safe placeholders.                                                                                  |
| Mock/fake agent             |                   Working | Runs a sandbox-backed fake command and returns completion output.                                            |
| CodexProvider               |               Implemented | Builds non-interactive Codex command and parses structured/plain output.                                     |
| Orchestrator                |                   Working | Handles completion, max iterations, errors, outputs, and events.                                             |
| Completion detector         |                   Working | Looks for exact completion token.                                                                            |
| Test runner                 |   Working through sandbox | Runs configured test command when sandbox handle is provided.                                                |
| Sync out / commit           |                   Working | Stages and commits worktree changes after completion and passing tests.                                      |
| Pull request creation       |           Future/disabled | Builds draft metadata only.                                                                                  |
| GitHub issue closing        |           Future/disabled | Builds close metadata only; does not close real issues.                                                      |
| `.ai-code` scaffold         |                   Working | Generates README, Dockerfile, env example, prompt templates, and coding standards.                           |
| sync-in                     |                   Minimal | Mostly reserved for future isolated/cloud sandbox modes.                                                     |
| Cloud sandbox               |                    Future | Out of scope for current release.                                                                            |
| Multi-agent workflows       |                    Future | Out of scope for current release.                                                                            |

---

## 12. Why the sandbox seam matters

The sandbox seam is one of the most important design ideas in the project.

The seam is:

```python
i_sandboxhandle_run()
```

RALPH does not need to know whether a command runs:

```text
locally
inside Docker
inside Podman
inside a future cloud sandbox
inside a future long-running container
```

RALPH only asks:

```text
Please run this command and give me stdout, stderr, and exit code.
```

That makes the code easier to extend.

Without this seam, `ralph.py` would become full of Docker-specific logic, local subprocess logic, and future cloud-sandbox logic.

With the seam, each provider can hide those details.

High-school explanation:

> The sandbox seam is like a universal wall outlet. RALPH plugs in a command, and the adapter decides where the electricity really comes from.

---

## 13. Docker bind-mount mode explained

Docker bind-mount mode means the host worktree is mounted into the container.

The intended mapping is:

```text
Windows/host worktree folder  ->  /workspace inside Docker
```

Then Docker runs commands with:

```text
-w /workspace
```

That means commands run inside the mounted project folder.

Why this is useful:

1. Docker gives a controlled runtime environment.
2. File changes still appear in the host worktree.
3. The host can inspect Git status after Docker exits.
4. RALPH does not need a separate sync-in/sync-out copy step for this mode.

Simple picture:

```text
Host machine
└── .ai_coder/ai_coder_worktrees/ralph-issue-123-fix-bug/
        |
        | bind mount
        v
Docker container
└── /workspace/
```

If Docker changes:

```text
/workspace/src/ai_coder/example.py
```

the host sees the same change in:

```text
.ai_coder/ai_coder_worktrees/ralph-issue-123-fix-bug/src/ai_coder/example.py
```

Important warning:

> Bind mounts can write back to the host by default, so using a separate worktree is important.

The current design combines:

```text
worktree safety + Docker runtime control
```

That is much safer than mounting the main repo directly.

---

## 14. Docker environment allowlists and redaction

The project does not pass every host environment variable into Docker.

That is good.

Instead, it has separate allowlists:

```text
docker_env_allowlist
docker_secret_env_allowlist
provider_env_allowlist
provider_secret_env_allowlist
```

### Normal env vars

Normal env vars are allowed to appear in logs.

Default normal Docker env:

```text
PYTHONUNBUFFERED
```

If `PYTHONUNBUFFERED` is missing, it may default to:

```text
1
```

### Secret env vars

Secret env vars are separate.

The default secret allowlist is empty.

That means early Docker mode does not automatically pass secrets like:

```text
OPENAI_API_KEY
ANTHROPIC_API_KEY
GH_TOKEN
```

If a secret env var is configured, the Docker command builder checks that it exists and is not empty.

Then command redaction hides configured secret values before logging.

High-school explanation:

> Normal env vars are like classroom supplies. Secret env vars are like passwords. RALPH should not dump passwords into logs.

---

## 15. CodexProvider explained

`CodexProvider` is the first real AI coding-agent provider path.

Its job is to know how to call Codex.

RALPH should not hard-code Codex command details.

The provider builds a command using:

```python
CodexCommandContract.i_codex_command_contract_build()
```

The command uses non-interactive mode:

```text
codex exec
```

It also uses:

```text
--json
--output-last-message
-
```

The `-` is important because it lets the provider pass the prompt through stdin.

Why stdin matters:

- Large GitHub issue bodies do not need to become command arguments.
- Windows paths with spaces are safer.
- Quotes and shell-like characters stay as text.
- Issue body text remains inert.

CodexProvider then parses output.

It prefers structured JSONL output when available.

It can normalize events into:

```text
session
text
tool_call
result
error
```

If structured output is not available, it falls back to plain stdout.

High-school explanation:

> CodexProvider is a translator. It translates RALPH's prompt into a Codex command and translates Codex output back into RALPH-friendly results.

---

## 16. `.ai-code` scaffold explained

The `.ai-code/` folder is for project-specific automation templates.

The scaffold command creates:

```text
.ai-code/README.md
.ai-code/.env.example
.ai-code/Dockerfile
.ai-code/prompts/implementation.md
.ai-code/prompts/review.md
.ai-code/prompts/merge.md
.ai-code/standards/coding-standards.md
```

These files are safe templates.

They are not supposed to contain real secrets.

They help future AI Code workflows know:

- how to implement,
- how to review,
- how to prepare merge work,
- what coding standards to follow,
- what Docker runtime might look like,
- what safe example env values look like.

The scaffold system skips existing files by default.

That is important because generated scaffolding should not accidentally overwrite human work.

---

## 17. How to install

From the project root:

```powershell
poetry install
```

Then run tests:

```powershell
poetry run pytest
```

If Poetry is unavailable in a particular environment, use:

```powershell
pytest
```

For this project, do not use:

```powershell
python -m pytest --capture=tee-sys
```

---

## 18. How to run AI Code

### Run the CLI

```powershell
poetry run ai-coder
```

or:

```powershell
poetry run python -m ai_coder
```

### Run with provided issue data

Example:

```powershell
poetry run ai-coder --issue-number 123 --issue-title "Fix parser bug" --issue-body "Parser fails on empty input." --label bug
```

### Run scaffold

```powershell
poetry run ai-coder scaffold --repo-path .
```

### Run scaffold and overwrite existing files

```powershell
poetry run ai-coder scaffold --repo-path . --overwrite
```

Only use overwrite when you intentionally want generated files to replace existing scaffold files.

---

## 19. Important safety rules

RALPH should follow these rules:

1. Work on one issue at a time.
2. Skip vague, unsafe, blocked, or already assigned issues.
3. Do not edit the main repo directly when worktree mode is required.
4. Create a worktree before agent work.
5. Run commands through the sandbox seam.
6. Treat issue text as inert.
7. Detect explicit completion with `<promise>COMPLETE</promise>`.
8. Run tests before committing.
9. Commit only after completion and passing tests.
10. Preserve worktrees when unsafe.
11. Do not create PRs automatically in the current release.
12. Do not close GitHub issues automatically in the current release.
13. Redact configured secret values from logs.

---

## 20. Important design strengths

### 1. The public seams are clear

Good examples:

```text
i_ralph_run()
i_repository_start()
i_repository_context_discover()
i_github_issue_select_actionable()
i_worktree_create()
i_worktree_cleanup()
i_sandbox_start()
i_prompt_resolve()
i_prompt_preprocess()
i_agent_provider_create()
i_orchestrator_run()
i_completion_detector_detect()
i_test_runner_run()
i_sync_out_merge()
i_pull_request_draft_build()
i_scaffold_create()
```

These names make it easy to see where callers cross module boundaries.

### 2. Result objects make behavior testable

Many modules return data classes instead of raw strings.

Examples:

```text
RalphResult
RepositoryStartResult
GitHubIssueSelectionResult
WorktreeCreateResult
SandboxStartResult
CommandResult
TestRunResult
SyncMergeResult
PullRequestDraftResult
GitHubIssueCloseResult
ScaffoldResult
```

That makes tests easier because tests can check fields directly.

### 3. Safety is built into the workflow

The current design blocks dirty host repos, uses worktrees, runs tests, uses dry-run GitHub automation, and preserves unsafe worktrees.

### 4. The sandbox seam is strong

This is one of the best architectural choices in the project.

It allows local and Docker execution to share the same command interface.

### 5. CodexProvider is correctly isolated

RALPH does not hard-code Codex command details.

That makes future providers easier to add.

---

## 21. Code issues and improvements to consider later

These are not emergency problems, but they are good cleanup candidates.

### Improvement 1 — Remove or merge the old `docker_sandbox_provider` module

There is a separate file:

```text
src/ai_coder/docker_sandbox_provider/docker_sandbox_provider.py
```

It looks older and much less complete than:

```text
src/ai_coder/sandbox_provider/sandbox_provider.py
```

The real Docker bind-mount implementation appears to live in `sandbox_provider/sandbox_provider.py`.

Recommendation:

> If no tests or imports need the old `docker_sandbox_provider` module, archive it or remove it in a future cleanup issue.

### Improvement 2 — Clean old copied project names in comments

Some utility files still have comments pointing to older projects, such as:

```text
src/test_browser_mcp/...
src/langgraph_projects/...
```

This is not usually a runtime bug, but it can confuse future maintainers.

Recommendation:

> Rename old comment paths to `src/ai_coder/...` when touching those files for related cleanup.

### Improvement 3 — Fix the `setup_config.__repr__()` formatting

In `setup_config.py`, the `__repr__()` string appears to concatenate the LLM part and GitHub allowlist part without a visible comma separator.

Current shape:

```python
f"llm={'Initialized' if self.llm else 'Not Initialized'}"
f"github_actionable_label_allowlist={...}"
```

That will display like:

```text
llm=Not Initializedgithub_actionable_label_allowlist=...
```

Recommendation:

> Add a comma and space after the `llm` text in a future cleanup issue.

### Improvement 4 — Consider reducing top-level exports

The top-level package file:

```text
src/ai_coder/__init__.py
```

currently exports worktree symbols.

That is not wrong, but it may make the top-level package look like it is only about worktrees.

Recommendation:

> Either keep the top-level package minimal or export the most important public seams intentionally.

### Improvement 5 — Keep `my_utils` isolated

Some `my_utils` modules are useful later, but not central to the current RALPH workflow.

Examples:

```text
postgres_store_loader.py
redis_saver_loader.py
token_usage.py
configuration.py
database_version_info.py
```

Recommendation:

> Avoid importing these modules from the core RALPH path unless they are actually needed.

That prevents optional dependencies from breaking the main tracer-bullet workflow.

### Improvement 6 — Update old wording that says behavior is stubbed

The old explanation said many areas were stubs.

Some are no longer stubs.

For example:

- worktree creation is now real,
- sandbox-backed tests are real,
- sync_out can commit real changes,
- Docker bind-mount provider exists,
- scaffold generation exists.

Recommendation:

> Update docs whenever a placeholder becomes real behavior.

---

## 22. How to add a future agent provider

A future provider should follow the existing pattern.

Steps:

1. Add a new provider class in `agent_provider.py` or a provider submodule.
2. Give it this method:

```python
i_agent_provider_run(prompt: str) -> AgentResponse
```

3. Keep provider-specific command construction inside the provider.
4. Pass prompts through stdin when possible.
5. Return `AgentResponse`.
6. Return normalized `AgentProviderEvent` values when possible.
7. Add the provider name to `SUPPORTED_AGENT_NAMES` in `setup_config.py`.
8. Update `i_agent_provider_create()`.
9. Add tests.

Example future providers:

```text
claude
opencode
local_mock
```

The rule is:

> RALPH should choose a provider, but the provider should know its own command details.

---

## 23. How to add a future sandbox provider

A future sandbox provider should follow the current sandbox seam.

It should provide:

```python
i_sandboxhandle_run(command, cwd=None, stdin_text="")
i_sandboxhandle_close()
```

It should return:

```python
CommandResult(stdout, stderr, exit_code)
```

Possible future sandbox providers:

```text
podman
long_running_docker
cloud_sandbox
test_fake
```

The rule is:

> RALPH should not care where commands run. It should only care about the normalized command result.

---

## 24. What is in scope now

Current / near-term scope:

1. Python project.
2. Windows 11 target.
3. Poetry install and pytest test flow.
4. One issue at a time.
5. Worktree safety.
6. Local sandbox.
7. Docker bind-mount sandbox.
8. Fake test agent.
9. CodexProvider path.
10. Prompt resolving and preprocessing.
11. Completion detection.
12. Test running through sandbox.
13. Git commit after passing tests.
14. Worktree cleanup or preservation.
15. Future-safe PR draft metadata.
16. Future-safe issue-close metadata.
17. `.ai-code` scaffolding.

---

## 25. What is intentionally future work

Future work includes:

1. Real automatic pull request creation.
2. Real automatic GitHub issue closing.
3. Long-running Docker containers.
4. Cloud sandbox providers.
5. Multi-agent workflows.
6. Full copy-in/copy-out sync for isolated sandboxes.
7. Stronger secret managers.
8. More real AI provider adapters.
9. More advanced completion detection.
10. Production deployment automation.

These are intentionally not all built at once.

That is good.

A small, working, safe workflow is better than a large system that is risky and hard to debug.

---

## 26. Final high-school summary

`ai_coder` is building **AI Code**, and **RALPH** is the coding agent inside it.

RALPH is like a careful student developer.

It should:

```text
Read one issue.
Pick a safe issue.
Create a separate work area.
Run commands through a sandbox.
Ask an agent to work.
Look for the completion signal.
Run tests.
Commit only if tests pass.
Prepare PR/close metadata safely.
Preserve work if something goes wrong.
```

The strongest parts of the current design are:

1. Clear public seams.
2. Safety-first worktree behavior.
3. Local and Docker sandbox support behind one command interface.
4. Inert issue text handling.
5. Exact completion token detection.
6. Test-before-commit workflow.
7. Placeholder GitHub automation instead of unsafe automatic closing.
8. Scaffold files for future project-specific automation.

The project is moving in the right direction because it is growing one small, testable slice at a time.

---

## 27. Background references used for concept alignment

These references support the general technical concepts used in the explanation:

- Poetry supports packages stored in a `src/` directory through `pyproject.toml`.
- pytest documents good practices for test layout and import behavior.
- Git worktree is the official Git feature for managing multiple working trees attached to one repository.
- Docker bind mounts map host files or directories into containers and can allow container writes to affect host files.
