# ZSpec

Composable specification pattern for Python 3.14+.

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

## License

MIT
