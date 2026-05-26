# zspec

[![PyPI](https://img.shields.io/pypi/v/zspec)](https://pypi.org/project/zspec/)
[![Python](https://img.shields.io/pypi/pyversions/zspec)](https://pypi.org/project/zspec/)
[![CI](https://github.com/oek1ng/zspec/actions/workflows/ci.yml/badge.svg)](https://github.com/oek1ng/zspec/actions/workflows/ci.yml)
[![Docs](https://readthedocs.org/projects/zspec/badge/)](https://zspec.readthedocs.io)
[![License](https://img.shields.io/pypi/l/zspec)](https://github.com/oek1ng/zspec/blob/main/LICENSE)

Composable specification pattern for Python 3.14+.

[Documentation](https://zspec.readthedocs.io) · [PyPI](https://pypi.org/project/zspec/) · [GitHub](https://github.com/oek1ng/zspec)

## Install

```bash
pip install zspec
```

## Quick start

```python
from dataclasses import dataclass
from zspec import Specification


@dataclass
class Product:
    price: int
    in_stock: bool


# Define rules as classes
class InStock(Specification[Product]):
    def is_satisfied_by(self, p: Product) -> bool:
        return p.in_stock


class MinPrice(Specification[Product]):
    def __init__(self, threshold: int) -> None:
        self.threshold = threshold

    def is_satisfied_by(self, p: Product) -> bool:
        return p.price >= self.threshold


# Compose with &, |, ^, ~
eligible = InStock() & MinPrice(100)

product = Product(price=200, in_stock=True)
assert eligible(product)
```

Or skip the class boilerplate:

```python
# Field comparisons
spec = Specification[Product].matching(price__gte=100, in_stock=True)

# Lambda predicates
spec = Specification[Product].matching(
    lambda p: p.price > 100,
    lambda p: p.in_stock,
)
```

## Why zspec?

| | |
|---|---|
| **Composable** | `&` `\|` `^` `~` — build complex rules from simple ones without new classes |
| **Zero dependencies** | Standard library only. Optional extras for SQLAlchemy, Django, Polars, and Pandas |
| **Type-safe** | Generic `Specification[T]` preserves candidate types through composition |
| **Database translators** | One spec → SQL, MongoDB, Django Q, SQLAlchemy, Polars, or Pandas expression |
| **Serializable** | `to_dict()` / `from_dict()` — store rules in JSON configs or databases |
| **Debuggable** | `explain()` prints a PASS / FAIL tree for every node |

## Filtering collections

```python
passed = list(eligible.filter(products))   # lazy generator
failed = list(eligible.reject(products))   # inverse
passed, failed = eligible.partition(products)
count = eligible.count(products)
```

## Debugging

```python
from zspec import explain

print(explain(eligible, product))
# AND FAIL
# ├── InStock PASS
# └── price >= 100 FAIL
```

## Serialization

```python
from zspec import to_dict, from_dict, registered

@registered
class InStock(Specification[Product]):
    ...

# Save
json.dump(to_dict(InStock() & MinPrice(100)), f)

# Load — @registered specs are auto-discovered
spec = from_dict(json.load(f))
```

## Translators

One spec — query any backend:

```python
# SQL
MySql().translate(eligible)          # SqlFragment("price >= %s AND in_stock", (100, True))

# MongoDB
MyMongo().translate(eligible)        # {"$and": [{...}, {...}]}

# Django
MyDjango().translate(eligible)       # Q(price__gte=100) & Q(in_stock=True)

# SQLAlchemy
MySA().translate(eligible)           # ColumnElement[bool]

# Polars
MyPolars().translate(eligible)       # pl.Expr

# Pandas
MyPandas().translate(eligible)       # query string
```

## License

MIT
