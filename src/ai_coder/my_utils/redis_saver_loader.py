# src/asset_processing_service/my_utils/redis_saver_loader.py

from __future__ import annotations

import socket
from typing import Optional, Tuple

from langgraph.checkpoint.redis import RedisSaver
from redis.exceptions import ConnectionError, TimeoutError


def _is_dns_resolution_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return (
        ("getaddrinfo failed" in msg)
        or ("name or service not known" in msg)
        or ("failed to resolve" in msg)
    )


def open_redis_saver_with_fallback(
    *,
    redis_url: str,
    redis_url_fallback: Optional[str] = None,
) -> Tuple[object, RedisSaver]:
    """
    Open RedisSaver using redis_url; if hostname/DNS resolution fails, retry redis_url_fallback.

    Returns: (saver_cm, saver)
      - saver_cm: the context manager returned by RedisSaver.from_conn_string(...)
      - saver: the entered RedisSaver
    """
    try:
        saver_cm = RedisSaver.from_conn_string(redis_url)
        saver = saver_cm.__enter__()
        saver.setup()
        return saver_cm, saver

    except (ConnectionError, TimeoutError, OSError, socket.gaierror) as e:
        if redis_url_fallback and _is_dns_resolution_error(e):
            saver_cm = RedisSaver.from_conn_string(redis_url_fallback)
            saver = saver_cm.__enter__()
            saver.setup()
            return saver_cm, saver
        raise
