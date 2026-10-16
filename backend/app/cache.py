from typing import Any, Optional
from cachetools import TTLCache

# In-memory TTL caches
# Macro indicators cache: 10-minute TTL (600 seconds)
_macro_cache = TTLCache(maxsize=100, ttl=600.0)

# Ticker quotes cache: 5-second TTL
_ticker_cache = TTLCache(maxsize=100, ttl=5.0)


def get_cached_macro(key: str) -> Optional[Any]:
    return _macro_cache.get(key)


def set_cached_macro(key: str, value: Any) -> None:
    _macro_cache[key] = value


def invalidate_macro_cache() -> None:
    _macro_cache.clear()


def get_cached_ticker(key: str) -> Optional[Any]:
    return _ticker_cache.get(key)


def set_cached_ticker(key: str, value: Any) -> None:
    _ticker_cache[key] = value


def invalidate_ticker_cache() -> None:
    _ticker_cache.clear()
