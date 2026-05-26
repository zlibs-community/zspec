"""Explain and visualize specification trees."""

from dataclasses import dataclass, field
from typing import Any

from zspec.specification import (
    AndSpecification,
    NotSpecification,
    OrSpecification,
    Specification,
    XorSpecification,
)


@dataclass
class ExplainNode:
    """Result of a specification check on a candidate."""

    passed: bool
    spec: str
    children: list[ExplainNode] = field(default_factory=list)


def explain(spec: Specification[Any], candidate: object) -> ExplainNode:
    """Evaluate *spec* against *candidate* and return a result tree.

    Each leaf specification produces a node with no children.
    Composite specifications (AND, OR, NOT, XOR) produce nodes
    with children for each sub-specification.

    Usage::

        result = explain(adult & verified, user)
        print(result.passed)
        for child in result.children:
            print(child.spec, child.passed)

    """
    match spec:
        case AndSpecification(left=left, right=right):
            left_result = explain(left, candidate)
            right_result = explain(right, candidate)
            return ExplainNode(
                passed=left_result.passed and right_result.passed,
                spec=str(spec),
                children=[left_result, right_result],
            )
        case OrSpecification(left=left, right=right):
            left_result = explain(left, candidate)
            right_result = explain(right, candidate)
            return ExplainNode(
                passed=left_result.passed or right_result.passed,
                spec=str(spec),
                children=[left_result, right_result],
            )
        case XorSpecification(left=left, right=right):
            left_result = explain(left, candidate)
            right_result = explain(right, candidate)
            return ExplainNode(
                passed=left_result.passed != right_result.passed,
                spec=str(spec),
                children=[left_result, right_result],
            )
        case NotSpecification(spec=inner):
            inner_result = explain(inner, candidate)
            return ExplainNode(
                passed=not inner_result.passed,
                spec=str(spec),
                children=[inner_result],
            )
        case _:
            return ExplainNode(
                passed=spec.is_satisfied_by(candidate),
                spec=str(spec),
            )


def to_ascii(spec: Specification[Any]) -> str:
    """Return an ASCII tree visualization of *spec*.

    Usage::

        print(to_ascii(eligible))
        # AND
        # ├── price >= 100
        # └── in_stock == True
    """
    return "\n".join(_ascii_lines(spec))


def _ascii_lines(spec: Specification[Any]) -> list[str]:
    lines = [str(spec)]
    children = list(_spec_children(spec))
    for i, child in enumerate(children):
        is_last = i == len(children) - 1
        child_lines = _ascii_lines(child)
        connector = "└── " if is_last else "├── "
        continuation = "    " if is_last else "│   "
        lines.append(connector + child_lines[0])
        lines.extend(continuation + line for line in child_lines[1:])
    return lines


def _spec_children(spec: Specification[Any]) -> list[Specification[Any]]:
    match spec:
        case AndSpecification(left=left, right=right):
            return [left, right]
        case OrSpecification(left=left, right=right):
            return [left, right]
        case XorSpecification(left=left, right=right):
            return [left, right]
        case NotSpecification(spec=inner):
            return [inner]
        case _:
            return []
