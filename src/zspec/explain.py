"""Explain why a candidate did or did not satisfy a specification."""


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
