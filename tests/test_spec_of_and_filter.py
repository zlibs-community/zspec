"""Tests for Specification.of(), filter(), reject(), partition(), true(), false()."""

from zspec import Specification


class TestSpecOf:
    def test_of_from_lambda(self) -> None:
        even = Specification.of(lambda x: x % 2 == 0)
        assert even(2) is True
        assert even(3) is False

    def test_of_str(self) -> None:
        even = Specification.of(lambda x: x % 2 == 0)
        assert "lambda" in str(even)

    def test_of_composable(self) -> None:
        even = Specification.of(lambda x: x % 2 == 0)
        positive = Specification.of(lambda x: x > 0)
        spec = even & positive
        assert spec(4)
        assert not spec(-2)

    def test_of_with_named_function(self) -> None:
        def is_positive(x: int) -> bool:
            return x > 0

        spec = Specification.of(is_positive)
        assert spec(5)
        assert "is_positive" in str(spec)


class TestFilter:
    def test_filter_empty(self) -> None:
        even = Specification.of(lambda x: x % 2 == 0)
        assert list(even.filter([])) == []

    def test_filter_all_match(self) -> None:
        positive = Specification.of(lambda x: x > 0)
        assert list(positive.filter([1, 2, 3])) == [1, 2, 3]

    def test_filter_some_match(self) -> None:
        even = Specification.of(lambda x: x % 2 == 0)
        assert list(even.filter([1, 2, 3, 4])) == [2, 4]

    def test_filter_composite(self) -> None:
        even = Specification.of(lambda x: x % 2 == 0)
        positive = Specification.of(lambda x: x > 0)
        spec = even & positive
        assert list(spec.filter(range(-5, 6))) == [2, 4]

    def test_filter_lazy(self) -> None:
        even = Specification.of(lambda x: x % 2 == 0)
        result = even.filter([2, 4, 6])
        assert next(result) == 2  # only consumes one element


class TestReject:
    def test_reject_empty(self) -> None:
        even = Specification.of(lambda x: x % 2 == 0)
        assert list(even.reject([])) == []

    def test_reject_all_pass(self) -> None:
        positive = Specification.of(lambda x: x > 0)
        assert list(positive.reject([1, 2, 3])) == []

    def test_reject_some(self) -> None:
        even = Specification.of(lambda x: x % 2 == 0)
        assert list(even.reject([1, 2, 3, 4])) == [1, 3]

    def test_reject_lazy(self) -> None:
        even = Specification.of(lambda x: x % 2 == 0)
        result = even.reject([1, 3, 5])
        assert next(result) == 1


class TestPartition:
    def test_partition_empty(self) -> None:
        even = Specification.of(lambda x: x % 2 == 0)
        assert even.partition([]) == ([], [])

    def test_partition(self) -> None:
        even = Specification.of(lambda x: x % 2 == 0)
        passed, failed = even.partition([1, 2, 3, 4])
        assert passed == [2, 4]
        assert failed == [1, 3]

    def test_partition_all_pass(self) -> None:
        positive = Specification.of(lambda x: x > 0)
        passed, failed = positive.partition([1, 2, 3])
        assert passed == [1, 2, 3]
        assert failed == []

    def test_partition_composite(self) -> None:
        even = Specification.of(lambda x: x % 2 == 0)
        positive = Specification.of(lambda x: x > 0)
        spec = even & positive
        passed, failed = spec.partition(range(1, 7))
        assert passed == [2, 4, 6]
        assert failed == [1, 3, 5]


class TestTrueFalse:
    def test_true(self) -> None:
        assert Specification.true()(None)
        assert str(Specification.true()) == "Of(<lambda>)"

    def test_false(self) -> None:
        assert not Specification.false()(None)

    def test_true_composable(self) -> None:
        even = Specification.of(lambda x: x % 2 == 0)
        spec = Specification.true() & even
        assert spec(4)
        assert not spec(5)

    def test_false_composable(self) -> None:
        even = Specification.of(lambda x: x % 2 == 0)
        spec = Specification.false() | even
        assert spec(4)
        assert not spec(5)
