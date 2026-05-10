from __future__ import annotations

import platform
import tempfile
from dataclasses import dataclass
from pathlib import Path

SANDBOX_REPO_DIR = "/workspace"
PARENT_GIT_SANDBOX_DIR = "/.ralph-parent-git"


@dataclass(frozen=True)
class DockerMount:
    host_path: Path
    sandbox_path: str
    readonly: bool = False


@dataclass(frozen=True)
class ParsedGitDirPath:
    parent_git_dir: str
    worktree_name: str


def i_mountutils_patch_git_mounts_for_windows(
    git_mounts: list[DockerMount],
    worktree_host_path: Path,
    sandbox_repo_dir: str = SANDBOX_REPO_DIR,
    platform_name: str | None = None,
) -> list[DockerMount]:
    """Patch Git mounts so Windows Git worktrees work inside Linux Docker."""
    active_platform = platform_name or platform.system().lower()

    if active_platform not in {"windows", "win32"}:
        return git_mounts

    git_entry_path = worktree_host_path / ".git"

    if not git_entry_path.exists():
        return git_mounts

    if git_entry_path.is_dir():
        return git_mounts

    try:
        git_entry_text = git_entry_path.read_text(encoding="utf-8").strip()
    except OSError:
        return git_mounts

    if not git_entry_text.startswith("gitdir:"):
        return git_mounts

    gitdir_path = git_entry_text.removeprefix("gitdir:").strip()
    parsed_gitdir = _parse_gitdir_path(gitdir_path)

    corrected_git_file_path = _create_corrected_git_file(parsed_gitdir.worktree_name)

    normalized_parent_git_dir = _normalize_path_text(parsed_gitdir.parent_git_dir)
    normalized_git_file_path = _normalize_path_text(str(git_entry_path))

    corrected_mounts: list[DockerMount] = []
    replaced_git_file = False

    for mount in git_mounts:
        normalized_host_path = _normalize_path_text(str(mount.host_path))

        if normalized_host_path == normalized_parent_git_dir:
            corrected_mounts.append(
                DockerMount(
                    host_path=mount.host_path,
                    sandbox_path=PARENT_GIT_SANDBOX_DIR,
                    readonly=mount.readonly,
                )
            )
            continue

        if normalized_host_path == normalized_git_file_path:
            corrected_mounts.append(
                DockerMount(
                    host_path=corrected_git_file_path,
                    sandbox_path=f"{sandbox_repo_dir}/.git",
                    readonly=True,
                )
            )
            replaced_git_file = True
            continue

        corrected_mounts.append(mount)

    if not replaced_git_file:
        corrected_mounts.append(
            DockerMount(
                host_path=corrected_git_file_path,
                sandbox_path=f"{sandbox_repo_dir}/.git",
                readonly=True,
            )
        )

    return corrected_mounts


def i_mountutils_build_docker_volume_args(
    mounts: list[DockerMount],
) -> list[str]:
    """Build docker -v arguments from DockerMount values."""
    volume_args: list[str] = []

    for mount in mounts:
        mount_text = f"{mount.host_path}:{mount.sandbox_path}"
        if mount.readonly:
            mount_text = f"{mount_text}:ro"

        volume_args.extend(["-v", mount_text])

    return volume_args


def _parse_gitdir_path(gitdir_path: str) -> ParsedGitDirPath:
    normalized_path = _normalize_path_text(gitdir_path).rstrip("/")
    path_parts = normalized_path.split("/")

    if len(path_parts) < 3 or path_parts[-2] != "worktrees":
        return ParsedGitDirPath(
            parent_git_dir="/".join(path_parts[:-1]),
            worktree_name=path_parts[-1],
        )

    worktree_name = path_parts[-1]
    parent_git_dir = "/".join(path_parts[:-2])

    return ParsedGitDirPath(
        parent_git_dir=parent_git_dir,
        worktree_name=worktree_name,
    )


def _create_corrected_git_file(worktree_name: str) -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="ralph-git-"))
    corrected_git_file_path = temp_dir / "git-override"
    corrected_git_file_path.write_text(
        f"gitdir: {PARENT_GIT_SANDBOX_DIR}/worktrees/{worktree_name}\n",
        encoding="utf-8",
    )
    return corrected_git_file_path


def _normalize_path_text(path_text: str) -> str:
    return path_text.replace("\\", "/")
