# src/ai_coder/ralph/ralph.py
"""
RALPH means:

R = Repository
A = Autonomous
L = Local
P = Patch
H = Helper

RALPH is the high-level local coding-agent workflow for this project.

RALPH should eventually automate this workflow:

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

Development workflow:

1. Explore — read the issue and examine relevant source files and tests.
2. Plan — decide what to change and why; keep changes small.
3. Red — write a failing test for missing behavior.
4. Green — write the smallest implementation to pass the test.
5. Refactor — improve the code while tests still pass.
6. Verify — run all tests before committing.
7. Commit — make one commit with message starting with `RALPH:`.
8. Close — only close the issue after tests pass and code is committed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ai_coder.agent_provider import AgentProvider, COMPLETE_TOKEN, MockAgentProvider
from ai_coder.completion_detector import i_completion_detector_detect
from ai_coder.github_issues import (
    GitHubIssue,
    i_github_issue_close,
    i_github_issue_from_file,
    i_github_issue_list,
    i_github_issue_select,
)
from ai_coder.orchestrator import OrchestratorResult, i_orchestrator_run
from ai_coder.prompt_preprocessor import i_prompt_preprocess
from ai_coder.prompt_resolver import i_prompt_resolve

from ai_coder.repository_context import i_repository_start
from ai_coder.sandbox_provider import i_sandbox_start
from ai_coder.sync_out import i_sync_out_merge
from ai_coder.test_runner import i_test_runner_run
from ai_coder.worktree_manager import (
    i_worktree_create,
    i_worktree_preserve,
)

from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()


DEFAULT_RALPH_PROMPT_TEMPLATE = """# RALPH Core Instructions

You are RALPH — Repository Autonomous Local Patch Helper.

RALPH is a minimal local coding-agent loop.

## Current Issue

Issue #{{ISSUE_NUMBER}}: {{ISSUE_TITLE}}

{{ISSUE_BODY}}

## Core Rules

- Work on one issue only.
- Keep the change small.
- Prefer tests that cross the public interface seam.
- Do not rename public interface functions unless the issue explicitly asks for it.
- Do not add unnecessary dependencies.
- Run pytest before saying the work is complete.

## Completion Signal

When the task is complete, output this exact completion signal:

{{COMPLETE_TOKEN}}
"""


@dataclass(frozen=True)
class RalphResult:
    selected_issue: GitHubIssue | None
    prompt: str
    orchestrator_result: OrchestratorResult | None
    completed: bool
    message: str


def i_ralph_run(
    issues: Iterable[GitHubIssue] | None = None,
    prompt_template: str = DEFAULT_RALPH_PROMPT_TEMPLATE,
    agent_provider: AgentProvider | None = None,
    max_iterations: int = 3,
    prompt_path: str | Path | None = None,
) -> RalphResult:
    logger.info("Starting RALPH run...")

    # 1. Start with a Git repository.
    logger.info("Step 1: Start with a Git repository.")
    repository_result = i_repository_start()
    logger.info(repository_result.message)

    # 2. Read open GitHub issues.
    logger.info("Step 2: Read open GitHub issues.")
    resolved_issues = _resolve_issue_source(issues, setup_config)

    # 3. Pick one actionable issue.
    logger.info("Step 3: Pick one actionable issue.")
    selected_issue = i_github_issue_select(resolved_issues)

    if selected_issue is None:
        return RalphResult(
            selected_issue=None,
            prompt="",
            orchestrator_result=None,
            completed=False,
            message="No open actionable issue selected.",
        )

    # 4. Create a safe working copy using a Git worktree.
    logger.info("Step 4: Create a safe working copy using a Git worktree.")
    worktree_result = i_worktree_create(
        repo_path=repository_result.repo_path,
        issue_number=selected_issue.number,
        issue_title=selected_issue.title,
    )
    logger.info(worktree_result.message)

    # 5. Start a sandbox or local execution environment.
    logger.info("Step 5: Start a sandbox or local execution environment.")
    sandbox_result = i_sandbox_start(worktree_result.worktree_path)
    logger.info(sandbox_result.message)

    # 6. Give an AI coding agent a prompt.
    logger.info("Step 6: Give an AI coding agent a prompt.")

    # 6a. Resolve prompt text from file or inline prompt.
    logger.info("Step 6a: Resolve prompt text from file or inline prompt.")
    raw_prompt_template = _resolve_prompt_text(
        prompt_template=prompt_template,
        prompt_path=prompt_path,
    )

    # 6b. Preprocess prompt after sandbox is ready.
    logger.info("Step 6b: Preprocess prompt after sandbox is ready.")
    prompt = _preprocess_prompt_after_sandbox_ready(
        raw_prompt_template=raw_prompt_template,
        selected_issue=selected_issue,
    )

    selected_agent_provider = agent_provider or MockAgentProvider()

    # 7. Let the agent edit files, run commands, and commit changes.
    logger.info("Step 7: Let the agent edit files, run commands, and commit changes.")
    orchestrator_result = i_orchestrator_run(
        selected_agent_provider,
        prompt,
        max_iterations=max_iterations,
    )

    # 8. Detect whether the task is complete.
    logger.info("Step 8: Detect whether the task is complete.")
    completion_result = i_completion_detector_detect(orchestrator_result.completed)
    logger.info(completion_result.message)

    # 9. Run tests.
    logger.info("Step 9: Run tests.")
    test_result = i_test_runner_run()
    logger.info(test_result.message)

    # 10. Sync or merge the finished work back to the host repo.
    logger.info("Step 10: Sync or merge the finished work back to the host repo.")
    sync_result = i_sync_out_merge(orchestrator_result.completed)
    logger.info(sync_result.message)

    # 11. Close the GitHub issue only after tests pass and the fix is committed.
    logger.info(
        "Step 11: Close the GitHub issue only after tests pass and the fix is committed."
    )
    close_result = i_github_issue_close(
        issue=selected_issue,
        tests_passed=test_result.passed,
        committed=sync_result.merged,
    )
    logger.info(close_result.message)

    # 12. Preserve the worktree if there are uncommitted changes or a failure.
    logger.info(
        "Step 12: Preserve the worktree if there are uncommitted changes or a failure."
    )
    preserve_result = i_worktree_preserve(
        completed=orchestrator_result.completed,
        has_uncommitted_changes=False,
    )
    logger.info(preserve_result.reason)

    ############################################################

    return RalphResult(
        selected_issue=selected_issue,
        prompt=prompt,
        orchestrator_result=orchestrator_result,
        completed=orchestrator_result.completed,
        message=(
            "RALPH completed the selected issue."
            if orchestrator_result.completed
            else "RALPH stopped before completion."
        ),
    )


def _resolve_issue_source(
    issues: Iterable[GitHubIssue] | None,
    setup_config: c_setup_config,
) -> tuple[GitHubIssue, ...]:
    if issues is not None:
        return tuple(issues)

    if setup_config.testing_flag:
        return (_build_test_github_issue(setup_config),)

    if setup_config.has_user_github_issue():
        return (_build_user_github_issue(setup_config),)

    if setup_config.github_issue_path.exists():
        return (
            i_github_issue_from_file(
                setup_config.github_issue_path,
                default_label=setup_config.label,
            ),
        )

    return i_github_issue_list(label=setup_config.label)


def _build_test_github_issue(setup_config: c_setup_config) -> GitHubIssue:
    issue_number = setup_config.issue_number if setup_config.issue_number > 0 else 1
    issue_title = setup_config.issue_title.strip() or "Minimal local RALPH loop"
    issue_body = setup_config.issue_body.strip() or (
        "Build fake issue input to mock agent completion flow."
    )

    return GitHubIssue(
        number=issue_number,
        title=issue_title,
        body=issue_body,
        labels=(setup_config.label,),
    )


def _build_user_github_issue(setup_config: c_setup_config) -> GitHubIssue:
    return GitHubIssue(
        number=setup_config.issue_number,
        title=setup_config.issue_title,
        body=setup_config.issue_body,
        labels=(setup_config.label,),
    )


def _build_master_prompt_template(
    prompt_template: str,
    prompt_path: str | Path | None,
) -> str:
    base_prompt = i_prompt_resolve(inline_prompt=prompt_template)

    if prompt_path is None:
        return base_prompt

    file_prompt = i_prompt_resolve(prompt_path=prompt_path)

    return (
        f"{base_prompt.rstrip()}\n\n"
        "###############################################################################\n"
        "# PROJECT PROMPT FROM PROMPT FILE\n"
        "###############################################################################\n\n"
        f"{file_prompt.strip()}\n"
    )


def _resolve_prompt_text(
    prompt_template: str,
    prompt_path: str | Path | None,
) -> str:
    logger.info("Step 6a: Resolve prompt text from file or inline prompt.")
    return _build_master_prompt_template(
        prompt_template=prompt_template,
        prompt_path=prompt_path,
    )


def _preprocess_prompt_after_sandbox_ready(
    raw_prompt_template: str,
    selected_issue: GitHubIssue,
) -> str:
    logger.info("Step 6b: Preprocess prompt after sandbox is ready.")
    return i_prompt_preprocess(
        raw_prompt_template,
        _build_prompt_replacements(selected_issue),
    )


def _build_prompt_replacements(
    selected_issue: GitHubIssue,
) -> dict[str, object]:
    return {
        "ISSUE_NUMBER": selected_issue.number,
        "ISSUE_TITLE": selected_issue.title,
        "ISSUE_BODY": selected_issue.body,
        "COMPLETE_TOKEN": COMPLETE_TOKEN,
    }
