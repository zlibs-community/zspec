"""SQLAlchemy expression translator for specification trees."""

from typing import override

from sqlalchemy.sql.expression import ColumnElement
from sqlalchemy.sql.expression import and_ as _sql_and
from sqlalchemy.sql.expression import not_ as _sql_not
from sqlalchemy.sql.expression import or_ as _sql_or

from zspec.translator import Translator


class SqlAlchemyTranslator(Translator[ColumnElement[bool]]):
    """Translate specifications into SQLAlchemy boolean expressions.

    Subclass and override ``_translate`` for each leaf specification::

        from sqlalchemy import Column, Integer, Boolean, Table, select
        from zspec.contrib.sqlalchemy import SqlAlchemyTranslator

        product = Table(
            "product", ...,
            Column("price", Integer),
            Column("in_stock", Boolean),
        )

        class MyTranslator(SqlAlchemyTranslator):
            def _translate(self, spec: Specification[Any]) -> ColumnElement[bool]:
                match spec:
                    case InStock():
                        return product.c.in_stock.is_(True)
                    case MinPrice(min_price=price):
                        return product.c.price >= price
                    case _:
                        raise NotImplementedError

        translator = MyTranslator()
        stmt = select(product).where(
            translator.translate(InStock() & MinPrice(100)),
        )
    """

    @override
    def _and(
        self,
        left: ColumnElement[bool],
        right: ColumnElement[bool],
    ) -> ColumnElement[bool]:
        """Combine with SQL AND."""
        return _sql_and(left, right)

    @override
    def _or(
        self,
        left: ColumnElement[bool],
        right: ColumnElement[bool],
    ) -> ColumnElement[bool]:
        """Combine with SQL OR."""
        return _sql_or(left, right)

    @override
    def _not(self, operand: ColumnElement[bool]) -> ColumnElement[bool]:
        """Negate with SQL NOT."""
        return _sql_not(operand)
