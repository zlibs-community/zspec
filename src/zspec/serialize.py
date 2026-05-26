"""Serialize specification trees to/from plain dicts."""

from collections.abc import Mapping
from typing import Any, cast

from zspec.specification import (
    FALSE_SPEC,
    TRUE_SPEC,
    AndSpecification,
    FieldSpec,
    NotSpecification,
    OrSpecification,
    Specification,
    XorSpecification,
)
from zspec.utils import slots_of

_BUILTINS: dict[str, type[Specification[Any]]] = {
    "AndSpecification": AndSpecification,
    "OrSpecification": OrSpecification,
    "NotSpecification": NotSpecification,
    "XorSpecification": XorSpecification,
    "FieldSpec": FieldSpec,
}

_auto_registry: dict[str, type[Specification[Any]]] = {}


def registered[TSpec](cls: type[TSpec]) -> type[TSpec]:
    """Register a ``Specification`` subclass for deserialization.

    Registered classes are discovered automatically by :func:`from_dict` —
    no manual ``registry`` dict needed.

    Usage::

        @registered
        class InStock(Specification[Product]):
            ...
    """
    _auto_registry[cls.__name__] = cast(type[Specification[Any]], cls)
    return cls


def to_dict(spec: Specification[Any]) -> dict[str, object]:
    """Serialize *spec* to a plain dictionary.

    Composite nodes are recursively serialized.  Leaf specifications
    keep their class name and all slot values.

    Usage::

        data = to_dict(InStock() & MinPrice(100))
        # {"type": "AndSpecification", "left": {...}, "right": {...}}

    ``Specification.of()`` specs and unregistered user-defined types
    will raise :exc:`TypeError`.
    """
    if spec is TRUE_SPEC:
        return {"type": "TRUE"}
    if spec is FALSE_SPEC:
        return {"type": "FALSE"}

    match spec:
        case AndSpecification() | OrSpecification() | XorSpecification():
            return {
                "type": type(spec).__name__,
                "left": to_dict(spec.left),
                "right": to_dict(spec.right),
            }
        case NotSpecification():
            return {
                "type": "NotSpecification",
                "spec": to_dict(spec.spec),
            }
        case FieldSpec():
            return {
                "type": "FieldSpec",
                "field": spec.field,
                "op": spec.op,
                "value": spec.value,
            }
        case _:
            return _to_dict_leaf(spec)


def _to_dict_leaf(spec: Specification[Any]) -> dict[str, object]:
    name = type(spec).__name__
    try:
        hash(spec)
    except TypeError:
        msg = (
            f"Cannot serialize {name}: specification is not hashable. "
            f"Use __slots__ for all fields."
        )
        raise TypeError(msg) from None
    data: dict[str, object] = {"type": name}
    for s in slots_of(spec):
        data[s] = getattr(spec, s)
    return data


_Registry = Mapping[str, type[Specification[Any]]]


def from_dict(
    data: Mapping[str, object],
    registry: _Registry | None = None,
) -> Specification[Any]:
    """Deserialize a specification tree from *data*.

    *registry* maps class names to ``Specification`` subclasses.
    Built-in types (composites, ``TRUE``, ``FALSE``, ``FieldSpec``)
    are always recognized.

    Usage::

        spec = from_dict({"type": "MinPrice", "threshold": 100})
    """
    reg: dict[str, type[Specification[Any]]] = {**_BUILTINS}
    reg.update(_auto_registry)
    if registry is not None:
        reg.update(registry)

    type_name: object = data["type"]
    if not isinstance(type_name, str):
        msg = f"Invalid spec data: 'type' must be a string, got {type_name!r}"
        raise TypeError(msg)

    if type_name == "TRUE":
        return cast(Specification[Any], TRUE_SPEC)
    if type_name == "FALSE":
        return cast(Specification[Any], FALSE_SPEC)

    return _from_dict_node(type_name, data, reg, registry)


def _from_dict_node(
    type_name: str,
    data: Mapping[str, object],
    reg: dict[str, type[Specification[Any]]],
    registry: Mapping[str, type[Specification[Any]]] | None,
) -> Specification[Any]:
    cls = reg.get(type_name)
    if cls is None:
        msg = (
            f"Unknown specification type {type_name!r}. "
            f"Register it via the ``registry`` parameter."
        )
        raise TypeError(msg)

    if type_name == "NotSpecification":
        inner = data["spec"]
        if not isinstance(inner, dict):
            msg = "Invalid NotSpecification data"
            raise TypeError(msg)
        return NotSpecification(from_dict(inner, registry))

    if type_name in {"AndSpecification", "OrSpecification", "XorSpecification"}:
        left = data.get("left")
        right = data.get("right")
        if not isinstance(left, dict) or not isinstance(right, dict):
            msg = f"Invalid {type_name} data"
            raise TypeError(msg)
        left_spec = from_dict(left, registry)
        right_spec = from_dict(right, registry)
        if type_name == "AndSpecification":
            return AndSpecification(left_spec, right_spec)
        if type_name == "OrSpecification":
            return OrSpecification(left_spec, right_spec)
        return XorSpecification(left_spec, right_spec)

    kwargs = {k: v for k, v in data.items() if k != "type"}
    return cls(**kwargs)
