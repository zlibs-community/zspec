"""Built-in Translator implementations."""

from typing import Any, NamedTuple, override

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
                        return super()._translate(spec)

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


class MongoTranslator(Translator[dict[str, Any]]):
    """Translate specifications into MongoDB filter documents.

    Subclass and override ``_translate`` for each leaf specification::

        class MyTranslator(MongoTranslator):
            def _translate(self, spec: Specification[Any]) -> dict[str, Any]:
                match spec:
                    case InStock():
                        return {"in_stock": True}
                    case MinPrice(min_price=price):
                        return {"price": {"$gte": price}}
                    case _:
                        return super()._translate(spec)

        translator = MyTranslator()
        results = collection.find(
            translator.translate(InStock() & MinPrice(100)),
        )
    """

    @override
    def _and(
        self,
        left: dict[str, Any],
        right: dict[str, Any],
    ) -> dict[str, Any]:
        """Combine with ``$and``."""
        return {"$and": [left, right]}

    @override
    def _or(
        self,
        left: dict[str, Any],
        right: dict[str, Any],
    ) -> dict[str, Any]:
        """Combine with ``$or``."""
        return {"$or": [left, right]}

    @override
    def _not(self, operand: dict[str, Any]) -> dict[str, Any]:
        """Negate with ``$nor``."""
        return {"$nor": [operand]}

    @override
    def _xor(
        self,
        left: dict[str, Any],
        right: dict[str, Any],
    ) -> dict[str, Any]:
        """Combine with native ``$xor``."""
        return {"$xor": [left, right]}
