"""Pydantic integration — use specifications as validators."""

from collections.abc import Callable

from zspec.specification import Specification


def validate[T](
    spec: Specification[T],
    *,
    message: str = "",
) -> Callable[[T], T]:
    """Return a callable that validates *candidate* against *spec*.

    Can be used as a Pydantic ``field_validator`` or ``model_validator``::

        from pydantic import BaseModel, field_validator

        class Product(BaseModel):
            price: int

            _check_price = field_validator("price")(
                validate(MinPrice(100), message="Price is too low"),
            )

    The returned function raises :exc:`ValueError` with *message*
    when the specification is not satisfied.
    """

    def _validator(candidate: T) -> T:
        if not spec.is_satisfied_by(candidate):
            msg = message or f"Does not satisfy {spec}"
            raise ValueError(msg)
        return candidate

    return _validator
