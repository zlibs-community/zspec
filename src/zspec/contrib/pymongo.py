"""PyMongo filter translator for specification trees."""

from typing import Any, override

from zspec.translator import Translator


class PyMongoTranslator(Translator[dict[str, Any]]):
    """Translate specifications into MongoDB filter documents.

    Subclass and override ``_translate`` for each leaf specification::

        from zspec.contrib.pymongo import PyMongoTranslator

        class MyTranslator(PyMongoTranslator):
            def _translate(self, spec: Specification[Any]) -> dict[str, Any]:
                match spec:
                    case InStock():
                        return {"in_stock": True}
                    case MinPrice(min_price=price):
                        return {"price": {"$gte": price}}
                    case _:
                        raise NotImplementedError

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
