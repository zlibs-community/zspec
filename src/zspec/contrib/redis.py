"""RediSearch query translator for specification trees."""

from typing import override

from zspec.translator import Translator


class RediSearchTranslator(Translator[str]):
    """Translate specifications into RediSearch ``FT.SEARCH`` query strings.

    Subclass and override ``_translate`` for each leaf specification::

        from zspec.contrib.redis import RediSearchTranslator

        class MyTranslator(RediSearchTranslator):
            def _translate(self, spec: Specification[Any]) -> str:
                match spec:
                    case InStock():
                        return "@in_stock:{true}"
                    case MinPrice(min_price=price):
                        return f"@price:[{price} +inf]"
                    case _:
                        return super()._translate(spec)

        translator = MyTranslator()
        q = translator.translate(InStock() & MinPrice(100))
        results = redis.ft("idx:products").search(q)
    """

    @override
    def _and(self, left: str, right: str) -> str:
        """Combine with space-separated AND."""
        return f"({left} {right})"

    @override
    def _or(self, left: str, right: str) -> str:
        """Combine with ``|`` operator."""
        return f"({left} | {right})"

    @override
    def _not(self, operand: str) -> str:
        """Negate with ``-`` prefix."""
        return f"-({operand})"
