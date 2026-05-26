"""Tests for specification pattern."""

from typing import override

from zspec import Specification


class Always(Specification[object]):
    """Specification satisfied by any candidate."""

    @override
    def is_satisfied_by(self, candidate: object) -> bool:
        return True


class Never(Specification[object]):
    """Specification satisfied by no candidate."""

    @override
    def is_satisfied_by(self, candidate: object) -> bool:
        return False


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


class TestSpecification:
    def test_is_satisfied_by(self) -> None:
        assert Always().is_satisfied_by(object())
        assert not Never().is_satisfied_by(object())

    def test_call_shorthand(self) -> None:
        assert Always()(None) is True
        assert Never()(None) is False

    def test_and_both_true(self) -> None:
        spec = Always() & Always()
        assert spec.is_satisfied_by(None)

    def test_and_one_false(self) -> None:
        spec = Always() & Never()
        assert not spec.is_satisfied_by(None)

    def test_and_both_false(self) -> None:
        spec = Never() & Never()
        assert not spec.is_satisfied_by(None)

    def test_or_both_true(self) -> None:
        spec = Always() | Always()
        assert spec.is_satisfied_by(None)

    def test_or_one_false(self) -> None:
        spec = Always() | Never()
        assert spec.is_satisfied_by(None)

    def test_or_both_false(self) -> None:
        spec = Never() | Never()
        assert not spec.is_satisfied_by(None)

    def test_not_true(self) -> None:
        spec = ~Always()
        assert not spec.is_satisfied_by(None)

    def test_not_false(self) -> None:
        spec = ~Never()
        assert spec.is_satisfied_by(None)


class TestComposition:
    def test_chained_and(self) -> None:
        gt = GreaterThan(5) & GreaterThan(10)
        assert gt(15)
        assert not gt(7)

    def test_chained_or(self) -> None:
        gt = GreaterThan(5) | GreaterThan(10)
        assert gt(7)
        assert gt(15)
        assert not gt(3)

    def test_combined_and_or(self) -> None:
        spec = GreaterThan(5) & (GreaterThan(10) | GreaterThan(20))
        assert spec(15)
        assert spec(25)
        assert not spec(7)
        assert not spec(3)

    def test_double_negation(self) -> None:
        spec = Always()
        assert (~~spec)(None) is True


class TestAllOfAnyOf:
    def test_all_of_empty(self) -> None:
        assert Specification.all_of([]) is None

    def test_all_of_empty_with_default(self) -> None:
        result = Specification.all_of([], default=Specification.true())
        assert result is not None
        assert result(None) is True

    def test_all_of_all_true(self) -> None:
        spec = Specification.all_of([Always(), Always(), Always()])
        assert spec is not None
        assert spec(None) is True
    def test_all_of_one_false(self) -> None:
        spec = Specification.all_of([Always(), Never(), Always()])
        assert spec is not None
        assert spec(None) is False
    def test_any_of_empty(self) -> None:
        assert Specification.any_of([]) is None

    def test_any_of_empty_with_default(self) -> None:
        result = Specification.any_of([], default=Specification.false())
        assert result is not None
        assert result(None) is False

    def test_any_of_all_false(self) -> None:
        spec = Specification.any_of([Never(), Never()])
        assert spec is not None
        assert spec(None) is False
    def test_any_of_one_true(self) -> None:
        spec = Specification.any_of([Never(), Always(), Never()])
        assert spec is not None
        assert spec(None) is True

class TestStringRepresentation:
    def test_leaf_str(self) -> None:
        assert str(Always()) == "Always"

    def test_custom_leaf_str(self) -> None:
        assert str(GreaterThan(5)) == "> 5"

    def test_and_str(self) -> None:
        spec = Always() & Never()
        assert str(spec) == "(Always AND Never)"

    def test_or_str(self) -> None:
        spec = Always() | Never()
        assert str(spec) == "(Always OR Never)"

    def test_not_str(self) -> None:
        assert str(~Always()) == "NOT (Always)"

    def test_nested_str(self) -> None:
        spec = Always() & (~Never() | Always())
        assert str(spec) == "(Always AND (NOT (Never) OR Always))"


class TestRepr:
    def test_leaf_repr(self) -> None:
        assert repr(Always()) == "Always()"

    def test_slot_repr(self) -> None:
        assert repr(GreaterThan(5)) == "GreaterThan(threshold=5)"

    def test_and_repr(self) -> None:
        spec = Always() & Never()
        assert repr(spec) == "AndSpecification(left=Always(), right=Never())"

    def test_or_repr(self) -> None:
        spec = Always() | Never()
        assert repr(spec) == "OrSpecification(left=Always(), right=Never())"

    def test_not_repr(self) -> None:
        assert repr(~Always()) == "NotSpecification(spec=Always())"


class TestEquality:
    def test_same_type_same_values_equal(self) -> None:
        assert GreaterThan(10) == GreaterThan(10)

    def test_same_type_different_values_not_equal(self) -> None:
        assert GreaterThan(10) != GreaterThan(20)

    def test_different_types_not_equal(self) -> None:
        assert Always() != Never()

    def test_and_equal(self) -> None:
        a = Always() & Never()
        b = Always() & Never()
        assert a == b

    def test_and_different(self) -> None:
        a = Always() & Never()
        b = Never() & Always()
        assert a != b

    def test_or_equal(self) -> None:
        a = Always() | Never()
        b = Always() | Never()
        assert a == b

    def test_not_equal(self) -> None:
        assert ~Always() == ~Always()

    def test_not_different(self) -> None:
        assert ~Always() != ~Never()

    def test_xor_equal(self) -> None:
        a = Always() ^ Never()
        b = Always() ^ Never()
        assert a == b

    def test_cross_type_not_equal(self) -> None:
        assert (Always() & Never()) != (Always() | Never())

    def test_nested_composite_equal(self) -> None:
        a = Always() & (~Never() | Always())
        b = Always() & (~Never() | Always())
        assert a == b

    def test_hash_equal_for_equal_specs(self) -> None:
        a = Always() & (~Never() | Always())
        b = Always() & (~Never() | Always())
        assert hash(a) == hash(b)

    def test_hash_different_for_different_specs(self) -> None:
        assert hash(Always() & Never()) != hash(Always() | Never())

    def test_usable_in_set(self) -> None:
        specs = {Always(), Always(), Never()}
        assert len(specs) == 2

    def test_usable_as_dict_key(self) -> None:
        d = {Always(): "yes", Never(): "no"}
        assert d[Always()] == "yes"


class TestSimplify:
    def test_and_with_false_is_false(self) -> None:
        result = Always() & Specification.false()
        assert result is Specification.false()

    def test_false_and_spec_is_false(self) -> None:
        result = Specification.false() & Always()
        assert result is Specification.false()

    def test_and_with_true_is_spec(self) -> None:
        result = Always() & Specification.true()
        assert result == Always()

    def test_true_and_spec_is_spec(self) -> None:
        result = Specification.true() & Always()
        assert result == Always()

    def test_or_with_true_is_true(self) -> None:
        result = Always() | Specification.true()
        assert result is Specification.true()

    def test_true_or_spec_is_true(self) -> None:
        result = Specification.true() | Never()
        assert result is Specification.true()

    def test_or_with_false_is_spec(self) -> None:
        result = Always() | Specification.false()
        assert result == Always()

    def test_false_or_spec_is_spec(self) -> None:
        result = Specification.false() | Always()
        assert result == Always()

    def test_xor_with_true_is_not(self) -> None:
        result = Always() ^ Specification.true()
        assert result == ~Always()

    def test_true_xor_spec_is_not(self) -> None:
        result = Specification.true() ^ Always()
        assert result == ~Always()

    def test_xor_with_false_is_spec(self) -> None:
        result = Always() ^ Specification.false()
        assert result == Always()

    def test_false_xor_spec_is_spec(self) -> None:
        result = Specification.false() ^ Always()
        assert result == Always()

    def test_double_negation(self) -> None:
        spec = Always()
        assert ~~spec is spec

    def test_not_true_is_false(self) -> None:
        assert ~Specification.true() is Specification.false()

    def test_not_false_is_true(self) -> None:
        assert ~Specification.false() is Specification.true()

    def test_deep_nested_simplifies(self) -> None:
        """True & (False | (spec & True)) simplifies to spec."""
        spec = Always() & Specification.false()
        assert spec is Specification.false()

    def test_true_and_false_is_false(self) -> None:
        result = Specification.true() & Specification.false()
        assert result is Specification.false()


class TestTypeSafety:
    def test_generic_preserves_type(self) -> None:
        spec: Specification[int] = GreaterThan(10) & GreaterThan(20)
        assert spec(25)
