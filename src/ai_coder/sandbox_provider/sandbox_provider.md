## What `sandbox_provider.py` means

`sandbox_provider.py` is the module that answers this question:

```text
Where does RALPH run commands?
```

For RALPH, commands are things like:

```powershell
poetry run pytest
git status --porcelain
git add .
git commit -m "Fix issue"
```

At first, those commands may run directly on your Windows computer. Later, they should run inside Docker. That is why `sandbox_provider.py` is important: it hides **how** commands run.

Your current project explanation says RALPH already has a `sandbox_provider` step after `worktree_manager` creates a safe worktree plan. Sandcastle also uses this idea: a sandbox provider tells the system how to execute commands in an isolated environment, and it has two styles: **bind-mount** and **isolated**.

---

## High-school explanation

Think of RALPH like a student robot doing homework.

```text
GitHub issue = homework assignment
Git repo = school binder
Git worktree = copied worksheet
Sandbox = desk where the robot works
sandbox_provider.py = the rulebook for choosing the desk
```

So `sandbox_provider.py` says:

```text
Do we let RALPH work on the normal Windows desk?
Or do we put RALPH inside a Docker desk?
```

RALPH should not care. RALPH should just say:

```python
sandbox.i_sandboxhandle_run(["poetry", "run", "pytest"])
```

Then the sandbox decides where that command really runs.

---

## Why this module is a seam

In your design vocabulary:

```text
Module:
sandbox_provider.py

Interface:
SandboxHandle
BindMountSandboxProvider

Implementation:
LocalSandboxHandle
DockerSandboxHandle

Seam:
RALPH calls i_sandboxhandle_run()

Adapter:
LocalSandboxProvider or DockerSandboxProvider

Depth:
The module hides subprocess and Docker details.

Leverage:
RALPH can switch from Windows local execution to Docker without rewriting ralph.py.

Locality:
Docker bugs stay inside sandbox_provider.py, not spread across the project.
```

That is the main purpose.

---

## The simplest correct mental model

```text
ralph.py
  |
  v
sandbox_provider.py
  |
  +-- LocalSandboxHandle
  |     runs commands on Windows
  |
  +-- DockerSandboxHandle
        runs commands inside Docker
```

RALPH should not do this:

```python
subprocess.run(["poetry", "run", "pytest"])
```

RALPH should do this:

```python
sandbox.i_sandboxhandle_run(["poetry", "run", "pytest"])
```

That keeps command execution behind one clean interface.

Python’s official docs say `subprocess.run()` is the recommended approach for normal subprocess execution, so `LocalSandboxHandle` can use `subprocess.run()` internally. ([Python documentation][1]) But only the sandbox adapter should know that.

---

## Why RALPH should use bind-mount first

You said RALPH should use **bind-mount**.

That means:

```text
Windows creates the worktree.
Docker mounts that worktree.
The agent edits files inside Docker.
The real changed files stay in the Windows worktree.
```

Docker bind mounts use this shape:

```text
docker run -v <host-path>:<container-path>[:opts]
```

The first path is the host path, and the second path is where that folder appears inside the container. ([Docker Documentation][2])

So RALPH should do this:

```text
Windows host:
C:\Users\ME\Documents\Python\2026\Projects\ai_code\.ralph\worktrees\issue-7

Docker container:
/workspace
```

Then inside Docker, RALPH or the agent works in:

```text
/workspace
```

But the real files are still in the Windows worktree.

---

## How `sandbox_provider.py` fits into the RALPH flow

Your flow should look like this:

```text
1. ralph.py selects a GitHub issue.
2. worktree_manager.py creates a safe Git worktree.
3. sandbox_provider.py starts the sandbox.
4. prompt_resolver.py loads the prompt.
5. prompt_preprocessor.py fills placeholders.
6. agent_provider.py runs the AI coding agent.
7. orchestrator.py loops until complete.
8. test_runner.py runs tests through the sandbox.
9. sync_out.py later merges or syncs.
10. worktree_manager.py preserves dirty worktrees on failure.
```

Git worktree is useful here because Git officially supports multiple working trees attached to the same repository, allowing more than one branch to be checked out at a time. ([Git][3])

So the safe rule is:

```text
Never let the AI agent work directly in the main repo.
Always give it a worktree.
Then mount that worktree into Docker.
```

---

## Recommended `sandbox_provider.py` design

For your naming rule, use:

```text
i_sandboxhandle_run()
i_sandboxhandle_close()
```

A good first version of `sandbox_provider.py` would define the shared interface and one local implementation first.

```python
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class CommandResult:
    stdout: str
    stderr: str
    exit_code: int


@dataclass(frozen=True)
class MountConfig:
    host_path: Path
    sandbox_path: str
    readonly: bool = False


class SandboxHandle(Protocol):
    worktree_path: Path

    def i_sandboxhandle_run(
        self,
        command: list[str],
        cwd: Path | None = None,
    ) -> CommandResult:
        ...

    def i_sandboxhandle_close(self) -> None:
        ...


class LocalSandboxHandle:
    def __init__(self, worktree_path: Path) -> None:
        self.worktree_path = worktree_path

    def i_sandboxhandle_run(
        self,
        command: list[str],
        cwd: Path | None = None,
    ) -> CommandResult:
        run_cwd = cwd or self.worktree_path

        completed_process = subprocess.run(
            command,
            cwd=run_cwd,
            capture_output=True,
            text=True,
            check=False,
        )

        return CommandResult(
            stdout=completed_process.stdout,
            stderr=completed_process.stderr,
            exit_code=completed_process.returncode,
        )

    def i_sandboxhandle_close(self) -> None:
        return None


def i_sandbox_start(worktree_path: Path) -> SandboxHandle:
    return LocalSandboxHandle(worktree_path=worktree_path)
```

This is still simple, but it creates the correct seam.

---

## What each part does

### `CommandResult`

This stores the result of running a command.

```python
@dataclass(frozen=True)
class CommandResult:
    stdout: str
    stderr: str
    exit_code: int
```

Meaning:

```text
stdout = normal output
stderr = error output
exit_code = 0 means success, non-zero usually means failure
```

Example:

```text
poetry run pytest
```

might return:

```text
stdout = "12 passed"
stderr = ""
exit_code = 0
```

Or if tests fail:

```text
stdout = "2 failed, 10 passed"
stderr = ""
exit_code = 1
```

---

### `MountConfig`

This is for Docker later.

```python
@dataclass(frozen=True)
class MountConfig:
    host_path: Path
    sandbox_path: str
    readonly: bool = False
```

Meaning:

```text
host_path = folder on Windows
sandbox_path = folder inside Docker
readonly = whether Docker can only read it
```

Example:

```python
MountConfig(
    host_path=Path(r"C:\Users\ME\Documents\Python\2026\Projects\ai_code\.ralph\worktrees\issue-7"),
    sandbox_path="/workspace",
    readonly=False,
)
```

This means:

```text
Mount this Windows folder into Docker as /workspace.
Docker can write to it.
```

---

### `SandboxHandle`

This is the interface.

```python
class SandboxHandle(Protocol):
    worktree_path: Path

    def i_sandboxhandle_run(...):
        ...

    def i_sandboxhandle_close(...):
        ...
```

A Python `Protocol` lets you define what methods an object must have without forcing inheritance. Python’s typing docs describe protocols as structural subtyping, meaning an object matches the protocol if it has the right shape. ([typing.python.org][4])

In plain English:

```text
Any object with worktree_path, i_sandboxhandle_run(), and i_sandboxhandle_close()
can be treated as a SandboxHandle.
```

So both of these can be valid later:

```text
LocalSandboxHandle
DockerSandboxHandle
```

as long as they provide the same interface.

---

### `LocalSandboxHandle`

This is the first adapter.

```python
class LocalSandboxHandle:
```

It runs commands directly on your Windows computer.

That is useful for the first tracer bullet because it is easier to test than Docker.

But RALPH still calls the same method:

```python
sandbox.i_sandboxhandle_run(...)
```

That means later you can swap:

```python
LocalSandboxHandle
```

for:

```python
DockerSandboxHandle
```

without changing the RALPH workflow.

---

### `i_sandbox_start()`

This is the public module interface.

```python
def i_sandbox_start(worktree_path: Path) -> SandboxHandle:
    return LocalSandboxHandle(worktree_path=worktree_path)
```

For now, it returns a local sandbox.

Later, it can decide:

```text
If sandbox_type == "local":
    return LocalSandboxHandle

If sandbox_type == "docker":
    return DockerSandboxHandle
```

So `i_sandbox_start()` is the doorway into the module.

---

## What the future Docker version should do

Later, `DockerSandboxHandle` should do something like this:

```text
1. Start Docker container.
2. Bind-mount the worktree into /workspace.
3. Run commands inside /workspace.
4. Stop/remove container when done.
```

The Docker command will conceptually look like:

```text
docker run --rm -v <worktree_path>:/workspace -w /workspace <image> <command>
```

That means:

```text
-v <worktree_path>:/workspace
```

mounts the Windows worktree into Docker.

And:

```text
-w /workspace
```

makes `/workspace` the working directory.

---

## What `sandbox_provider.py` should NOT do yet

For your first tracer bullet, do not make this too big.

Do **not** add all of this immediately:

```text
full Docker lifecycle
cloud sandbox
copyIn / copyOut
network settings
interactive terminal mode
Claude session storage
multi-provider config system
```

Sandcastle has those ideas, but your Python project should grow one safe slice at a time.

Right now, `sandbox_provider.py` should focus on this:

```text
Can RALPH run a command through a sandbox handle?
```

That is the first win.

---

## Best version for your project right now

For `ai_code`, the purpose of `sandbox_provider.py` should be:

```text
Provide one small interface that lets RALPH run commands in a worktree,
first locally, then inside Docker using a bind mount.
```

The most important public names should be:

```text
CommandResult
MountConfig
SandboxHandle
LocalSandboxHandle
i_sandbox_start()
i_sandboxhandle_run()
i_sandboxhandle_close()
```

The most important design rule:

```text
RALPH should never call subprocess.run() directly.
RALPH should only call sandbox.i_sandboxhandle_run().
```

That gives your project the right architecture for moving from local Windows execution to Docker bind-mount execution later.

[1]: https://docs.python.org/3/library/subprocess.html?utm_source=chatgpt.com "Subprocess management"
[2]: https://docs.docker.com/engine/storage/bind-mounts/?utm_source=chatgpt.com "Bind mounts"
[3]: https://git-scm.com/docs/git-worktree?utm_source=chatgpt.com "Git - git-worktree Documentation"
[4]: https://typing.python.org/en/latest/reference/protocols.html?utm_source=chatgpt.com "Protocols and structural subtyping"
