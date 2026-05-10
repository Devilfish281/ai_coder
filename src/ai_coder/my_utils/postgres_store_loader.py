# src/asset_processing_service/my_utils/postgres_store_loader.py

from __future__ import annotations

import socket
from typing import Optional, Tuple

import psycopg
from langgraph.store.postgres import PostgresStore


def _is_dns_resolution_error(exc: BaseException) -> bool:
    # psycopg wraps lower-level socket errors; message match is the most reliable here.
    msg = str(exc).lower()
    return ("getaddrinfo failed" in msg) or ("failed to resolve host" in msg)


def open_postgres_store_with_fallback(
    *,
    db_url: str,
    db_url_fallback: Optional[str] = None,
) -> Tuple[object, PostgresStore]:
    """
    Open PostgresStore using db_url; if hostname resolution fails, retry db_url_fallback.

    Returns: (store_cm, store)
      - store_cm: the context manager returned by PostgresStore.from_conn_string(...)
      - store: the entered PostgresStore
    """
    try:
        store_cm = PostgresStore.from_conn_string(db_url)
        store = store_cm.__enter__()
        return store_cm, store

    except (psycopg.OperationalError, OSError, socket.gaierror) as e:
        if db_url_fallback and _is_dns_resolution_error(e):
            # Retry using fallback
            store_cm = PostgresStore.from_conn_string(db_url_fallback)
            store = store_cm.__enter__()
            return store_cm, store

        raise
