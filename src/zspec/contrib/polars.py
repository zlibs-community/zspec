"""Polars expression translator for specification trees."""

from typing import override

from polars import Expr

from zspec.translator import Translator


class PolarsTranslator(Translator[Expr]):
    """Translate specifications into Polars expressions.

    Subclass and override ``_translate`` for each leaf specification::

        import polars as pl
        from zspec.contrib.polars import PolarsTranslator

        class MyTranslator(PolarsTranslator):
            def _translate(self, spec: Specification[Any]) -> pl.Expr:
                match spec:
                    case InStock():
                        return pl.col("in_stock")
                    case MinPrice(threshold=price):
                        return pl.col("price") >= price
                    case _:
                        return super()._translate(spec)

        translator = MyTranslator()
        df.filter(translator.translate(InStock() & MinPrice(100)))
    """

    @override
    def _and(self, left: Expr, right: Expr) -> Expr:
        """Combine with ``&``."""
        return left & right

    @override
    def _or(self, left: Expr, right: Expr) -> Expr:
        """Combine with ``|``."""
        return left | right

    @override
    def _not(self, operand: Expr) -> Expr:
        """Negate with ``~``."""
        return ~operand

    @override
    def _xor(self, left: Expr, right: Expr) -> Expr:
        """Combine with native ``^``."""
        return left ^ right
