"""Tests for explain()."""


from typing import override

from zspec import Specification, to_ascii
from zspec.explain import ExplainNode, explain


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


class TestExplain:
    def test_leaf_passed(self) -> None:
        result = explain(Always(), None)
        assert result.passed is True
        assert result.spec == "Always"
        assert result.children == []

    def test_leaf_failed(self) -> None:
        result = explain(Never(), None)
        assert result.passed is False
        assert result.spec == "Never"

    def test_and_both_passed(self) -> None:
        result = explain(Always() & Always(), None)
        assert result.passed is True
        assert len(result.children) == 2
        assert all(c.passed for c in result.children)

    def test_and_one_failed(self) -> None:
        result = explain(Always() & Never(), None)
        assert result.passed is False
        assert result.children[0].passed is True
        assert result.children[1].passed is False

    def test_or_one_passed(self) -> None:
        result = explain(Always() | Never(), None)
        assert result.passed is True

    def test_not(self) -> None:
        result = explain(~Never(), None)
        assert result.passed is True
        assert result.children[0].passed is False

    def test_xor(self) -> None:
        result = explain(Always() ^ Never(), None)
        assert result.passed is True
        result2 = explain(Always() ^ Always(), None)
        assert result2.passed is False

    def test_nested_tree(self) -> None:
        result = explain(Always() & (~Never() | Always()), None)
        assert result.passed is True
        assert result.spec == "(Always AND (NOT (Never) OR Always))"
        assert len(result.children) == 2

    def test_explain_node_dataclass(self) -> None:
        node = ExplainNode(passed=True, spec="test")
        assert node.passed is True
        assert node.spec == "test"
        assert node.children == []


class TestToAscii:
    def test_leaf(self) -> None:
        result = to_ascii(Always())
        assert result == "Always"

    def test_and(self) -> None:
        result = to_ascii(Always() & Never())
        assert result == "(Always AND Never)\n├── Always\n└── Never"

    def test_or(self) -> None:
        result = to_ascii(Always() | Never())
        assert result == "(Always OR Never)\n├── Always\n└── Never"

    def test_not(self) -> None:
        result = to_ascii(~Always())
        assert result == "NOT (Always)\n└── Always"

    def test_xor(self) -> None:
        result = to_ascii(Always() ^ Never())
        assert result == "(Always XOR Never)\n├── Always\n└── Never"

    def test_nested(self) -> None:
        result = to_ascii(Always() & (~Never() | Always()))
        lines = result.split("\n")
        assert lines[0] == "(Always AND (NOT (Never) OR Always))"
        assert "├── Always" in lines
        assert "└── (NOT (Never) OR Always)" in lines

    def test_true(self) -> None:
        assert to_ascii(Specification.true()) == "TRUE"

    def test_false(self) -> None:
        assert to_ascii(Specification.false()) == "FALSE"
