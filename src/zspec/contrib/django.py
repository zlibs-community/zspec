"""Django Q-object translator for specification trees."""


from typing import override

from django.db.models import Q

from zspec.translator import Translator


class DjangoQTranslator(Translator[Q]):
    """Translate specifications into Django ``Q`` objects.

    Subclass and override ``_translate`` for each leaf specification::

        from zspec.contrib.django import DjangoQTranslator

        class MyTranslator(DjangoQTranslator):
            def _translate(self, spec: Specification[Any]) -> Q:
                from django.db.models import Q

                match spec:
                    case InStock():
                        return Q(in_stock=True)
                    case MinPrice(min_price=price):
                        return Q(price__gte=price)
                    case _:
                        return super()._translate(spec)

        translator = MyTranslator()
        results = Product.objects.filter(
            translator.translate(InStock() & MinPrice(100)),
        )
    """

    @override
    def _and(self, left: Q, right: Q) -> Q:
        """Combine with ``&``."""
        return left & right

    @override
    def _or(self, left: Q, right: Q) -> Q:
        """Combine with ``|``."""
        return left | right

    @override
    def _not(self, operand: Q) -> Q:
        """Negate with ``~``."""
        return ~operand
