# src/ai_coder/my_utils/env_loader.py
import threading

from dotenv import load_dotenv

_ENV_LOADED = False
_ENV_LOCK = threading.Lock()


def load_dotenv_once(*, override: bool = False) -> bool:
    """Load .env exactly once per process. Returns True if this call performed loading."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return False
    with _ENV_LOCK:
        if _ENV_LOADED:
            return False
        load_dotenv(override=override)
        _ENV_LOADED = True
        return True
