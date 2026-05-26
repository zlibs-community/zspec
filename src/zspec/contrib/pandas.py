"""Pandas query-string translator for specification trees."""

from typing import override

from zspec.translator import Translator


class PandasTranslator(Translator[str]):
    """Translate specifications into Pandas query strings.

    Subclass and override ``_translate`` for each leaf specification::

        import pandas as pd
        from zspec.contrib.pandas import PandasTranslator

        class MyTranslator(PandasTranslator):
            def _translate(self, spec: Specification[Any]) -> str:
                match spec:
                    case InStock():
                        return "in_stock == True"
                    case MinPrice(threshold=price):
                        return f"price >= {price}"
                    case _:
                        return super()._translate(spec)

        translator = MyTranslator()
        df.query(translator.translate(InStock() & MinPrice(100)))
    """

    @override
    def _and(self, left: str, right: str) -> str:
        """Combine with ``and``."""
        return f"({left}) and ({right})"

    @override
    def _or(self, left: str, right: str) -> str:
        """Combine with ``or``."""
        return f"({left}) or ({right})"

    @override
    def _not(self, operand: str) -> str:
        """Negate with ``not``."""
        return f"not ({operand})"

    @override
    def _xor(self, left: str, right: str) -> str:
        """Combine with ``!=`` (boolean XOR in Pandas query syntax)."""
        return f"({left}) != ({right})"
