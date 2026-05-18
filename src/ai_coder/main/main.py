# src/ai_coder/main/main.py
from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


from ai_coder.display import ConsoleDisplay, i_display_redact_text
from ai_coder.github_issues import (
    GitHubIssue,
    ProvidedIssueData,
    i_github_issue_from_provided,
)


from ai_coder.ralph import i_ralph_run

from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()

RELEASE_1_AGENT_CHOICES = ("mock",)


@dataclass(frozen=True)
class CliConfigOverrides:
    issue_number: int
    issue_title: str
    issue_body: str
    label: str
    max_iterations: int
    prompt_path: Path
    github_issue_path: Path
    repo_path: Path
    agent: str
    dry_run: bool
    sandbox_mode: str


def main(
    argv: Sequence[str] | None = None,
) -> int:
    use_logger_t = argv is None
    _write_info("Starting ai-coder...", use_logger=use_logger_t)

    # try:
    #     setup_config.validate_initialization()
    # except ValueError as error:
    #     _write_error(f"Configuration error: {error}", use_logger=use_logger_t)
    #     return 1

    parser = argparse.ArgumentParser(
        prog="ai-coder",
        description="Run the minimal local RALPH tracer-bullet loop.",
    )
    parser.add_argument(
        "--issue-number",
        type=int,
        default=setup_config.issue_number,
        help="GitHub issue number for the local tracer-bullet run....",
    )
    parser.add_argument(
        "--issue-title",
        default=setup_config.issue_title,
        help="GitHub issue title for the local tracer-bullet run.",
    )
    parser.add_argument(
        "--issue-body",
        default=setup_config.issue_body,
        help="GitHub issue body for the local tracer-bullet run.",
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
        "--github-issue-path",
        default=setup_config.github_issue_path,
        help="Path to the local fallback GitHub issue markdown file.",
    )
    parser.add_argument(
        "--repo-path",
        default=setup_config.repo_path,
        help="Path to the local Git repository RALPH should use.",
    )

    parser.add_argument(
        "--agent",
        default=setup_config.default_agent,
        help="Agent provider to use. Release 1 supports only 'mock'.",
    )

    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=setup_config.dry_run,
        help="Run safely without real issue-closing or destructive actions.",
    )

    parser.add_argument(
        "--sandbox",
        default=getattr(setup_config, "sandbox_mode", "local"),
        help="Set RALPH sandbox mode in setup_config.py.",
    )

    # Parse the command-line arguments
    args = parser.parse_args(argv)

    cli_overrides = _cli_overrides_from_args(args)

    cli_error = _validate_cli_overrides_before_apply(cli_overrides)
    if cli_error is not None:
        _write_error(cli_error, use_logger=use_logger_t)
        return 1

    ###########################################################################
    # Write CLI args into setup_config.py.
    #
    # Rule:
    #   CLI args are user input.
    #   setup_config.py is the program truth.
    #   After this point, main.py reads values from setup_config only.
    ###########################################################################
    _apply_cli_overrides_to_setup_config(cli_overrides)

    try:
        setup_config.validate_initialization()
    except ValueError as error:
        _write_error(f"Configuration error: {error}", use_logger=use_logger_t)
        return 1

    if setup_config.issue_number > 1000:
        _write_warning(
            "Warning: issue_number is unusually high for a local tracer-bullet run.",
            use_logger=use_logger_t,
        )

    if len(setup_config.issue_title) > 100:
        _write_warning(
            "Warning: issue_title is quite long for a local tracer-bullet run.",
            use_logger=use_logger_t,
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

    logger.info(
        "Start RALPH with issue: %s, title: %s, body length: %d, label: %s",
        issues[0].number if issues else "N/A",
        issues[0].title if issues else "N/A",
        len(issues[0].body) if issues else 0,
        issues[0].labels if issues else "N/A",
    )

    _write_info(
        "Using max_iterations: %d",
        setup_config.max_iterations,
        use_logger=use_logger_t,
    )
    _write_info(
        "Using repository path: %s",
        setup_config.repo_path,
        use_logger=use_logger_t,
    )
    _write_info(
        "Using prompt path: %s",
        setup_config.prompt_path,
        use_logger=use_logger_t,
    )

    result = i_ralph_run(
        issues,
        max_iterations=setup_config.max_iterations,
        prompt_path=setup_config.prompt_path,
        repo_path=setup_config.repo_path,
        display=ConsoleDisplay(
            secret_values=setup_config.i_setup_config_secret_values(),
        ),
    )

    _write_info("#" * 80, use_logger=use_logger_t)
    _write_info("RALPH run completed.", use_logger=use_logger_t)
    _write_info("#" * 80, use_logger=use_logger_t)
    _write_info("#" * 80, use_logger=use_logger_t)

    _write_info(
        f"RALPH selected issue #{result.selected_issue.number if result.selected_issue else 'N/A'}: {result.selected_issue.title if result.selected_issue else 'N/A'}",
        use_logger=use_logger_t,
    )

    # _write_info(f"RALPH final prompt:\n{result.prompt}", use_logger=use_logger_t)
    _write_info(
        f"RALPH final prompt length: {len(result.prompt)}",
        use_logger=use_logger_t,
    )

    _write_info(
        f"RALPH orchestrator iterations: {result.orchestrator_result.iterations if result.orchestrator_result else 'N/A'}",
        use_logger=use_logger_t,
    )

    _write_info(
        f"RALPH orchestrator final output:\n{result.orchestrator_result.final_output if result.orchestrator_result else 'N/A'}",
        use_logger=use_logger_t,
    )

    _write_info(f"RALPH completed: {result.completed}", use_logger=use_logger_t)
    _write_info(f"RALPH message: {result.message}", use_logger=use_logger_t)

    if result.selected_issue is None:
        _write_error(
            "RALPH did not select any issue to work on.", use_logger=use_logger_t
        )
        _write_error(result.message, use_logger=use_logger_t)
        return 1

    _write_info(
        f"Selected issue #{result.selected_issue.number}: {result.selected_issue.title}",
        use_logger=use_logger_t,
    )
    _write_info(result.message, use_logger=use_logger_t)

    if result.orchestrator_result is not None:
        _write_info(
            f"Iterations: {result.orchestrator_result.iterations}",
            use_logger=use_logger_t,
        )
        _write_info(result.orchestrator_result.final_output, use_logger=use_logger_t)

    return 0 if result.completed else 1


def _cli_overrides_from_args(args: argparse.Namespace) -> CliConfigOverrides:
    return CliConfigOverrides(
        issue_number=args.issue_number,
        issue_title=args.issue_title,
        issue_body=args.issue_body,
        label=args.label,
        max_iterations=args.max_iterations,
        prompt_path=Path(args.prompt_path),
        github_issue_path=Path(args.github_issue_path),
        repo_path=Path(args.repo_path),
        agent=args.agent.strip().lower(),
        dry_run=bool(args.dry_run),
        sandbox_mode=args.sandbox.strip().lower(),
    )


def _validate_cli_overrides_before_apply(
    cli_overrides: CliConfigOverrides,
) -> str | None:
    """Validate CLI overrides before mutating setup_config.py."""

    if cli_overrides.max_iterations < 1:
        return "Error: --max-iterations must be at least 1."

    if not cli_overrides.repo_path.exists():
        return f"Error: --repo-path does not exist: {cli_overrides.repo_path}"

    if not cli_overrides.prompt_path.exists():
        return f"Error: --prompt-path does not exist: {cli_overrides.prompt_path}"

    if cli_overrides.agent not in RELEASE_1_AGENT_CHOICES:
        return "Error: --agent must be 'mock' for Release 1."

    if cli_overrides.sandbox_mode not in {"local", "docker"}:
        return "Error: --sandbox must be 'local' or 'docker'."

    user_issue_was_provided = _has_user_issue_cli_overrides(cli_overrides)

    if user_issue_was_provided and cli_overrides.issue_number < 1:
        return "Error: --issue-number must be a positive integer."

    if user_issue_was_provided and not cli_overrides.issue_title.strip():
        return "Error: --issue-title cannot be empty."

    if user_issue_was_provided and not cli_overrides.issue_body.strip():
        return "Error: --issue-body cannot be empty."

    if user_issue_was_provided and not cli_overrides.label.strip():
        return "Error: --label cannot be empty."

    return None


def _apply_cli_overrides_to_setup_config(
    cli_overrides: CliConfigOverrides,
) -> None:
    """Apply validated CLI overrides into setup_config.py."""

    setup_config.issue_number = cli_overrides.issue_number
    setup_config.issue_title = cli_overrides.issue_title
    setup_config.issue_body = cli_overrides.issue_body
    setup_config.label = cli_overrides.label
    setup_config.max_iterations = cli_overrides.max_iterations
    setup_config.prompt_path = cli_overrides.prompt_path
    setup_config.github_issue_path = cli_overrides.github_issue_path
    setup_config.repo_path = cli_overrides.repo_path
    setup_config.default_agent = cli_overrides.agent
    setup_config.dry_run = cli_overrides.dry_run
    setup_config.sandbox_mode = cli_overrides.sandbox_mode


def _has_user_issue_cli_overrides(
    cli_overrides: CliConfigOverrides,
) -> bool:
    return (
        cli_overrides.issue_number > 0
        or bool(cli_overrides.issue_title.strip())
        or bool(cli_overrides.issue_body.strip())
    )


def _write_info(
    message: str,
    *message_args: object,
    use_logger: bool,
) -> None:
    formatted_message = _redact_message(
        _format_message(message, message_args),
    )

    if use_logger:
        logger.info(formatted_message)
        return

    print(formatted_message)


def _write_warning(
    message: str,
    *message_args: object,
    use_logger: bool,
) -> None:
    formatted_message = _redact_message(
        _format_message(message, message_args),
    )

    if use_logger:
        logger.warning(formatted_message)
        return

    print(formatted_message)


def _write_error(
    message: str,
    *message_args: object,
    use_logger: bool,
) -> None:
    formatted_message = _redact_message(
        _format_message(message, message_args),
    )

    if use_logger:
        logger.error(formatted_message)
        return

    print(formatted_message)


def _format_message(
    message: str,
    message_args: tuple[object, ...],
) -> str:
    if not message_args:
        return message

    return message % message_args


def _redact_message(message: str) -> str:
    return i_display_redact_text(
        message,
        setup_config.i_setup_config_secret_values(),
    )


def _build_fake_issue_from_config() -> GitHubIssue:
    provided_issue = ProvidedIssueData(
        number=setup_config.issue_number,
        title=setup_config.issue_title,
        body=setup_config.issue_body,
        labels=(setup_config.label,),
    )

    return i_github_issue_from_provided(provided_issue)
