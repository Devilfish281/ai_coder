# ai_coder Program Explanation

## Purpose

`ai_coder` is a Python learning project that is building **RALPH**.

**RALPH** means:

```text
R = Repository
A = Autonomous
L = Local
P = Patch
H = Helper
```

In plain English, RALPH is meant to become a coding helper that can look at GitHub issues, choose one issue, create a safe place to work, ask an AI coding agent to make a fix, run tests, sync the result back, and close the issue only when the work is safe and complete.

This project is inspired by Sandcastle, but it is being rebuilt in Python as a smaller learning project. The current version is a **tracer bullet**. That means it does not try to build the whole final system at once. Instead, it builds a thin end-to-end path that proves the idea works.

## High-Level Program Flow

Think of the whole program like a school assembly line.

Each module has one job. RALPH is the manager that calls each module in the correct order.

```text
User runs ai-coder
        |
        v
main module reads command-line arguments and config
        |
        v
setup_config loads .env settings
        |
        v
ralph starts the 12-step RALPH workflow
        |
        v
repository_context selects the repo
        |
        v
github_issues loads or selects an issue
        |
        v
worktree_manager creates a safe worktree plan
        |
        v
sandbox_provider starts a local/test sandbox
        |
        v
prompt_resolver gets prompt text
        |
        v
prompt_preprocessor fills placeholders
        |
        v
agent_provider provides a mock coding agent
        |
        v
orchestrator runs the agent loop
        |
        v
completion_detector explains completion status
        |
        v
test_runner stubs pytest execution
        |
        v
sync_out stubs merge/sync
        |
        v
github_issues stubs issue closing
        |
        v
worktree_manager decides preserve/cleanup behavior
```

## Current RALPH Workflow

Your `ralph.py` currently follows this 12-step roadmap:

```text
1. Start with a Git repository.
2. Read open GitHub issues.
3. Pick one actionable issue.
4. Create a safe working copy using a Git worktree.
5. Start a sandbox or local execution environment.
6. Give an AI coding agent a prompt.
7. Let the agent edit files, run commands, and commit changes.
8. Detect whether the task is complete.
9. Run tests.
10. Sync or merge the finished work back to the host repo.
11. Close the GitHub issue only after tests pass and the fix is committed.
12. Preserve the worktree if there are uncommitted changes or a failure.
```

Right now, many steps are still safe stubs. A **stub** is a simple placeholder implementation. It returns a result object and message, but it does not do the full real-world action yet.

For example:

- `i_worktree_create()` builds the Git worktree command but does not run it yet.
- `i_test_runner_run()` returns a passing test result but does not run pytest yet.
- `i_sync_out_merge()` says sync is stubbed and does not merge real commits yet.
- `i_github_issue_close()` does not actually close a GitHub issue yet.

That is good for a tracer bullet because it lets the whole flow run safely while you build one real feature at a time.

## Project Layout

Your project uses a `src/` layout:

```text
ai_coder/
├── pyproject.toml
├── README.md
├── src/
│   ├── ai_coder/
│   │   ├── __main__.py
│   │   ├── setup_config.py
│   │   ├── agent_provider/
│   │   ├── completion_detector/
│   │   ├── display/
│   │   ├── github_issues/
│   │   ├── main/
│   │   ├── my_utils/
│   │   ├── orchestrator/
│   │   ├── prompt_preprocessor/
│   │   ├── prompt_resolver/
│   │   ├── ralph/
│   │   ├── repository_context/
│   │   ├── sandbox_provider/
│   │   ├── sync_in/
│   │   ├── sync_out/
│   │   ├── test_runner/
│   │   └── worktree_manager/
│   └── prompts/
│       ├── github_issue.md
│       ├── github_issue_template.md
│       └── prompt.md
└── var/
    └── logs/
```

The `src/` layout separates project source code from tests, configuration, logs, and temporary files.

---

# Module-by-Module Explanation

## `pyproject.toml`

This file is the project configuration file.

It tells Poetry:

- the project name is `ai-coder`,
- the project uses Python `>=3.12,<3.14`,
- the package code is under `src/ai_coder`,
- the dev test tool is `pytest`.

It also tells pytest:

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

That means pytest should look in `tests/` for tests and should put `src/` on the Python import path.

## `src/ai_coder/__main__.py`

This file lets the user run the program like this:

```powershell
python -m ai_coder
```

It does three main things:

1. Loads `.env` once.
2. Gets the global setup config and logger.
3. Calls `main()`.

It also handles `KeyboardInterrupt`, so if the user presses `Ctrl+C`, the program logs that it was interrupted instead of crashing with a messy traceback.

## `src/ai_coder/setup_config.py`

This module manages project configuration.

It reads values from `.env`, such as:

- `OPENAI_MODEL`
- `TESTING_FLAG`
- `ISSUE_NUMBER`
- `ISSUE_TITLE`
- `ISSUE_BODY`
- `LABEL`
- `MAX_ITERATIONS`
- `PROMPT_PATH`
- `GITHUB_ISSUE_PATH`
- `GITHUB_ISSUE_DIR`
- `GITHUB_ISSUE_FILE_NAME`

The main class is:

```python
class c_setup_config(BaseModel):
```

This class is a singleton. That means the project tries to create only one shared setup object.

Important methods:

### `get_instance()`

Returns the single shared config object.

### `get_env()`

Reads an environment variable and returns a clean string.

### `env_bool()`

Turns values like `"true"`, `"yes"`, or `"1"` into `True`.

### `env_int()`

Turns an environment variable into an integer.

### `resolve_github_issue_path()`

Builds the path to the local GitHub issue markdown file.

Your priority order is:

```text
1. GITHUB_ISSUE_DIR + GITHUB_ISSUE_FILE_NAME
2. GITHUB_ISSUE_DIR + file name from GITHUB_ISSUE_PATH
3. directory from GITHUB_ISSUE_PATH + GITHUB_ISSUE_FILE_NAME
4. GITHUB_ISSUE_PATH
5. default src/prompts/github_issue.md
```

### `has_user_github_issue()`

Returns `True` if the user provided issue data through `.env` or command-line values.

### `validate_initialization()`

Checks that the config is usable before the program runs.

It checks:

- user issue data is complete if provided,
- `MAX_ITERATIONS` is at least `1`,
- `OPENAI_MODEL` is not empty,
- `PROMPT_PATH` exists,
- optionally, OpenAI API key is present if `require_llm=True`.

## `src/ai_coder/main/main.py`

This is the command-line entry point.

It uses `argparse` to read command-line flags like:

```powershell
--issue-number
--issue-title
--issue-body
--label
--max-iterations
--prompt-path
```

Then it decides:

- Did the user provide an issue?
- Should RALPH use that issue?
- Should RALPH read a local issue file?
- Should RALPH later read real GitHub issues?

The most important line is:

```python
result = i_ralph_run(...)
```

That line passes control to RALPH.

Important helper functions:

### `_has_user_issue_args()`

Checks whether issue fields were provided.

### `_build_fake_issue()`

Builds a `GitHubIssue` object from command-line arguments.

### `_write_info()`, `_write_warning()`, `_write_error()`

These functions either log messages or print messages, depending on how `main()` is called.

## `src/ai_coder/ralph/ralph.py`

This is the heart of the program.

`ralph.py` is the high-level workflow controller.

The main public interface is:

```python
i_ralph_run()
```

This function runs the 12-step RALPH workflow.

Current flow:

1. Start repository context with `i_repository_start()`.
2. Resolve issues with `_resolve_issue_source()`.
3. Pick one issue with `i_github_issue_select()`.
4. Create a worktree plan with `i_worktree_create()`.
5. Start a sandbox stub with `i_sandbox_start()`.
6. Build and preprocess the prompt.
7. Run the agent loop with `i_orchestrator_run()`.
8. Detect completion with `i_completion_detector_detect()`.
9. Run tests with `i_test_runner_run()`.
10. Sync/merge with `i_sync_out_merge()`.
11. Close the issue with `i_github_issue_close()`.
12. Preserve or clean up the worktree with `i_worktree_preserve()`.

Important data class:

```python
@dataclass(frozen=True)
class RalphResult:
```

This object is the final result of a RALPH run.

It contains:

- `selected_issue`
- `prompt`
- `orchestrator_result`
- `completed`
- `message`

## `src/ai_coder/agent_provider/agent_provider.py`

This module defines how RALPH talks to an AI coding agent.

Important pieces:

### `COMPLETE_TOKEN`

```text
<promise>COMPLETE</promise>
```

This is the exact signal that means the agent says the task is done.

### `AgentResponse`

A small result object with:

- `output`
- `error`

### `AgentProvider`

A protocol. A protocol is like a promise that says:

> Any real agent provider must have this method.

```python
i_agent_provider_run(prompt: str) -> AgentResponse
```

### `MockAgentProvider`

This is the fake agent used for the tracer bullet.

It does not call OpenAI, Claude, Codex, or any external service.

It returns deterministic output, which makes tests easy and safe.

## `src/ai_coder/orchestrator/orchestrator.py`

The orchestrator is the loop runner.

It repeatedly calls the agent until one of these happens:

- the agent output contains `<promise>COMPLETE</promise>`,
- max iterations are reached,
- the agent returns an error.

Main interface:

```python
i_orchestrator_run()
```

Input:

- `agent_provider`
- `prompt`
- `max_iterations`
- `completion_token`

Output:

```python
OrchestratorResult
```

This result includes:

- `completed`
- `iterations`
- `outputs`
- `final_output`
- `error`

High-school explanation:

The orchestrator is like a teacher asking:

> Are you done yet?

It asks the agent again and again, but only up to the maximum number of tries.

## `src/ai_coder/completion_detector/completion_detector.py`

This module explains whether completion happened.

The actual completion check currently happens in the orchestrator. This module wraps that boolean into a clearer result object.

Main interface:

```python
i_completion_detector_detect(completed: bool)
```

If `completed=True`, it returns:

```text
The orchestrator detected the completion signal.
```

If `completed=False`, it returns:

```text
The orchestrator did not detect the completion signal.
```

## `src/ai_coder/github_issues/github_issues.py`

This module handles GitHub issue data.

Important data classes:

### `GitHubIssue`

Represents one issue.

Fields:

- `number`
- `title`
- `body`
- `labels`
- `state`
- `blocked_by`

### `GitHubIssueCloseResult`

Represents the result of trying to close an issue.

Fields:

- `issue_number`
- `closed`
- `message`

Important interfaces:

### `i_github_issue_from_file()`

Reads a local markdown issue file like:

```text
src/prompts/github_issue.md
```

It can understand this format:

```markdown
# Create new issue

## Add a title

Fix local RALPH loop

## Add a description

### ISSUE_BODY

...

### LABELS

Polish
```

It extracts:

- title from `## Add a title`,
- body from `## Add a description`,
- labels from `### LABELS`.

### `i_github_issue_list()`

Runs:

```powershell
gh issue list
```

and turns GitHub CLI JSON output into `GitHubIssue` objects.

This is not ideal for unit tests, so tests should use fake issue data or monkeypatch this behavior.

### `i_github_issue_select()`

Picks the best issue to work on.

Priority order:

```text
1. bug
2. tracer
3. feature / enhancement
4. polish
5. refactor
6. anything else
```

It also avoids issues blocked by another open issue.

### `i_github_issue_close()`

Currently a stub. It does not close GitHub issues yet.

That is good because closing issues should only happen after:

- tests pass,
- work is committed,
- sync/merge succeeds.

## `src/ai_coder/worktree_manager/worktree_manager.py`

This module manages Git worktree planning.

A Git worktree lets the program create a separate working folder for a branch. That means RALPH can work on code without directly changing the main repo folder.

Important data classes:

### `WorktreeCreateResult`

Contains:

- `repo_path`
- `worktree_path`
- `branch_name`
- `command`
- `created`
- `message`

### `WorktreePreserveResult`

Contains:

- `preserved`
- `reason`

Important interfaces:

### `i_worktree_sanitize_branch_name()`

Turns a raw title into something safer for a branch name.

Example:

```text
Fix Local RALPH Loop!
```

becomes something like:

```text
fix-local-ralph-loop
```

### `i_worktree_branch_name()`

Creates a branch name like:

```text
ralph/issue-7-fix-local-ralph-loop
```

### `i_worktree_create_command()`

Builds the command list for:

```powershell
git worktree add -b ...
```

It does not run the command yet.

### `i_worktree_create()`

Builds a worktree result object.

Currently, it is still a stub:

```python
created=False
```

### `i_worktree_preserve()`

Decides if a worktree should be preserved.

It preserves when:

- uncommitted changes exist,
- RALPH did not complete.

It does not preserve when:

- RALPH completed successfully,
- there are no uncommitted changes.

## `src/ai_coder/repository_context/repository_context.py`

This module chooses the repository path.

Main interface:

```python
i_repository_start()
```

If no path is passed, it uses:

```python
Path.cwd()
```

That means it treats the current terminal folder as the repo.

Current behavior is a stub because it does not yet check whether the path is really a Git repository.

Future improvement:

- check for `.git`,
- or run `git rev-parse --show-toplevel`.

## `src/ai_coder/sandbox_provider/sandbox_provider.py`

This module defines where commands run.

Important data classes:

### `CommandResult`

Contains:

- `stdout`
- `stderr`
- `exit_code`

### `SandboxStartResult`

Contains:

- `working_directory`
- `provider_name`
- `started`
- `message`

Important classes and functions:

### `LocalSandboxProvider`

This can run commands locally using `subprocess.run()`.

Example future use:

```python
provider.i_sandbox_run(("poetry", "run", "pytest"))
```

### `i_sandbox_start()`

Currently a stub. It returns a successful sandbox start result but does not start Docker, Podman, or a real isolated environment.

For now, that is okay because this is a tracer bullet.

## `src/ai_coder/prompt_resolver/prompt_resolver.py`

This module gets the raw prompt text.

Main interface:

```python
i_prompt_resolve()
```

It supports two input styles:

### Inline prompt

```python
i_prompt_resolve(inline_prompt="Fix the bug")
```

### Prompt file

```python
i_prompt_resolve(prompt_path="src/prompts/prompt.md")
```

It prevents using both at the same time.

If the prompt file does not exist, it raises a helpful `FileNotFoundError`.

## `src/ai_coder/prompt_preprocessor/prompt_preprocessor.py`

This module fills placeholders inside a prompt.

Main interface:

```python
i_prompt_preprocess(raw_prompt, values)
```

Example:

```text
Issue #{{ISSUE_NUMBER}}: {{ISSUE_TITLE}}
```

with:

```python
{
    "ISSUE_NUMBER": 7,
    "ISSUE_TITLE": "Fix local RALPH loop",
}
```

becomes:

```text
Issue #7: Fix local RALPH loop
```

Important security note:

Right now, this only does placeholder replacement. That is good and safe for the first tracer bullet.

Future command expansion like:

```text
!`git log --oneline -5`
```

should be added carefully later, because command execution can be dangerous.

## `src/ai_coder/test_runner/test_runner.py`

This module represents test execution.

Main interface:

```python
i_test_runner_run()
```

Current behavior:

- returns `passed=True`,
- stores the command `("poetry", "run", "pytest")`,
- says test running is stubbed.

Future behavior:

- actually run `poetry run pytest`,
- if Poetry is unavailable, run `pytest`,
- return real stdout, stderr, and exit code.

## `src/ai_coder/sync_in/sync_in.py`

This module will eventually copy files into a sandbox or worktree.

Main interface:

```python
i_sync_in_run(source_path, target_path)
```

Current behavior:

- returns source and target paths,
- says `changed=False`.

It is a placeholder for future file-copy behavior.

## `src/ai_coder/sync_out/sync_out.py`

This module will eventually copy or merge work back from a sandbox/worktree to the host repo.

Important data classes:

### `SyncOutResult`

For file-copy sync.

### `SyncMergeResult`

For merge/sync status.

Important interfaces:

### `i_sync_out_run()`

Currently returns `changed=False`.

### `i_sync_out_merge()`

If RALPH completed, it returns a stub message saying sync is not implemented yet.

If RALPH did not complete, it skips sync.

## `src/ai_coder/display/display.py`

This module controls user-facing output.

### `SilentDisplay`

Stores messages in a list.

This is useful for tests because it avoids printing to the terminal.

### `ConsoleDisplay`

Prints messages to the terminal.

This is useful when running locally.

## `src/ai_coder/my_utils/env_loader.py`

This module loads `.env` once per process.

Main interface:

```python
load_dotenv_once()
```

It uses a lock so multiple threads do not load `.env` at the same time.

This protects your config from being loaded repeatedly.

## `src/ai_coder/my_utils/logger_setup.py`

This module builds the project logger.

It supports:

- console logging,
- rotating file logging,
- asynchronous file writing,
- environment-variable configuration.

Important issue to notice:

Some internal attribute names still say `_test_browser_mcp_handler`. That looks copied from an older project. It works as an internal marker, but it should eventually be renamed to something like `_ai_coder_handler`.

## `src/ai_coder/my_utils/llm_loader.py`

This module lazily creates a `ChatOpenAI` object.

Main interfaces:

- `init_llm_once()`
- `get_llm_or_init()`

It uses a lock and global flag to avoid initializing the LLM repeatedly.

Current RALPH tracer-bullet code does not rely on a real LLM yet because it uses `MockAgentProvider`.

## `src/ai_coder/my_utils/token_usage.py`

This module tracks token usage against hardcoded rate-limit tables.

It reads:

```text
token_usage_tier.json
```

It starts a background thread to reset token usage every 60 seconds.

Important note:

This module is much bigger than the rest of the tracer-bullet code. It may be useful later, but it is not part of the simple RALPH loop yet.

## `src/ai_coder/my_utils/configuration.py`

This module looks like a LangGraph helper copied from another project.

It defines:

- `ConfigSchema`
- `Configuration`
- `TodoKind`

It is not central to RALPH right now.

## `src/ai_coder/my_utils/postgres_store_loader.py`

This module opens a LangGraph `PostgresStore`.

It includes fallback behavior when DNS resolution fails.

It is not part of the current RALPH tracer bullet.

Also, it imports packages like `psycopg` and `langgraph.store.postgres`. If those dependencies are not installed, importing this module could fail.

## `src/ai_coder/my_utils/redis_saver_loader.py`

This module opens a LangGraph `RedisSaver`.

It includes fallback behavior when DNS resolution fails.

It is not part of the current RALPH tracer bullet.

Also, it imports Redis-related packages. If those dependencies are not installed, importing this module could fail.

## `src/prompts/prompt.md`

This is the project prompt file.

RALPH merges this file with the built-in default RALPH prompt.

This means RALPH gets:

1. core RALPH instructions,
2. project-specific instructions from `prompt.md`.

## `src/prompts/github_issue.md`

This is the local fallback GitHub issue file.

If no issue is passed by the command line or `.env`, and `TESTING_FLAG` is false, RALPH can load this local file before trying the real GitHub CLI.

## `src/prompts/github_issue_template.md`

This is a template for creating local issue files.

It helps keep issue title, body, and labels consistent.

---

# What Happens When You Run the Program

## Example Command

```powershell
poetry run python -m ai_coder
```

## Step-by-Step Runtime

### 1. Python starts `__main__.py`

Python finds:

```text
src/ai_coder/__main__.py
```

and runs it.

### 2. `.env` is loaded

The project calls:

```python
load_dotenv_once()
```

### 3. Config and logger are created

The project calls:

```python
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()
```

### 4. `main()` runs

`main()` validates config, reads command-line arguments, and decides whether an issue was provided by the user.

### 5. `i_ralph_run()` runs

RALPH starts the 12-step workflow.

### 6. RALPH selects an issue

RALPH checks sources in this order:

```text
1. issues passed directly into i_ralph_run()
2. testing issue if TESTING_FLAG=true
3. user issue from .env or command line
4. local github_issue.md file
5. real gh issue list command
```

### 7. RALPH builds the prompt

It combines:

```text
DEFAULT_RALPH_PROMPT_TEMPLATE
+
src/prompts/prompt.md
```

Then it replaces placeholders like:

```text
{{ISSUE_NUMBER}}
{{ISSUE_TITLE}}
{{ISSUE_BODY}}
{{COMPLETE_TOKEN}}
```

### 8. RALPH runs the mock agent

The mock agent returns output that includes:

```text
<promise>COMPLETE</promise>
```

### 9. The orchestrator detects completion

The orchestrator sees the completion token and returns:

```python
completed=True
```

### 10. RALPH finishes

RALPH returns a `RalphResult`.

---

# Current Implementation Status

| Area | Current Status | Explanation |
|---|---|---|
| Command-line entry | Working tracer bullet | `main.py` can call RALPH. |
| Config loading | Working | `.env` and defaults are loaded by `setup_config.py`. |
| GitHub issue model | Working | `GitHubIssue` data model exists. |
| Local issue file parsing | Working | `github_issue.md` can be parsed. |
| Issue selection | Working | Bug/tracer/feature/polish/refactor priority exists. |
| Prompt resolving | Working | Inline and file prompt loading exist. |
| Prompt preprocessing | Working | Placeholder replacement exists. |
| Agent provider | Mock only | No real Claude/Codex/OpenCode provider yet. |
| Orchestrator | Basic working | Handles max iterations and completion token. |
| Repository context | Stub | Does not validate real Git repo yet. |
| Worktree creation | Stub | Builds command but does not run Git yet. |
| Sandbox startup | Stub | Does not start real Docker/Podman yet. |
| Test runner | Stub | Does not run real pytest yet. |
| Sync out | Stub | Does not merge or copy commits yet. |
| GitHub close | Stub | Does not close real GitHub issues yet. |
| Worktree preserve | Basic decision only | Does not inspect real Git status yet. |

---

# Important Design Strengths

## 1. Clear module seams

Most modules expose a small public interface like:

```text
i_ralph_run()
i_orchestrator_run()
i_prompt_resolve()
i_prompt_preprocess()
i_worktree_create()
i_github_issue_select()
```

That is good because callers do not need to know the internal details.

## 2. Result objects are easy to test

The project uses many small frozen data classes like:

```python
@dataclass(frozen=True)
class OrchestratorResult:
```

This is good because tests can check return values directly.

## 3. The mock agent is safe

`MockAgentProvider` lets you test the full RALPH loop without spending money or calling real AI services.

## 4. The tracer-bullet approach is correct

The project does not try to build Docker, GitHub, OpenAI, and Git worktree automation all at once.

That is the right learning-project approach.

---

# Important Issues and Improvements

## 1. Top-level `ai_coder/__init__.py` exports worktree symbols

Your top-level package currently exports only worktree-manager objects.

That is not wrong technically, but it is confusing.

Better long-term:

```python
from __future__ import annotations
```

Keep worktree exports inside:

```text
src/ai_coder/worktree_manager/__init__.py
```

## 2. Some files still have old project names in comments

Examples:

```text
src/test_browser_mcp/tools/my_utils/...
src/asset_processing_service/my_utils/...
src/langgraph_projects/my_utils/...
```

These are comments, not runtime errors, but they make the project harder to understand.

They should eventually be renamed to `ai_coder`.

## 3. `logger_setup.py` still uses `_test_browser_mcp_handler`

This is an internal marker name copied from another project.

It should eventually become:

```text
_ai_coder_handler
_ai_coder_handler_type
```

## 4. Global config makes tests more fragile

You intentionally keep this pattern:

```python
load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()
```

That is okay.

But tests that change environment variables must refresh the module-level globals after `monkeypatch.setenv()`.

Example:

```python
import ai_coder.ralph.ralph as ralph_module
from ai_coder.setup_config import c_setup_config


def _refresh_ralph_config() -> None:
    c_setup_config._instance = None
    ralph_module.setup_config = c_setup_config.get_instance()
    ralph_module.logger = ralph_module.setup_config.get_logger()
```

## 5. Step 6 should be split for clarity

Your RALPH Step 6 should be written like this:

```text
6a. Resolve prompt text from file or inline prompt.
6b. Preprocess prompt after sandbox is ready.
```

This keeps `PromptResolver` and `PromptPreprocessor` as two separate jobs.

## 6. Some utility modules may be extra for this tracer bullet

These modules are not part of the current RALPH loop:

```text
postgres_store_loader.py
redis_saver_loader.py
token_usage.py
configuration.py
database_version_info.py
```

They can stay for now, but they are not needed for the first RALPH tracer bullet.

If imports from these modules cause dependency problems, consider moving them to `archive/` or removing them until needed.

---

# Recommended Next Steps

## Step 1: Make repository validation real

Update:

```python
i_repository_start()
```

so it checks that the selected path is actually inside a Git repo.

## Step 2: Make test runner real

Update:

```python
i_test_runner_run()
```

so it actually runs:

```powershell
poetry run pytest
```

Then fallback to:

```powershell
pytest
```

## Step 3: Make worktree creation real

Update:

```python
i_worktree_create()
```

so it actually runs the command from `i_worktree_create_command()`.

## Step 4: Detect real uncommitted changes

Add a function that runs:

```powershell
git status --porcelain
```

Then use that result in:

```python
i_worktree_preserve()
```

## Step 5: Keep GitHub issue closing last

Do not close real GitHub issues until the project can prove:

```text
agent completed
tests passed
work was committed
sync succeeded
```

---

# Simple Mental Model

Imagine RALPH as a robot mechanic.

```text
GitHub issue = repair ticket
Repository = garage
Worktree = safe repair bay
Sandbox = safety cage
Prompt = instruction sheet
Agent = robot mechanic
Orchestrator = supervisor
Completion detector = done checker
Test runner = quality inspector
Sync out = move repaired car back
GitHub close = mark repair ticket complete
Preserve worktree = keep the repair bay if something went wrong
```

Right now, the robot mechanic is still in training.

It can walk through the whole repair process, but many tools are fake tools. That is okay because the goal is to prove the workflow first.

---

# References

- Poetry `pyproject.toml` documentation: https://python-poetry.org/docs/pyproject/
- pytest test discovery documentation: https://docs.pytest.org/en/stable/explanation/goodpractices.html
- Python `dataclasses` documentation: https://docs.python.org/3/library/dataclasses.html
- Python `pathlib` documentation: https://docs.python.org/3/library/pathlib.html
