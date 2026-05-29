"""Elasticsearch query DSL translator for specification trees."""

from typing import Any, override

from zspec.translator import Translator


class ElasticsearchTranslator(Translator[dict[str, Any]]):
    """Translate specifications into Elasticsearch query DSL documents.

    Subclass and override ``_translate`` for each leaf specification::

        from zspec.contrib.elasticsearch import ElasticsearchTranslator

        class MyTranslator(ElasticsearchTranslator):
            def _translate(self, spec: Specification[Any]) -> dict[str, Any]:
                match spec:
                    case InStock():
                        return {"term": {"in_stock": True}}
                    case MinPrice(min_price=price):
                        return {"range": {"price": {"gte": price}}}
                    case _:
                        return super()._translate(spec)

        translator = MyTranslator()
        results = es.search(
            index="products",
            query=translator.translate(InStock() & MinPrice(100)),
        )
    """

    @override
    def _and(
        self,
        left: dict[str, Any],
        right: dict[str, Any],
    ) -> dict[str, Any]:
        """Combine with ES ``bool.must``."""
        return {"bool": {"must": [left, right]}}

    @override
    def _or(
        self,
        left: dict[str, Any],
        right: dict[str, Any],
    ) -> dict[str, Any]:
        """Combine with ES ``bool.should``."""
        return {"bool": {"should": [left, right]}}

    @override
    def _not(self, operand: dict[str, Any]) -> dict[str, Any]:
        """Negate with ES ``bool.must_not``."""
        return {"bool": {"must_not": [operand]}}
