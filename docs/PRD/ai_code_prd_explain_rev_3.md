# Explain PRD: `ai_code_prd_rev_3.md`

A **PRD** means **Product Requirements Document**. Think of it like a **blueprint before building a house**. Before programmers start coding, the PRD explains:

What are we building?
Why are we building it?
Who is it for?
What must it do?
What is not included yet?
How will we know when it works?

Atlassian describes a PRD as a document that defines the product’s purpose, features, and behavior so the team knows what to build. ([Atlassian][1]) Your PRD is for a Python project called **AI Code**, and the coding agent inside it is called **RALPH**.

---

# 1. Big picture

Your PRD says:

**AI Code** is a Python project that will help a solo developer safely work through GitHub issues one at a time.

**RALPH** is the autonomous coding agent inside AI Code.

RALPH should act like a careful junior developer:

1. Pick one GitHub issue.
2. Create a safe Git worktree.
3. Work inside that safe copy.
4. Run commands through a sandbox.
5. Let an AI coding agent make changes.
6. Run tests.
7. Commit only if tests pass.
8. Preserve the worktree if something fails.

That last part is very important. The goal is not just “let AI write code.” The goal is **let AI write code safely**.

---

# 2. Problem statement

The problem is this:

Right now, you have to do many manual steps every time you want to fix a GitHub issue.

You must:

1. Read the issue.
2. Decide if the issue is clear enough.
3. Create a branch or worktree.
4. Prepare a prompt.
5. Run an AI coding tool.
6. Watch the output.
7. Review code changes.
8. Run tests.
9. Commit safe work.
10. Save failed work for debugging.

That is repetitive.

It is also risky because an AI agent could:

1. Edit your main project directly.
2. Hide command output.
3. Close an issue too early.
4. Leak secrets in logs.
5. Delete useful failed work.

So the PRD says AI Code should make this process safer and repeatable.

---

# 3. Solution

The solution is a controlled workflow.

RALPH should eventually do this:

```text
Read GitHub issues
Pick one actionable issue
Create Git worktree
Start sandbox
Prepare prompt
Run AI coding agent
Detect completion
Run tests
Commit successful changes
Preserve failed work
Later: create PR or close issue
```

The most important idea is:

**RALPH should not touch the main repo directly.**

Instead, it should work in a separate Git worktree. Git officially supports multiple working trees attached to one repository, which allows different branches to be checked out in separate directories. ([Git][2])

In simple words:

Your main project stays safe.
RALPH works in a separate copy.
If RALPH breaks something, you can inspect that separate copy without ruining your main folder.

---

# 4. First usable release

The PRD says the first release should be a **local single-issue tracer bullet**.

A tracer bullet means:

Build the smallest useful version that proves the whole idea works from start to finish.

So Release 1 should not try to build everything.

Release 1 should only prove this flow:

```text
Fake/provided issue
    ↓
Create worktree
    ↓
Start local sandbox
    ↓
Resolve prompt
    ↓
Run fake/test agent
    ↓
Detect <promise>COMPLETE</promise>
    ↓
Run pytest
    ↓
Commit if tests pass
    ↓
Preserve worktree if failure
```

This is smart because it avoids building a giant system too early.

You are proving the skeleton first.

---

# 5. Release phases

Your PRD breaks the future project into phases:

## Phase 1: Local single-issue tracer bullet

This is the first working version.

It uses:

```text
one issue
local sandbox
fake/test agent
pytest
commit after success
preserve on failure
```

## Phase 2: Docker bind-mount sandbox

This means RALPH can run commands inside Docker while the files still live on your Windows machine.

Docker bind mounts let a file or directory from the host machine appear inside a container. ([Docker Documentation][3]) Your PRD says the worktree should be mounted inside Docker at:

```text
/workspace
```

So inside Docker, commands run in:

```text
/workspace
```

But the actual files are still in the host worktree.

## Phase 3: Real AI coding-agent loop with CodexProvider

This is when RALPH moves from a fake/test agent to the real Codex provider.

## Phase 4: GitHub issue automation

This is when RALPH starts reading real GitHub issues automatically.

## Phase 5: Safe commit and PR workflow

This is when RALPH can create pull requests after successful work.

## Later phases

Later phases include:

```text
.ai-code/ template scaffolding
long-running Docker containers
multi-agent workflows
cloud sandbox providers
```

The PRD is doing the right thing by putting cloud sandboxes and multi-agent workflows far in the future.

---

# 6. Product identity

The PRD locks in these names:

```text
Product name: AI Code
Agent name: RALPH
Python package name: ai_coder
Future scaffold folder: .ai-code/
```

This matters because names affect code, documentation, GitHub issues, folders, commands, and tests.

The PRD also says not to use outside reference-project names. That means this project should become its own product, not just a copy of another system.

---

# 7. Core modules

The PRD wants AI Code to be built from small Python modules.

Important future modules include:

```text
setup_config.py
CLI entry point
RALPH orchestration
GitHub issue selection
worktree management
sandbox provider
Docker command utilities
agent provider
completion detection
prompt resolver
prompt preprocessor
test runner
display/logging
repository context discovery
template scaffolding
future sync-in/sync-out
```

The simple idea is:

Each module should have one job.

For example:

```text
worktree_manager.py
```

should handle Git worktrees.

```text
sandbox_provider.py
```

should handle command execution.

```text
prompt_resolver.py
```

should load prompt text.

```text
agent_provider.py
```

should know how to run a fake agent, Codex, or another future agent.

This keeps the project easier to understand.

---

# 8. Interface naming rule

The PRD says public interface functions must use this pattern:

```text
i_<module_name>_<action>()
```

Examples:

```python
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

This is like labeling the front door of each module.

A caller should use the public seam.

Private helper functions should start with:

```python
_
```

Example:

```python
def _build_branch_name():
    ...
```

That tells other programmers:

“This is internal. Do not call it from outside.”

---

# 9. setup_config.py is the source of truth

This is one of the most important design decisions.

The PRD says:

```text
setup_config.py is AI Code’s final runtime source of truth.
```

That means the final settings should live in one place.

The expected flow is:

```text
Load defaults and .env values
Validate them
Parse CLI arguments
Apply valid CLI values into setup_config.py
Validate again
Run RALPH using setup_config.py
```

Why is this good?

Because without this rule, configuration can get scattered everywhere:

```text
some in CLI
some in .env
some in random modules
some in hard-coded constants
```

That becomes confusing.

The PRD says: let CLI and `.env` feed into setup_config.py, but after validation, runtime modules should read from setup_config.py.

---

# 10. Worktree safety model

This PRD cares a lot about Git worktrees.

The rule is:

```text
Create a Git worktree before the agent edits code.
```

A worktree is like a separate checkout of your repo.

Example:

```text
Main repo:
C:\Users\ME\Documents\Python\2026\Projects\ai_coder

RALPH worktree:
C:\Users\ME\Documents\Python\2026\Projects\ai_coder-worktrees\issue-007
```

RALPH edits the second folder, not the main one.

The PRD says AI Code must:

1. Create one worktree per issue attempt.
2. Use a branch name connected to the issue.
3. Preserve the worktree on failure.
4. Preserve the worktree if uncommitted changes remain.
5. Remove the worktree only when the run succeeds and is clean.
6. Show the preserved worktree path to the user.

This is the safety belt of the whole project.

---

# 11. Sandbox provider

The PRD says RALPH should not directly know whether commands run locally, in Docker, or in a future cloud sandbox.

Instead, RALPH should call a sandbox seam:

```python
i_sandboxhandle_run()
```

The sandbox provider decides how to run the command.

That means this:

```text
RALPH says: run pytest
Sandbox decides: local? Docker? future cloud?
```

This is good design because later you can replace local execution with Docker without rewriting the orchestrator.

---

# 12. Docker bind-mount mode

In Phase 2, Docker mode should work like this:

```text
Host worktree path
    ↓ mounted into Docker
/workspace
    ↓ commands run here
pytest, agent commands, etc.
```

The container sees the mounted files. If the container edits files, the host worktree sees those edits too. Docker’s own documentation describes bind mounts as mounting a host file or directory into a container. ([Docker Documentation][3])

Your PRD says:

```text
Do not use sync-in/sync-out yet for Docker bind-mount mode.
```

That makes sense because bind mounts already share the files.

Sync-in/sync-out is for future isolated or cloud sandboxes.

---

# 13. Windows 11 Docker path handling

The PRD says Windows 11 is the main target.

That matters because Docker paths can be tricky on Windows.

For example, a Windows path looks like:

```text
C:\Users\ME\Documents\Python\2026\Projects\ai_coder
```

But Docker often needs paths in a different format.

The PRD says path conversion should be hidden behind a small utility seam.

That is good because you do not want Windows path logic spread across:

```text
ralph.py
orchestrator.py
sandbox_provider.py
agent_provider.py
```

Keep it in one place.

---

# 14. Secret and environment variable handling

This section is about safety.

The PRD says:

Do not pass all host environment variables into Docker.

That is important because your computer may have secrets like:

```text
OPENAI_API_KEY
ANTHROPIC_API_KEY
GH_TOKEN
```

Early Docker mode should not automatically pass these.

Instead, the PRD wants two allowlists:

```text
normal env allowlist
secret env allowlist
```

Normal environment variables can be logged.

Secret environment variables must be redacted.

The PRD also says the default secret allowlist should be empty.

That is cautious and good.

---

# 15. Prompt handling

The PRD says AI Code must support:

```text
inline prompts
prompt files
```

So the user can either type a prompt directly or use a reusable file.

There are two steps:

## Step 1: Resolve prompt

This means find the prompt text.

Example:

```text
Read prompt from file
```

or

```text
Use inline prompt text
```

The seam is:

```python
i_prompt_resolve()
```

## Step 2: Preprocess prompt

This means replace placeholders.

Example:

```text
{issue_number}
{issue_title}
{issue_body}
{branch_name}
{worktree_path}
```

The seam is:

```python
i_prompt_preprocess()
```

The PRD says preprocessing should happen only after the sandbox is ready because some placeholders may depend on sandbox-aware context.

Very important rule:

```text
Issue text is inert text.
```

That means if a GitHub issue body contains something like:

```powershell
delete everything
```

RALPH must not treat that as a real command.

It is just text.

---

# 16. Agent providers

The PRD says RALPH should not hard-code one AI tool.

Instead, it should use agent providers.

Early version:

```text
Fake/test agent
```

First real version:

```text
CodexProvider
```

Future versions:

```text
ClaudeProvider
OpenCodeProvider
other providers
```

The provider should know:

1. How to build the command.
2. How to pass the prompt.
3. How to parse output.
4. How to return normalized results.

This keeps RALPH from becoming messy.

RALPH should not know every detail of Codex, Claude, Docker, prompts, and tests all in one file.

---

# 17. CodexProvider

The PRD says Codex is the first real AI coding-agent provider.

CodexProvider should:

1. Start in non-interactive mode.
2. Prefer structured output when possible.
3. Fall back to plain stdout parsing.
4. Prefer stdin for large prompts.
5. Avoid putting large GitHub issue bodies directly in command arguments.
6. Avoid logging the full raw prompt.
7. Avoid logging secrets.
8. Test long prompts and special characters on Windows.

The important idea:

The provider owns Codex-specific details.

RALPH should only say:

```text
Run this agent provider with this prompt.
```

---

# 18. Completion detection

RALPH should not guess when the agent is done.

The PRD says the main completion signal is:

```xml
<promise>COMPLETE</promise>
```

So if the fake agent or Codex outputs:

```xml
<promise>COMPLETE</promise>
```

RALPH knows the agent claims the task is finished.

But that is not enough.

RALPH must still run tests.

The success path is:

```text
Agent says COMPLETE
Tests pass
Code changes exist
Commit succeeds
Result = complete
```

---

# 19. Result statuses

Every RALPH run must return one clear status:

```text
complete
incomplete
failed
blocked
no_changes
```

Here is what they mean:

## `complete`

Everything worked.

```text
Agent said COMPLETE
Tests passed
Changes were committed
```

## `incomplete`

The agent did not finish before max iterations.

Example:

```text
RALPH tried 3 times, but never saw <promise>COMPLETE</promise>
```

## `failed`

Something broke.

Example:

```text
agent command failed
sandbox command failed
pytest failed
git commit failed
```

## `blocked`

RALPH could not start or continue.

Example:

```text
missing config
missing Docker image
missing credentials
unsafe repo state
no actionable issue
```

## `no_changes`

The agent said complete, but no code changed.

That usually means the run should not be considered successful unless the issue specifically required no code change.

---

# 20. GitHub issue handling

The PRD says AI Code should eventually read real GitHub issues.

But it must be careful.

It should skip issues that are:

```text
too vague
blocked
already assigned
unsafe
not actionable
```

It should use issue information in the prompt:

```text
issue number
title
body
labels
```

But it must never close an issue before:

```text
tests pass
changes are committed
```

Pull requests and automatic issue closing are future work, not Release 1.

---

# 21. Repository context

RALPH needs some information about the repo before giving the prompt to the agent.

For example:

```text
repo root
active branch
whether the repo is dirty
package manager
test command
important files
```

But the PRD says repository context must stay small.

Do not include huge or sensitive folders like:

```text
.git/
.venv/
node_modules/
__pycache__/
.pytest_cache/
.env
.env.*
logs
large binary files
```

This matters because prompts should not contain secrets or useless noise.

---

# 22. Display and logging

The PRD wants the user to understand what happened.

RALPH should show:

```text
selected issue
current phase
agent output
command failures
stdout
stderr
exit code
test result
commit hash
preserved worktree path
```

This is important because if RALPH fails, you need to debug it.

The PRD also says logs should redact configured secret values.

That means logs should show something like:

```text
OPENAI_API_KEY=***
```

not the real key.

---

# 23. Testing philosophy

The PRD says tests should focus on behavior.

That means do not mostly test private helper functions.

Instead, test public seams like:

```python
i_worktree_create()
i_prompt_resolve()
i_prompt_preprocess()
i_sandboxhandle_run()
i_orchestrator_run()
i_ralph_run()
```

The question each test should answer is:

```text
When the user runs this public function, does the system do the right thing?
```

The PRD also mentions pytest monkeypatch for environment variable tests. Pytest’s documentation says monkeypatch can safely set or delete environment variables during tests. ([pytest][4])

That is useful for testing things like:

```text
missing GH_TOKEN
missing OPENAI_API_KEY
PYTHONUNBUFFERED defaulting to 1
secret env redaction
```

---

# 24. What is out of scope?

The PRD clearly says Release 1 should not do these yet:

```text
multiple issues at once
parallel planning
multiple AI agents
long-running Docker containers
cloud sandboxes
automatic Docker image building
automatic GitHub issue closing
pull request creation
complex sync-in/sync-out
full template scaffolding
production deployment
deleting dirty worktrees
hiding logs from the user
```

This is good.

It protects the project from becoming too big too fast.

---

# 25. Open questions

The PRD still has unresolved decisions.

Important ones include:

```text
What exact command starts AI Code?
What CLI flags should Release 1 support?
What setup_config.py fields are required first?
What exactly should the fake/test agent do?
Should Release 1 use real GitHub issues or fake/provided issues?
What should commit messages look like?
Should RALPH print a suggested PR command after commit?
What Docker image contents are required?
What Codex CLI flags should be used first?
What scaffold templates should .ai-code/ support first?
```

These open questions should probably become GitHub issues or a decision document.

---

# 26. Simple explanation of the whole PRD

This PRD says:

```text
We are building AI Code, a Python tool for Windows 11.

Inside AI Code is RALPH, an autonomous coding agent.

RALPH will eventually read GitHub issues and fix them one at a time.

But RALPH must be safe.

It should never edit the main repo directly.

It should create a Git worktree, run commands through a sandbox, use a prompt, run an AI agent, detect completion, run tests, commit only if tests pass, and preserve failed work for review.

Release 1 should be very small:
one issue, local sandbox, fake/test agent, pytest, commit, preserve on failure.

Docker, Codex, GitHub automation, PR creation, templates, multi-agent workflows, and cloud sandboxes come later.
```

---

# 27. Best next step

The best next step is to turn the open Release 1 questions into one small GitHub issue:

```text
Confirm Release 1 runtime contract
```

That issue should decide:

```text
start command
CLI flags
minimum setup_config.py fields
fake/test agent behavior
commit message format
whether Release 1 uses fake or real GitHub issue input
```

After that, the project can safely continue with small tracer-bullet implementation issues.

[1]: https://www.atlassian.com/agile/product-management/requirements?utm_source=chatgpt.com "What is a Product Requirements Document (PRD)?"
[2]: https://git-scm.com/docs/git-worktree?utm_source=chatgpt.com "Git - git-worktree Documentation"
[3]: https://docs.docker.com/engine/storage/bind-mounts/?utm_source=chatgpt.com "Bind mounts"
[4]: https://docs.pytest.org/en/stable/how-to/monkeypatch.html?utm_source=chatgpt.com "How to monkeypatch/mock modules and environments"
