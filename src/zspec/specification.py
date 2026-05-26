"""Specification pattern — composable business rule objects."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Iterator
from functools import reduce
from operator import and_, or_
from typing import Any, Final, cast, override

from zspec.utils import slots_of


class Specification[T](ABC):
    """Abstract specification that can be combined with ``&``, ``|``, ``~``, ``^``."""

    __slots__: tuple[str, ...] = ()

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """Check whether *candidate* satisfies this specification."""
        raise NotImplementedError

    def __and__(self, other: Specification[T]) -> Specification[T]:
        """Combine with *other* via logical AND."""
        if isinstance(self, _FalseSpecification):
            return cast(Specification[T], _FALSE_SPEC)
        if isinstance(other, _FalseSpecification):
            return cast(Specification[T], _FALSE_SPEC)
        if isinstance(self, _TrueSpecification):
            return other
        if isinstance(other, _TrueSpecification):
            return self
        return AndSpecification(left=self, right=other)

    def __or__(self, other: Specification[T]) -> Specification[T]:
        """Combine with *other* via logical OR."""
        if isinstance(self, _TrueSpecification):
            return cast(Specification[T], _TRUE_SPEC)
        if isinstance(other, _TrueSpecification):
            return cast(Specification[T], _TRUE_SPEC)
        if isinstance(self, _FalseSpecification):
            return other
        if isinstance(other, _FalseSpecification):
            return self
        return OrSpecification(self, other)

    def __xor__(self, other: Specification[T]) -> Specification[T]:
        """Combine with *other* via logical XOR."""
        if isinstance(self, _TrueSpecification):
            return ~other
        if isinstance(other, _TrueSpecification):
            return ~self
        if isinstance(self, _FalseSpecification):
            return other
        if isinstance(other, _FalseSpecification):
            return self
        return XorSpecification(self, other)

    def __invert__(self) -> Specification[T]:
        """Negate this specification."""
        return NotSpecification(self)

    @override
    def __repr__(self) -> str:
        """Return ``ClassName(attr=value, ...)`` for all slots."""
        args = ", ".join(
            f"{s}={getattr(self, s)!r}" for s in slots_of(self)
        )
        return f"{type(self).__name__}({args})"

    @override
    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return all(
            getattr(self, s) == getattr(other, s) for s in slots_of(self)
        )

    @override
    def __hash__(self) -> int:
        return hash(
            (type(self), tuple(getattr(self, s) for s in slots_of(self))),
        )

    @override
    def __str__(self) -> str:
        """Return the class name. Override in subclasses for custom rendering."""
        return type(self).__name__

    def __call__(self, candidate: T) -> bool:
        """Evaluate the specification against *candidate*."""
        return self.is_satisfied_by(candidate)

    def filter(self, candidates: Iterable[T]) -> Iterator[T]:
        """Yield candidates that satisfy this specification."""
        return (c for c in candidates if self(c))

    def reject(self, candidates: Iterable[T]) -> Iterator[T]:
        """Yield candidates that do **not** satisfy this specification."""
        return (c for c in candidates if not self(c))

    def partition(
        self,
        candidates: Iterable[T],
    ) -> tuple[list[T], list[T]]:
        """Split into ``(passed, failed)`` lists."""
        passed: list[T] = []
        failed: list[T] = []
        for c in candidates:
            if self(c):
                passed.append(c)
            else:
                failed.append(c)
        return passed, failed

    @classmethod
    def of(cls, fn: Callable[[T], bool]) -> Specification[T]:
        """Create a specification from *fn*.

        Usage::

            adult = Specification.of(lambda u: u.age >= 18)
        """
        name = getattr(fn, "__name__", "fn")
        spec_type = type(
            f"Of({name})",
            (Specification,),
            {
                "__slots__": (),
                "is_satisfied_by": staticmethod(fn),
            },
        )
        return cast(Specification[T], spec_type())

    @classmethod
    def true(cls) -> Specification[T]:
        """Return a specification satisfied by **any** candidate."""
        return cast(Specification[T], _TRUE_SPEC)

    @classmethod
    def false(cls) -> Specification[T]:
        """Return a specification satisfied by **no** candidate."""
        return cast(Specification[T], _FALSE_SPEC)

    @classmethod
    def all_of(
        cls,
        specs: Iterable[Specification[T]],
        default: Specification[T] | None = None,
    ) -> Specification[T] | None:
        """Return a specification satisfied when **all** of *specs* are.

        Returns *default* when *specs* is empty.
        """
        items = list(specs)
        if not items:
            return default
        return reduce(and_, items)

    @classmethod
    def any_of(
        cls,
        specs: Iterable[Specification[T]],
        default: Specification[T] | None = None,
    ) -> Specification[T] | None:
        """Return a specification satisfied when **any** of *specs* is.

        Returns *default* when *specs* is empty.
        """
        items = list(specs)
        if not items:
            return default
        return reduce(or_, items)


class _TrueSpecification[T](Specification[T]):
    """Internal: specification that is always satisfied."""

    __slots__ = ()

    @override
    def is_satisfied_by(self, candidate: T) -> bool:
        return True

    @override
    def __invert__(self) -> Specification[T]:
        return cast(Specification[T], _FALSE_SPEC)

    @override
    def __str__(self) -> str:
        return "TRUE"


class _FalseSpecification[T](Specification[T]):
    """Internal: specification that is never satisfied."""

    __slots__ = ()

    @override
    def is_satisfied_by(self, candidate: T) -> bool:
        return False

    @override
    def __invert__(self) -> Specification[T]:
        return cast(Specification[T], _TRUE_SPEC)

    @override
    def __str__(self) -> str:
        return "FALSE"


_TRUE_SPEC: Final[_TrueSpecification[Any]] = _TrueSpecification()
_FALSE_SPEC: Final[_FalseSpecification[Any]] = _FalseSpecification()


class AndSpecification[T](Specification[T]):
    """Conjunction of two specifications (produced by ``&``)."""

    __slots__ = ("left", "right")

    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        """Initialize with *left* and *right* specifications."""
        self.left = left
        self.right = right

    @override
    def is_satisfied_by(self, candidate: T) -> bool:
        """Check whether *candidate* satisfies both specifications."""
        return self.left.is_satisfied_by(
            candidate,
        ) and self.right.is_satisfied_by(candidate)

    @override
    def __str__(self) -> str:
        return f"({self.left} AND {self.right})"


class OrSpecification[T](Specification[T]):
    """Disjunction of two specifications (produced by ``|``)."""

    __slots__ = ("left", "right")

    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        """Initialize with *left* and *right* specifications."""
        self.left = left
        self.right = right

    @override
    def is_satisfied_by(self, candidate: T) -> bool:
        """Check whether *candidate* satisfies at least one specification."""
        return (
            self.left.is_satisfied_by(candidate)
            or self.right.is_satisfied_by(candidate)
        )

    @override
    def __str__(self) -> str:
        return f"({self.left} OR {self.right})"


class NotSpecification[T](Specification[T]):
    """Negation of a specification (produced by ``~``)."""

    __slots__ = ("spec",)

    def __init__(self, spec: Specification[T]) -> None:
        """Initialize with *spec* to negate."""
        self.spec = spec

    @override
    def is_satisfied_by(self, candidate: T) -> bool:
        """Check whether *candidate* does **not** satisfy the specification."""
        return not self.spec.is_satisfied_by(candidate)

    @override
    def __invert__(self) -> Specification[T]:
        """Negate — double negation returns the inner spec."""
        return self.spec

    @override
    def __str__(self) -> str:
        return f"NOT ({self.spec})"


class XorSpecification[T](Specification[T]):
    """Exclusive disjunction of two specifications (produced by ``^``)."""

    __slots__ = ("left", "right")

    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        """Initialize with *left* and *right* specifications."""
        self.left = left
        self.right = right

    @override
    def is_satisfied_by(self, candidate: T) -> bool:
        """Check whether exactly one specification is satisfied."""
        return self.left(candidate) != self.right(candidate)

    @override
    def __str__(self) -> str:
        return f"({self.left} XOR {self.right})"
