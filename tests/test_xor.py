"""Tests for XOR specification."""


from typing import override

from zspec import Specification, XorSpecification


class Always(Specification[object]):
    __slots__ = ()

    @override
    def is_satisfied_by(self, candidate: object) -> bool:
        return True

    @override
    def __str__(self) -> str:
        return "Always"


class Never(Specification[object]):
    __slots__ = ()

    @override
    def is_satisfied_by(self, candidate: object) -> bool:
        return False

    @override
    def __str__(self) -> str:
        return "Never"


class TestXor:
    def test_both_false(self) -> None:
        spec = Never() ^ Never()
        assert not spec(None)

    def test_both_true(self) -> None:
        spec = Always() ^ Always()
        assert not spec(None)

    def test_one_true(self) -> None:
        spec = Always() ^ Never()
        assert spec(None)

    def test_other_true(self) -> None:
        spec = Never() ^ Always()
        assert spec(None)

    def test_str(self) -> None:
        spec = Always() ^ Never()
        assert str(spec) == "(Always XOR Never)"

    def test_repr(self) -> None:
        spec = Always() ^ Never()
        assert repr(spec) == "XorSpecification(left=Always(), right=Never())"

    def test_type_matches(self) -> None:
        spec = Always() ^ Never()
        assert isinstance(spec, XorSpecification)
