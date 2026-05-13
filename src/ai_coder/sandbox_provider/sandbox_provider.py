# src/ai_coder/sandbox_provider/sandbox_provider.py
"""Sandbox provider seam for RALPH.

Module:
    ``sandbox_provider.py``

Purpose:
    This module decides where RALPH commands run.

    RALPH should not call ``subprocess.run()`` directly. RALPH should call the
    sandbox handle interface instead:

    .. code-block:: python

        sandbox.i_sandboxhandle_run(["poetry", "run", "pytest"])

    The adapter then decides whether the command runs locally on Windows or
    inside Docker.

Design vocabulary:
    Module:
        Anything with an interface and an implementation.

    Interface:
        ``SandboxHandle`` and ``i_sandbox_start()``.

    Implementation:
        ``LocalSandboxProvider`` and ``DockerSandboxProvider``.

    Seam:
        The call to ``i_sandboxhandle_run()``.

    Adapter:
        The concrete local or Docker class that satisfies the seam.

    Depth:
        This module hides subprocess and Docker details.

    Leverage:
        RALPH can move from local execution to Docker without rewriting
        ``ralph.py``.

    Locality:
        Docker-specific bugs stay in this module and ``mount_utils.py``.

Notes:
    ``setup_config.py`` is the source of truth for Docker settings.

    The first Docker implementation uses one ``docker run --rm`` container per
    command. A long-running container with ``docker exec`` can be added later
    when RALPH runs a real AI coding-agent session.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Protocol, Sequence

from ai_coder.sandbox_provider.mount_utils import (
    DockerMount,
    SANDBOX_REPO_DIR,
    i_mountutils_build_docker_volume_args,
    i_mountutils_patch_git_mounts_for_windows,
)
from ai_coder.sandbox_provider.docker_command_utils import i_dockercommand_redact


from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()


@dataclass(frozen=True)
class CommandResult:
    """Result returned after a sandbox command runs.

    :param stdout: Text written to standard output.
    :param stderr: Text written to standard error.
    :param exit_code: Process exit code. ``0`` usually means success.
    """

    stdout: str
    stderr: str
    exit_code: int

    @property
    def succeeded(self) -> bool:
        """Return ``True`` when the command exit code is ``0``.

        :return: ``True`` if the command succeeded, otherwise ``False``.
        """

        return self.exit_code == 0


@dataclass(frozen=True)
class MountConfig:
    """General mount configuration for future sandbox providers.

    This class is intentionally small. Docker-specific mount conversion is
    handled by ``DockerMount`` in ``mount_utils.py``.

    :param host_path: Path on the host machine.
    :param sandbox_path: Path inside the sandbox.
    :param readonly: Whether the sandbox should mount the path read-only.
    """

    host_path: Path
    sandbox_path: str
    readonly: bool = False


@dataclass(frozen=True)
class SandboxStartResult:
    """Result returned when starting a sandbox.

    This keeps your earlier public shape but adds ``handle`` so callers can run
    commands through the sandbox seam.

    :param working_directory: Host-side working directory.
    :param provider_name: Name of the selected provider.
    :param started: Whether the sandbox was created successfully.
    :param message: Human-readable startup message.
    :param handle: Concrete sandbox handle used to run commands.
    """

    working_directory: Path
    provider_name: str
    started: bool
    message: str
    handle: SandboxHandle | None = None


class SandboxHandle(Protocol):
    """Interface used by RALPH to run commands.

    Any concrete adapter that has these methods can act as a sandbox handle.
    """

    worktree_path: Path

    def i_sandboxhandle_run(
        self,
        command: list[str],
        cwd: Path | None = None,
    ) -> CommandResult:
        """Run a command through the sandbox.

        :param command: Command and arguments to execute.
        :param cwd: Optional working directory.
        :return: Captured command result.
        """
        # env_args = self._build_env_args()
        # secret_env_args = self._build_secret_env_args()

        # docker_command = [
        #     "docker",
        #     "run",
        #     "--rm",
        #     *env_args,
        #     *secret_env_args,
        #     *volume_args,
        #     "-w",
        #     sandbox_cwd,
        #     self.image_name,
        #     *command,
        # ]

        ...

    def i_sandboxhandle_close(self) -> None:
        """Close or clean up the sandbox handle.

        Local and one-shot Docker handles do not need much cleanup yet, but this
        method keeps the interface ready for a future long-running container.
        """

        ...


class BindMountSandboxProvider(Protocol):
    """Interface for providers that mount a host worktree into a sandbox."""

    name: str

    def i_bindmountsandbox_create(self, worktree_path: Path) -> SandboxHandle:
        """Create a bind-mount sandbox handle.

        :param worktree_path: Host-side worktree path.
        :return: Sandbox handle.
        """

        ...


class DockerImageMissingError(RuntimeError):
    """Raised when the configured Docker image does not exist locally."""


class LocalSandboxProvider:
    """Run commands directly on the host machine.

    This adapter is useful for the first tracer bullet and for tests. It uses
    the same ``i_sandboxhandle_run()`` seam as Docker, so RALPH does not need to
    know where the command really runs.

    :param working_directory: Host directory where commands should run.
    """

    name = "local"

    def __init__(self, working_directory: str | Path) -> None:
        self.worktree_path = Path(working_directory)
        self.working_directory = self.worktree_path
        logger.debug(
            "Initialized LocalSandboxProvider with working_directory=%s",
            self.working_directory,
        )

    def i_sandbox_run(self, command: Sequence[str]) -> CommandResult:
        """Backward-compatible local command runner.

        Prefer ``i_sandboxhandle_run()`` in new RALPH code.

        :param command: Command and arguments to execute.
        :return: Captured command result.
        """

        return self.i_sandboxhandle_run(list(command))

    def i_sandboxhandle_run(
        self,
        command: list[str],
        cwd: Path | None = None,
    ) -> CommandResult:
        """Run a command locally.

        :param command: Command and arguments to execute.
        :param cwd: Optional host-side working directory.
        :return: Captured command result.
        :raises ValueError: If ``command`` is empty.
        """

        _validate_command(command)

        run_cwd = cwd or self.worktree_path
        logger.debug(
            "Running local sandbox command. cwd=%s command=%s",
            run_cwd,
            command,
        )

        completed_process = subprocess.run(
            command,
            cwd=run_cwd,
            capture_output=True,
            text=True,
            check=False,
        )

        result = _command_result_from_completed_process(completed_process)
        _log_command_result("local", command, result)
        return result

    def i_sandboxhandle_close(self) -> None:
        """Close the local sandbox handle.

        Local execution does not create a background process, so there is
        nothing to stop.
        """

        return None


class DockerSandboxProvider:
    """Run commands inside Docker using a bind-mounted worktree.

    The first Docker slice uses one ``docker run --rm`` container per command.
    The worktree is mounted into the container as ``/workspace``.

    Docker settings come from ``setup_config.py`` unless explicitly passed for
    tests.

    :param worktree_path: Host-side Git worktree path.
    :param host_repo_path: Host-side repository root. If omitted, this class
        tries to infer it from Git metadata.
    :param image_name: Optional Docker image override for tests.
    :param docker_build_command: Optional build command override for tests.
    """

    name = "docker"

    def __init__(
        self,
        worktree_path: str | Path,
        host_repo_path: str | Path | None = None,
        image_name: str | None = None,
        docker_build_command: str | None = None,
    ) -> None:
        self.worktree_path = Path(worktree_path)
        self.working_directory = self.worktree_path
        self.host_repo_path = (
            Path(host_repo_path)
            if host_repo_path is not None
            else _resolve_host_repo_path(self.worktree_path)
        )

        self.image_name = image_name or setup_config.docker_image_name
        self.docker_build_command = (
            docker_build_command or setup_config.get_docker_build_command()
        )

        logger.info(
            "Initializing DockerSandboxProvider. worktree_path=%s image_name=%s",
            self.worktree_path,
            self.image_name,
        )

        # TODO: Later replace one-shot docker run with a long-running container.
        # TODO: Later add docker exec support for interactive AI coding sessions.
        self._check_docker_image_exists()

    def i_sandboxhandle_run(
        self,
        command: list[str],
        cwd: Path | None = None,
    ) -> CommandResult:
        """Run one command inside Docker.

        This uses a fresh short-lived container for every command. File changes
        still persist because the worktree is bind-mounted into Docker.

        :param command: Command and arguments to run inside Docker.
        :param cwd: Optional host-side or relative working directory.
        :return: Captured command result.
        :raises ValueError: If ``command`` is empty.
        """

        _validate_command(command)

        sandbox_cwd = self._resolve_sandbox_cwd(cwd)
        env_args = self._build_env_args()
        secret_env_args = self._build_secret_env_args()
        volume_args = self._build_volume_args()

        docker_command = [
            "docker",
            "run",
            "--rm",
            *env_args,
            *secret_env_args,
            *volume_args,
            "-w",
            sandbox_cwd,
            self.image_name,
            *command,
        ]

        redacted_docker_command = i_dockercommand_redact(
            docker_command,
            setup_config.docker_secret_env_allowlist,
        )

        logger.debug(
            "Running Docker sandbox command. docker_command=%s",
            redacted_docker_command,
        )

        # TODO: Later stream Docker output live instead of only capturing it after completion.
        completed_process = subprocess.run(
            docker_command,
            capture_output=True,
            text=True,
            check=False,
        )

        result = _command_result_from_completed_process(completed_process)
        _log_command_result("docker", command, result)
        return result

    def i_sandboxhandle_close(self) -> None:
        """Close the Docker sandbox handle.

        The current Docker adapter uses ``docker run --rm`` for each command, so
        there is no long-running container to stop yet.
        """

        return None

    def _check_docker_image_exists(self) -> None:
        """Verify the Docker image exists locally.

        :raises DockerImageMissingError: If Docker cannot inspect the image.
        """

        logger.debug(
            "Checking Docker image exists. image_name=%s",
            self.image_name,
        )

        completed_process = subprocess.run(
            ["docker", "image", "inspect", self.image_name],
            capture_output=True,
            text=True,
            check=False,
        )

        if completed_process.returncode == 0:
            logger.info(
                "Docker image exists. image_name=%s",
                self.image_name,
            )
            return

        error_text = (
            completed_process.stderr.strip() or completed_process.stdout.strip()
        )
        message = (
            f"Docker image is missing: {self.image_name}\n\n"
            "Build it with:\n\n"
            f"{self.docker_build_command}"
        )

        if error_text:
            message = f"{message}\n\nDocker said:\n{error_text}"

        logger.error(
            "Docker image missing. image_name=%s build_command=%s error=%s",
            self.image_name,
            self.docker_build_command,
            error_text,
        )

        raise DockerImageMissingError(message)

    def _build_volume_args(self) -> list[str]:
        """Build Docker ``-v`` arguments for the worktree and Git metadata.

        :return: Docker volume arguments suitable for ``subprocess.run()``.
        """

        worktree_mount = DockerMount(
            host_path=self.worktree_path,
            sandbox_path=SANDBOX_REPO_DIR,
        )

        git_mounts = _build_git_mounts(self.worktree_path, self.host_repo_path)

        patched_git_mounts = i_mountutils_patch_git_mounts_for_windows(
            git_mounts=git_mounts,
            worktree_host_path=self.worktree_path,
            sandbox_repo_dir=SANDBOX_REPO_DIR,
        )

        all_mounts = [worktree_mount, *patched_git_mounts]
        logger.debug(
            "Built Docker sandbox mounts. mounts=%s",
            all_mounts,
        )

        # TODO: Later support extra user-defined mounts from setup_config.py.
        return i_mountutils_build_docker_volume_args(all_mounts)

    def _build_env_args(self) -> list[str]:  #
        """Build safe Docker environment variable arguments.

        Only variables listed in ``setup_config.docker_env_allowlist`` are
        passed into Docker.

        Secrets are intentionally not included by default.

        :return: Docker ``-e`` arguments.
        """

        env_args: list[str] = []  #
        allowed_env_names = getattr(  #
            setup_config,  #
            "docker_env_allowlist",  #
            ("PYTHONUNBUFFERED",),  #
        )  #

        for env_name in allowed_env_names:  #
            cleaned_name = str(env_name).strip()  #
            if not cleaned_name:  #
                continue  #

            env_value = os.getenv(cleaned_name)  #

            if env_value is None and cleaned_name == "PYTHONUNBUFFERED":  #
                env_value = "1"  #

            if env_value is None:  #
                logger.debug(  #
                    "Skipping Docker env var because it is not set. env_name=%s",  #
                    cleaned_name,  #
                )  #
                continue  #

            env_args.extend(["-e", f"{cleaned_name}={env_value}"])  #

        logger.debug(  #
            "Built Docker env args. env_names=%s",  #
            [
                env_args[index + 1].split("=", 1)[0]
                for index in range(0, len(env_args), 2)
            ],  #
        )  #

        # TODO: Later support setup_config.py allowlist entries for AI agent secrets.
        # TODO: Later consider Docker secrets for sensitive values instead of env vars.
        return env_args  #

    def _resolve_sandbox_cwd(self, cwd: Path | None) -> str:
        """Convert a host-side ``cwd`` into the Docker-side path.

        :param cwd: Optional host-side or relative working directory.
        :return: Docker-side working directory.
        """

        if cwd is None:
            return SANDBOX_REPO_DIR

        cwd_path = Path(cwd)

        if not cwd_path.is_absolute():
            return str(PurePosixPath(SANDBOX_REPO_DIR) / cwd_path.as_posix())

        try:
            relative_path = cwd_path.resolve().relative_to(self.worktree_path.resolve())
        except ValueError:
            return SANDBOX_REPO_DIR

        return str(PurePosixPath(SANDBOX_REPO_DIR) / relative_path.as_posix())


def i_sandbox_start(
    working_directory: str | Path,
    provider_name: str | None = None,
) -> SandboxStartResult:
    """Start the configured sandbox.

    ``setup_config.py`` is the source of truth. The ``provider_name`` parameter
    is kept for compatibility with older code, but new code should set
    ``setup_config.sandbox_mode`` and let this function read from config.

    :param working_directory: Host-side worktree or working directory.
    :param provider_name: Legacy fallback provider name.
    :return: Sandbox startup result with a command handle.
    :raises ValueError: If the configured sandbox mode is not supported.
    """

    sandbox_mode = getattr(
        setup_config,
        "sandbox_mode",
        provider_name or "local",
    )

    sandbox_mode = str(sandbox_mode).strip().lower()

    logger.info(
        "Starting sandbox. sandbox_mode=%s working_directory=%s",
        sandbox_mode,
        working_directory,
    )

    if sandbox_mode == "local":
        resolved_working_directory = Path(working_directory)

        if not resolved_working_directory.exists():
            message = (
                "Local sandbox startup failed: "
                f"working directory does not exist: {resolved_working_directory}"
            )
            logger.error(message)

            return SandboxStartResult(
                working_directory=resolved_working_directory,
                provider_name="local",
                started=False,
                message=message,
                handle=None,
            )

        handle: SandboxHandle = LocalSandboxProvider(resolved_working_directory)

        message = "Started local sandbox provider."
        logger.info(
            "%s working_directory=%s",
            message,
            resolved_working_directory,
        )

        return SandboxStartResult(
            working_directory=resolved_working_directory,
            provider_name="local",
            started=True,
            message=message,
            handle=handle,
        )

    if sandbox_mode == "docker":
        _validate_docker_config_if_available()

        handle = DockerSandboxProvider(
            worktree_path=working_directory,
        )

        logger.info(
            "Started Docker bind-mount sandbox provider. working_directory=%s image_name=%s",
            working_directory,
            setup_config.docker_image_name,
        )
        return SandboxStartResult(
            working_directory=Path(working_directory),
            provider_name="docker",
            started=True,
            message="Started Docker bind-mount sandbox provider.",
            handle=handle,
        )

    logger.error(
        "Unsupported sandbox mode. sandbox_mode=%s",
        sandbox_mode,
    )

    raise ValueError(
        "Unsupported sandbox mode. Expected 'local' or 'docker', "
        f"got {sandbox_mode!r}."
    )


def _build_git_mounts(
    worktree_path: Path,
    host_repo_path: Path,
) -> list[DockerMount]:
    """Build Git metadata mounts for Docker.

    The worktree itself is already mounted as ``/workspace``. This helper adds
    Git metadata mounts only when a linked worktree needs access to the parent
    repository ``.git`` directory.

    :param worktree_path: Host-side worktree path.
    :param host_repo_path: Host-side repository path.
    :return: Docker mounts for Git metadata.
    """

    git_entry_path = worktree_path / ".git"

    if not git_entry_path.exists():
        logger.debug(
            "No .git entry found in worktree. worktree_path=%s",
            worktree_path,
        )
        return []

    if git_entry_path.is_dir():
        logger.debug(
            "Worktree has real .git directory; no extra Git metadata mount needed. git_entry_path=%s",
            git_entry_path,
        )
        return []

    parent_git_dir = _read_parent_git_dir_from_git_file(git_entry_path)

    if parent_git_dir is None:
        parent_git_dir = host_repo_path / ".git"
        logger.debug(
            "Could not parse parent Git dir from .git file; using host repo .git. parent_git_dir=%s",
            parent_git_dir,
        )
    else:
        logger.debug(
            "Parsed parent Git dir from worktree .git file. parent_git_dir=%s",
            parent_git_dir,
        )

    # TODO: Later add tests for worktrees created from nested repository paths.
    return [
        DockerMount(
            host_path=parent_git_dir,
            sandbox_path=str(parent_git_dir),
        )
    ]


def _read_parent_git_dir_from_git_file(git_entry_path: Path) -> Path | None:
    """Read the parent Git directory from a worktree ``.git`` file.

    A linked worktree usually has a ``.git`` file containing a line such as:

    .. code-block:: text

        gitdir: C:/path/to/repo/.git/worktrees/my-worktree

    :param git_entry_path: Path to the worktree ``.git`` file.
    :return: Parent ``.git`` directory if it can be parsed.
    """

    try:
        git_entry_text = git_entry_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None

    if not git_entry_text.startswith("gitdir:"):
        return None

    gitdir_text = git_entry_text.removeprefix("gitdir:").strip()
    normalized_gitdir_text = gitdir_text.replace("\\", "/").rstrip("/")
    path_parts = normalized_gitdir_text.split("/")

    if len(path_parts) < 3 or path_parts[-2] != "worktrees":
        return None

    parent_git_text = "/".join(path_parts[:-2])

    if len(parent_git_text) == 2 and parent_git_text.endswith(":"):
        parent_git_text = f"{parent_git_text}/"

    return Path(parent_git_text)


def _resolve_host_repo_path(worktree_path: Path) -> Path:
    """Resolve the host repository path for a worktree.

    For the first tracer bullet, this uses Git metadata when possible and falls
    back to the worktree path.

    :param worktree_path: Host-side worktree path.
    :return: Best-effort host repository path.
    """

    git_entry_path = worktree_path / ".git"

    if git_entry_path.is_dir():
        return worktree_path

    parent_git_dir = _read_parent_git_dir_from_git_file(git_entry_path)

    if parent_git_dir is None:
        return worktree_path

    if parent_git_dir.name == ".git":
        return parent_git_dir.parent

    return worktree_path


def _validate_docker_config_if_available() -> None:
    """Run Docker config validation when ``setup_config.py`` provides it.

    This function uses the module-level ``setup_config`` object because
    ``setup_config.py`` is the source of truth for the whole program.
    """

    validate_docker_configuration = getattr(
        setup_config,
        "validate_docker_configuration",
        None,
    )

    if callable(validate_docker_configuration):
        validate_docker_configuration()


def _validate_command(command: Sequence[str]) -> None:
    """Validate a command before execution.

    :param command: Command and arguments.
    :raises ValueError: If the command is empty.
    """

    if not command:
        logger.error("Sandbox command validation failed: command cannot be empty.")
        raise ValueError("command cannot be empty")


def _log_command_result(
    provider_name: str,
    command: Sequence[str],
    result: CommandResult,
) -> None:
    """Log a sandbox command result.

    :param provider_name: Sandbox provider name.
    :param command: Command and arguments that were executed.
    :param result: Captured command result.
    """

    if result.succeeded:
        logger.debug(
            "Sandbox command succeeded. provider=%s exit_code=%s command=%s",
            provider_name,
            result.exit_code,
            list(command),
        )
        return

    logger.warning(
        "Sandbox command failed. provider=%s exit_code=%s command=%s stderr=%s",
        provider_name,
        result.exit_code,
        list(command),
        result.stderr.strip(),
    )


def _command_result_from_completed_process(
    completed_process: subprocess.CompletedProcess[str],
) -> CommandResult:
    """Convert ``subprocess.CompletedProcess`` into ``CommandResult``.

    :param completed_process: Finished subprocess result.
    :return: Project command result.
    """

    return CommandResult(
        stdout=completed_process.stdout or "",
        stderr=completed_process.stderr or "",
        exit_code=completed_process.returncode,
    )


def _build_secret_env_args() -> list[str]:
    """Build Docker env args for secret-like values.

    For the local learning prototype, this may use normal Docker -e args.
    Later this function can be changed to Docker secrets or another secret
    provider without changing DockerSandboxProvider.i_sandboxhandle_run().
    """
