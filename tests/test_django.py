"""Tests for DjangoQTranslator."""


from typing import Any, override

import pytest

django = pytest.importorskip("django")
from django.conf import settings

settings.configure(
    INSTALLED_APPS=["django.contrib.contenttypes"],
    DATABASES={},
    USE_TZ=True,
)
django.setup()

Q = django.db.models.Q

from zspec import Specification
from zspec.contrib.django import DjangoQTranslator


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


class MyDjango(DjangoQTranslator):
    @override
    def _translate(self, spec: Specification[Any]) -> Any:
        match spec:
            case InStock():
                return Q(in_stock=True)
            case MinPrice(min_price=price):
                return Q(price__gte=price)
            case _:
                msg = f"Unknown spec: {type(spec).__name__}"
                raise NotImplementedError(msg)


class TestDjangoQTranslator:
    def test_leaf(self) -> None:
        t = MyDjango()
        result = t.translate(InStock())
        assert result == Q(in_stock=True)

    def test_and(self) -> None:
        t = MyDjango()
        result = t.translate(InStock() & MinPrice(100))
        expected = Q(in_stock=True) & Q(price__gte=100)
        assert result == expected

    def test_or(self) -> None:
        t = MyDjango()
        result = t.translate(InStock() | MinPrice(100))
        expected = Q(in_stock=True) | Q(price__gte=100)
        assert result == expected

    def test_not(self) -> None:
        t = MyDjango()
        result = t.translate(~InStock())
        assert result == ~Q(in_stock=True)

    def test_nested(self) -> None:
        t = MyDjango()
        spec = InStock() & (~MinPrice(50) | MinPrice(100))
        result = t.translate(spec)
        expected = Q(in_stock=True) & (~Q(price__gte=50) | Q(price__gte=100))
        assert result == expected

    def test_abstract_not_instantiable(self) -> None:
        with pytest.raises(TypeError):
            DjangoQTranslator()  # type: ignore[abstract]
