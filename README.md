# ZSpec

Composable specification pattern for Python 3.14+.

## The problem

Business rules tend to spread across your codebase. A check like *"is this order eligible for free shipping?"* might live in a service method, duplicated in a view, slightly different in a validation layer. When requirements change, you hunt down every copy and hope you found them all.

The Specification pattern solves this by turning each rule into a single, testable object. Combine them with `&`, `|`, `~` to express complex logic without writing new classes.

## Installation

```bash
pip install zspec
```

## Quick start

```python
from dataclasses import dataclass
from zspec import Specification


@dataclass
class Product:
    name: str
    price: int
    in_stock: bool


# Define specifications as simple subclasses
class InStock(Specification[Product]):
    def is_satisfied_by(self, p: Product) -> bool:
        return p.in_stock


class Affordable(Specification[Product]):
    def __init__(self, max_price: int) -> None:
        self.max_price = max_price

    def is_satisfied_by(self, p: Product) -> bool:
        return p.price <= self.max_price


# Compose with &, |, ~
in_stock = InStock()
reasonable = Affordable(max_price=1000)
eligible = in_stock & reasonable

product = Product(name="Laptop", price=800, in_stock=True)
assert eligible(product)  # True -- callable directly
assert eligible.is_satisfied_by(product)  # same thing
```

## Features

- **Composable** --- combine specs with `&` (and), `|` (or), `~` (not)
- **Type-safe** --- generic `Specification[T]` preserves the candidate type
- **Bulk combinators** --- `Specification.all_of(...)` and `Specification.any_of(...)`
- **Zero dependencies** --- standard library only
- **Python 3.14+** --- leverages modern generics (`class Foo[T]`)

## API overview

| Method | Description |
|---|---|
| `spec & other` | Both must be satisfied (AND) |
| `spec \| other` | At least one must be satisfied (OR) |
| `~spec` | Negation (NOT) |
| `spec(candidate)` | Shorthand for `is_satisfied_by` |
| `Specification.all_of(specs)` | Reduce with AND, returns `None` for empty input |
| `Specification.any_of(specs)` | Reduce with OR, returns `None` for empty input |

## Translators

Convert specification trees to SQL, JSON, or strings:

```python
from zspec import SqlTranslator, SqlFragment, Specification


class MinPrice(Specification[Any]):
    def __init__(self, price: int) -> None:
        self.price = price

    def is_satisfied_by(self, candidate: object) -> bool:
        return True  # evaluated in DB


class MySql(SqlTranslator):
    def _translate(self, spec: Specification[Any]) -> SqlFragment:
        match spec:
            case MinPrice(price=price):
                return SqlFragment("price >= %s", (price,))
            case _:
                raise NotImplementedError


spec = MinPrice(100) & MinPrice(200)
fragment = MySql().translate(spec)
assert fragment.sql == "(price >= %s AND price >= %s)"
assert fragment.params == (100, 200)
```

## License

MIT
