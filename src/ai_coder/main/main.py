# src/ai_coder/main/main.py
from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from ai_coder.github_issues import GitHubIssue
from ai_coder.ralph import i_ralph_run

from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()


def main(
    argv: Sequence[str] | None = None,
) -> int:
    use_logger = argv is None
    _write_info("Starting ai-coder...", use_logger)

    try:
        setup_config.validate_initialization()
    except ValueError as error:
        _write_error(f"Configuration error: {error}", use_logger)
        return 1

    parser = argparse.ArgumentParser(
        prog="ai-coder",
        description="Run the minimal local RALPH tracer-bullet loop.",
    )
    parser.add_argument(
        "--issue-number",
        type=int,
        default=setup_config.issue_number,
        help="Fake issue number for the local tracer-bullet run.",
    )
    parser.add_argument(
        "--issue-title",
        default=setup_config.issue_title,
        help="Fake issue title for the local tracer-bullet run.",
    )
    parser.add_argument(
        "--issue-body",
        default=setup_config.issue_body,
        help="Fake issue body for the local tracer-bullet run.",
    )
    parser.add_argument(
        "--label",
        default=setup_config.label,
        help="Fake issue label used by priority selection.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=setup_config.max_iterations,
        help="Maximum orchestrator iterations.",
    )

    parser.add_argument(
        "--prompt-path",
        default=setup_config.prompt_path,
        help="Path to the RALPH prompt markdown file.",
    )

    parser.add_argument(
        "--sandbox",
        choices=["local", "docker"],
        default=getattr(setup_config, "sandbox_mode", "local"),
        help="Set RALPH sandbox mode in setup_config.py.",
    )

    # Parse the command-line arguments
    args = parser.parse_args(argv)

    cli_error = _validate_cli_args_before_apply(args)
    if cli_error is not None:
        _write_error(cli_error, use_logger)
        return 1
    ###########################################################################
    # Write CLI args into setup_config.py.
    #
    # Rule:
    #   CLI args are user input.
    #   setup_config.py is the program truth.
    #   After this point, main.py reads values from setup_config only.
    ###########################################################################
    _apply_cli_args_to_setup_config(args)

    try:
        setup_config.validate_initialization()
    except ValueError as error:
        _write_error(f"Configuration error: {error}", use_logger)
        return 1

    if setup_config.issue_number > 1000:
        _write_warning(
            "Warning: issue_number is unusually high for a local tracer-bullet run.",
            use_logger,
        )

    if len(setup_config.issue_title) > 100:
        _write_warning(
            "Warning: issue_title is quite long for a local tracer-bullet run.",
            use_logger,
        )
    ###########################################################################
    # BUILDING A FAKE ISSUE AND RUNNING RALPH LOCALLY
    #
    # RALPH means:
    #   R = Repository
    #   A = Autonomous
    #   L = Local
    #   P = Patch
    #   H = Helper
    #
    # RALPH is the local coding-agent runner for this project. In this
    # tracer-bullet version, we build one fake GitHub issue, pass it into
    # i_ralph_run(), let RALPH select the issue, and run the minimal
    # orchestrator loop.
    #
    # In the real version, this section will fetch open GitHub issues,
    # choose one actionable issue, create a safe worktree, ask an AI coding
    # agent to make a patch, run tests, commit the fix, and only then close
    # the issue.
    ###########################################################################

    ###########################################################################
    # BUILDING A FAKE ISSUE AND RUNNING RALPH LOCALLY
    # In a real implementation, this is where we would fetch issues from GitHub and run RALPH on them.
    #############################################################################
    issues = (
        [_build_fake_issue_from_config()]
        if setup_config.has_user_github_issue()
        else None
    )

    result = i_ralph_run(
        issues,
        max_iterations=setup_config.max_iterations,
        prompt_path=setup_config.prompt_path,
    )

    if result.selected_issue is None:
        _write_error(result.message, use_logger)
        return 1

    _write_info(
        f"Selected issue #{result.selected_issue.number}: {result.selected_issue.title}",
        use_logger,
    )
    _write_info(result.message, use_logger)

    if result.orchestrator_result is not None:
        _write_info(
            f"Iterations: {result.orchestrator_result.iterations}",
            use_logger,
        )
        _write_info(result.orchestrator_result.final_output, use_logger)

    return 0 if result.completed else 1


def _validate_cli_args_before_apply(
    args: argparse.Namespace,
) -> str | None:
    """Validate CLI args before mutating setup_config.py.

    CLI args are still only user input.
    setup_config.py remains the runtime source of truth after valid args are applied.
    """

    if args.max_iterations < 1:
        return "Error: --max-iterations must be at least 1."

    user_issue_was_provided = _has_user_issue_args(args)

    if user_issue_was_provided and args.issue_number < 1:
        return "Error: --issue-number must be a positive integer."

    if user_issue_was_provided and not args.issue_title.strip():
        return "Error: --issue-title cannot be empty."

    if user_issue_was_provided and not args.issue_body.strip():
        return "Error: --issue-body cannot be empty."

    if user_issue_was_provided and not args.label.strip():
        return "Error: --label cannot be empty."

    return None


def _apply_cli_args_to_setup_config(args: argparse.Namespace) -> None:
    """Apply parsed CLI args into setup_config.py.

    CLI args are input only.
    setup_config.py remains the source of truth for the program.
    """
    setup_config.issue_number = args.issue_number
    setup_config.issue_title = args.issue_title
    setup_config.issue_body = args.issue_body
    setup_config.label = args.label
    setup_config.max_iterations = args.max_iterations
    setup_config.prompt_path = Path(args.prompt_path)

    sandbox_mode = getattr(args, "sandbox", None)
    if sandbox_mode is not None and hasattr(setup_config, "sandbox_mode"):
        setup_config.sandbox_mode = sandbox_mode.strip().lower()


def _has_user_issue_args(args: argparse.Namespace) -> bool:
    return (
        args.issue_number > 0
        or bool(args.issue_title.strip())
        or bool(args.issue_body.strip())
    )


def _write_info(message: str, use_logger: bool) -> None:
    if use_logger:
        logger.info(message)
        return

    print(message)


def _write_warning(message: str, use_logger: bool) -> None:
    if use_logger:
        logger.warning(message)
        return

    print(message)


def _write_error(message: str, use_logger: bool) -> None:
    if use_logger:
        logger.error(message)
        return

    print(message)


def _build_fake_issue_from_config() -> GitHubIssue:
    return GitHubIssue(
        number=setup_config.issue_number,
        title=setup_config.issue_title,
        body=setup_config.issue_body,
        labels=(setup_config.label,),
    )
