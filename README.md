# AI Code

AI Code is a Python project for safely automating one GitHub issue at a time.

RALPH is the coding agent inside AI Code. In Release 1, RALPH is a local single-issue tracer bullet: it proves the safe workflow with one fake or provided issue before the project grows into broader automation.

RALPH is not production-ready full autonomy. It should behave like a careful junior developer: work in a safe Git worktree, run commands through a sandbox seam, run tests, commit only successful work, and preserve failed or dirty work for human review.

## What AI Code does

AI Code helps a solo Python developer repeat the issue-fixing workflow safely.

The long-term workflow is:

1. Read or receive one GitHub issue.
2. Decide whether the issue is actionable.
3. Create an isolated Git worktree.
4. Start a sandbox provider.
5. Resolve and preprocess a prompt.
6. Run an agent provider.
7. Detect completion with `<promise>COMPLETE</promise>`.
8. Run tests.
9. Commit only after tests pass.
10. Preserve failed or dirty worktrees for inspection.
11. Keep pull request creation and issue closing disabled until a safe future workflow enables them.

## What problem AI Code solves

Fixing GitHub issues with an AI coding tool can be repetitive and risky.

A developer must usually:

- read the issue,
- decide whether the work is safe and actionable,
- create a branch or worktree,
- prepare a prompt,
- run an agent,
- watch command output,
- run tests,
- commit safe work,
- preserve failed attempts,
- avoid closing issues too early,
- avoid leaking secrets in logs.

AI Code puts those steps behind small Python seams so each part can be tested and improved one tracer-bullet slice at a time.

## What RALPH does

RALPH is the high-level workflow inside AI Code.

For the current Release 1 path, RALPH can:

- receive one fake or provided issue,
- select one actionable issue,
- create a safe worktree,
- start the local sandbox adapter,
- resolve prompt text,
- preprocess prompt placeholders after the sandbox is ready,
- run the mock agent through the sandbox seam,
- detect `<promise>COMPLETE</promise>`,
- run the configured test command,
- commit and sync only successful work,
- preserve failed or dirty worktrees,
- return a clear status and readable output.

## Current Release 1 scope

Release 1 is the local single-issue tracer bullet.

It focuses on proving the end-to-end safety model with local execution:

- one fake or provided issue,
- local sandbox mode,
- mock agent provider by default,
- prompt resolving and preprocessing,
- explicit completion detection,
- pytest execution,
- safe worktree creation,
- safe commit/sync behavior when tests pass,
- preservation on failure or dirty state,
- visible progress output.

This release is intentionally small. The goal is to prove that the workflow works before adding more automation.

## What is intentionally future work

These features are not automatic Release 1 behavior:

- processing multiple issues in one run,
- automatic pull request creation,
- automatic GitHub issue closing,
- production deployment automation,
- long-running Docker containers,
- cloud sandbox providers,
- multi-agent workflows,
- full autonomous GitHub issue management.

Docker and CodexProvider are later-phase or optional paths. Keep the default Release 1 command local and mock-provider friendly unless you are specifically testing those paths.

## Requirements

- Windows 11 target environment
- Python `>=3.12,<3.14`
- Poetry
- Git
- pytest through the Poetry dev dependency group
- A Git repository for worktree-based runs

## Install

Clone the repository and install dependencies with Poetry:

```powershell
git clone <repo-url>
cd ai_coder
poetry install
```

Poetry reads `pyproject.toml`, installs the project dependencies, and uses `poetry.lock` when present for repeatable dependency versions.

## Configuration overview

`src/ai_coder/setup_config.py` is the final runtime source of truth.

The expected flow is:

1. Load defaults and environment values.
2. Parse CLI arguments.
3. Validate CLI values before applying them.
4. Apply valid CLI values into `setup_config.py`.
5. Validate the final configuration.
6. Run RALPH using the final setup config values.

Useful user-facing configuration values include:

| Name                 | Purpose                                                                 |
| -------------------- | ----------------------------------------------------------------------- |
| `REPO_PATH`          | Local repository path RALPH should use.                                 |
| `PROMPT_PATH`        | Prompt markdown file path.                                              |
| `GITHUB_REPO`        | GitHub owner/repository name.                                           |
| `RALPH_AGENT`        | Agent provider name, usually `mock` for Release 1.                      |
| `RALPH_SANDBOX_MODE` | Sandbox mode, usually `local` for Release 1.                            |
| `TEST_COMMAND`       | Test command, defaulting to `poetry run pytest`.                        |
| `DRY_RUN`            | Safety mode for future GitHub automation.                               |
| `CODEX_COMMAND`      | Codex command path or name when using the optional Codex provider path. |

CLI values should be validated before they change the runtime configuration.

## Run the local Release 1 tracer bullet

Use the console script:

```powershell
poetry run ai-coder --repo-path . --issue-number 57 --issue-title "Add Release 1 user documentation" --issue-body "Document Release 1 usage." --label "polish" --agent mock --sandbox local --dry-run
```

If the console script is not available, use the package module entry point:

```powershell
poetry run python -m ai_coder --repo-path . --issue-number 57 --issue-title "Add Release 1 user documentation" --issue-body "Document Release 1 usage." --label "polish" --agent mock --sandbox local --dry-run
```

What to expect:

- RALPH validates configuration.
- RALPH selects the provided issue.
- RALPH creates or uses a safe worktree path.
- RALPH starts the local sandbox.
- RALPH runs the mock agent through the sandbox seam.
- RALPH looks for `<promise>COMPLETE</promise>`.
- RALPH runs the configured test command.
- RALPH reports the final result.
- Release 1 does not automatically open a pull request or close a GitHub issue.

## Run tests

Preferred command:

```powershell
poetry run pytest
```

Run one test file:

```powershell
poetry run pytest tests/ralph/test_release1_end_to_end.py
```

Run the README documentation coverage tests:

```powershell
poetry run pytest tests/test_docs/test_readme_release1_documentation.py
poetry run pytest tests/test_docs/test_readme_provider_sandbox_extension_documentation.py
```

Fallback only when Poetry is unavailable:

```powershell
pytest
```

## Worktree safety model

RALPH protects the main working tree by using Git worktrees.

A Git worktree is a separate working directory attached to the same repository. This lets RALPH work on an isolated branch or path instead of editing the main checkout directly.

The safety rules are:

- create a worktree before agent code edits,
- use a branch name traceable to the issue,
- preserve the worktree if a run fails,
- preserve the worktree if uncommitted changes remain,
- remove only clean successful worktrees when cleanup is safe,
- show the preserved worktree path so the developer can inspect it.

Dirty worktrees must not be deleted after failure.

## Sandbox seam

RALPH runs commands through the sandbox seam:

```text
i_sandboxhandle_run()
```

Release 1 uses local sandbox execution. The orchestrator should not need to know whether a command runs locally, in Docker, or in a future cloud sandbox.

The seam gives AI Code depth and flexibility: Docker or future sandbox providers can replace local execution later without rewriting the orchestrator.

## Result statuses

Common result statuses are:

| Status       | Meaning                                                                                                                    |
| ------------ | -------------------------------------------------------------------------------------------------------------------------- |
| `complete`   | The agent signaled completion, tests passed, and successful work was committed.                                            |
| `failed`     | The agent, sandbox command, tests, or commit step failed.                                                                  |
| `blocked`    | RALPH could not safely continue because of configuration, credentials, Docker image, issue selection, or repository state. |
| `incomplete` | The agent did not reach completion before the run stopped.                                                                 |
| `no_changes` | The agent completed, but no code changes were detected.                                                                    |

## GitHub PR and issue-closing safety

Release 1 does not create pull requests automatically.

Release 1 does not close GitHub issues automatically.

Future PR or issue-close metadata may be shown as disabled, placeholder, or dry-run output. That output is for human review. A future issue close workflow should only run after:

- one actionable issue was selected,
- RALPH completed the task,
- tests passed,
- work was committed,
- the commit hash is known,
- no dirty worktree state blocks cleanup,
- human approval or a future trusted automation setting allows it.

Use `close #<issue_number>` in a PR only when human review confirms that the issue should close after merge. Use `Refs #<issue_number>` when the PR should only link to the issue.

## `.ai-code` scaffold files

AI Code can create project-specific workflow template files under `.ai-code/`.

Create the scaffold in the current repository:

```powershell
poetry run ai-coder scaffold --repo-path .
```

Existing files are skipped by default. Use overwrite only when you intentionally want to replace existing scaffold files:

```powershell
poetry run ai-coder scaffold --repo-path . --overwrite
```

The scaffold may include:

- `.ai-code/README.md`,
- `.ai-code/.env.example`,
- `.ai-code/Dockerfile`,
- `.ai-code/prompts/implementation.md`,
- `.ai-code/prompts/review.md`,
- `.ai-code/prompts/merge.md`,
- `.ai-code/standards/coding-standards.md`.

Do not put real secrets in `.ai-code/.env.example`.

## Troubleshooting

### `--repo-path` does not exist

Pass a real repository path:

```powershell
poetry run ai-coder --repo-path .
```

### `--prompt-path` does not exist

Confirm the configured prompt file exists. The default prompt path comes from `setup_config.py`.

### Codex requires `CODEX_COMMAND`

The default Release 1 path uses `--agent mock`.

Only use `--agent codex` when `CODEX_COMMAND` is configured and you are intentionally testing the Codex provider path.

### Docker mode requires Docker configuration

The default Release 1 path uses `--sandbox local`.

Only use `--sandbox docker` when the Docker image and Docker settings are configured.

## Developer notes

AI Code uses small public interface seams. Public functions should follow this pattern:

```text
i_<module_name>_<action>()
```

Examples:

- `i_ralph_run()`
- `i_sandbox_start()`
- `i_sandboxhandle_run()`
- `i_worktree_create()`
- `i_prompt_resolve()`
- `i_prompt_preprocess()`
- `i_orchestrator_run()`
- `i_github_issue_select()`
- `i_test_runner_run()`

Development should stay tracer-bullet focused:

1. Read the related tests.
2. Add or update a failing behavior test when behavior is missing.
3. Write the smallest implementation needed to pass.
4. Refactor only after tests pass.
5. Run `poetry run pytest`.
6. Do not change unrelated files.
7. Do not add dependencies unless the issue clearly requires them.
8. Do not claim future features are available until tests prove they are.

# My Stuff

## Current Status

AI Code is a Python learning project for building **RALPH**, a safe coding-agent workflow that works through one GitHub issue at a time.

The current codebase has moved beyond the first tiny mock-only slice. The default path is still the safe Release 1 local tracer bullet, but the project now also has tested extension seams for Docker bind-mount execution, scaffold generation, GitHub issue safety metadata, Codex preflight checks, CodexProvider output normalization, and provider-specific environment allowlists.

The safest way to think about the project is:

```text
Release 1 default path:
provided issue -> safe worktree -> local sandbox -> mock agent -> tests -> commit/sync safety

Optional extension paths:
Docker bind-mount sandbox
CodexProvider command adapter
Codex final-message-file and JSONL output handling
Provider-specific environment allowlists for Codex commands
dry-run GitHub PR / issue-close metadata
.ai-code scaffold templates
```

Automatic pull request creation and automatic GitHub issue closing are still not production behavior. They remain disabled, placeholder, or dry-run safety workflows unless a future tested issue explicitly enables them.

## What Problem AI Code Solves

AI Code helps a solo Python developer safely repeat the GitHub issue-fixing workflow.

Without AI Code, the developer has to manually:

- read the issue,
- decide whether the work is actionable,
- create a branch or worktree,
- prepare a prompt,
- run an AI coding tool,
- review command output,
- run tests,
- commit safe work,
- preserve failed attempts,
- avoid closing issues too early,
- avoid leaking secrets in logs.

AI Code puts these steps behind small Python module seams so each part can be tested, improved, and replaced one tracer-bullet slice at a time.

The main safety goal is simple: RALPH should not risk the main repository checkout. It should work in an isolated worktree, run commands through a sandbox seam, run tests, commit only safe changes, and preserve failed or dirty work for human review.

## What RALPH Does

RALPH is the high-level workflow inside AI Code.

For the current tested path, RALPH can:

- receive one fake or provided issue,
- select one actionable issue,
- create or use a safe worktree path,
- start the selected sandbox adapter,
- resolve prompt text,
- preprocess safe placeholders after the sandbox is ready,
- create the selected agent provider through `i_agent_provider_create()`,
- run the agent through the orchestrator,
- display normalized provider events when available,
- detect `<promise>COMPLETE</promise>`,
- run the configured test command,
- commit and sync only successful work,
- preserve failed or dirty worktrees,
- expose phase results through the public `RalphResult`,
- return a clear status and readable output.

Long term, RALPH should automate one GitHub issue at a time from issue selection through safe commit and later human-approved PR or issue-close workflow.

## Current Release 1 Scope

Release 1 is the local single-issue tracer bullet.

It focuses on proving the end-to-end safety model with local execution:

- one fake or provided issue,
- local sandbox mode,
- mock agent provider by default,
- prompt resolving and preprocessing,
- explicit completion detection,
- pytest execution,
- safe worktree creation,
- safe commit and sync behavior when tests pass,
- preservation on failure or dirty state,
- visible progress output.

Release 1 is intentionally small. Its job is to prove the workflow before adding broader automation.

## Current Phase 3 Codex Scope

CodexProvider is the first real coding-agent provider path.

The current CodexProvider code supports:

- command construction inside `CodexCommandContract`,
- non-interactive `codex exec`,
- `--cd <worktree-path>`,
- `--sandbox workspace-write`,
- `--color never`,
- `--json`,
- `--output-last-message <path>`,
- prompt text passed through stdin,
- final message file output priority,
- structured JSONL event fallback,
- plain stdout fallback,
- stderr and provider diagnostics for failures,
- normalized provider-readable events.

The output priority is:

1. final message file output,
2. structured JSONL events,
3. plain stdout fallback,
4. stderr or provider diagnostics for failures.

The important rule is that the orchestrator should not parse raw Codex JSONL. Codex-specific output handling belongs inside `CodexProvider`. The orchestrator receives normal `AgentResponse.output`, `AgentResponse.error`, and `AgentResponse.events`.

## Codex JSONL Event Normalization

CodexProvider now normalizes supported JSONL stdout into provider-readable events.

Normalized event types may include:

- `text`
- `tool_call`
- `result`
- `error`
- `session`

Useful behavior includes:

- missing final message file can fall back to JSONL agent-message text,
- final message file still wins over JSONL and stdout,
- plain stdout is still visible when stdout is not structured JSONL,
- session id values are preserved when available,
- text-like events become normalized text events,
- result-like events become normalized result events,
- tool-call-like events become tool-call or result events depending on status,
- error-like events become normalized error events,
- malformed JSONL creates a visible diagnostic or parse-error event,
- non-zero Codex exit still fails the provider response.

This keeps provider-specific Codex output details behind the provider seam.

## Codex Preflight Checks

Codex preflight is a read-only readiness check for the first Codex smoke-proof path.

The current checks can verify:

- selected provider is `codex`,
- sandbox mode is `local`,
- `CODEX_COMMAND` is configured,
- the Codex executable can be found,
- `codex --version` can run,
- prompt input is available,
- issue input is available,
- pull request creation is disabled or dry-run,
- issue closing is disabled or dry-run.

Preflight should not create providers, start sandboxes, create worktrees, call models, commit changes, create pull requests, or close GitHub issues.

## Provider-Specific Environment Support

Provider-specific environment support is now documented as a small Codex-focused tracer-bullet slice.

The purpose is to let `CodexProvider` receive only explicitly allowed provider environment variables while leaving normal project commands unchanged.

Use normal provider allowlists for non-secret values:

```text
RALPH_PROVIDER_ENV_ALLOWLIST=CODEX_HOME
```

Use secret provider allowlists for secret values:

```text
RALPH_PROVIDER_SECRET_ENV_ALLOWLIST=OPENAI_API_KEY
```

Important behavior:

- `setup_config.provider_env_allowlist` controls normal provider environment names.
- `setup_config.provider_secret_env_allowlist` controls secret provider environment names.
- Missing normal provider environment variables are skipped.
- Missing or empty provider secret environment variables produce a clear error.
- `CodexProvider` passes the provider environment only to the Codex sandbox command.
- `FakeTestAgentProvider` does not receive the Codex/provider environment.
- `poetry install`, `poetry run pytest`, `git`, project setup, sync, and commit commands do not receive the Codex/provider environment.
- Codex prompt text still goes through stdin.
- Codex command arguments stay focused on safe provider command pieces and do not receive issue bodies or prompt text.
- `OPENAI_API_KEY` is not included by default. Add it only when a real Codex workflow explicitly needs it.

This keeps the provider environment path narrow and testable. It does not make the whole local sandbox use a restricted environment by default.

## Step 19 Manual Acceptance Checklist

Verification command completed:

```powershell
poetry run pytest
```

Result reported by the developer:

```text
All tests passed.
```

Completed checklist:

- [x] `LocalSandboxProvider.i_sandboxhandle_run()` accepts an optional custom environment.
- [x] Local sandbox commands with no custom environment still behave like before.
- [x] A local sandbox command with a custom environment does not inherit unallowed host env vars.
- [x] Provider normal env vars come from `setup_config.provider_env_allowlist`.
- [x] Provider secret env vars come from `setup_config.provider_secret_env_allowlist`.
- [x] Missing normal provider env vars are skipped.
- [x] Missing secret provider env vars produce a clear error.
- [x] `CodexProvider` passes the custom provider environment to the sandbox.
- [x] `FakeTestAgentProvider` does not pass the Codex/provider environment.
- [x] `pytest` commands do not receive the provider-specific custom environment.
- [x] `git` or sync/commit commands do not receive the provider-specific custom environment.
- [x] Codex prompt still goes through stdin.
- [x] Codex command arguments stay unchanged except for internal sandbox keyword arguments.
- [x] No new dependencies were added.

Simple commit message:

```text
RALPH: document provider environment support
```

Suggested commit commands:

```powershell
git add README.md
git commit -m "RALPH: document provider environment support"
```

## What Is Intentionally Future Work

The following features are not automatic Release 1 behavior:

- processing multiple issues in one run,
- automatic pull request creation,
- automatic GitHub issue closing,
- production deployment automation,
- long-running Docker containers,
- cloud sandbox providers,
- multi-agent workflows,
- full autonomous GitHub issue management.

Docker and CodexProvider are optional or later-phase paths. Keep the default Release 1 path local and mock-provider friendly unless you are specifically testing those paths.

## Requirements

- Windows 11 target environment
- Python `>=3.12,<3.14`
- Poetry
- Git
- pytest through the Poetry dev dependency group
- A Git repository for worktree-based runs

## Install

Clone the repository and install dependencies with Poetry:

```powershell
git clone <repo-url>
cd ai_coder
poetry install
```

Poetry reads `pyproject.toml`, installs project dependencies, and uses `poetry.lock` when present for repeatable dependency versions.

Verify the install by running:

```powershell
poetry run pytest
```

## Configuration Overview

`src/ai_coder/setup_config.py` is the final runtime source of truth.

The expected configuration flow is:

1. Load defaults and environment values.
2. Parse CLI arguments.
3. Validate CLI values before applying them.
4. Apply valid CLI values into `setup_config.py`.
5. Validate the final configuration.
6. Run RALPH using the final setup config values.

Useful user-facing configuration values include:

| Name                                  | Purpose                                                                                             |
| ------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `REPO_PATH`                           | Local repository path RALPH should use.                                                             |
| `PROMPT_PATH`                         | Prompt markdown file path.                                                                          |
| `GITHUB_REPO`                         | GitHub owner/repository name.                                                                       |
| `RALPH_AGENT`                         | Agent provider name. Use `mock` for the default local tracer bullet or `codex` for Codex testing.   |
| `RALPH_SANDBOX_MODE`                  | Sandbox mode. Use `local` for the default path or `docker` when testing Docker bind-mount behavior. |
| `TEST_COMMAND`                        | Test command, defaulting to `poetry run pytest`.                                                    |
| `DRY_RUN`                             | Safety mode for future GitHub automation.                                                           |
| `CODEX_COMMAND`                       | Codex command path or name when using the optional Codex provider path.                             |
| `RALPH_PROVIDER_ENV_ALLOWLIST`        | Normal provider environment variable names allowed for provider commands such as Codex.             |
| `RALPH_PROVIDER_SECRET_ENV_ALLOWLIST` | Secret provider environment variable names allowed for provider commands such as Codex.             |
| `RALPH_DOCKER_IMAGE_NAME`             | Docker image name for Docker sandbox testing.                                                       |
| `RALPH_GITHUB_ISSUE_CLOSE_ENABLED`    | Future issue-close enablement flag. Real issue closing is still disabled or placeholder behavior.   |

CLI values should be validated before they change runtime configuration.

## Run the Local Release 1 Tracer Bullet

Use the console script:

```powershell
poetry run ai-coder --repo-path . --issue-number 57 --issue-title "Add Release 1 user documentation" --issue-body "Document Release 1 usage." --label "polish" --agent mock --sandbox local --dry-run
```

If the console script is not available, use the package module entry point:

```powershell
poetry run python -m ai_coder --repo-path . --issue-number 57 --issue-title "Add Release 1 user documentation" --issue-body "Document Release 1 usage." --label "polish" --agent mock --sandbox local --dry-run
```

What to expect:

- RALPH validates configuration.
- RALPH selects the provided issue.
- RALPH creates or uses a safe worktree path.
- RALPH starts the local sandbox.
- RALPH runs the mock agent through the sandbox seam.
- RALPH looks for `<promise>COMPLETE</promise>`.
- RALPH runs the configured test command.
- RALPH reports the final result.
- Release 1 does not automatically open a pull request or close a GitHub issue.

## Run Codex Preflight

Use Codex preflight only when intentionally testing the Codex path.

Recommended environment shape:

```powershell
$env:RALPH_AGENT="codex"
$env:RALPH_SANDBOX_MODE="local"
$env:CODEX_COMMAND="codex"
$env:DRY_RUN="true"
```

The preflight behavior is read-only. It verifies readiness and safety settings before any real Codex smoke proof should run.

## Run Tests

Preferred command:

```powershell
poetry run pytest
```

Run one test file:

```powershell
poetry run pytest tests/ralph/test_release1_end_to_end.py
```

Run README documentation tests:

```powershell
poetry run pytest tests/test_docs/test_readme_release1_documentation.py
poetry run pytest tests/test_docs/test_readme_provider_sandbox_extension_documentation.py
```

Run tests in a folder:

```powershell
poetry run pytest tests/ralph/
```

Fallback only when Poetry is unavailable:

```powershell
pytest
```

Do not use this command for this project:

```powershell
python -m pytest --capture=tee-sys
```

## Worktree Safety Model

RALPH protects the main working tree by using Git worktrees.

A Git worktree is a separate working directory attached to the same repository. This lets RALPH work on an isolated branch or path instead of editing the main checkout directly.

The safety rules are:

- create a worktree before agent code edits,
- use a branch name traceable to the issue,
- preserve the worktree if a run fails,
- preserve the worktree if uncommitted changes remain,
- remove only clean successful worktrees when cleanup is safe,
- show the preserved worktree path so the developer can inspect it.

Dirty worktrees must not be deleted after failure.

## Sandbox Seam

RALPH runs commands through the sandbox seam:

```text
i_sandboxhandle_run()
```

The high-level workflow starts sandboxes through:

```text
i_sandbox_start()
```

The sandbox adapter returns a normalized command result with:

- `stdout`
- `stderr`
- `exit_code`
- success or failure state

Release 1 uses local sandbox execution. Docker bind-mount mode is an optional tested extension path. Future cloud or long-running sandbox providers should stay behind the same seam.

## Docker Bind-Mount Sandbox

Docker bind-mount mode lets the container work directly in a mounted host worktree.

In Docker bind-mount mode:

1. RALPH creates or receives a host Git worktree path.
2. The Docker sandbox mounts that host worktree into the container.
3. The container sees the mounted worktree at `/workspace`.
4. Commands run with `/workspace` as the container working directory.
5. File edits made inside Docker appear in the host worktree.
6. The host can inspect Git state after the Docker command finishes.
7. Dirty or failed worktrees are preserved for human review.

The default Docker image is:

```text
ai-code-ralph-test-runtime:latest
```

Do not pass the full host environment into Docker. Use explicit allowlists:

```text
docker_env_allowlist
docker_secret_env_allowlist
provider_env_allowlist
provider_secret_env_allowlist
```

The default normal Docker env allowlist includes:

```text
PYTHONUNBUFFERED
```

The default secret Docker env allowlist is empty.

Docker command redaction belongs in:

```text
i_dockercommand_redact()
```

## Result Statuses

Common result statuses are:

| Status       | Meaning                                                                                                                    |
| ------------ | -------------------------------------------------------------------------------------------------------------------------- |
| `complete`   | The agent signaled completion, tests passed, and successful work was committed.                                            |
| `failed`     | The agent, sandbox command, tests, or commit step failed.                                                                  |
| `blocked`    | RALPH could not safely continue because of configuration, credentials, Docker image, issue selection, or repository state. |
| `incomplete` | The agent did not reach completion before the run stopped.                                                                 |
| `no_changes` | The agent completed, but no code changes were detected.                                                                    |

A failed, blocked, incomplete, or dirty run should preserve useful context for human review.

## Architecture

AI Code is built as a small Python system with clear module seams.

RALPH coordinates the workflow, but it should not hide all behavior inside one large file. Each major responsibility lives behind a small public interface so the project can grow one tracer-bullet slice at a time.

```text
User runs AI Code
        |
        v
Load setup_config.py
        |
        v
Read one provided or fake issue
        |
        v
Select one actionable issue
        |
        v
Create a safe Git worktree
        |
        v
Start sandbox provider
(local by default)
        |
        v
Resolve prompt / prompt file
        |
        v
Preprocess safe placeholders
        |
        v
Run selected agent through sandbox seam
        |
        v
Display normalized provider events
        |
        v
Detect <promise>COMPLETE</promise>
        |
        v
Run pytest through sandbox seam
        |
        v
Commit only after tests pass
        |
        v
Preserve failed or dirty worktrees
        |
        v
Print readable result
```

Release 1 focuses on proving this end-to-end path locally. Docker, Codex, automatic pull requests, automatic issue closing, and multi-agent workflows are later-phase or disabled placeholder behavior unless current tests prove otherwise.

## Main Modules

- **`setup_config.py`** — Final runtime source of truth for validated configuration values.
- **`main`** — CLI entry point for `ai-coder` and `ai-coder scaffold`.
- **`ralph`** — High-level workflow that selects one issue and coordinates the run.
- **`github_issues`** — Reads, represents, filters, selects, and safely prepares issue-close metadata.
- **`worktree_manager`** — Creates, checks, removes, and preserves safe Git worktrees.
- **`sandbox_provider`** — Runs commands behind the sandbox seam.
- **`agent_provider`** — Creates mock or Codex agent providers behind one interface.
- **`codex_preflight`** — Performs read-only Codex readiness and safety checks.
- **`orchestrator`** — Runs the agent loop until completion, failure, or max iterations.
- **`completion_detector`** — Detects the explicit `<promise>COMPLETE</promise>` signal.
- **`prompt_resolver`** — Loads prompt text from inline text or prompt files.
- **`prompt_preprocessor`** — Replaces safe placeholders while keeping issue text inert.
- **`project_setup`** — Runs baseline project setup checks before the agent phase.
- **`test_runner`** — Runs the configured test command through the sandbox seam.
- **`sync_in` / `sync_out`** — Minimal seams for current sync behavior and future isolated or cloud sandbox file movement.
- **`display`** — Shows phases, selected issues, agent events, command results, test results, commits, and preserved worktrees.
- **`pull_request_draft`** — Builds future-safe PR draft metadata without opening a PR automatically.
- **`scaffold`** — Creates `.ai-code/` workflow template files.
- **`repository_context`** — Gathers safe repository context for prompt construction.

## Current Implementation Status

### Working Now

- AI Code can run from the `ai-coder` console script.
- AI Code can also run with `python -m ai_coder`.
- CLI arguments are validated before being applied into `setup_config.py`.
- RALPH can receive one provided issue from CLI arguments.
- GitHub issue data is treated as inert text.
- Issue labels and assignments can be used to select or skip issues.
- RALPH can select one actionable issue.
- RALPH can build a prompt from issue data.
- RALPH can create, preserve, and clean up safe worktrees.
- RALPH can start a local sandbox adapter.
- RALPH can run a fake/test agent through the sandbox seam.
- RALPH can detect `<promise>COMPLETE</promise>`.
- RALPH can run pytest through the sandbox seam.
- RALPH can commit and sync successful changes.
- RALPH can preserve failed or dirty worktrees.
- RALPH exposes setup, test, sync, cleanup, PR draft, and issue-close phase results.
- Display code can show normalized provider events.
- Docker bind-mount support exists behind the sandbox provider seam.
- Docker environment allowlists and redaction helpers exist.
- CodexProvider can run through the provider seam.
- CodexProvider can prefer final message file output.
- CodexProvider can parse structured JSONL events when final message output is unavailable.
- CodexProvider can fall back to plain stdout when output is not structured JSONL.
- CodexProvider preserves non-zero exit behavior.
- Codex preflight can verify provider, sandbox, executable, prompt input, issue input, PR safety, and issue-close safety.
- Provider-specific environment allowlists are documented and verified for the Codex command path.
- PR creation is represented only as future/disabled draft metadata.
- GitHub issue closing is represented only as future/disabled or dry-run placeholder behavior.
- `.ai-code/` scaffold templates can be generated.
- The test suite passes with `poetry run pytest`.

### Still Future or Disabled

- Automatic pull request creation is not automatic behavior.
- Automatic GitHub issue closing is not automatic behavior.
- Cloud sandbox providers are not implemented.
- Long-running Docker container orchestration is not implemented.
- Multi-agent workflows are not implemented.
- Full autonomous GitHub issue management is not implemented.
- Real issue closing should wait for committed work, passing tests, clean state, and human approval.

## Provider and Sandbox Extension Guide

AI Code keeps agent execution and command execution behind small public seams. This lets RALPH stay simple while the project grows from the Release 1 local tracer bullet into Docker, Codex, and future adapters.

Current code and tests are the source of truth. This section documents extension points; it does not mean every future provider, cloud sandbox, pull request workflow, or issue-close workflow is implemented.

### Adding a Future Agent Provider

To add a future agent provider, keep the provider behind the agent provider seam.

Use this checklist:

1. Add a provider class that satisfies `AgentProvider`.
2. Implement `i_agent_provider_run(prompt: str) -> AgentResponse`.
3. Keep provider-specific command construction inside the provider.
4. Prefer stdin or a safe temporary file for large prompt text.
5. Treat issue title, issue body, labels, and assignment data as inert text.
6. Return normalized events when the provider supports structured output.
7. Add the provider name to config validation only when the provider is ready.
8. Add the provider to `i_agent_provider_create()`.
9. Add tests with fake sandbox handles.
10. Do not add new secrets to default allowlists.

Future agent provider examples may include Claude, OpenCode, or another local command adapter, but they are future extension points until tests prove them.

### Adding a Future Sandbox Provider

To add a future sandbox provider, keep command execution behind the sandbox seam.

Use this checklist:

1. Add a provider and handle pair that satisfies the sandbox seam.
2. Start the provider through `i_sandbox_start()`.
3. Run commands through `i_sandboxhandle_run()`.
4. Return a normalized `CommandResult`.
5. Keep provider-specific details inside the adapter.
6. Do not leak Docker, Podman, cloud, or remote execution details into RALPH or the orchestrator.
7. Use explicit environment allowlists.
8. Redact configured secret values.
9. Preserve worktree safety.
10. Add tests for start behavior, command execution, failure behavior, and environment handling.

Only add `sync_in` or `sync_out` behavior for isolated or cloud sandboxes that need file copy. Local mode and Docker bind-mount mode work directly in the worktree path and do not need separate file syncing.

## `.ai-code` Scaffold Files

AI Code can create project-specific workflow template files under `.ai-code/`.

Create the scaffold in the current repository:

```powershell
poetry run ai-coder scaffold --repo-path .
```

Existing files are skipped by default. Use overwrite only when you intentionally want to replace existing scaffold files:

```powershell
poetry run ai-coder scaffold --repo-path . --overwrite
```

The scaffold may include:

- `.ai-code/README.md`,
- `.ai-code/.env.example`,
- `.ai-code/Dockerfile`,
- `.ai-code/prompts/implementation.md`,
- `.ai-code/prompts/review.md`,
- `.ai-code/prompts/merge.md`,
- `.ai-code/standards/coding-standards.md`.

Do not put real secrets in `.ai-code/.env.example`.

## Scaffold Commands

Run the test suite first:

```powershell
poetry run pytest
```

Create `.ai-code/` scaffold files in the current repository:

```powershell
poetry run ai-coder scaffold --repo-path .
```

Create scaffold files in a safe temporary folder:

```powershell
mkdir temp_scaffold_check
poetry run ai-coder scaffold --repo-path temp_scaffold_check
```

Check the generated scaffold folder:

```powershell
dir temp_scaffold_check\.ai-code
type temp_scaffold_check\.ai-code\.env.example
type temp_scaffold_check\.ai-code\README.md
type temp_scaffold_check\.ai-code\prompts\implementation.md
type temp_scaffold_check\.ai-code\prompts\review.md
type temp_scaffold_check\.ai-code\prompts\merge.md
type temp_scaffold_check\.ai-code\standards\coding-standards.md
```

Run scaffold a second time to confirm existing files are skipped:

```powershell
poetry run ai-coder scaffold --repo-path temp_scaffold_check
```

Run scaffold with overwrite only when you intentionally want to replace existing scaffold files:

```powershell
poetry run ai-coder scaffold --repo-path temp_scaffold_check --overwrite
```

Do not put real secrets in `.ai-code/.env.example`.

## Design Philosophy

AI Code uses **tracer bullets**.

A tracer bullet is a thin end-to-end slice that proves the idea works before advanced features are added. Instead of building the full autonomous coding system in one large step, AI Code adds small working slices that can be tested and understood.

Design principles:

- Build small slices.
- Prefer readable Python over clever abstractions.
- Do not rewrite the whole project for one issue.
- Do not change unrelated files.
- Do not add dependencies unless the issue clearly requires them.
- Keep public interfaces small.
- Hide implementation details behind module seams.
- Treat external issue data as inert text.
- Run tests before claiming success.
- Preserve failed or dirty worktrees for human review.
- Avoid claiming future features are available before tests prove them.

Public interface functions should use this naming pattern:

```text
i_<module_name>_<action>()
```

Examples:

```text
i_ralph_run()
i_worktree_create()
i_worktree_preserve()
i_sandbox_start()
i_sandboxhandle_run()
i_prompt_resolve()
i_prompt_preprocess()
i_orchestrator_run()
i_github_issue_select()
i_test_runner_run()
```

Private helper functions should start with `_`.

## Development Workflow

RALPH follows a small, test-first development workflow:

1. **Explore** — Read the issue, parent PRD, related source files, and related tests.
2. **Plan** — Decide the smallest safe change.
3. **Red** — Add or update a failing pytest test when behavior is missing.
4. **Green** — Write the smallest implementation needed to pass.
5. **Refactor** — Improve the code only after tests pass.
6. **Verify** — Run the full test suite.
7. **Commit** — Commit safe changes with a message starting with `RALPH:`.
8. **Preserve or close later** — Preserve failed or dirty work. Do not close issues automatically in Release 1.

Preferred test command:

```powershell
poetry run pytest
```

Fallback when Poetry is unavailable:

```powershell
pytest
```

Do not use this command for this project:

```powershell
python -m pytest --capture=tee-sys
```

## Issue Priority

RALPH should work through issues in this order:

1. **Bug fixes** — Broken behavior affecting users.
2. **Tracer bullets** — Thin end-to-end slices that prove an approach works.
3. **Polish** — User-visible improvements, documentation, error messages, or UX.
4. **Refactors** — Internal cleanup with no user-visible behavior change.

RALPH should work on one issue per run.

RALPH should skip issues that are vague, blocked, unsafe, assigned to someone else, or outside the configured label workflow.

## Safe PR and GitHub Issue Close Policy

RALPH does not create pull requests automatically in Release 1.

RALPH does not close GitHub issues automatically in Release 1.

Future pull request creation is allowed only when all of these are true:

1. One actionable issue was selected.
2. The issue was not skipped as vague, blocked, assigned, unsafe, or outside workflow rules.
3. RALPH worked in a safe worktree or safe branch.
4. The agent produced `<promise>COMPLETE</promise>`.
5. Required tests passed.
6. Successful changes were committed.
7. The commit hash is known.
8. The worktree is clean after commit, or remaining dirty state is treated as a blocker.
9. GitHub access is configured and authenticated.
10. Dry-run mode is disabled.
11. Human approval has been granted.

Future GitHub issue closing is allowed only when all of these are true:

1. One actionable issue was selected.
2. The issue is fully completed.
3. The agent produced `<promise>COMPLETE</promise>`.
4. Required tests passed.
5. Successful changes were committed.
6. The commit hash is known.
7. The safe workflow reached final status `complete`.
8. No uncommitted work remains that should be preserved for review.
9. The issue is not blocked, unsafe, assigned to someone else, or outside configured label rules.
10. Human approval has been granted.

Direct issue closing with `gh issue close` remains disabled by default.

Automatic pull request creation remains disabled by default.

Automatic issue closing remains disabled by default.

When RALPH eventually creates PR bodies, use:

```text
Refs #<issue_number>
```

Use this only when human review confirms the PR should close the issue after merge:

```text
close #<issue_number>
```

## Project Structure

```text
ai_coder/
├── pyproject.toml
├── poetry.lock
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
│   ├── .env.example
│   ├── Dockerfile
│   ├── prompt.md
│   ├── ai_coder_worktrees/
│   └── logs/
├── docker/
│   └── ralph-test-runtime/
│       └── Dockerfile
├── src/
│   └── ai_coder/
│       ├── __init__.py
│       ├── __main__.py
│       ├── setup_config.py
│       ├── agent_provider/
│       ├── codex_preflight/
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
    ├── codex_preflight/
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

## Troubleshooting

### `--repo-path` does not exist

Pass a real repository path:

```powershell
poetry run ai-coder --repo-path .
```

### `--prompt-path` does not exist

Confirm the configured prompt file exists. The default prompt path comes from `setup_config.py`.

### Codex requires `CODEX_COMMAND`

The default Release 1 path uses `--agent mock`.

Only use `--agent codex` when `CODEX_COMMAND` is configured and you are intentionally testing the Codex provider path.

### Docker mode requires Docker configuration

The default Release 1 path uses `--sandbox local`.

Only use `--sandbox docker` when the Docker image and Docker settings are configured.

### Tests fail

Run the full suite:

```powershell
poetry run pytest
```

Then fix the first failing test before claiming the issue is done.

## Developer Notes

This project is intentionally small and readable.

Rules for future changes:

- Read related tests before changing behavior.
- Prefer tests that cross public seams.
- Avoid testing private helpers directly unless the behavior is small, security-sensitive, or hard to reach.
- Do not add dependencies unless the issue clearly requires them.
- Do not claim future automation is available before tests prove it.
- Preserve worktrees when failures or uncommitted changes exist.
- Keep `setup_config.py` as the final runtime configuration source of truth.
- Keep Codex-specific output parsing inside `CodexProvider`.
- Keep Docker-specific mounting and redaction inside the sandbox provider layer.

## License

This project is part of the AI Code learning project.

## scaffold command overwrites files only when --overwrite is passed.

poetry run ai-coder scaffold --repo-path . --overwrite
