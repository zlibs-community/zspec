# ZSpec

Composable specification pattern for Python 3.14+.

Define business rules as objects, then combine them with `&`, `|`, `^`, `~` to express complex logic.

[Get Started :material-arrow-right:](usage.md){ .md-button }
[GitHub :fontawesome-brands-github:](https://github.com/oek1ng/zspec){ .md-button }

## The problem

Business rules tend to spread across your codebase. A check like *"is this order eligible for free shipping?"* might live in a service method, duplicated in a view, slightly different in a validation layer. When requirements change, you hunt down every copy and hope you found them all.

The Specification pattern solves this by turning each rule into a single, testable object. Combine them with `&`, `|`, `^`, `~` to express complex logic without writing new classes.

## Why ZSpec?

| | |
|---|---|
| **Composable** | Combine specs with `&`, `|`, `^`, `~` — build complex rules from simple ones without new classes. |
| **Zero dependencies** | Standard library only. Optional extras for SQLAlchemy and Django. |
| **Type-safe** | Generic `Specification[T]` preserves candidate types through composition. Full pyrefly strict mode support. |

## Install

```bash
pip install zspec
```

## Five-minute example

```python
from dataclasses import dataclass
from zspec import Specification


@dataclass
class Order:
    total: int
    is_paid: bool


class Paid(Specification[Order]):
    def is_satisfied_by(self, order: Order) -> bool:
        return order.is_paid


class MinimumAmount(Specification[Order]):
    def __init__(self, amount: int) -> None:
        self.amount = amount

    def is_satisfied_by(self, order: Order) -> bool:
        return order.total >= self.amount


# Compose with &, |, ~
free_shipping = Paid() & MinimumAmount(500)

order = Order(total=600, is_paid=True)
assert free_shipping(order)
```

## Operators at a glance

| Operator | Description |
|---|---|
| `spec & other` | Both satisfied (AND) |
| `spec \| other` | At least one satisfied (OR) |
| `spec ^ other` | Exactly one satisfied (XOR) |
| `~spec` | Negation (NOT) |
| `spec(candidate)` | Shorthand for `is_satisfied_by` |
