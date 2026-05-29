"""Tests for Pydantic integration."""

from typing import override

import pytest

from zspec import Specification
from zspec.contrib.pydantic import validate


class Gt(Specification[int]):
    __slots__ = ("threshold",)

    def __init__(self, threshold: int) -> None:
        self.threshold = threshold

    @override
    def is_satisfied_by(self, candidate: int) -> bool:
        return candidate > self.threshold


class LongerThan(Specification[str]):
    __slots__ = ("min_len",)

    def __init__(self, min_len: int) -> None:
        self.min_len = min_len

    @override
    def is_satisfied_by(self, candidate: str) -> bool:
        return len(candidate) > self.min_len


class TestValidate:
    def test_passing_value(self) -> None:
        v = validate(Gt(5))
        assert v(10) == 10

    def test_failing_value(self) -> None:
        v = validate(Gt(5))
        with pytest.raises(ValueError, match="Does not satisfy"):
            v(3)

    def test_custom_message(self) -> None:
        v = validate(Gt(5), message="Must be > 5")
        with pytest.raises(ValueError, match="Must be > 5"):
            v(3)

    def test_composite_spec(self) -> None:
        v = validate(Gt(5) & Gt(10))
        assert v(15) == 15
        with pytest.raises(ValueError, match="Does not satisfy"):
            v(7)

    def test_negation(self) -> None:
        v = validate(~Gt(5))
        assert v(3) == 3
        with pytest.raises(ValueError, match="Does not satisfy"):
            v(10)

    def test_string_spec(self) -> None:
        v = validate(LongerThan(3))
        assert v("hello") == "hello"
        with pytest.raises(ValueError, match="Does not satisfy"):
            v("hi")
