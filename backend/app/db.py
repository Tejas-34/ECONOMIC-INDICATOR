from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional, Sequence, Tuple, Union
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from backend.app.config import settings

_pool: Optional[AsyncConnectionPool] = None


async def init_pool() -> AsyncConnectionPool:
    """Initialize the global psycopg3 async connection pool."""
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(
            conninfo=settings.DATABASE_URL,
            min_size=settings.DB_MIN_SIZE,
            max_size=settings.DB_MAX_SIZE,
            kwargs={"row_factory": dict_row},
            open=False
        )
        await _pool.open()
    return _pool


async def close_pool() -> None:
    """Close all open connections in the global pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> Optional[AsyncConnectionPool]:
    """Retrieve reference to global connection pool."""
    return _pool


@asynccontextmanager
async def get_connection() -> AsyncGenerator[psycopg.AsyncConnection, None]:
    """Lease a connection from the pool and automatically return it on context exit."""
    pool = get_pool()
    if pool is None:
        raise RuntimeError("Database connection pool is not initialized. Call init_pool() first.")
    async with pool.connection() as conn:
        yield conn


async def fetch_all(query: str, params: Union[Sequence[Any], Dict[str, Any]] = ()) -> List[Dict[str, Any]]:
    """Execute parameterized SELECT query and return all matching rows as dictionaries."""
    async with get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def fetch_one(query: str, params: Union[Sequence[Any], Dict[str, Any]] = ()) -> Optional[Dict[str, Any]]:
    """Execute parameterized SELECT query and return single matching row or None."""
    async with get_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            return dict(row) if row else None


async def execute_write(query: str, params: Union[Sequence[Any], Dict[str, Any]] = ()) -> int:
    """Execute INSERT/UPDATE/DELETE query within a transaction and return affected row count."""
    async with get_connection() as conn:
        async with conn.transaction():
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                return cur.rowcount


async def execute_many(query: str, params_seq: Sequence[Union[Sequence[Any], Dict[str, Any]]]) -> int:
    """Execute batch parameterized queries within a single transaction."""
    async with get_connection() as conn:
        async with conn.transaction():
            async with conn.cursor() as cur:
                for params in params_seq:
                    await cur.execute(query, params)
                return len(params_seq)
