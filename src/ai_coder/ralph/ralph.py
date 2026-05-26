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


from ai_coder.display import (
    DisplayProtocol,
    SilentDisplay,
    i_display_agent_events,
    i_display_cleanup_result,
    i_display_command_failure,
    i_display_commit_result,
    i_display_github_automation_dry_run_summary,
    i_display_issue_skip_reasons,
    i_display_phase,
    i_display_pull_request_draft,
    i_display_selected_issue,
    i_display_test_result,
    i_display_issue_close_result,
)

from ai_coder.codex_preflight import i_codex_preflight_check

from ai_coder.pull_request_draft import (
    PullRequestDraftResult,
    i_pull_request_draft_build,
)


from ai_coder.agent_provider import (
    AgentProvider,
    COMPLETE_TOKEN,
    i_agent_provider_create,
)

from ai_coder.completion_detector import i_completion_detector_detect


from ai_coder.github_issues import (
    GitHubIssue,
    GitHubIssueReadError,
    i_github_issue_close,
    i_github_issue_from_file,
    i_github_issue_list,
    i_github_issue_select_actionable,
    GitHubIssueCloseResult,
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

from ai_coder.project_setup import (
    ProjectSetupResult,
    i_project_setup_run,
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


GitHub issue

Issue #{{ISSUE_NUMBER}}: {{ISSUE_TITLE}}

Issue number: {{ISSUE_NUMBER}}

Issue title: {{ISSUE_TITLE}}

Issue labels: {{ISSUE_LABELS}}

Issue body:

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
    :ivar project_setup_result: Project setup phase result when project setup
        ran, or ``None`` when RALPH stopped before project setup.
    :vartype project_setup_result: ProjectSetupResult | None
    :ivar test_result: Final test phase result when final tests ran, or
        ``None`` when RALPH stopped before the final test phase.
    :vartype test_result: TestRunResult | None
    :ivar sync_result: Sync/commit phase result when Step 10 actually ran,
        or ``None`` when RALPH stopped before sync/commit or skipped
        sync/commit because completion/tests did not allow it.
    :vartype sync_result: SyncMergeResult | None
    :ivar cleanup_result: Cleanup/preservation phase result when cleanup ran,
        or ``None`` when RALPH stopped before any cleanup phase.
    :vartype cleanup_result: WorktreeCleanupResult | None
    """

    selected_issue: GitHubIssue | None
    prompt: str
    orchestrator_result: OrchestratorResult | None
    completed: bool
    message: str
    status: str = RALPH_STATUS_INCOMPLETE
    project_setup_result: ProjectSetupResult | None = None
    test_result: TestRunResult | None = None
    sync_result: SyncMergeResult | None = None
    cleanup_result: WorktreeCleanupResult | None = None
    pull_request_draft_result: PullRequestDraftResult | None = None
    issue_close_result: GitHubIssueCloseResult | None = None


def i_ralph_run(
    issues: Iterable[GitHubIssue] | None = None,
    prompt_template: str = DEFAULT_RALPH_PROMPT_TEMPLATE,
    agent_provider: AgentProvider | None = None,
    max_iterations: int = 3,
    prompt_path: str | Path | None = None,
    repo_path: str | Path | None = None,
    allow_no_changes: bool = False,
    display: DisplayProtocol | None = None,
    require_codex_preflight: bool = False,
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
    :param display: Optional display adapter. When omitted, RALPH uses
        ``SilentDisplay`` so tests and callers do not get noisy output.
    :type display: DisplayProtocol | None
    :param require_codex_preflight: When ``True``, run the read-only Codex
        provider/sandbox preflight before issue reading or worktree creation.
    :type require_codex_preflight: bool
    :return: Final workflow result.
    :rtype: RalphResult

    """

    logger.info("Starting RALPH run...")
    active_display = display if display is not None else SilentDisplay()

    #############################################
    # 1. Start with a Git repository.
    logger.info("Step 1: Start with a Git repository.")
    active_display.i_display_message("Step 1: Start with a Git repository.")
    i_display_phase(active_display, "setup")

    repository_result = i_repository_start(repo_path or setup_config.repo_path)

    logger.info(repository_result.message)
    active_display.i_display_message(repository_result.message)

    if not repository_result.ready:
        logger.info(
            "EXIT:`Repository context is blocked. RALPH will stop before issue selection."
        )

        return RalphResult(
            selected_issue=None,
            prompt="",
            orchestrator_result=None,
            completed=False,
            message=repository_result.message,
            status=RALPH_STATUS_BLOCKED,
        )

    if require_codex_preflight:
        logger.info("Step 1a: Run Codex preflight checks.")
        active_display.i_display_message("Step 1a: Run Codex preflight checks.")
        i_display_phase(active_display, "preflight")

        codex_preflight_result = i_codex_preflight_check(setup_config)

        logger.info(codex_preflight_result.message)
        active_display.i_display_message(codex_preflight_result.message)

        if codex_preflight_result.blocked:
            logger.info(
                "Codex preflight blocked RALPH before issue reading and worktree creation."
            )

            return RalphResult(
                selected_issue=None,
                prompt="",
                orchestrator_result=None,
                completed=False,
                message=codex_preflight_result.message,
                status=RALPH_STATUS_BLOCKED,
            )

    #############################################
    # 2. Read open GitHub issues.
    logger.info("Step 2: Read open GitHub issues.")
    active_display.i_display_message("Step 2: Read open GitHub issues.")

    try:
        resolved_issues = _resolve_issue_source(issues, setup_config)
    except GitHubIssueReadError as error:
        message_result = str(error)
        logger.info("GitHub issue reading blocked RALPH: %s", message_result)
        active_display.i_display_message(message_result)

        return RalphResult(
            selected_issue=None,
            prompt="",
            orchestrator_result=None,
            completed=False,
            message=message_result,
            status=RALPH_STATUS_BLOCKED,
        )

    logger.info(
        f"Resolved {len(resolved_issues)} open GitHub issues to consider for this run."
    )

    logger.info(f"Issue numbers: {[issue.number for issue in resolved_issues]}")
    logger.info(f"Issue titles: {[issue.title for issue in resolved_issues]}")
    logger.info(f"Issue labels: {[issue.labels for issue in resolved_issues]}")
    logger.info(f"Issue states: {[issue.state for issue in resolved_issues]}")
    # logger.info(f"Issue bodies: {[issue.body for issue in resolved_issues]}")
    logger.info(f"Issue body lengths: {[len(issue.body) for issue in resolved_issues]}")
    logger.info(f"Issue blocked_by: {[issue.blocked_by for issue in resolved_issues]}")

    #############################################
    # 3. Pick one actionable issue.
    logger.info("Step 3: Pick one actionable issue.")
    active_display.i_display_message("Step 3: Pick one actionable issue.")

    selection_result = i_github_issue_select_actionable(resolved_issues)
    i_display_issue_skip_reasons(
        active_display,
        selection_result.skipped_issues,
    )
    selected_issue = selection_result.selected_issue

    if selected_issue is None:
        message_result = _format_no_actionable_issue_message(
            selection_result.skipped_issues,
        )
        active_display.i_display_message("No open actionable issue selected.")
        return RalphResult(
            selected_issue=None,
            prompt="",
            orchestrator_result=None,
            completed=False,
            message=message_result,
            status=RALPH_STATUS_BLOCKED,
        )

    logger.info(f"Selected issue #{selected_issue.number}: {selected_issue.title}")

    i_display_selected_issue(
        active_display,
        issue_number=selected_issue.number,
        issue_title=selected_issue.title,
    )

    #############################################
    # 4. Create a safe working copy using a Git worktree.
    logger.info("Step 4: Create a safe working copy using a Git worktree.")
    active_display.i_display_message(
        "Step 4: Create a safe working copy using a Git worktree."
    )
    i_display_phase(active_display, "worktree")

    worktree_result = i_worktree_create(
        repo_path=repository_result.repo_path,
        issue_number=selected_issue.number,
        issue_title=selected_issue.title,
    )
    logger.info(worktree_result.message)
    active_display.i_display_message(worktree_result.message)

    if not worktree_result.created:
        logger.info("Worktree creation failed. RALPH will stop before sandbox startup.")
        active_display.i_display_message("RALPH blocked before sandbox startup.")
        return RalphResult(
            selected_issue=selected_issue,
            prompt="",
            orchestrator_result=None,
            completed=False,
            message=worktree_result.message,
            status="blocked",
        )

    #############################################
    # 5. Start a sandbox or local execution environment.
    logger.info("Step 5: Start a sandbox or local execution environment.")
    active_display.i_display_message(
        "Step 5: Start a sandbox or local execution environment."
    )
    i_display_phase(active_display, "sandbox")

    sandbox_result = i_sandbox_start(worktree_result.worktree_path)
    logger.info(sandbox_result.message)
    active_display.i_display_message(sandbox_result.message)

    if not sandbox_result.started:
        logger.info(
            "Sandbox startup failed. Preserving worktree before stopping RALPH."
        )
        i_display_phase(active_display, "cleanup")
        cleanup_result = i_worktree_cleanup(
            repo_path=repository_result.repo_path,
            worktree_path=worktree_result.worktree_path,
            completed=False,
        )
        logger.info(f"Worktree removed: {cleanup_result.removed}")
        logger.info(f"Worktree preserved: {cleanup_result.preserved}")
        logger.info(cleanup_result.reason)
        logger.info(cleanup_result.message)
        i_display_cleanup_result(
            active_display,
            removed=cleanup_result.removed,
            preserved=cleanup_result.preserved,
            worktree_path=cleanup_result.worktree_path,
            message=cleanup_result.message,
        )
        message_result = f"{sandbox_result.message}\n{cleanup_result.message}"

        return RalphResult(
            selected_issue=selected_issue,
            prompt="",
            orchestrator_result=None,
            completed=False,
            message=message_result,
            status="blocked",
            cleanup_result=cleanup_result,
        )

    #############################################
    # 5a. Detect Poetry, run poetry install, run poetry run pytest.
    logger.info("Step 5a: Detect Poetry, run poetry install, run poetry run pytest.")
    active_display.i_display_message(
        "Step 5a: Detect Poetry, run poetry install, run poetry run pytest."
    )

    project_setup_result = i_project_setup_run(
        worktree_path=worktree_result.worktree_path,
        sandbox_handle=sandbox_result.handle,
    )
    logger.info(project_setup_result.message)
    active_display.i_display_message(project_setup_result.message)

    if project_setup_result.blocked:
        logger.info("Project setup blocked. Preserving worktree before stopping RALPH.")
        _display_project_setup_failure(active_display, project_setup_result)
        i_display_phase(active_display, "cleanup")
        cleanup_result = i_worktree_cleanup(
            repo_path=repository_result.repo_path,
            worktree_path=worktree_result.worktree_path,
            completed=False,
        )
        logger.info(f"Worktree removed: {cleanup_result.removed}")
        logger.info(f"Worktree preserved: {cleanup_result.preserved}")
        logger.info(cleanup_result.reason)
        logger.info(cleanup_result.message)
        i_display_cleanup_result(
            active_display,
            removed=cleanup_result.removed,
            preserved=cleanup_result.preserved,
            worktree_path=cleanup_result.worktree_path,
            message=cleanup_result.message,
        )

        message_result = f"{project_setup_result.message}\n{cleanup_result.message}"

        return RalphResult(
            selected_issue=selected_issue,
            prompt="",
            orchestrator_result=None,
            completed=False,
            message=message_result,
            status=RALPH_STATUS_BLOCKED,
            project_setup_result=project_setup_result,
            cleanup_result=cleanup_result,
        )

    #############################################
    # 5b. Discover prompt-safe repository context.
    logger.info("Step 5b: Discover prompt-safe repository context.")
    active_display.i_display_message(
        "Step 5b: Discover prompt-safe repository context."
    )

    repository_context_result = i_repository_context_discover(
        worktree_result.worktree_path
    )

    logger.info(repository_context_result.prompt_summary)

    #############################################
    # 6. Give an AI coding agent a prompt.
    logger.info("Step 6: Give an AI coding agent a prompt.")
    active_display.i_display_message("Step 6: Give an AI coding agent a prompt.")
    i_display_phase(active_display, "prompt")
    #############################################
    # 6a. Resolve prompt text from file or inline prompt.
    logger.info("Step 6a: Resolve prompt text from file or inline prompt.")
    active_display.i_display_message(
        "Step 6a: Resolve prompt text from file or inline prompt."
    )

    raw_prompt_template = _resolve_prompt_text(
        prompt_template=prompt_template,
        prompt_path=prompt_path,
    )
    logger.info("Resolved prompt template length: %d", len(raw_prompt_template))
    active_display.i_display_message("Prompt resolved.")
    active_display.i_display_message(
        f"Prompt template length: {len(raw_prompt_template)}"
    )

    #############################################
    # 6b. Preprocess prompt after sandbox is ready.
    logger.info("Step 6b: Preprocess prompt after sandbox is ready.")
    active_display.i_display_message(
        "Step 6b: Preprocess prompt after sandbox is ready."
    )

    # logger.info(f"Raw prompt template before preprocessing:\n{raw_prompt_template}")
    logger.info(
        "Raw prompt template length before preprocessing: %d", len(raw_prompt_template)
    )

    logger.info(
        "Selected issue for prompt preprocessing: %s",
        f"#{selected_issue.number} - {selected_issue.title}",
    )

    prompt = _preprocess_prompt_after_sandbox_ready(
        raw_prompt_template=raw_prompt_template,
        selected_issue=selected_issue,
        repository_context_summary=repository_context_result.prompt_summary,
        branch_name=worktree_result.branch_name,
        worktree_path=worktree_result.worktree_path,
    )

    # logger.info(f"Final prompt after preprocessing:\n{prompt}")
    logger.info("Final prompt length after preprocessing: %d", len(prompt))
    active_display.i_display_message(f"Final prompt length: {len(prompt)}")

    selected_agent_provider = _build_default_agent_provider(
        agent_provider=agent_provider,
        sandbox_handle=sandbox_result.handle,
    )

    i_display_phase(active_display, "agent")
    logger.info(f"Using agent provider: {selected_agent_provider.__class__.__name__}")
    active_display.i_display_message(
        f"Agent provider: {selected_agent_provider.__class__.__name__}"
    )

    #############################################
    # 7. Let the agent edit files, run commands, and commit changes.
    logger.info("Step 7: Let the agent edit files, run commands, and commit changes.")
    active_display.i_display_message(
        "Step 7: Let the agent edit files, run commands, and commit changes."
    )

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
    # logger.info("Final agent output: %s", orchestrator_result.final_output)
    # logger.info("All agent outputs: %s", orchestrator_result.outputs)
    logger.info(
        "Final agent output summary: %s",
        _short_display_text(orchestrator_result.final_output),
    )

    logger.info(
        "Agent output count: %d",
        len(orchestrator_result.outputs),
    )
    logger.info(
        "Agent event count: %d",
        len(orchestrator_result.events),
    )
    i_display_agent_events(active_display, orchestrator_result.events)

    logger.info(
        "Agent provider used: %s",
        selected_agent_provider.__class__.__name__,
    )

    active_display.i_display_message(
        f"Agent completed: {orchestrator_result.completed}"
    )
    active_display.i_display_message(
        f"Agent final output: {_short_display_text(orchestrator_result.final_output)}"
    )
    # logger.info(f"Prompt given to agent: {prompt}")

    #############################################
    # 8. Detect whether the task is complete.
    logger.info("Step 8: Detect whether the task is complete.")
    active_display.i_display_message("Step 8: Detect whether the task is complete.")
    completion_result = i_completion_detector_detect(orchestrator_result.final_output)

    logger.info(completion_result.message)
    active_display.i_display_message(completion_result.message)

    #############################################
    # 9. Run tests.
    logger.info("Step 9: Run tests.")
    active_display.i_display_message("Step 9: Run tests.")
    i_display_phase(active_display, "tests")

    test_command = _build_test_command_tuple(repository_context_result.test_command)
    active_display.i_display_message(
        f"Test command: {_format_command_for_display(test_command)}"
    )

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
    i_display_test_result(
        active_display,
        passed=test_result.passed,
        stdout=test_result.stdout,
        stderr=test_result.stderr,
        exit_code=test_result.exit_code,
    )

    #############################################
    # 10. Sync or merge the finished work back to the host repo.
    logger.info("Step 10: Sync or merge the finished work back to the host repo.")
    active_display.i_display_message(
        "Step 10: Sync or merge the finished work back to the host repo."
    )
    i_display_phase(active_display, "commit")

    should_commit = (
        orchestrator_result.completed
        and test_result.passed
        and not getattr(test_result, "blocked", False)
    )

    sync_result: SyncMergeResult | None = None

    if should_commit:
        sync_result = i_sync_out_merge(
            completed=True,
            worktree_path=worktree_result.worktree_path,
            issue_number=selected_issue.number,
            issue_title=selected_issue.title,
            commit_message_template=setup_config.commit_message_template,
        )
        logger.info(sync_result.message)
        _display_sync_result(active_display, sync_result)
    else:
        skipped_sync_message = (
            "Skipped sync or commit because RALPH did not complete "
            "or tests did not pass."
        )
        logger.info(skipped_sync_message)
        active_display.i_display_message(skipped_sync_message)

    sync_committed = bool(sync_result and sync_result.committed)
    sync_failed = bool(sync_result and sync_result.failed)
    sync_has_changes = bool(sync_result and sync_result.has_changes)
    sync_allows_cleanup = bool(
        sync_result
        and not sync_failed
        and (sync_result.merged or (allow_no_changes and not sync_has_changes))
    )
    sync_commit_hash = sync_result.commit_hash if sync_result else ""
    sync_has_uncommitted_changes = (
        True if sync_result and sync_result.has_uncommitted_changes else None
    )

    #############################################
    # 11. Close the GitHub issue only after tests pass and the fix is committed.
    logger.info(
        "Step 11: Close the GitHub issue only after tests pass and the fix is committed."
    )
    active_display.i_display_message(
        "Step 11: Close the GitHub issue only after tests pass and the fix is committed."
    )

    logger.info("Step 11a: Prepare future pull request draft metadata.")
    active_display.i_display_message(
        "Step 11a: Prepare future pull request draft metadata."
    )
    i_display_phase(active_display, "pull_request")

    pull_request_final_status = (
        RALPH_STATUS_COMPLETE
        if orchestrator_result.completed
        and test_result.passed
        and sync_committed
        and not sync_failed
        and not sync_has_uncommitted_changes
        else RALPH_STATUS_FAILED
    )

    pull_request_draft_result = i_pull_request_draft_build(
        issue_number=selected_issue.number,
        issue_title=selected_issue.title,
        head_branch=worktree_result.branch_name,
        commit_hash=sync_commit_hash,
        base_branch="main",
        tests_passed=test_result.passed,
        committed=sync_committed,
        final_status=pull_request_final_status,
        verification_command=_format_command_for_display(test_command),
    )

    i_display_pull_request_draft(active_display, pull_request_draft_result)

    logger.info("Step 11b: Prepare future issue close placeholder metadata.")
    active_display.i_display_message(
        "Step 11b: Prepare future issue close placeholder metadata."
    )
    i_display_phase(active_display, "issue_close")

    close_result = i_github_issue_close(
        issue=selected_issue,
        tests_passed=test_result.passed,
        committed=sync_committed,
        completed=orchestrator_result.completed,
        final_status=pull_request_final_status,
        commit_hash=sync_commit_hash,
        enabled=setup_config.github_issue_close_enabled,
        dry_run=setup_config.dry_run,
        verification_command=_format_command_for_display(test_command),
    )

    logger.info(
        f"Close issue result: Issue #{close_result.issue_number} closed: {close_result.closed}"
    )

    logger.info(close_result.message)
    i_display_issue_close_result(active_display, close_result)

    logger.info("Step 11c: Show GitHub automation dry-run summary.")
    active_display.i_display_message(
        "Step 11c: Show GitHub automation dry-run summary."
    )
    i_display_github_automation_dry_run_summary(
        active_display,
        selected_issue_number=selected_issue.number,
        selected_issue_title=selected_issue.title,
        final_status=pull_request_final_status,
        pull_request_draft_result=pull_request_draft_result,
        issue_close_result=close_result,
        dry_run=setup_config.dry_run,
    )

    #############################################
    # 12. Preserve the worktree if there are uncommitted changes or a failure.
    logger.info("Step 12: Preserve or clean up the worktree based on final run state.")

    active_display.i_display_message(
        "Step 12: Preserve or clean up the worktree based on final run state."
    )
    i_display_phase(active_display, "cleanup")

    cleanup_completed = (
        orchestrator_result.completed and test_result.passed and sync_allows_cleanup
    )

    cleanup_has_uncommitted_changes = sync_has_uncommitted_changes

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
    i_display_cleanup_result(
        active_display,
        removed=cleanup_result.removed,
        preserved=cleanup_result.preserved,
        worktree_path=cleanup_result.worktree_path,
        message=cleanup_result.message,
    )

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

    if sync_result is not None and sync_failed:
        message_parts.append(sync_result.message)
    elif sync_result is not None and sync_committed:
        message_parts.append(sync_result.message)

    if result_status == RALPH_STATUS_NO_CHANGES and sync_result is not None:
        message_parts.append(sync_result.message)

    message_parts.append(cleanup_result.message)
    message_result = "\n".join(message_parts)

    logger.info(f"Selected issue: #{selected_issue.number} - {selected_issue.title}")
    logger.info(f"Orchestrator result: {orchestrator_result}")
    logger.info(f"Completion detected: {completion_result.completed}")
    logger.info(f"Message: {message_result}")

    ###########################################################################
    # Final normal return
    ###########################################################################
    return RalphResult(
        selected_issue=selected_issue,
        prompt=prompt,
        orchestrator_result=orchestrator_result,
        completed=result_status == RALPH_STATUS_COMPLETE,
        message=message_result,
        status=result_status,
        project_setup_result=project_setup_result,
        test_result=test_result,
        sync_result=sync_result,
        cleanup_result=cleanup_result,
        pull_request_draft_result=pull_request_draft_result,
        issue_close_result=close_result,
    )


def _build_default_agent_provider(
    agent_provider: AgentProvider | None,
    sandbox_handle: Any,
) -> AgentProvider:
    """
    Return the caller-provided agent provider or build one through the public seam.

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
        raise ValueError("sandbox_handle is required for the default agent provider.")

    worktree_path = _worktree_path_from_sandbox_handle(sandbox_handle)

    return i_agent_provider_create(
        provider_name=setup_config.default_agent,
        sandbox_handle=sandbox_handle,
        worktree_path=worktree_path,
        codex_command=setup_config.codex_command,
        provider_env_allowlist=setup_config.provider_env_allowlist,
        provider_secret_env_allowlist=setup_config.provider_secret_env_allowlist,
    )


def _worktree_path_from_sandbox_handle(sandbox_handle: Any) -> Path:
    """
    Return the worktree path stored on a sandbox handle.

    :param sandbox_handle: Sandbox handle created by the sandbox provider.
    :type sandbox_handle: Any
    :return: Host-side worktree path for command-based providers.
    :rtype: Path
    :raises ValueError: If the sandbox handle does not expose a usable worktree path.

    :meta private:
    """

    raw_worktree_path = getattr(sandbox_handle, "worktree_path", None)

    if raw_worktree_path is None:
        raw_worktree_path = getattr(sandbox_handle, "working_directory", None)

    if raw_worktree_path is None:
        raise ValueError(
            "sandbox_handle must expose worktree_path or working_directory."
        )

    return Path(raw_worktree_path)


def _display_project_setup_failure(
    display: DisplayProtocol,
    project_setup_result: ProjectSetupResult,
) -> None:
    """
    Display command diagnostics when project setup blocks RALPH.

    :param display: Display adapter for user-facing progress output.
    :type display: DisplayProtocol
    :param project_setup_result: Project setup result to inspect.
    :type project_setup_result: ProjectSetupResult
    :return: None.
    :rtype: None

    :meta private:
    """

    if project_setup_result.install_ran and not project_setup_result.install_passed:
        i_display_command_failure(
            display,
            stdout=project_setup_result.install_stdout,
            stderr=project_setup_result.install_stderr,
            exit_code=project_setup_result.install_exit_code,
        )
        return

    if (
        project_setup_result.baseline_tests_ran
        and not project_setup_result.baseline_tests_passed
    ):
        i_display_command_failure(
            display,
            stdout=project_setup_result.baseline_test_stdout,
            stderr=project_setup_result.baseline_test_stderr,
            exit_code=project_setup_result.baseline_test_exit_code,
        )


def _display_sync_result(
    display: DisplayProtocol,
    sync_result: SyncMergeResult,
) -> None:
    """
    Display commit or sync result details.

    :param display: Display adapter for user-facing progress output.
    :type display: DisplayProtocol
    :param sync_result: Sync/commit result to display.
    :type sync_result: SyncMergeResult
    :return: None.
    :rtype: None

    :meta private:
    """

    if sync_result.failed:
        display.i_display_message(sync_result.message)
        i_display_command_failure(
            display,
            stdout=sync_result.stdout,
            stderr=sync_result.stderr,
            exit_code=sync_result.exit_code,
        )
        return

    i_display_commit_result(
        display,
        committed=sync_result.committed,
        commit_hash=sync_result.commit_hash,
        message=sync_result.message,
    )


def _format_command_for_display(command: tuple[str, ...]) -> str:
    """
    Format a command tuple for display output.

    :param command: Command tuple to format.
    :type command: tuple[str, ...]
    :return: Readable command string.
    :rtype: str

    :meta private:
    """

    if not command:
        return "<missing>"

    return " ".join(command)


def _short_display_text(
    output_text: str,
    max_length: int = 300,
) -> str:
    """
    Return a short one-line output summary for display.

    :param output_text: Text to summarize.
    :type output_text: str
    :param max_length: Maximum display length before truncation.
    :type max_length: int
    :return: Short display-safe text.
    :rtype: str

    :meta private:
    """

    cleaned_output_text = " ".join(output_text.split())

    if not cleaned_output_text:
        return "<empty>"

    if len(cleaned_output_text) <= max_length:
        return cleaned_output_text

    return f"{cleaned_output_text[: max_length - 3]}..."


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
    sync_result: SyncMergeResult | None,
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
    :param sync_result: Result from the sync or commit seam, or ``None`` when
        RALPH stopped before sync/commit or skipped sync/commit.
    :type sync_result: SyncMergeResult | None
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

    if sync_result is None:
        return RALPH_STATUS_FAILED

    if sync_result.failed:
        return RALPH_STATUS_FAILED

    if code_changes_detected:
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
        try:
            return (
                i_github_issue_from_file(
                    setup_config.github_issue_path,
                    default_label=setup_config.label,
                ),
            )
        except FileNotFoundError:
            logger.warning(
                "GitHub issue file was not found while reading %s. "
                "Falling back to GitHub issues from the API.",
                setup_config.github_issue_path,
                exc_info=True,
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


def _format_no_actionable_issue_message(
    skipped_issues: Iterable[object],
) -> str:
    message_parts = ["No open actionable issue selected."]

    for skipped_issue in skipped_issues:
        skip_message = str(getattr(skipped_issue, "message", "")).strip()

        if skip_message:
            message_parts.append(skip_message)

    return "\n".join(message_parts)


def _format_no_actionable_issue_message(
    skipped_issues: Iterable[object],
) -> str:
    message_parts = ["No open actionable issue selected."]

    for skipped_issue in skipped_issues:
        skip_message = str(getattr(skipped_issue, "message", "")).strip()

        if skip_message:
            message_parts.append(skip_message)

    return "\n".join(message_parts)
