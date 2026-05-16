# src/ai_coder/ralph/ralph.py
"""
Run the RALPH local coding-agent workflow.

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

This module exposes one main interface seam: :func:`i_ralph_run`.
The remaining functions are private helpers that keep the public seam small.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path

from typing import Any, Iterable

from ai_coder.agent_provider import (
    AgentProvider,
    COMPLETE_TOKEN,
    FakeTestAgentProvider,
    MockAgentProvider,
)

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

from ai_coder.repository_context import (
    i_repository_context_discover,
    i_repository_start,
)


from ai_coder.sandbox_provider import i_sandbox_start


from ai_coder.sync_out import SyncMergeResult, i_sync_out_merge
from ai_coder.test_runner import TestRunResult, i_test_runner_run
from ai_coder.worktree_manager import (
    WorktreeCleanupResult,
    i_worktree_cleanup,
    i_worktree_create,
)


from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()

#: Default prompt text used when the caller does not pass a prompt file.
DEFAULT_RALPH_PROMPT_TEMPLATE = """# RALPH Core Instructions

You are RALPH — Repository Autonomous Local Patch Helper.

RALPH is a minimal local coding-agent loop.


Repository context

{{REPOSITORY_CONTEXT}}


Issue #{{ISSUE_NUMBER}}: {{ISSUE_TITLE}}

{{ISSUE_BODY}}


"""


#: Status returned when RALPH completed, tests passed, and work was merged.
RALPH_STATUS_COMPLETE = "complete"
#: Status returned when RALPH stopped before the completion signal.
RALPH_STATUS_INCOMPLETE = "incomplete"
#: Status returned when an agent, test, sync, or cleanup step failed.
RALPH_STATUS_FAILED = "failed"
#: Status returned when RALPH could not safely start or continue.
RALPH_STATUS_BLOCKED = "blocked"
#: Status returned when the run completed but no code changes were detected.
RALPH_STATUS_NO_CHANGES = "no_changes"

#: Complete set of valid :class:`RalphResult` status values.
RALPH_RESULT_STATUSES = (
    RALPH_STATUS_COMPLETE,
    RALPH_STATUS_INCOMPLETE,
    RALPH_STATUS_FAILED,
    RALPH_STATUS_BLOCKED,
    RALPH_STATUS_NO_CHANGES,
)


@dataclass(frozen=True)
class RalphResult:
    """
    Store the final result of one RALPH workflow run.

    :ivar selected_issue: GitHub issue selected for the run, or ``None`` when
        RALPH stopped before issue selection.
    :vartype selected_issue: GitHubIssue | None
    :ivar prompt: Final prompt sent to the agent after preprocessing.
    :vartype prompt: str
    :ivar orchestrator_result: Result returned by the orchestrator, or ``None``
        when RALPH stopped before the agent loop.
    :vartype orchestrator_result: OrchestratorResult | None
    :ivar completed: ``True`` when the workflow reached the complete status.
    :vartype completed: bool
    :ivar message: Human-readable summary of the final workflow state.
    :vartype message: str
    :ivar status: Stable machine-readable status for the workflow result.
    :vartype status: str
    """

    selected_issue: GitHubIssue | None
    prompt: str
    orchestrator_result: OrchestratorResult | None
    completed: bool
    message: str
    status: str = RALPH_STATUS_INCOMPLETE


def i_ralph_run(
    issues: Iterable[GitHubIssue] | None = None,
    prompt_template: str = DEFAULT_RALPH_PROMPT_TEMPLATE,
    agent_provider: AgentProvider | None = None,
    max_iterations: int = 3,
    prompt_path: str | Path | None = None,
    repo_path: str | Path | None = None,
    allow_no_changes: bool = False,
) -> RalphResult:
    """
    Run one end-to-end RALPH tracer-bullet workflow.

    The workflow starts from a Git repository, selects one actionable issue,
    creates a worktree, starts a sandbox, prepares a prompt, runs the agent,
    checks completion, runs tests, syncs successful work, closes the issue only
    after success, and then cleans up or preserves the worktree.

    :param issues: Optional iterable of issues to use instead of loading issues
        from configuration, a file, or the GitHub API.
    :type issues: Iterable[GitHubIssue] | None
    :param prompt_template: Inline prompt template used as the base RALPH
        prompt.
    :type prompt_template: str
    :param agent_provider: Optional provider used by the orchestrator. When not
        provided, RALPH builds a default fake test provider from the sandbox
        handle.
    :type agent_provider: AgentProvider | None
    :param max_iterations: Maximum number of orchestrator iterations allowed.
    :type max_iterations: int
    :param prompt_path: Optional path to an additional prompt file.
    :type prompt_path: str | Path | None
    :param repo_path: Optional repository path. When omitted, the configured
        repository path is used.
    :type repo_path: str | Path | None
    :param allow_no_changes: Treat a completed, passing run with no detected code
        changes as complete instead of ``no_changes``.
    :type allow_no_changes: bool
    :return: Final workflow result.
    :rtype: RalphResult
    """

    logger.info("Starting RALPH run...")

    # 1. Start with a Git repository.
    logger.info("Step 1: Start with a Git repository.")

    repository_result = i_repository_start(repo_path or setup_config.repo_path)

    logger.info(repository_result.message)

    if not repository_result.ready:
        logger.info(
            "Repository context is blocked. RALPH will stop before issue selection."
        )

        return RalphResult(
            selected_issue=None,
            prompt="",
            orchestrator_result=None,
            completed=False,
            message=repository_result.message,
            status="blocked",
        )

    logger.info("Step 2: Read open GitHub issues.")

    logger.info("Step 2: Read open GitHub issues.")
    resolved_issues = _resolve_issue_source(issues, setup_config)
    logger.info(
        f"Resolved {len(resolved_issues)} open GitHub issues to consider for this run."
    )
    logger.info(f"Issue numbers: {[issue.number for issue in resolved_issues]}")
    logger.info(f"Issue titles: {[issue.title for issue in resolved_issues]}")
    logger.info(f"Issue labels: {[issue.labels for issue in resolved_issues]}")
    logger.info(f"Issue states: {[issue.state for issue in resolved_issues]}")
    logger.info(f"Issue bodies: {[issue.body for issue in resolved_issues]}")
    logger.info(f"Issue blocked_by: {[issue.blocked_by for issue in resolved_issues]}")

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
            status=RALPH_STATUS_BLOCKED,
        )

    logger.info(f"Selected issue #{selected_issue.number}: {selected_issue.title}")

    # 4. Create a safe working copy using a Git worktree.
    logger.info("Step 4: Create a safe working copy using a Git worktree.")
    worktree_result = i_worktree_create(
        repo_path=repository_result.repo_path,
        issue_number=selected_issue.number,
        issue_title=selected_issue.title,
    )
    logger.info(worktree_result.message)

    if not worktree_result.created:
        logger.info("Worktree creation failed. RALPH will stop before sandbox startup.")
        return RalphResult(
            selected_issue=selected_issue,
            prompt="",
            orchestrator_result=None,
            completed=False,
            message=worktree_result.message,
            status="blocked",
        )

    # 5. Start a sandbox or local execution environment.

    logger.info("Step 5: Start a sandbox or local execution environment.")
    sandbox_result = i_sandbox_start(worktree_result.worktree_path)
    logger.info(sandbox_result.message)

    if not sandbox_result.started:
        logger.info(
            "Sandbox startup failed. Preserving worktree before stopping RALPH."
        )
        cleanup_result = i_worktree_cleanup(
            repo_path=repository_result.repo_path,
            worktree_path=worktree_result.worktree_path,
            completed=False,
        )
        logger.info(f"Worktree removed: {cleanup_result.removed}")
        logger.info(f"Worktree preserved: {cleanup_result.preserved}")
        logger.info(cleanup_result.reason)
        logger.info(cleanup_result.message)

        message_result = f"{sandbox_result.message}\n{cleanup_result.message}"

        return RalphResult(
            selected_issue=selected_issue,
            prompt="",
            orchestrator_result=None,
            completed=False,
            message=message_result,
            status="blocked",
        )

    logger.info("Step 5b: Discover prompt-safe repository context.")
    repository_context_result = i_repository_context_discover(
        repository_result.repo_path
    )

    logger.info(repository_context_result.prompt_summary)

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
    logger.info(f"Raw prompt template before preprocessing:\n{raw_prompt_template}")
    logger.info(
        f"Selected issue for prompt preprocessing: #{selected_issue.number} - {selected_issue.title}"
    )

    prompt = _preprocess_prompt_after_sandbox_ready(
        raw_prompt_template=raw_prompt_template,
        selected_issue=selected_issue,
        repository_context_summary=repository_context_result.prompt_summary,
        branch_name=worktree_result.branch_name,
        worktree_path=worktree_result.worktree_path,
    )

    logger.info(f"Final prompt after preprocessing:\n{prompt}")

    selected_agent_provider = _build_default_agent_provider(
        agent_provider=agent_provider,
        sandbox_handle=sandbox_result.handle,
    )

    logger.info(f"Using agent provider: {selected_agent_provider.__class__.__name__}")

    # 7. Let the agent edit files, run commands, and commit changes.
    logger.info("Step 7: Let the agent edit files, run commands, and commit changes.")
    orchestrator_result = i_orchestrator_run(
        selected_agent_provider,
        prompt,
        max_iterations=max_iterations,
    )

    logger.info(
        "Orchestrator result: completed=%s, iterations=%d, error=%s",
        orchestrator_result.completed,
        orchestrator_result.iterations,
        orchestrator_result.error,
    )
    logger.info("Final agent output: %s", orchestrator_result.final_output)
    logger.info("All agent outputs: %s", orchestrator_result.outputs)
    logger.info(
        "Agent provider used: %s",
        selected_agent_provider.__class__.__name__,
    )
    # logger.info(f"Prompt given to agent: {prompt}")

    # 8. Detect whether the task is complete.
    logger.info("Step 8: Detect whether the task is complete.")
    completion_result = i_completion_detector_detect(orchestrator_result.final_output)

    logger.info(completion_result.message)

    # 9. Run tests.

    logger.info("Step 9: Run tests.")
    test_command = _build_test_command_tuple(repository_context_result.test_command)
    test_result = i_test_runner_run(
        sandbox_handle=sandbox_result.handle,
        command=test_command,
    )
    logger.info(f"Tests passed: {test_result.passed}")
    logger.info(f"Test command: {test_result.command}")
    logger.info(f"Test exit code: {test_result.exit_code}")
    logger.info(f"Test stdout: {test_result.stdout}")
    logger.info(f"Test stderr: {test_result.stderr}")

    logger.info(test_result.message)

    # 10. Sync or merge the finished work back to the host repo.
    logger.info("Step 10: Sync or merge the finished work back to the host repo.")

    should_commit = (
        orchestrator_result.completed
        and test_result.passed
        and not getattr(test_result, "blocked", False)
    )

    if should_commit:
        sync_result = i_sync_out_merge(
            completed=True,
            worktree_path=worktree_result.worktree_path,
            issue_number=selected_issue.number,
            issue_title=selected_issue.title,
            commit_message_template=setup_config.commit_message_template,
        )
    else:
        sync_result = SyncMergeResult(
            merged=False,
            committed=False,
            failed=False,
            worktree_path=worktree_result.worktree_path,
            message=(
                "Skipped sync or commit because RALPH did not complete "
                "or tests did not pass."
            ),
        )

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

    logger.info(
        f"Close issue result: Issue #{close_result.issue_number} closed: {close_result.closed}"
    )
    logger.info(close_result.message)

    # 12. Preserve the worktree if there are uncommitted changes or a failure.
    logger.info("Step 12: Preserve or clean up the worktree based on final run state.")

    cleanup_completed = (
        orchestrator_result.completed
        and test_result.passed
        and not getattr(sync_result, "failed", False)
    )

    cleanup_has_uncommitted_changes = (
        True if getattr(sync_result, "has_uncommitted_changes", False) else None
    )

    cleanup_result = i_worktree_cleanup(
        repo_path=repository_result.repo_path,
        worktree_path=worktree_result.worktree_path,
        completed=cleanup_completed,
        has_uncommitted_changes=cleanup_has_uncommitted_changes,
    )

    logger.info(f"Worktree removed: {cleanup_result.removed}")
    logger.info(f"Worktree preserved: {cleanup_result.preserved}")
    logger.info(cleanup_result.reason)
    logger.info(cleanup_result.message)

    code_changes_detected = _code_changes_detected_from_cleanup(cleanup_result)

    result_status = _status_from_run_results(
        orchestrator_result=orchestrator_result,
        test_result=test_result,
        sync_result=sync_result,
        cleanup_result=cleanup_result,
        allow_no_changes=allow_no_changes,
        code_changes_detected=code_changes_detected,
    )

    workflow_message = _workflow_message_for_status(result_status)
    message_parts = [workflow_message]

    if orchestrator_result.error:
        message_parts.append(orchestrator_result.error)

    if not test_result.passed:
        message_parts.append(test_result.message)
        message_parts.append(_format_test_result_diagnostics(test_result))

    if getattr(sync_result, "failed", False):
        message_parts.append(sync_result.message)
    elif getattr(sync_result, "committed", False):
        message_parts.append(sync_result.message)

    if result_status == RALPH_STATUS_NO_CHANGES:
        message_parts.append(sync_result.message)

    message_parts.append(cleanup_result.message)
    message_result = "\n".join(message_parts)

    logger.info(f"Selected issue: #{selected_issue.number} - {selected_issue.title}")
    logger.info(f"Orchestrator result: {orchestrator_result}")
    logger.info(f"Completion detected: {completion_result.completed}")
    logger.info(f"Message: {message_result}")

    return RalphResult(
        selected_issue=selected_issue,
        prompt=prompt,
        orchestrator_result=orchestrator_result,
        completed=result_status == RALPH_STATUS_COMPLETE,
        message=message_result,
        status=result_status,
    )


def _build_default_agent_provider(
    agent_provider: AgentProvider | None,
    sandbox_handle: Any,
) -> AgentProvider:
    """
    Return the caller-provided agent provider or build the default fake provider.

    :param agent_provider: Optional provider supplied by tests or callers.
    :type agent_provider: AgentProvider | None
    :param sandbox_handle: Sandbox handle used to build the default provider.
    :type sandbox_handle: Any
    :return: Agent provider for the orchestrator loop.
    :rtype: AgentProvider
    :raises ValueError: If no provider is supplied and ``sandbox_handle`` is
        ``None``.

    :meta private:
    """

    if agent_provider is not None:
        return agent_provider

    if sandbox_handle is None:
        raise ValueError("sandbox_handle is required for the default fake test agent.")

    return FakeTestAgentProvider(sandbox_handle)


def _build_test_command_tuple(test_command: str) -> tuple[str, ...]:
    """
    Convert a shell-style test command string into a command tuple.

    :param test_command: Test command text discovered from configuration or the
        repository context.
    :type test_command: str
    :return: Split command tuple, or an empty tuple when no command is available.
    :rtype: tuple[str, ...]

    :meta private:
    """

    cleaned_test_command = test_command.strip()

    if not cleaned_test_command:
        return ()

    return tuple(shlex.split(cleaned_test_command))


def _format_test_result_diagnostics(test_result: TestRunResult) -> str:
    """
    Build a readable diagnostic block from a failed test result.

    :param test_result: Test runner result to summarize.
    :type test_result: TestRunResult
    :return: Multi-line text containing command, exit code, stdout, and stderr.
    :rtype: str

    :meta private:
    """

    command_text = " ".join(test_result.command) if test_result.command else "<missing>"
    stdout_text = test_result.stdout if test_result.stdout else "<empty>"
    stderr_text = test_result.stderr if test_result.stderr else "<empty>"

    return (
        f"Test command: {command_text}\n"
        f"Test exit code: {test_result.exit_code}\n"
        "Test stdout:\n"
        f"{stdout_text}\n"
        "Test stderr:\n"
        f"{stderr_text}"
    )


def _status_from_run_results(
    orchestrator_result: OrchestratorResult,
    test_result: TestRunResult,
    sync_result: SyncMergeResult,
    cleanup_result: WorktreeCleanupResult,
    allow_no_changes: bool = False,
    code_changes_detected: bool = False,
) -> str:
    """
    Derive the final RALPH status from the major workflow step results.

    :param orchestrator_result: Result from the agent orchestration loop.
    :type orchestrator_result: OrchestratorResult
    :param test_result: Result from the test runner seam.
    :type test_result: TestRunResult
    :param sync_result: Result from the sync or commit seam.
    :type sync_result: SyncMergeResult
    :param cleanup_result: Result from the worktree cleanup seam.
    :type cleanup_result: WorktreeCleanupResult
    :param allow_no_changes: Whether no-change completion should count as
        complete.
    :type allow_no_changes: bool
    :param code_changes_detected: Whether cleanup detected dirty worktree state
        or status output.
    :type code_changes_detected: bool
    :return: One value from :data:`RALPH_RESULT_STATUSES`.
    :rtype: str

    :meta private:
    """

    if not orchestrator_result.completed:
        if (
            orchestrator_result.error
            and orchestrator_result.error
            != "Maximum iterations reached before completion."
        ):
            return RALPH_STATUS_FAILED

        return RALPH_STATUS_INCOMPLETE

    if getattr(test_result, "blocked", False):
        return RALPH_STATUS_BLOCKED

    if not test_result.passed:
        return RALPH_STATUS_FAILED

    if sync_result.failed:
        return RALPH_STATUS_FAILED

    if sync_result.merged:
        return RALPH_STATUS_COMPLETE

    if not code_changes_detected:
        if allow_no_changes:
            return RALPH_STATUS_COMPLETE

        return RALPH_STATUS_NO_CHANGES

    return RALPH_STATUS_FAILED


def _code_changes_detected_from_cleanup(
    cleanup_result: WorktreeCleanupResult,
) -> bool:
    """
    Detect whether cleanup reported possible code changes.

    :param cleanup_result: Worktree cleanup result to inspect.
    :type cleanup_result: WorktreeCleanupResult
    :return: ``True`` when cleanup reported a dirty worktree or status output.
    :rtype: bool

    :meta private:
    """

    if cleanup_result.reason == "worktree_dirty":
        return True

    if cleanup_result.status_output.strip():
        return True

    return False


def _workflow_message_for_status(status: str) -> str:
    """
    Convert a RALPH status value into a short human-readable message.

    :param status: Machine-readable RALPH status value.
    :type status: str
    :return: Human-readable workflow summary.
    :rtype: str

    :meta private:
    """

    if status == RALPH_STATUS_COMPLETE:
        return "RALPH completed the selected issue."

    if status == RALPH_STATUS_FAILED:
        return "RALPH failed before completion."

    if status == RALPH_STATUS_BLOCKED:
        return "RALPH was blocked before completion."

    if status == RALPH_STATUS_NO_CHANGES:
        return "RALPH completed, but no code changes were detected."

    return "RALPH stopped before completion."


def _resolve_issue_source(
    issues: Iterable[GitHubIssue] | None,
    setup_config: c_setup_config,
) -> tuple[GitHubIssue, ...]:
    """
    Resolve the source of GitHub issues for the current RALPH run.

    The precedence is: caller-provided issues, test issue, user-configured
    issue, issue file, then the GitHub API.

    :param issues: Optional issues supplied directly by the caller.
    :type issues: Iterable[GitHubIssue] | None
    :param setup_config: Application configuration object.
    :type setup_config: c_setup_config
    :return: Issues available for selection.
    :rtype: tuple[GitHubIssue, ...]

    :meta private:
    """

    logger.info("START: Resolving issue source...")
    if issues is not None:
        logger.info("Using provided issues from User arguments.")
        return tuple(issues)

    if setup_config.testing_flag:
        logger.info("Using test GitHub issue.")
        return (_build_test_github_issue(setup_config),)

    if setup_config.has_user_github_issue():
        logger.info("Using user-provided GitHub issue.")
        return (_build_user_github_issue(setup_config),)

    if setup_config.github_issue_path.exists():
        logger.info("Using GitHub issue from file.")
        return (
            i_github_issue_from_file(
                setup_config.github_issue_path,
                default_label=setup_config.label,
            ),
        )

    logger.info("Using GitHub issues from the API.")
    return i_github_issue_list(label=setup_config.label)


def _build_test_github_issue(setup_config: c_setup_config) -> GitHubIssue:
    """
    Build a fake GitHub issue from test configuration values.

    :param setup_config: Application configuration object with test issue
        defaults.
    :type setup_config: c_setup_config
    :return: Test issue used for a local tracer-bullet run.
    :rtype: GitHubIssue

    :meta private:
    """

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
    """
    Build a GitHub issue from user-provided configuration values.

    :param setup_config: Application configuration object with issue fields.
    :type setup_config: c_setup_config
    :return: User-configured GitHub issue.
    :rtype: GitHubIssue

    :meta private:
    """

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
    """
    Combine the inline prompt template with an optional prompt file.

    :param prompt_template: Inline prompt template text.
    :type prompt_template: str
    :param prompt_path: Optional path to an additional project prompt file.
    :type prompt_path: str | Path | None
    :return: Resolved prompt template text.
    :rtype: str

    :meta private:
    """

    base_prompt = i_prompt_resolve(inline_prompt=prompt_template)

    if prompt_path is None:
        return base_prompt

    file_prompt = i_prompt_resolve(prompt_path=prompt_path)

    if not base_prompt.strip():
        return file_prompt

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
    """
    Resolve RALPH prompt text from inline text and an optional prompt file.

    :param prompt_template: Inline prompt template text.
    :type prompt_template: str
    :param prompt_path: Optional prompt file path.
    :type prompt_path: str | Path | None
    :return: Raw prompt template before placeholder preprocessing.
    :rtype: str

    :meta private:
    """

    logger.info("Step 6a: Resolve prompt text from file or inline prompt.")
    return _build_master_prompt_template(
        prompt_template=prompt_template,
        prompt_path=prompt_path,
    )


def _preprocess_prompt_after_sandbox_ready(
    raw_prompt_template: str,
    selected_issue: GitHubIssue,
    repository_context_summary: str = "",
    branch_name: str = "",
    worktree_path: str | Path | None = None,
) -> str:
    """
    Replace prompt placeholders after the sandbox and worktree are ready.

    :param raw_prompt_template: Prompt template before placeholder replacement.
    :type raw_prompt_template: str
    :param selected_issue: Issue selected for this RALPH run.
    :type selected_issue: GitHubIssue
    :param repository_context_summary: Prompt-safe repository context summary.
    :type repository_context_summary: str
    :param branch_name: Worktree branch name created for the issue.
    :type branch_name: str
    :param worktree_path: Worktree path created for the issue.
    :type worktree_path: str | Path | None
    :return: Final prompt text sent to the agent.
    :rtype: str

    :meta private:
    """

    logger.info("Step 6b: Preprocess prompt after sandbox is ready.")
    return i_prompt_preprocess(
        raw_prompt_template,
        _build_prompt_replacements(
            selected_issue=selected_issue,
            repository_context_summary=repository_context_summary,
            branch_name=branch_name,
            worktree_path=worktree_path,
        ),
    )


def _build_prompt_replacements(
    selected_issue: GitHubIssue,
    repository_context_summary: str = "",
    branch_name: str = "",
    worktree_path: str | Path | None = None,
) -> dict[str, object]:
    """
    Build the placeholder replacement dictionary for prompt preprocessing.

    :param selected_issue: Issue selected for the current RALPH run.
    :type selected_issue: GitHubIssue
    :param repository_context_summary: Prompt-safe repository context summary.
    :type repository_context_summary: str
    :param branch_name: Worktree branch name created for the issue.
    :type branch_name: str
    :param worktree_path: Worktree path created for the issue.
    :type worktree_path: str | Path | None
    :return: Mapping of placeholder names to safe replacement values.
    :rtype: dict[str, object]

    :meta private:
    """

    return {
        "ISSUE_NUMBER": selected_issue.number,
        "ISSUE_TITLE": selected_issue.title,
        "ISSUE_BODY": selected_issue.body,
        "ISSUE_LABELS": _format_issue_labels(selected_issue.labels),
        "BRANCH_NAME": branch_name,
        "WORKTREE_PATH": "" if worktree_path is None else str(worktree_path),
        "REPOSITORY_CONTEXT": repository_context_summary,
        "COMPLETE_TOKEN": COMPLETE_TOKEN,
    }


def _format_issue_labels(labels: tuple[str, ...]) -> str:
    """
    Format issue labels for prompt insertion.

    :param labels: GitHub issue labels.
    :type labels: tuple[str, ...]
    :return: Comma-separated label text.
    :rtype: str

    :meta private:
    """

    return ", ".join(labels)
