"""Tests for ElasticsearchTranslator."""

from typing import Any, override

from zspec import Specification
from zspec.contrib.elasticsearch import ElasticsearchTranslator


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


class ProductTranslator(ElasticsearchTranslator):
    @override
    def _translate(self, spec: Specification[Any]) -> dict[str, Any]:
        match spec:
            case InStock():
                return {"term": {"in_stock": True}}
            case MinPrice(min_price=price):
                return {"range": {"price": {"gte": price}}}
            case _:
                return super()._translate(spec)


class TestElasticsearch:
    def translator(self) -> ProductTranslator:
        return ProductTranslator()

    def test_leaf_in_stock(self) -> None:
        t = self.translator()
        assert t.translate(InStock()) == {"term": {"in_stock": True}}

    def test_leaf_min_price(self) -> None:
        t = self.translator()
        assert t.translate(MinPrice(100)) == {
            "range": {"price": {"gte": 100}},
        }

    def test_and(self) -> None:
        t = self.translator()
        result = t.translate(InStock() & MinPrice(100))
        assert result == {
            "bool": {
                "must": [
                    {"term": {"in_stock": True}},
                    {"range": {"price": {"gte": 100}}},
                ],
            },
        }

    def test_or(self) -> None:
        t = self.translator()
        result = t.translate(InStock() | MinPrice(100))
        assert result == {
            "bool": {
                "should": [
                    {"term": {"in_stock": True}},
                    {"range": {"price": {"gte": 100}}},
                ],
            },
        }

    def test_not(self) -> None:
        t = self.translator()
        result = t.translate(~InStock())
        assert result == {
            "bool": {"must_not": [{"term": {"in_stock": True}}]},
        }

    def test_xor(self) -> None:
        t = self.translator()
        result = t.translate(InStock() ^ MinPrice(100))
        left = {"term": {"in_stock": True}}
        right = {"range": {"price": {"gte": 100}}}
        assert result == {
            "bool": {
                "must": [
                    {"bool": {"should": [left, right]}},
                    {"bool": {"must_not": [{"bool": {"must": [left, right]}}]}},
                ],
            },
        }

    def test_nested(self) -> None:
        t = self.translator()
        result = t.translate(InStock() & (MinPrice(10) | ~InStock()))
        assert result["bool"]["must"][0] == {"term": {"in_stock": True}}
        assert "bool" in result["bool"]["must"][1]

    def test_unsupported_leaf_raises(self) -> None:
        class Unknown(Specification[object]):
            @override
            def is_satisfied_by(self, candidate: object) -> bool:
                return True

        t = self.translator()
        try:
            t.translate(Unknown())
        except NotImplementedError:
            pass
        else:
            msg = "Expected NotImplementedError"
            raise AssertionError(msg)
