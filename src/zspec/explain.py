"""Explain and visualize specification trees."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, override

from zspec.specification import (
    AndSpecification,
    NotSpecification,
    OrSpecification,
    Specification,
    XorSpecification,
)


@dataclass
class ExplainNode:
    """Result of a specification check on a candidate.

    The ``__str__`` renders a tree with PASS / FAIL markers::

        AND FAIL
        ├── InStock PASS
        └── price >= 100 FAIL
    """

    passed: bool
    spec: str
    children: list[ExplainNode] = field(default_factory=list)

    @override
    def __str__(self) -> str:
        """Return an ASCII tree with PASS / FAIL for each node."""
        return "\n".join(
            _render_tree(
                self,
                label=lambda n: f"{n.spec} {'PASS' if n.passed else 'FAIL'}",
                children=lambda n: n.children,
            ),
        )


def explain(spec: Specification[Any], candidate: object) -> ExplainNode:
    """Evaluate *spec* against *candidate* and return a result tree.

    Each leaf specification produces a node with no children.
    Composite specifications (AND, OR, NOT, XOR) produce nodes
    with children for each sub-specification.

    Usage::

        print(explain(eligible, product))
        # AND FAIL
        # ├── InStock PASS
        # └── price >= 100 FAIL
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
    return "\n".join(
        _render_tree(spec, label=str, children=_spec_children),
    )


def _render_tree[T](
    root: T,
    *,
    label: Callable[[T], str],
    children: Callable[[T], list[T]],
) -> list[str]:
    """Render *root* as an ASCII tree, one string per line."""
    lines = [label(root)]
    kids = children(root)
    for i, child in enumerate(kids):
        is_last = i == len(kids) - 1
        child_lines = _render_tree(child, label=label, children=children)
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
