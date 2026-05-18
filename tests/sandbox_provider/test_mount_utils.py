# tests/sandbox_provider/test_mount_utils.py
from __future__ import annotations

from pathlib import Path

from ai_coder.sandbox_provider.mount_utils import (
    PARENT_GIT_SANDBOX_DIR,
    SANDBOX_REPO_DIR,
    DockerMount,
    i_mountutils_build_docker_volume_args,
    i_mountutils_patch_git_mounts_for_windows,
    i_mountutils_to_docker_host_path,
)


def test_mountutils_converts_windows_backslashes_to_forward_slashes() -> None:
    result = i_mountutils_to_docker_host_path(
        r"C:\Users\ME\Documents\ai_coder",
        platform_name="windows",
    )

    assert result == "C:/Users/ME/Documents/ai_coder"


def test_mountutils_preserves_windows_drive_letter() -> None:
    result = i_mountutils_to_docker_host_path(
        r"C:\Users\ME\project",
        platform_name="windows",
    )

    assert result == "C:/Users/ME/project"
    assert result.startswith("C:/")
    assert not result.startswith("/c/")


def test_mountutils_preserves_spaces_in_windows_paths() -> None:
    result = i_mountutils_to_docker_host_path(
        r"C:\Users\ME\My Projects\ai_coder",
        platform_name="windows",
    )

    assert result == "C:/Users/ME/My Projects/ai_coder"


def test_mountutils_preserves_safe_special_characters_in_windows_paths() -> None:
    result = i_mountutils_to_docker_host_path(
        r"C:\Users\ME\Project & Notes\ai_coder [test]",
        platform_name="windows",
    )

    assert result == "C:/Users/ME/Project & Notes/ai_coder [test]"


def test_mountutils_strips_unnecessary_outer_quotes_before_conversion() -> None:
    result = i_mountutils_to_docker_host_path(
        r'"C:\Users\ME\My Project\ai_coder"',
        platform_name="windows",
    )

    assert result == "C:/Users/ME/My Project/ai_coder"


def test_mountutils_keeps_posix_path_unchanged_for_non_windows_platform() -> None:
    result = i_mountutils_to_docker_host_path(
        "/home/me/ai_coder",
        platform_name="linux",
    )

    assert result == "/home/me/ai_coder"


def test_mountutils_build_docker_volume_args_uses_converted_windows_host_path() -> None:
    mount = DockerMount(
        host_path=Path(r"C:\Users\ME\My Project"),
        sandbox_path=SANDBOX_REPO_DIR,
    )

    result = i_mountutils_build_docker_volume_args(
        [mount],
        platform_name="windows",
    )

    assert result == ["-v", "C:/Users/ME/My Project:/workspace"]


def test_mountutils_build_docker_volume_args_keeps_readonly_suffix_after_conversion() -> (
    None
):
    mount = DockerMount(
        host_path=Path(r"C:\Users\ME\My Project"),
        sandbox_path=SANDBOX_REPO_DIR,
        readonly=True,
    )

    result = i_mountutils_build_docker_volume_args(
        [mount],
        platform_name="windows",
    )

    assert result == ["-v", "C:/Users/ME/My Project:/workspace:ro"]


def test_mountutils_patch_git_mounts_for_windows_still_returns_git_patch_mounts(
    tmp_path,
) -> None:
    worktree_path = (
        tmp_path / "repo" / ".ai_coder" / "ai_coder_worktrees" / "ralph-issue-31"
    )
    parent_git_dir = tmp_path / "repo" / ".git"
    worktree_git_dir = parent_git_dir / "worktrees" / "ralph-issue-31"

    worktree_path.mkdir(parents=True)
    worktree_git_dir.mkdir(parents=True)

    git_file_path = worktree_path / ".git"
    git_file_path.write_text(
        f"gitdir: {str(worktree_git_dir).replace('/', '\\')}\n",
        encoding="utf-8",
    )

    git_mounts = [
        DockerMount(
            host_path=parent_git_dir,
            sandbox_path="/workspace/.git",
            readonly=False,
        ),
        DockerMount(
            host_path=git_file_path,
            sandbox_path="/workspace/.git",
            readonly=True,
        ),
    ]

    result = i_mountutils_patch_git_mounts_for_windows(
        git_mounts=git_mounts,
        worktree_host_path=worktree_path,
        platform_name="windows",
    )

    assert len(result) == 2
    assert result[0].host_path == parent_git_dir
    assert result[0].sandbox_path == PARENT_GIT_SANDBOX_DIR
    assert result[1].sandbox_path == "/workspace/.git"
    assert result[1].readonly is True
    assert result[1].host_path.read_text(encoding="utf-8") == (
        "gitdir: /.ralph-parent-git/worktrees/ralph-issue-31\n"
    )
