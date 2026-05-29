"""Tests for RediSearchTranslator."""

from typing import Any, override

from zspec import Specification
from zspec.contrib.redis import RediSearchTranslator


class InStock(Specification[object]):
    @override
    def is_satisfied_by(self, candidate: object) -> bool:
        return True


class MinPrice(Specification[object]):
    __slots__ = ("min_price",)

    def __init__(self, min_price: int) -> None:
        self.min_price = min_price

    @override
    def is_satisfied_by(self, candidate: object) -> bool:
        return True


class Tag(Specification[object]):
    __slots__ = ("value",)

    def __init__(self, value: str) -> None:
        self.value = value

    @override
    def is_satisfied_by(self, candidate: object) -> bool:
        return True


class ProductTranslator(RediSearchTranslator):
    @override
    def _translate(self, spec: Specification[Any]) -> str:
        match spec:
            case InStock():
                return "@in_stock:{true}"
            case MinPrice(min_price=price):
                return f"@price:[{price} +inf]"
            case Tag(value=val):
                return f"@tag:{{{val}}}"
            case _:
                return super()._translate(spec)


class TestRediSearch:
    def translator(self) -> ProductTranslator:
        return ProductTranslator()

    def test_leaf_in_stock(self) -> None:
        t = self.translator()
        assert t.translate(InStock()) == "@in_stock:{true}"

    def test_leaf_min_price(self) -> None:
        t = self.translator()
        assert t.translate(MinPrice(100)) == "@price:[100 +inf]"

    def test_and(self) -> None:
        t = self.translator()
        result = t.translate(InStock() & MinPrice(100))
        assert result == "(@in_stock:{true} @price:[100 +inf])"

    def test_or(self) -> None:
        t = self.translator()
        result = t.translate(InStock() | MinPrice(100))
        assert result == "(@in_stock:{true} | @price:[100 +inf])"

    def test_not(self) -> None:
        t = self.translator()
        result = t.translate(~InStock())
        assert result == "-(@in_stock:{true})"

    def test_xor(self) -> None:
        t = self.translator()
        result = t.translate(InStock() ^ MinPrice(100))
        assert "(" in result
        assert "-(" in result

    def test_nested(self) -> None:
        t = self.translator()
        result = t.translate(InStock() & (MinPrice(10) | ~Tag("foo")))
        assert "@in_stock:{true}" in result
        assert "@price:[10 +inf]" in result
        assert "-(@tag:{foo})" in result
