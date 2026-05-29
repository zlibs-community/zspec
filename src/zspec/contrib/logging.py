"""Logging wrapper for translators — logs each translation step."""

import logging
from typing import Any

from zspec.specification import Specification
from zspec.translator import Translator

logger = logging.getLogger(__name__)


class LoggingTranslator[T]:
    """Wraps a :class:`~zspec.Translator` and logs each translation step.

    Usage::

        import logging
        logging.getLogger("zspec.contrib.logging").setLevel(logging.DEBUG)

        translator = LoggingTranslator(MySqlTranslator())
        result = translator.translate(InStock() & MinPrice(100))
    """

    __slots__ = ("_inner",)

    def __init__(self, translator: Translator[T]) -> None:
        """Initialize with *translator* to wrap."""
        self._inner = translator

    def translate(self, spec: Specification[Any]) -> T:
        """Translate *spec* and log the step."""
        logger.debug("%s", spec)
        result = self._inner.translate(spec)
        logger.debug("  -> %s", result)
        return result

    @property
    def inner(self) -> Translator[T]:
        """The wrapped translator."""
        return self._inner
