# Translator

Visitor, обходящий дерево спецификаций и преобразующий его в другую форму — SQL, фильтры MongoDB, Django Q-объекты и всё остальное.

## Встроенные трансляторы

### SqlTranslator

Генерирует параметризованный SQL из дерева спецификаций. Унаследуйтесь и переопределите `_translate` для каждого типа спецификации:

```python
from zspec import SqlTranslator, SqlFragment, Specification


class MinAge(Specification[Any]):
    def __init__(self, age: int) -> None:
        self.age = age

    def is_satisfied_by(self, candidate: object) -> bool:
        return True  # вычисляется в БД


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

Генерирует нативные SQLAlchemy-выражения. Установка: `pip install zspec[sqlalchemy]`:

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

Генерирует Django ``Q``-объекты. Установка: ``pip install zspec[django]``:

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

Генерирует фильтры MongoDB — без дополнительных зависимостей:

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

## Свой транслятор

Унаследуйтесь от `Translator[TResult]` и реализуйте четыре метода:

| Метод | Назначение |
|---|---|
| `_translate(spec)` | Преобразовать листовую спецификацию в TResult |
| `_and(left, right)` | Скомбинировать два результата через И |
| `_or(left, right)` | Скомбинировать два результата через ИЛИ |
| `_not(operand)` | Отрицание результата |
| `_xor(left, right)` | XOR — по умолчанию `(A OR B) AND NOT (A AND B)` |
