"""Tests for CachingSpecification."""

import concurrent.futures
import time
from typing import override

from zspec import CachingSpecification, Specification


class CounterSpec(Specification[object]):
    """Spec that counts how many times is_satisfied_by was called."""

    __slots__ = ("_count",)

    def __init__(self) -> None:
        self._count = 0

    @property
    def call_count(self) -> int:
        return self._count

    @override
    def is_satisfied_by(self, candidate: object) -> bool:
        self._count += 1
        return True


class KeySpec(Specification[str]):
    """Spec that records which keys were evaluated."""

    __slots__ = ("_keys",)

    def __init__(self) -> None:
        self._keys: list[str] = []

    @property
    def eval_keys(self) -> list[str]:
        return self._keys

    @override
    def is_satisfied_by(self, candidate: str) -> bool:
        self._keys.append(candidate)
        return len(candidate) > 3


class GreaterThan(Specification[int]):
    __slots__ = ("threshold",)

    def __init__(self, threshold: int) -> None:
        self.threshold = threshold

    @override
    def is_satisfied_by(self, candidate: int) -> bool:
        return candidate > self.threshold

    @override
    def __str__(self) -> str:
        return f"> {self.threshold}"


class TestCachingSpecification:
    def test_caches_result(self) -> None:
        inner = CounterSpec()
        cached = CachingSpecification.wrap(inner)
        assert cached(None)
        assert cached(None)
        assert cached(None)
        assert inner.call_count == 1

    def test_different_candidate_not_cached(self) -> None:
        inner = KeySpec()
        cached = CachingSpecification.wrap(inner)
        cached("hello")
        cached("world")
        assert inner.eval_keys == ["hello", "world"]

    def test_ttl_expires(self) -> None:
        inner = CounterSpec()
        cached = CachingSpecification.wrap(inner, ttl=0.01)
        assert cached(None)
        time.sleep(0.02)
        assert cached(None)
        assert inner.call_count == 2

    def test_ttl_not_expired(self) -> None:
        inner = CounterSpec()
        cached = CachingSpecification.wrap(inner, ttl=60.0)
        assert cached(None)
        assert cached(None)
        assert inner.call_count == 1

    def test_clear_cache(self) -> None:
        inner = CounterSpec()
        cached = CachingSpecification.wrap(inner)
        assert cached(None)
        assert cached(None)
        cached.clear()
        assert cached(None)
        assert inner.call_count == 2

    def test_size(self) -> None:
        inner = KeySpec()
        cached = CachingSpecification.wrap(inner)
        assert cached.size == 0
        cached("hello")
        assert cached.size == 1
        cached("hello")
        assert cached.size == 1
        cached("world")
        assert cached.size == 2

    def test_maxsize_eviction(self) -> None:
        inner = KeySpec()
        cached = CachingSpecification.wrap(inner, maxsize=2)
        cached("aaaa")
        cached("bbbb")
        cached("cccc")
        assert cached.size == 2
        eval_keys = inner.eval_keys
        assert "aaaa" in eval_keys
        assert "bbbb" in eval_keys
        assert "cccc" in eval_keys

    def test_maxsize_re_evaluates_evicted(self) -> None:
        inner = KeySpec()
        cached = CachingSpecification.wrap(inner, maxsize=2)
        cached("aaaa")
        cached("bbbb")
        cached("cccc")
        cached("aaaa")
        assert inner.eval_keys.count("aaaa") == 2


class TestCachingComposition:
    def test_cached_and_composes(self) -> None:
        inner = CounterSpec()
        cached = CachingSpecification.wrap(inner)
        spec = cached & cached
        assert spec(None)
        assert inner.call_count == 1

    def test_cached_or_composes(self) -> None:
        inner = CounterSpec()
        cached = CachingSpecification.wrap(inner)
        spec = cached | cached
        assert spec(None)
        assert inner.call_count == 1

    def test_cached_with_other_spec(self) -> None:
        base = GreaterThan(0)
        cached = CachingSpecification.wrap(base)
        spec = cached & GreaterThan(5)
        assert spec(7)
        assert spec(7)
        assert spec(3) is False

    def test_filter_uses_cache(self) -> None:
        inner = CounterSpec()
        cached = CachingSpecification.wrap(inner)
        items = [1, 1, 2, 2]
        result = list(cached.filter(items))
        assert result == [1, 1, 2, 2]
        assert inner.call_count == 2


class TestCachingReprAndStr:
    def test_repr(self) -> None:
        inner = GreaterThan(10)
        cached = CachingSpecification.wrap(inner, ttl=30.0, maxsize=256)
        r = repr(cached)
        assert "GreaterThan(threshold=10)" in r
        assert "ttl=30.0" in r
        assert "maxsize=256" in r

    def test_str(self) -> None:
        inner = GreaterThan(10)
        cached = CachingSpecification.wrap(inner)
        assert str(cached) == "Caching(> 10)"


class TestCachingEquality:
    def test_same_spec_same_ttl_equal(self) -> None:
        a = CachingSpecification.wrap(GreaterThan(10), ttl=30)
        b = CachingSpecification.wrap(GreaterThan(10), ttl=30)
        assert a == b

    def test_different_ttl_not_equal(self) -> None:
        a = CachingSpecification.wrap(GreaterThan(10), ttl=30)
        b = CachingSpecification.wrap(GreaterThan(10), ttl=60)
        assert a != b

    def test_different_spec_not_equal(self) -> None:
        a = CachingSpecification.wrap(GreaterThan(10))
        b = CachingSpecification.wrap(GreaterThan(20))
        assert a != b

    def test_hash_equal_for_equal_caches(self) -> None:
        a = CachingSpecification.wrap(GreaterThan(10), ttl=30)
        b = CachingSpecification.wrap(GreaterThan(10), ttl=30)
        assert hash(a) == hash(b)

    def test_usable_in_set(self) -> None:
        specs = {
            CachingSpecification.wrap(GreaterThan(10)),
            CachingSpecification.wrap(GreaterThan(10)),
            CachingSpecification.wrap(GreaterThan(20)),
        }
        assert len(specs) == 2


class TestCachingThreadSafety:
    def test_concurrent_access(self) -> None:
        inner = CounterSpec()
        cached = CachingSpecification.wrap(inner)

        def check(n: int) -> bool:
            return cached(n)

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            results = list(ex.map(check, [42] * 100))
        assert all(results)
        assert inner.call_count == 1
