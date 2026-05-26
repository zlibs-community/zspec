"""Tests for Specification[Product].matching."""

from dataclasses import dataclass

from zspec import Specification


@dataclass
class Product:
    price: int
    in_stock: bool


class TestFromAttrs:
    def test_eq(self) -> None:
        spec = Specification[Product].matching(in_stock=True)
        assert spec(Product(price=10, in_stock=True))
        assert not spec(Product(price=10, in_stock=False))

    def test_gte(self) -> None:
        spec = Specification[Product].matching(price__gte=100)
        assert spec(Product(price=100, in_stock=True))
        assert spec(Product(price=200, in_stock=True))
        assert not spec(Product(price=50, in_stock=True))

    def test_gt(self) -> None:
        spec = Specification[Product].matching(price__gt=100)
        assert spec(Product(price=101, in_stock=True))
        assert not spec(Product(price=100, in_stock=True))

    def test_lte(self) -> None:
        spec = Specification[Product].matching(price__lte=100)
        assert spec(Product(price=100, in_stock=True))
        assert not spec(Product(price=101, in_stock=True))

    def test_lt(self) -> None:
        spec = Specification[Product].matching(price__lt=100)
        assert spec(Product(price=99, in_stock=True))
        assert not spec(Product(price=100, in_stock=True))

    def test_ne(self) -> None:
        spec = Specification[Product].matching(price__ne=100)
        assert spec(Product(price=50, in_stock=True))
        assert not spec(Product(price=100, in_stock=True))

    def test_combined(self) -> None:
        spec = Specification[Product].matching(price__gte=100, in_stock=True)
        assert spec(Product(price=100, in_stock=True))
        assert not spec(Product(price=100, in_stock=False))
        assert not spec(Product(price=50, in_stock=True))

    def test_single_field_returns_field_spec(self) -> None:
        spec = Specification[Product].matching(price__gte=100)
        assert type(spec).__name__ == "_FieldSpec"

    def test_empty_returns_true(self) -> None:
        spec = Specification[Product].matching()
        assert spec is Specification.true()
        assert spec(Product(price=0, in_stock=False))

    def test_str(self) -> None:
        spec = Specification[Product].matching(price__gte=100)
        assert str(spec) == "price >= 100"

    def test_str_multiple(self) -> None:
        spec = Specification[Product].matching(price__gte=100, in_stock=True)
        assert str(spec) == "(price >= 100 AND in_stock == True)"

    def test_composable_with_operators(self) -> None:
        cheap = Specification[Product].matching(price__gte=100)
        stocked = Specification[Product].matching(in_stock=True)
        spec = cheap & stocked
        assert spec(Product(price=100, in_stock=True))
        assert not spec(Product(price=50, in_stock=True))
