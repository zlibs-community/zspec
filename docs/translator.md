# Translator

A visitor that walks a specification tree and translates it into another form — SQL, MongoDB filters, Django Q objects, or anything else.

## Built-in translators

### SqlTranslator

Generates parameterized SQL from a specification tree. Subclass and override `_translate` for each leaf specification:

```python
from dataclasses import dataclass
from zspec import SqlTranslator, SqlFragment, Specification


@dataclass
class Person:
    age: int


class MinAge(Specification[Person]):
    def __init__(self, age: int) -> None:
        self.age = age

    def is_satisfied_by(self, candidate: Person) -> bool:
        return candidate.age >= self.age


class MySql(SqlTranslator):
    def _translate(self, spec: Specification[Person]) -> SqlFragment:
        match spec:
            case MinAge(age=age):
                return SqlFragment("age >= %s", (age,))
            case _:
                return super()._translate(spec)


translator = MySql()
spec = MinAge(18) & MinAge(21)
fragment = translator.translate(spec)
assert fragment.sql == "(age >= %s AND age >= %s)"
assert fragment.params == (18, 21)
```

### SqlAlchemyTranslator

Generate native SQLAlchemy expressions. Install with `pip install zspec[sqlalchemy]`, then subclass and override `_translate`:

```python
from dataclasses import dataclass
from sqlalchemy import Table, Column, Integer, Boolean, select
from zspec import Specification
from zspec.contrib.sqlalchemy import SqlAlchemyTranslator


@dataclass
class Product:
    price: int
    in_stock: bool


class InStock(Specification[Product]):
    def is_satisfied_by(self, candidate: Product) -> bool:
        return candidate.in_stock


class MinPrice(Specification[Product]):
    def __init__(self, min_price: int) -> None:
        self.min_price = min_price

    def is_satisfied_by(self, candidate: Product) -> bool:
        return candidate.price >= self.min_price


product = Table(
    "product", ...,
    Column("price", Integer),
    Column("in_stock", Boolean),
)

class MyTranslator(SqlAlchemyTranslator):
    def _translate(self, spec: Specification[Product]) -> ColumnElement[bool]:
        match spec:
            case InStock():
                return product.c.in_stock.is_(True)
            case MinPrice(min_price=price):
                return product.c.price >= price
            case _:
                return super()._translate(spec)

translator = MyTranslator()
stmt = select(product).where(
    translator.translate(InStock() & MinPrice(100)),
)
```

### DjangoQTranslator

Generate Django ``Q`` objects. Install with ``pip install zspec[django]``:

```python
from dataclasses import dataclass
from django.db.models import Q
from zspec import Specification
from zspec.contrib.django import DjangoQTranslator


@dataclass
class Product:
    price: int
    in_stock: bool


class InStock(Specification[Product]):
    def is_satisfied_by(self, candidate: Product) -> bool:
        return candidate.in_stock


class MinPrice(Specification[Product]):
    def __init__(self, min_price: int) -> None:
        self.min_price = min_price

    def is_satisfied_by(self, candidate: Product) -> bool:
        return candidate.price >= self.min_price


class MyTranslator(DjangoQTranslator):
    def _translate(self, spec: Specification[Product]) -> Q:
        match spec:
            case InStock():
                return Q(in_stock=True)
            case MinPrice(min_price=price):
                return Q(price__gte=price)
            case _:
                return super()._translate(spec)

translator = MyTranslator()
# results = Product.objects.filter(
#     translator.translate(InStock() & MinPrice(100)),
# )
```

### MongoTranslator

Generate MongoDB filter documents — no extra dependencies:

```python
from dataclasses import dataclass
from zspec import MongoTranslator, Specification


@dataclass
class Product:
    price: int
    in_stock: bool


class InStock(Specification[Product]):
    def is_satisfied_by(self, candidate: Product) -> bool:
        return candidate.in_stock


class MinPrice(Specification[Product]):
    def __init__(self, min_price: int) -> None:
        self.min_price = min_price

    def is_satisfied_by(self, candidate: Product) -> bool:
        return candidate.price >= self.min_price


class MyTranslator(MongoTranslator):
    def _translate(self, spec: Specification[Product]) -> dict[str, Any]:
        match spec:
            case InStock():
                return {"in_stock": True}
            case MinPrice(min_price=price):
                return {"price": {"$gte": price}}
            case _:
                return super()._translate(spec)

translator = MyTranslator()
# results = collection.find(
#     translator.translate(InStock() & MinPrice(100)),
# )
```

### PolarsTranslator

Generate native Polars expressions. Install with ``pip install zspec[polars]``:

```python
from dataclasses import dataclass
import polars as pl
from zspec import Specification
from zspec.contrib.polars import PolarsTranslator


@dataclass
class Product:
    price: int
    in_stock: bool


class InStock(Specification[Product]):
    def is_satisfied_by(self, candidate: Product) -> bool:
        return candidate.in_stock


class MinPrice(Specification[Product]):
    def __init__(self, min_price: int) -> None:
        self.min_price = min_price

    def is_satisfied_by(self, candidate: Product) -> bool:
        return candidate.price >= self.min_price


class MyTranslator(PolarsTranslator):
    def _translate(self, spec: Specification[Product]) -> pl.Expr:
        match spec:
            case InStock():
                return pl.col("in_stock")
            case MinPrice(min_price=price):
                return pl.col("price") >= price
            case _:
                return super()._translate(spec)

translator = MyTranslator()
df = pl.DataFrame({"price": [50, 200], "in_stock": [True, True]})
result = df.filter(translator.translate(InStock() & MinPrice(100)))
```

### PandasTranslator

Generate Pandas query strings. Install with ``pip install zspec[pandas]``:

```python
from dataclasses import dataclass
import pandas as pd
from zspec import Specification
from zspec.contrib.pandas import PandasTranslator


@dataclass
class Product:
    price: int
    in_stock: bool


class InStock(Specification[Product]):
    def is_satisfied_by(self, candidate: Product) -> bool:
        return candidate.in_stock


class MinPrice(Specification[Product]):
    def __init__(self, min_price: int) -> None:
        self.min_price = min_price

    def is_satisfied_by(self, candidate: Product) -> bool:
        return candidate.price >= self.min_price


class MyTranslator(PandasTranslator):
    def _translate(self, spec: Specification[Product]) -> str:
        match spec:
            case InStock():
                return "in_stock == True"
            case MinPrice(min_price=price):
                return f"price >= {price}"
            case _:
                return super()._translate(spec)

translator = MyTranslator()
df = pd.DataFrame({"price": [50, 200], "in_stock": [True, True]})
result = df.query(translator.translate(InStock() & MinPrice(100)))
```

## Using translators with real queries

Translators produce **filter fragments** — not full queries. Joins, projections,
and ordering stay in your control.

### SQL with JOIN

```python
fragment = MySql().translate(InStock() & Category("Books"))

query = f"""
    SELECT p.*
    FROM products p
    JOIN categories c ON p.category_id = c.id
    WHERE {fragment.sql}
"""
cursor.execute(query, fragment.params)
```

### MongoDB with `$lookup`

```python
filter_doc = MyMongo().translate(InStock() & Category("Books"))

pipeline = [
    {"$lookup": {
        "from": "categories",
        "localField": "category_id",
        "foreignField": "_id",
        "as": "category",
    }},
    {"$unwind": "$category"},
    {"$match": filter_doc},
]
collection.aggregate(pipeline)
```

### Django ORM with `select_related`

```python
q = MyDjango().translate(InStock() & Category("Books"))

Product.objects.select_related("category").filter(q)
```

### SQLAlchemy with `.join()`

```python
expr = MySA().translate(InStock() & Category("Books"))

stmt = select(Product).join(Category).where(expr)
session.execute(stmt)
```

### Pandas with pre-joined DataFrame

```python
query_str = MyPandas().translate(InStock() & Category("Books"))

df = pd.merge(products_df, categories_df, on="category_id")
result = df.query(query_str)
```

### Polars with pre-joined DataFrame

```python
expr = MyPolars().translate(InStock() & Category("Books"))

df = products_df.join(categories_df, on="category_id")
result = df.filter(expr)
```

## Writing a custom translator

Subclass `Translator[TResult]` and implement four methods:

| Method | Purpose |
|---|---|
| `_translate(spec)` | Convert a leaf specification to TResult |
| `_and(left, right)` | Combine two results with AND |
| `_or(left, right)` | Combine two results with OR |
| `_not(operand)` | Negate a result |
| `_xor(left, right)` | XOR — defaults to `(A OR B) AND NOT (A AND B)` |
