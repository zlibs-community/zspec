"""Tests for PolarsTranslator."""

from typing import override

import pytest

pl = pytest.importorskip("polars")

from zspec import Specification
from zspec.contrib.polars import PolarsTranslator


class InStock(Specification[object]):
    __slots__ = ()

    @override
    def is_satisfied_by(self, candidate: object) -> bool:
        return True


class MinPrice(Specification[object]):
    __slots__ = ("threshold",)

    def __init__(self, threshold: int) -> None:
        self.threshold = threshold

    @override
    def is_satisfied_by(self, candidate: object) -> bool:
        return True


class MyPolars(PolarsTranslator):
    @override
    def _translate(self, spec: Specification[object]) -> pl.Expr:
        match spec:
            case InStock():
                return pl.col("in_stock")
            case MinPrice(threshold=price):
                return pl.col("price") >= price
            case _:
                return super()._translate(spec)


class TestPolarsTranslator:
    def test_leaf(self) -> None:
        t = MyPolars()
        df = pl.DataFrame({"in_stock": [True, False]})
        result = df.filter(t.translate(InStock()))
        assert len(result) == 1

    def test_and(self) -> None:
        t = MyPolars()
        df = pl.DataFrame({"in_stock": [True, False], "price": [200, 50]})
        result = df.filter(t.translate(InStock() & MinPrice(100)))
        assert len(result) == 1

    def test_or(self) -> None:
        t = MyPolars()
        df = pl.DataFrame({"in_stock": [True, False, False], "price": [200, 50, 150]})
        result = df.filter(t.translate(InStock() | MinPrice(100)))
        assert len(result) == 2

    def test_not(self) -> None:
        t = MyPolars()
        df = pl.DataFrame({"in_stock": [True, False]})
        result = df.filter(t.translate(~InStock()))
        assert len(result) == 1

    def test_xor(self) -> None:
        t = MyPolars()
        df = pl.DataFrame({"in_stock": [True, True, False], "price": [200, 50, 200]})
        result = df.filter(t.translate(InStock() ^ MinPrice(100)))
        assert len(result) == 2

    def test_nested(self) -> None:
        t = MyPolars()
        df = pl.DataFrame(
            {"in_stock": [True, True, True], "price": [200, 40, 150]},
        )
        spec = InStock() & (~MinPrice(50) | MinPrice(200))
        result = df.filter(t.translate(spec))
        assert len(result) == 2

    def test_abstract_not_instantiable(self) -> None:
        with pytest.raises(TypeError):
            PolarsTranslator()  # type: ignore[abstract]
