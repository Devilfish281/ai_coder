# src/test_browser_mcp/tools/my_utils/llm_loader.py

import threading
from typing import Optional

from langchain_openai import ChatOpenAI

_LLM_INITIALIZED = False
_LLM_LOCK = threading.Lock()


def init_llm_once(
    setup_config,
    *,
    temperature: float = 0.0,
    streaming: bool = True,
) -> bool:
    """
    Initialize setup_config.llm exactly once per process.

    Returns True if THIS call performed initialization, otherwise False.
    """
    global _LLM_INITIALIZED

    # Fast path (no lock)
    if _LLM_INITIALIZED and setup_config.llm is not None:
        return False

    with _LLM_LOCK:
        # Double-check inside lock
        if _LLM_INITIALIZED and setup_config.llm is not None:
            return False

        model = getattr(setup_config, "openai_model", None)
        if not model:
            raise ValueError(
                "setup_config.openai_model is missing/empty; cannot init LLM."
            )

        setup_config.llm = ChatOpenAI(
            temperature=temperature,
            model=model,
            streaming=streaming,
        )

        _LLM_INITIALIZED = True
        return True


def get_llm_or_init(
    setup_config,
    *,
    temperature: float = 0.0,
    streaming: bool = True,
) -> ChatOpenAI:
    """
    Return setup_config.llm, initializing it once if needed.
    """
    if setup_config.llm is None or not _LLM_INITIALIZED:
        init_llm_once(setup_config, temperature=temperature, streaming=streaming)
    if setup_config.llm is None:
        raise ValueError("LLM initialization failed; setup_config.llm is still None.")
    return setup_config.llm
