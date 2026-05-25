"""Tests for MongoTranslator."""

from typing import Any, override

import pytest

from zspec import MongoTranslator, Specification


class InStock(Specification[object]):
    __slots__ = ()

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


class MyMongo(MongoTranslator):
    @override
    def _translate(self, spec: Specification[Any]) -> Any:
        match spec:
            case InStock():
                return {"in_stock": True}
            case MinPrice(min_price=price):
                return {"price": {"$gte": price}}
            case _:
                return super()._translate(spec)


class TestMongoTranslator:
    def test_leaf(self) -> None:
        t = MyMongo()
        assert t.translate(InStock()) == {"in_stock": True}

    def test_slot_leaf(self) -> None:
        t = MyMongo()
        assert t.translate(MinPrice(100)) == {"price": {"$gte": 100}}

    def test_and(self) -> None:
        t = MyMongo()
        result = t.translate(InStock() & MinPrice(100))
        assert result == {
            "$and": [{"in_stock": True}, {"price": {"$gte": 100}}],
        }

    def test_or(self) -> None:
        t = MyMongo()
        result = t.translate(InStock() | MinPrice(100))
        assert result == {
            "$or": [{"in_stock": True}, {"price": {"$gte": 100}}],
        }

    def test_not(self) -> None:
        t = MyMongo()
        result = t.translate(~InStock())
        assert result == {"$nor": [{"in_stock": True}]}

    def test_nested(self) -> None:
        t = MyMongo()
        spec = InStock() & (~MinPrice(50) | MinPrice(100))
        result = t.translate(spec)
        assert result == {
            "$and": [
                {"in_stock": True},
                {
                    "$or": [
                        {"$nor": [{"price": {"$gte": 50}}]},
                        {"price": {"$gte": 100}},
                    ],
                },
            ],
        }

    def test_abstract_not_instantiable(self) -> None:
        with pytest.raises(TypeError):
            MongoTranslator()  # type: ignore[abstract]
