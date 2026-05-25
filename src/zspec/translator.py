"""Visitor-style translator that walks a specification tree."""

from abc import ABC, abstractmethod
from typing import Any

from zspec import AndSpecification, NotSpecification, OrSpecification, Specification


class Translator[TResult](ABC):
    """Walk a specification tree and translate it into *TResult*."""

    def translate(self, spec: Specification[Any]) -> TResult:
        """Recursively translate *spec* into *TResult*."""
        match spec:
            case AndSpecification(left=left, right=right):
                return self._and(self.translate(left), self.translate(right))
            case OrSpecification(left=left, right=right):
                return self._or(self.translate(left), self.translate(right))
            case NotSpecification(spec=inner):
                return self._not(self.translate(inner))
            case _:
                return self._translate(spec)

    @abstractmethod
    def _translate(self, spec: Specification[Any]) -> TResult:
        msg = f"Specification {type(spec).__name__} is not supported"
        raise NotImplementedError(msg)

    @abstractmethod
    def _and(self, left: TResult, right: TResult) -> TResult:
        raise NotImplementedError

    @abstractmethod
    def _or(self, left: TResult, right: TResult) -> TResult:
        raise NotImplementedError

    @abstractmethod
    def _not(self, operand: TResult) -> TResult:
        raise NotImplementedError
