"""Tests for Translator and SqlTranslator."""

from typing import Any, override

import pytest

from zspec import (
    Specification,
    SqlFragment,
    SqlTranslator,
    Translator,
)


class Even(Specification[int]):
    __slots__ = ()

    @override
    def is_satisfied_by(self, candidate: int) -> bool:
        return candidate % 2 == 0


class Positive(Specification[int]):
    __slots__ = ()

    @override
    def is_satisfied_by(self, candidate: int) -> bool:
        return candidate > 0


class EvenSql(SqlTranslator):
    @override
    def _translate(self, spec: Specification[Any]) -> Any:
        match spec:
            case Even():
                return SqlFragment("value %% 2 = 0", ())
            case Positive():
                return SqlFragment("value > 0", ())
            case _:
                msg = f"Unknown spec: {type(spec).__name__}"
                raise NotImplementedError(msg)


class TestTranslator:
    def test_translate_leaf(self) -> None:
        class StrTranslator(Translator[str]):
            @override
            def _translate(self, spec: Specification[Any]) -> Any:
                return type(spec).__name__

            @override
            def _and(self, left: Any, right: Any) -> Any:
                return f"({left} AND {right})"

            @override
            def _or(self, left: Any, right: Any) -> Any:
                return f"({left} OR {right})"

            @override
            def _not(self, operand: Any) -> Any:
                return f"NOT ({operand})"

        t = StrTranslator()
        assert t.translate(Even()) == "Even"

    def test_translate_and(self) -> None:
        class StrTranslator(Translator[str]):
            @override
            def _translate(self, spec: Specification[Any]) -> Any:
                return type(spec).__name__

            @override
            def _and(self, left: Any, right: Any) -> Any:
                return f"({left} AND {right})"

            @override
            def _or(self, left: Any, right: Any) -> Any:
                return f"({left} OR {right})"

            @override
            def _not(self, operand: Any) -> Any:
                return f"NOT ({operand})"

        t = StrTranslator()
        result = t.translate(Even() & Positive())
        assert result == "(Even AND Positive)"

    def test_translate_nested(self) -> None:
        class StrTranslator(Translator[str]):
            @override
            def _translate(self, spec: Specification[Any]) -> Any:
                return type(spec).__name__

            @override
            def _and(self, left: Any, right: Any) -> Any:
                return f"({left} AND {right})"

            @override
            def _or(self, left: Any, right: Any) -> Any:
                return f"({left} OR {right})"

            @override
            def _not(self, operand: Any) -> Any:
                return f"NOT ({operand})"

        t = StrTranslator()
        result = t.translate(Even() & ~Positive() | Even())
        assert result == "((Even AND NOT (Positive)) OR Even)"

    def test_translate_xor(self) -> None:
        class StrTranslator(Translator[str]):
            @override
            def _translate(self, spec: Specification[Any]) -> Any:
                return type(spec).__name__

            @override
            def _and(self, left: Any, right: Any) -> Any:
                return f"({left} AND {right})"

            @override
            def _or(self, left: Any, right: Any) -> Any:
                return f"({left} OR {right})"

            @override
            def _not(self, operand: Any) -> Any:
                return f"NOT ({operand})"

        t = StrTranslator()
        result = t.translate(Even() ^ Positive())
        assert result == "((Even OR Positive) AND NOT ((Even AND Positive)))"

    def test_translate_not_implemented(self) -> None:
        t = EvenSql()
        try:
            t.translate(Even())
        except NotImplementedError:
            pytest.fail("Should not raise for registered spec types")

    def test_abstract_translator_not_instantiable(self) -> None:
        with pytest.raises(TypeError):
            Translator[str]()  # type: ignore[abstract]


class TestSqlTranslator:
    def test_leaf(self) -> None:
        t = EvenSql()
        result = t.translate(Even())
        assert result == SqlFragment("value %% 2 = 0", ())

    def test_and(self) -> None:
        t = EvenSql()
        result = t.translate(Even() & Positive())
        assert result.sql == "(value %% 2 = 0 AND value > 0)"
        assert result.params == ()

    def test_not(self) -> None:
        t = EvenSql()
        result = t.translate(~Even())
        assert result.sql == "NOT (value %% 2 = 0)"
        assert result.params == ()

    def test_nested(self) -> None:
        t = EvenSql()
        spec = Even() & (~Positive() | Even())
        result = t.translate(spec)
        assert result.sql == (
            "(value %% 2 = 0 AND (NOT (value > 0) OR value %% 2 = 0))"
        )


class TestSqlFragment:
    def test_named_tuple_fields(self) -> None:
        f = SqlFragment("x = %s", (1,))
        assert f.sql == "x = %s"
        assert f.params == (1,)

    def test_params_accumulation(self) -> None:
        f1 = SqlFragment("a = %s", (1,))
        f2 = SqlFragment("b = %s", (2,))
        t = EvenSql()
        result = t._and(f1, f2)
        assert result.params == (1, 2)
