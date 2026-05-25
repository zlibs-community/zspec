# ZSpec

Composable specification pattern for Python 3.14+.

Define business rules as objects, then combine them with `&` (and), `|` (or), and `~` (not).

## The problem

Business rules tend to spread across your codebase. A check like *"is this order eligible for free shipping?"* might live in a service method, duplicated in a view, slightly different in a validation layer. When requirements change, you hunt down every copy and hope you found them all.

The Specification pattern solves this by turning each rule into a single, testable object. Combine them with `&`, `|`, `~` to express complex logic without writing new classes.

## Why?

The Specification pattern lets you:

- **Reuse** business rules across the codebase
- **Combine** simple rules into complex ones without writing new classes
- **Test** rules in isolation
- **Keep** domain logic out of your models

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
    items_count: int


class Paid(Specification[Order]):
    def is_satisfied_by(self, order: Order) -> bool:
        return order.is_paid


class MinimumAmount(Specification[Order]):
    def __init__(self, amount: int) -> None:
        self.amount = amount

    def is_satisfied_by(self, order: Order) -> bool:
        return order.total >= self.amount


# Compose
free_shipping = Paid() & MinimumAmount(500)

order = Order(total=600, is_paid=True, items_count=3)
assert free_shipping(order)  # callable
assert free_shipping.is_satisfied_by(order)  # explicit
```
