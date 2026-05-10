# src/ai_coder/sandbox_provider/docker_command_utils.py
"""Docker command utility helpers for sandbox providers.

This module contains small helpers for Docker command list processing.

It does not import setup_config.py.

setup_config.py remains the source of truth for which environment variable
names are secret-like. The caller passes those names into this module.
"""

from __future__ import annotations

from collections.abc import Sequence

REDACTED_VALUE = "<redacted>"


def i_dockercommand_redact(
    command: Sequence[str],
    secret_env_names: Sequence[str],
) -> list[str]:
    """Return a Docker command copy with secret env values redacted.

    Supports these Docker env argument shapes:

    .. code-block:: text

        -e NAME=value
        --env NAME=value
        --env=NAME=value

    Only names listed in ``secret_env_names`` are redacted.

    :param command: Docker command as a list-like sequence.
    :param secret_env_names: Environment variable names whose values must be hidden.
    :return: Redacted command as ``list[str]``.
    """

    secret_name_set = {
        str(secret_name).strip()
        for secret_name in secret_env_names
        if str(secret_name).strip()
    }

    redacted_command = [str(part) for part in command]
    index = 0

    while index < len(redacted_command):
        current_part = redacted_command[index]

        if current_part in {"-e", "--env"}:
            next_index = index + 1
            if next_index < len(redacted_command):
                redacted_command[next_index] = _redact_env_assignment(
                    redacted_command[next_index],
                    secret_name_set,
                )
                index += 2
                continue

        if current_part.startswith("--env="):
            env_assignment = current_part.removeprefix("--env=")
            redacted_assignment = _redact_env_assignment(
                env_assignment,
                secret_name_set,
            )
            redacted_command[index] = f"--env={redacted_assignment}"

        index += 1

    return redacted_command


def _redact_env_assignment(
    env_assignment: str,
    secret_name_set: set[str],
) -> str:
    """Redact one ``NAME=value`` assignment when the name is secret-like.

    :param env_assignment: Environment assignment text.
    :param secret_name_set: Secret environment variable names.
    :return: Original or redacted assignment.
    """

    if "=" not in env_assignment:
        return env_assignment

    env_name, _env_value = env_assignment.split("=", 1)

    if env_name not in secret_name_set:
        return env_assignment

    return f"{env_name}={REDACTED_VALUE}"
