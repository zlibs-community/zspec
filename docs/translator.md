# Translator

A visitor that walks a specification tree and translates it into another form — SQL, MongoDB filters, Django Q objects, or anything else.

## Built-in translators

### SqlTranslator

Generates parameterized SQL from a specification tree. Subclass and override `_translate` for each leaf specification:

```python
from zspec import SqlTranslator, SqlFragment, Specification


class MinAge(Specification[Any]):
    def __init__(self, age: int) -> None:
        self.age = age

    def is_satisfied_by(self, candidate: object) -> bool:
        return True  # evaluated in DB


class MySql(SqlTranslator):
    def _translate(self, spec: Specification[Any]) -> SqlFragment:
        match spec:
            case MinAge(age=age):
                return SqlFragment("age >= %s", (age,))
            case _:
                raise NotImplementedError(
                    f"Unknown spec: {type(spec).__name__}"
                )


translator = MySql()
spec = MinAge(18) & MinAge(21)
fragment = translator.translate(spec)
assert fragment.sql == "(age >= %s AND age >= %s)"
assert fragment.params == (18, 21)
```

### SqlAlchemyTranslator

Generate native SQLAlchemy expressions. Install with `pip install zspec[sqlalchemy]`, then subclass and override `_translate`:

```python
from sqlalchemy import Table, Column, Integer, Boolean, select
from zspec.contrib.sqlalchemy import SqlAlchemyTranslator

product = Table(
    "product", ...,
    Column("price", Integer),
    Column("in_stock", Boolean),
)

class MyTranslator(SqlAlchemyTranslator):
    def _translate(self, spec: Specification[Any]) -> ColumnElement[bool]:
        match spec:
            case InStock():
                return product.c.in_stock.is_(True)
            case MinPrice(min_price=price):
                return product.c.price >= price
            case _:
                raise NotImplementedError

translator = MyTranslator()
stmt = select(product).where(
    translator.translate(InStock() & MinPrice(100)),
)
```

### DjangoQTranslator

Generate Django ``Q`` objects. Install with ``pip install zspec[django]``:

```python
from django.db.models import Q
from zspec.contrib.django import DjangoQTranslator

class MyTranslator(DjangoQTranslator):
    def _translate(self, spec: Specification[Any]) -> Q:
        match spec:
            case InStock():
                return Q(in_stock=True)
            case MinPrice(min_price=price):
                return Q(price__gte=price)
            case _:
                raise NotImplementedError

translator = MyTranslator()
results = Product.objects.filter(
    translator.translate(InStock() & MinPrice(100)),
)
```

### MongoTranslator

Generate MongoDB filter documents — no extra dependencies:

```python
from zspec import MongoTranslator

class MyTranslator(MongoTranslator):
    def _translate(self, spec: Specification[Any]) -> dict[str, Any]:
        match spec:
            case InStock():
                return {"in_stock": True}
            case MinPrice(min_price=price):
                return {"price": {"$gte": price}}
            case _:
                raise NotImplementedError

translator = MyTranslator()
results = collection.find(
    translator.translate(InStock() & MinPrice(100)),
)
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
