# Context

We are building a new Python project named `ai_coder`.

The project goal is to build **RALPH** — an autonomous coding agent that works through GitHub issues one at a time.

RALPH is inspired by Sandcastle, but this project must be written in Python.

This project is a small learning project. Build it in clear, simple, readable Python first. Do not try to rebuild the full Sandcastle system in one step.

## What RALPH should eventually do

RALPH should automate this workflow:

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

## Important rule

Build this project in small tracer-bullet slices.

A tracer bullet means:

> Build a thin end-to-end version that proves the idea works before adding advanced features.

Do not build every module fully at once.

Start with the smallest useful version of RALPH, then improve it one GitHub issue at a time.

---

# Coding rules

- Build small slices.
- Do not rewrite the whole project.
- Do not change unrelated files.
- Do not add new dependencies unless the issue clearly requires it.
- Do not leave commented-out code.
- Do not add TODO comments.
- Prefer small, readable Python code.
- Prefer explicit names over clever abstractions.
- Keep interfaces small.
- Hide implementation details behind clear module seams.
- Write tests for behavior, not internal implementation.
- Preserve existing public interface functions unless the issue explicitly requires a rename.

---

# Target project

## Project name

```text
ai_coder
```

## Language

```text
Python
```

## Package manager

```text
Poetry
```

## Test runner

```text
pytest
```

## Operating system target

```text
Windows 11
```

## Development style

Use clean Python modules under `src/`.

Use tests under `tests/`.

Prefer simple code over clever code.

Do not add unnecessary dependencies.

---

# Project structure

### Important Modules:

- AgentProvider: Python classes for Claude/Codex/OpenCode commands
- Orchestrator: Python loop that runs the agent until complete
- WorktreeManager: Python wrapper around git worktree
- SandboxProvider: Python Docker/Podman/local sandbox runner
- PromptResolver: Python prompt file loader
- PromptPreprocessor: Python placeholder replacement and safe command expansion
- syncIn / syncOut: Python file copy and Git commit sync
- Display: Python terminal output/logging

### The big architecture picture

```
User runs Sandcastle
        |
        v
Read prompt / prompt file
        |
        v
Create Git worktree / branch
        |
        v
Start sandbox provider
(Docker, Podman, Vercel, Daytona, etc.)
        |
        v
Run lifecycle hooks
        |
        v
Start AI agent
(Claude Code, Codex, Pi, OpenCode)
        |
        v
Orchestrator loops:
  - send prompt
  - stream output
  - parse text/tool calls/result
  - check for COMPLETE
  - enforce timeouts
        |
        v
Collect commits
        |
        v
Sync changes back to host repo
        |
        v
Merge or preserve branch/worktree
        |
        v
Clean up safely
```

# Initial project structure

Create or maintain this structure:

```text
ai_coder/
├── pyproject.toml
├── README.md
├── src/
│   └── ai_coder/
│       ├── __init__.py
│       ├── agent_provider.py
│       ├── orchestrator.py
│       ├── worktree_manager.py
│       ├── sandbox_provider.py
│       ├── prompt_resolver.py
│       ├── prompt_preprocessor.py
│       ├── sync_in.py
│       ├── sync_out.py
│       ├── display.py
│       ├── github_issues.py
│       └── ralph.py
└── tests/
    ├── test_agent_provider.py
    ├── test_orchestrator.py
    ├── test_worktree_manager.py
    ├── test_prompt_resolver.py
    ├── test_prompt_preprocessor.py
    ├── test_github_issues.py
    └── test_ralph.py
```

If the project already has a different structure, preserve the existing structure unless the GitHub issue explicitly asks to change it.

---

## Project design vocabulary

Use these terms consistently:

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

## Interface naming rule

Interface functions must follow this naming pattern:

```text
i_ + module_name + verb/action
```

Examples:

```text
i_worktree_create()
i_prompt_resolve()
i_orchestrator_run()
i_github_issue_select()
```

Do not expose many public functions.

Prefer a small interface with useful behavior hidden behind it.

Private helper functions should start with `_`.

---

## Expected behavior source of truth

Expected behavior is defined by the tests.

Read this file before changing behavior:

```text
tests/
```

# Testing rules

Expected behavior is defined by tests.

Before changing behavior:

1. Read the related tests.
2. Add or update a failing pytest test when behavior is missing.
3. Write the smallest implementation needed to pass.
4. Refactor only after tests pass.

Use this test command first:

```powershell
poetry run pytest
```

If Poetry is not available inside the environment, use:

```powershell
pytest
```

Do not use this command for this project:

```powershell
python -m pytest --capture=tee-sys
```

When testing printed output, use pytest output capture such as `capsys`.

Avoid testing private implementation details directly.

Prefer tests that cross the public interface seam.

---

# Done

When all actionable issues are complete (or you are blocked on all remaining ones), output the completion signal:

<promise>COMPLETE</promise>
