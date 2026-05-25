"""Tests for Specification.of() and filter()."""

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
