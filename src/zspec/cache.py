"""Memoizing specification — caches ``is_satisfied_by`` results with TTL."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any, cast, override

from zspec.specification import Specification


def _cache_key(candidate: object) -> int:
    """Return a cache key for *candidate*."""
    return id(candidate)


class CachingSpecification[T](Specification[T]):
    """Wraps a specification and caches ``is_satisfied_by`` results.

    Usage::

        spec = CachingSpecification.wrap(HeavySpec(), ttl=30.0, maxsize=256)
        spec(product)  # computes on first call, cached for 30 seconds
    """

    __slots__ = ("_cache", "_lock", "_maxsize", "_spec", "_ttl")

    def __init__(
        self,
        spec: Specification[T],
        *,
        ttl: float = 60.0,
        maxsize: int = 1024,
    ) -> None:
        """Initialize with *spec*, *ttl* in seconds, and *maxsize*."""
        self._spec: Specification[T] = spec
        self._ttl: float = ttl
        self._maxsize: int = maxsize
        self._cache: OrderedDict[int, tuple[float, bool]] = OrderedDict()
        self._lock: threading.Lock = threading.Lock()

    @classmethod
    def wrap(
        cls,
        spec: Specification[T],
        *,
        ttl: float = 60.0,
        maxsize: int = 1024,
    ) -> CachingSpecification[T]:
        """Wrap *spec* with a TTL cache.

        Args:
            spec: The specification to cache.
            ttl: Time-to-live in seconds (default 60).
            maxsize: Maximum number of cached entries (default 1024).

        """
        return cls(spec, ttl=ttl, maxsize=maxsize)

    @override
    def is_satisfied_by(self, candidate: T) -> bool:
        """Check *candidate*, returning a cached result if still fresh."""
        key = _cache_key(candidate)
        now = time.monotonic()
        with self._lock:
            if key in self._cache:
                timestamp, result = self._cache[key]
                if now - timestamp < self._ttl:
                    self._cache.move_to_end(key)
                    return result
            result = self._spec.is_satisfied_by(candidate)
            self._cache[key] = (now, result)
            self._cache.move_to_end(key)
            if len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)
            return result

    @override
    def __repr__(self) -> str:
        return (
            f"CachingSpecification(spec={self._spec!r}, "
            f"ttl={self._ttl!r}, maxsize={self._maxsize!r})"
        )

    @override
    def __str__(self) -> str:
        return f"Caching({self._spec})"

    @override
    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        o = cast(CachingSpecification[Any], other)
        return self._spec == o._spec and self._ttl == o._ttl

    @override
    def __hash__(self) -> int:
        return hash((type(self), self._spec, self._ttl))

    def clear(self) -> None:
        """Clear all cached results."""
        with self._lock:
            self._cache.clear()

    @property
    def size(self) -> int:
        """Number of cached entries."""
        with self._lock:
            return len(self._cache)
