# RALPH: Autonomous Coding Agent

RALPH is an autonomous Python coding agent that works through GitHub issues one at a time.

Inspired by Sandcastle, RALPH automates the full workflow of reading issues, creating isolated working environments, running an AI agent, and syncing completed work back to the repository.

## What RALPH Does

1. Start with a Git repository
2. Read open GitHub issues
3. Pick one actionable issue (prioritized by type)
4. Create a safe working copy using a Git worktree
5. Start a sandbox or local execution environment
6. Give an AI coding agent a prompt
7. Let the agent edit files, run commands, and commit changes
8. Detect whether the task is complete
9. Run tests
10. Sync or merge the finished work back to the host repo
11. Close the GitHub issue only after tests pass and the fix is committed
12. Preserve the worktree if there are uncommitted changes or failures

## Architecture

```
User runs RALPH
        |
        v
Read prompt / prompt file
        |
        v
Create Git worktree / branch
        |
        v
Start sandbox provider
(Docker, Podman, local, etc.)
        |
        v
Start AI agent
(Claude, Codex, mock, etc.)
        |
        v
Orchestrator loops:
  - send prompt
  - stream output
  - check for COMPLETE signal
  - enforce iteration limits
        |
        v
Collect commits
        |
        v
Sync changes back to host repo
        |
        v
Close or comment on GitHub issue
        |
        v
Clean up safely
```

## Main Modules

- **`AgentProvider`** — Defines which AI coding agent RALPH runs (mock, Claude, Codex, etc.)
- **`Orchestrator`** — Main loop that runs the agent until completion, max iterations, or error
- **`WorktreeManager`** — Wraps Git worktree commands for safe, isolated working copies
- **`SandboxProvider`** — Defines where the agent executes (local, Docker, Podman, etc.)
- **`PromptResolver`** — Loads prompts from files or inline strings
- **`PromptPreprocessor`** — Prepares prompt text with placeholder replacement and safe command expansion
- **`GitHubIssues`** — Reads and updates GitHub issues with intelligent priority selection
- **`SyncIn` / `SyncOut`** — Moves files and commits in and out of isolated sandboxes
- **`Display`** — Controls terminal output and logging
- **`RALPH`** — High-level workflow orchestrator

## Getting Started

**Prerequisites:**

- Python 3.9+
- Poetry (package manager)
- Git
- Windows 11 (target OS)

**Installation:**

```bash
# Clone the repository
git clone <repo-url>
cd ai_coder

# Install dependencies with Poetry
poetry install
```

**Running Tests:**

```powershell
poetry run pytest
```

Run with verbose output:

```powershell
poetry run pytest -v
```

Run tests for a specific module:

```powershell
poetry run pytest tests/orchestrator/
```

## Current Implementation Status

### What's Working

- **Orchestrator** — Runs an agent in a loop, detects completion, enforces iteration limits
- **AgentProvider** — Protocol interface with a MockAgentProvider for testing
- **GitHub Issues** — Data model and priority-based issue selection (Bug > Tracer > Polish > Refactor)
- **PromptPreprocessor** — Simple template placeholder replacement (`{{KEY}}` → value)
- **RALPH** — End-to-end workflow: selects issue → builds prompt → runs orchestrator
- **Full test coverage** — All modules have pytest tests

### What's Planned

- **WorktreeManager** — Git worktree creation and cleanup
- **SandboxProvider** — Local/Docker execution environment
- **PromptResolver** — Load prompts from files
- **SyncIn/SyncOut** — File and commit synchronization
- **Display** — Rich terminal output
- **Real AgentProviders** — Integration with Claude, Codex, etc.

## Design Philosophy

This project uses **tracer bullets** — build a thin end-to-end version that proves the idea works before adding advanced features. Rather than building every module fully at once, we implement small slices that work together.

**Design Principles:**

- Small slices — each change is a thin, focused improvement
- Readable code — prefer clarity over cleverness
- No extra dependencies — only add libraries when required
- Clear interfaces — hide implementation details behind module seams
- Test-driven — write failing tests first, then implement
- No dead code — delete instead of commenting out

**Interface Naming:**

All public interface functions follow this pattern:

```
i_ + module_name + verb/action
```

Examples: `i_orchestrator_run()`, `i_worktree_create()`, `i_prompt_resolve()`, `i_github_issue_select()`

## Development Workflow

RALPH uses a **Red → Green → Refactor** workflow:

1. **Explore** — Read the issue and examine relevant source files and tests
2. **Plan** — Decide what to change and why; keep changes small
3. **Red** — Write a failing test for missing behavior
4. **Green** — Write the smallest implementation to pass the test
5. **Refactor** — Improve the code while tests still pass
6. **Verify** — Run all tests before committing
7. **Commit** — Make one commit with message starting with `RALPH:`
8. **Close** — Only close the issue after tests pass and code is committed

## Project Structure

```
ai_coder/
├── pyproject.toml          # Poetry configuration
├── README.md               # This file
├── src/
│   └── ai_coder/           # Main package
│       ├── __init__.py
│       ├── agent_provider/
│       ├── orchestrator/
│       ├── worktree_manager/
│       ├── sandbox_provider/
│       ├── prompt_resolver/
│       ├── prompt_preprocessor/
│       ├── github_issues/
│       ├── sync_in/
│       ├── sync_out/
│       ├── display/
│       └── ralph/
└── tests/                  # Test suite
    ├── agent_provider/
    ├── orchestrator/
    ├── worktree_manager/
    ├── sandbox_provider/
    ├── prompt_resolver/
    ├── prompt_preprocessor/
    ├── github_issues/
    ├── sync_in/
    ├── sync_out/
    ├── display/
    └── ralph/
```

## Issue Priority

Work through issues in this order:

1. **Bug fixes** — Broken behavior affecting users
2. **Tracer bullets** — Thin end-to-end slices that prove an approach works
3. **Polish** — Improving existing functionality (error messages, UX, docs)
4. **Refactors** — Internal cleanups with no user-visible change

Only one issue is worked on per iteration.

## License

This project is part of the Sandcastle initiative.

## Contributing

This project follows its own development workflow. See the main prompt for detailed rules on code style, commit messages, testing, and issue resolution.

---

**Note:** This is a learning project designed to be clear and simple before adding advanced features. Each GitHub issue represents a thin slice of functionality that builds on the previous work.

## Can run with both:

poetry run ai-coder
poetry run python -m ai_coder

## Release 1 runtime contract

The Release 1 command, CLI flags, setup config fields, fake agent behavior, and commit message format are documented in:

```text
docs/release_1_runtime_contract.md
```
