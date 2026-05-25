"""Built-in Translator implementations."""

from typing import NamedTuple, override

from zspec.translator import Translator


class SqlFragment(NamedTuple):
    """SQL clause fragment with bound parameters."""

    sql: str
    params: tuple[object, ...]


class SqlTranslator(Translator[SqlFragment]):
    """Translate specifications into parameterized SQL.

    Subclass and override ``_translate`` for each leaf specification::

        class MyTranslator(SqlTranslator):
            def _translate(self, spec: Specification[Any]) -> SqlFragment:
                match spec:
                    case InStock():
                        return SqlFragment("in_stock = %s", (True,))
                    case MinPrice(min_price=price):
                        return SqlFragment("price >= %s", (price,))
                    case _:
                        msg = f"Specification {type(spec).__name__} is not supported"
                        raise NotImplementedError(msg)

    """

    @override
    def _and(self, left: SqlFragment, right: SqlFragment) -> SqlFragment:
        """Combine with AND."""
        return SqlFragment(
            f"({left.sql} AND {right.sql})",
            left.params + right.params,
        )

    @override
    def _or(self, left: SqlFragment, right: SqlFragment) -> SqlFragment:
        """Combine with OR."""
        return SqlFragment(
            f"({left.sql} OR {right.sql})",
            left.params + right.params,
        )

    @override
    def _not(self, operand: SqlFragment) -> SqlFragment:
        """Negate."""
        return SqlFragment(f"NOT ({operand.sql})", operand.params)
