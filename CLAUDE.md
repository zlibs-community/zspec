# zspec — AI-friendly specification library

Composable specification pattern for Python 3.14+. Turn business rules into
objects, combine them with boolean operators, translate to database queries.

## Core API

```python
from zspec import Specification, fields, explain, to_ascii
from zspec import to_dict, from_dict, registered
```

### Defining specs

```python
class InStock(Specification[Product]):
    def is_satisfied_by(self, p: Product) -> bool:
        return p.in_stock
```

### Quick factories (no subclass needed)

```python
# Keyword-based
Specification[Product].matching(price__gte=100, in_stock=True)

# Lambda predicates
Specification[Product].matching(lambda p: p.price > 100)

# Negation
Specification[Product].excluding(price__gt=1000)

# Field proxies
F = fields(Product)
Specification[Product].matching(F.price >= 100)
```

### Composition

```python
eligible = InStock() & MinPrice(100)     # AND
either = Admin() | Moderator()           # OR
exactly_one = Admin() ^ Moderator()      # XOR
not_banned = ~Banned()                   # NOT
spec = Specification.true()              # always passes
```

### Filtering

```python
list(eligible.filter(products))          # lazy generator
passed, failed = eligible.partition(products)
eligible.count(products)                 # int
```

### Debugging

```python
print(explain(eligible, product))        # PASS/FAIL tree
print(to_ascii(eligible))                # spec structure tree
```

### Serialization

```python
@registered  # auto-discovered by from_dict
class MinPrice(Specification[Product]):
    ...

json.dump(to_dict(spec), f)
spec = from_dict(json.load(f))           # no registry needed
```

### Translators

Subclass and override `_translate`. Each translator has `_and`, `_or`, `_not`, `_xor`:

| Translator | Result type | Extra |
|---|---|---|
| `SqlTranslator` | `SqlFragment` | — |
| `MongoTranslator` | `dict[str, Any]` | — |
| `DjangoQTranslator` | `Q` | `zspec[django]` |
| `SqlAlchemyTranslator` | `ColumnElement[bool]` | `zspec[sqlalchemy]` |
| `PolarsTranslator` | `pl.Expr` | `zspec[polars]` |

## Anti-patterns

- Don't use `isinstance` checks inside `is_satisfied_by` — rely on the type parameter `T`
- Don't mutate state in `is_satisfied_by` — specs are value objects
- Don't create specs with `__dict__` — use `__slots__` only (required for `__eq__`/`__hash__`)
- Use `Specification.of()` for one-liners, `matching()` for field checks, subclass for complex logic

## Type system

All specs are generic: `Specification[T]`. The `T` preserves through composition:

```python
a: Specification[User] = Adult() & EmailVerified()  # T = User
```

## Project layout

```
src/zspec/
  specification.py   # core: Specification, composites, FieldSpec, fields()
  explain.py         # explain(), to_ascii(), ExplainNode
  serialize.py       # to_dict(), from_dict(), registered()
  translator.py      # abstract Translator base
  translators.py     # SqlTranslator, MongoTranslator
  utils.py           # slots_of()
  contrib/
    django.py        # DjangoQTranslator
    sqlalchemy.py    # SqlAlchemyTranslator
    polars.py        # PolarsTranslator
```
