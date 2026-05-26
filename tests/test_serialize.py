"""Tests for to_dict / from_dict serialization."""

from collections.abc import Mapping
from typing import Any, ClassVar, override

from zspec import (
    Specification,
    from_dict,
    registered,
    to_dict,
)


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


class TestToDict:
    def test_leaf(self) -> None:
        spec = InStock()
        data = to_dict(spec)
        assert data == {"type": "InStock"}

    def test_leaf_with_slots(self) -> None:
        spec = MinPrice(100)
        data = to_dict(spec)
        assert data == {"type": "MinPrice", "threshold": 100}

    def test_and(self) -> None:
        spec = InStock() & MinPrice(100)
        data = to_dict(spec)
        assert data["type"] == "AndSpecification"

    def test_or(self) -> None:
        spec = InStock() | MinPrice(100)
        data = to_dict(spec)
        assert data["type"] == "OrSpecification"

    def test_not(self) -> None:
        spec = ~InStock()
        data = to_dict(spec)
        assert data["type"] == "NotSpecification"

    def test_xor(self) -> None:
        spec = InStock() ^ MinPrice(100)
        data = to_dict(spec)
        assert data["type"] == "XorSpecification"

    def test_true(self) -> None:
        assert to_dict(Specification.true()) == {"type": "TRUE"}

    def test_false(self) -> None:
        assert to_dict(Specification.false()) == {"type": "FALSE"}

    def test_field_spec(self) -> None:
        spec = Specification[object].matching(price__gte=100)
        data = to_dict(spec)
        expected = {
            "type": "FieldSpec",
            "field": "price",
            "op": "gte",
            "value": 100,
        }
        assert data == expected


class TestFromDict:
    _REGISTRY: ClassVar[Mapping[str, type[Specification[Any]]]] = {
        "InStock": InStock,
        "MinPrice": MinPrice,
    }

    def test_leaf(self) -> None:
        spec = from_dict({"type": "InStock"}, self._REGISTRY)
        assert spec == InStock()

    def test_leaf_with_slots(self) -> None:
        spec = from_dict(
            {"type": "MinPrice", "threshold": 100}, self._REGISTRY,
        )
        assert spec == MinPrice(100)

    def test_and(self) -> None:
        data: dict[str, object] = {
            "type": "AndSpecification",
            "left": {"type": "InStock"},
            "right": {"type": "MinPrice", "threshold": 100},
        }
        spec = from_dict(data, self._REGISTRY)
        assert spec == InStock() & MinPrice(100)

    def test_or(self) -> None:
        data: dict[str, object] = {
            "type": "OrSpecification",
            "left": {"type": "InStock"},
            "right": {"type": "MinPrice", "threshold": 100},
        }
        spec = from_dict(data, self._REGISTRY)
        assert spec == InStock() | MinPrice(100)

    def test_not(self) -> None:
        data: dict[str, object] = {
            "type": "NotSpecification",
            "spec": {"type": "InStock"},
        }
        spec = from_dict(data, self._REGISTRY)
        assert spec == ~InStock()

    def test_xor(self) -> None:
        data: dict[str, object] = {
            "type": "XorSpecification",
            "left": {"type": "InStock"},
            "right": {"type": "MinPrice", "threshold": 100},
        }
        spec = from_dict(data, self._REGISTRY)
        assert spec == InStock() ^ MinPrice(100)

    def test_true(self) -> None:
        spec = from_dict({"type": "TRUE"}, self._REGISTRY)
        assert spec is Specification.true()

    def test_false(self) -> None:
        spec = from_dict({"type": "FALSE"}, self._REGISTRY)
        assert spec is Specification.false()

    def test_field_spec(self) -> None:
        data: dict[str, object] = {
            "type": "FieldSpec",
            "field": "price",
            "op": "gte",
            "value": 100,
        }
        spec = from_dict(data, self._REGISTRY)
        assert spec == Specification[object].matching(price__gte=100)


class TestRoundtrip:
    _REGISTRY: ClassVar[Mapping[str, type[Specification[Any]]]] = {
        "InStock": InStock,
        "MinPrice": MinPrice,
    }

    def test_leaf(self) -> None:
        original = InStock()
        assert from_dict(to_dict(original), self._REGISTRY) == original

    def test_composite(self) -> None:
        original = InStock() & (~MinPrice(50) | MinPrice(100))
        result = from_dict(to_dict(original), self._REGISTRY)
        assert result == original

    def test_xor(self) -> None:
        original = InStock() ^ MinPrice(100)
        assert from_dict(to_dict(original), self._REGISTRY) == original

    def test_field_spec(self) -> None:
        original = Specification[object].matching(
            price__gte=100, in_stock=True,
        )
        result = from_dict(to_dict(original))
        assert result == original


@registered
class _Tagged(Specification[object]):
    __slots__ = ("label",)

    def __init__(self, label: str) -> None:
        self.label = label

    @override
    def is_satisfied_by(self, candidate: object) -> bool:
        return True


class TestRegistered:
    def test_auto_discovered(self) -> None:
        spec = _Tagged("greeting")
        restored = from_dict(to_dict(spec))
        assert restored == spec

    def test_manual_registry_overrides_auto(self) -> None:
        class Other(Specification[object]):
            __slots__ = ("label",)

            def __init__(self, label: str) -> None:
                self.label = label

            @override
            def is_satisfied_by(self, candidate: object) -> bool:
                return True

        spec = _Tagged("original")
        data = to_dict(spec)
        restored = from_dict(data, {"_Tagged": Other})
        assert restored == Other("original")
