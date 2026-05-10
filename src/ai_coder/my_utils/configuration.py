# src/langgraph_projects/my_utils/configuration.py
# This file defines a Configuration dataclass that can be constructed from a RunnableConfig.
# It is used to extract user_id and thread_id from the RunnableConfig passed to the graph nodes.
# The Configuration class has a class method from_runnable_config that takes a RunnableConfig or a dict and returns a Configuration instance.
# how to use:
# from langgraph_projects.my_utils.configuration import Configuration
# config = Configuration.from_runnable_config(runnable_config)
# The Configuration class is frozen, meaning its instances are immutable after creation.

# src/langgraph_projects/my_utils/configuration.py

from dataclasses import dataclass  # Changed Code
from typing import Any, Literal, Mapping, NotRequired, TypedDict  # Changed Code

from langchain_core.runnables.config import RunnableConfig  # (TypedDict-like)
from pydantic import BaseModel, Field

TodoKind = Literal["personal", "work"]


class ConfigSchema(TypedDict, total=False):
    """
    Keys allowed under RunnableConfig["configurable"].

    Use this as your LangGraph config_schema so Studio knows what fields exist.
    """

    thread_id: NotRequired[str]
    user_id: NotRequired[str]
    todo_kind: NotRequired[TodoKind]


def _normalize_todo_kind(value: Any, default: TodoKind = "personal") -> TodoKind:
    """Coerce todo_kind into the allowed literals ("personal" | "work")."""
    if value in ("personal", "work"):
        return value
    return default


def _get_configurable(
    config: RunnableConfig | Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    """
    Safely extract the 'configurable' mapping from RunnableConfig or a plain dict.
    """
    if not config:
        return {}
    # RunnableConfig is TypedDict-like, but Studio may pass a plain dict.
    try:
        conf = config.get("configurable", {})  # type: ignore[union-attr]
    except Exception:
        conf = {}
    return conf or {}


@dataclass(frozen=True)
class Configuration:
    """Convenience wrapper for reading runtime config inside nodes."""

    user_id: str = ""
    thread_id: str = "1"
    todo_kind: TodoKind = "personal"

    @classmethod
    def from_runnable_config(
        cls, config: RunnableConfig | Mapping[str, Any] | None
    ) -> "Configuration":
        cfg = _get_configurable(config)

        return cls(
            user_id=str(cfg.get("user_id", "")),
            thread_id=str(cfg.get("thread_id", "1")),
            todo_kind=_normalize_todo_kind(cfg.get("todo_kind", "personal")),
        )


# ---- Compatibility export ----
# Allows: from langgraph_projects.my_utils.configuration import configuration
# so callers can do: configuration.Configuration.from_runnable_config(...)
import sys as _sys

configuration = _sys.modules[__name__]

__all__ = ["TodoKind", "ConfigSchema", "Configuration", "configuration"]
