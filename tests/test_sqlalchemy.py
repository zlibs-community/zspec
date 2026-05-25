"""Tests for SqlAlchemyTranslator."""


from typing import Any, override

import pytest

sa = pytest.importorskip("sqlalchemy")
ColumnElement = sa.sql.expression.ColumnElement

from zspec import Specification
from zspec.contrib.sqlalchemy import SqlAlchemyTranslator


class Even(Specification[object]):
    __slots__ = ()

    @override
    def is_satisfied_by(self, candidate: object) -> bool:
        return isinstance(candidate, int) and candidate % 2 == 0


class Positive(Specification[object]):
    __slots__ = ()

    @override
    def is_satisfied_by(self, candidate: object) -> bool:
        return isinstance(candidate, int) and candidate > 0


class EvenSqlAlchemy(SqlAlchemyTranslator):
    @override
    def _translate(self, spec: Specification[Any]) -> Any:
        match spec:
            case Even():
                return sa.column("val") % 2 == 0
            case Positive():
                return sa.column("val") > 0
            case _:
                return super()._translate(spec)


class TestSqlAlchemyTranslator:
    def test_leaf(self) -> None:
        t = EvenSqlAlchemy()
        result = t.translate(Even())
        assert "val % :val_1 = :param_1" in str(result)

    def test_and(self) -> None:
        t = EvenSqlAlchemy()
        result = t.translate(Even() & Positive())
        assert " AND " in str(result)

    def test_not(self) -> None:
        t = EvenSqlAlchemy()
        result = t.translate(~Even())
        assert "NOT" in str(result) or "!=" in str(result)

    def test_nested(self) -> None:
        t = EvenSqlAlchemy()
        spec = Even() & (~Positive() | Even())
        result = t.translate(spec)
        assert " AND " in str(result)
        assert "(" in str(result)

    def test_abstract_not_instantiable(self) -> None:
        with pytest.raises(TypeError):
            SqlAlchemyTranslator()  # type: ignore[abstract]
