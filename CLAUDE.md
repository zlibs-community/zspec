# zspec — AI-friendly specification library

Composable specification pattern for Python 3.12+. Turn business rules into
objects, combine them with boolean operators, translate to database queries.

## Core API

```python
from zspec import Specification, fields, explain, to_ascii
from zspec import to_dict, from_dict, CachingSpecification
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

### Caching

```python
from zspec import CachingSpecification

spec = CachingSpecification.wrap(HeavySpec(), ttl=30.0, maxsize=1024)
spec(product)          # computes on first call
spec(product)          # returns cached result for 30 seconds
spec.clear()           # invalidate cache
spec.size              # number of cached entries
```

Cached specs compose with operators, `filter`, `partition`, `count`. Thread-safe.

### Debugging

```python
print(explain(eligible, product))        # PASS/FAIL tree
print(to_ascii(eligible))                # spec structure tree
```

### Serialization

```python
json.dump(to_dict(spec), f)
spec = from_dict(json.load(f))           # auto-discovers via __init_subclass__
```

YAML and TOML work identically — load to dict, pass to `from_dict`:

```python
import tomllib                           # stdlib since 3.11
spec = from_dict(tomllib.load(open("spec.toml")))

import yaml                              # pip install pyyaml
spec = from_dict(yaml.safe_load(open("spec.yaml")))
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
| `PandasTranslator` | `str` | `zspec[pandas]` |
| `ElasticsearchTranslator` | `dict[str, Any]` | `zspec[elasticsearch]` |
| `RediSearchTranslator` | `str` | `zspec[redis]` |

### Pydantic integration

```python
from zspec.contrib.pydantic import validate

class Product(BaseModel):
    price: int
    _check_price = field_validator("price")(
        validate(MinPrice(100), message="Price is too low"),
    )
```

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
  serialize.py       # to_dict(), from_dict()
  cache.py           # CachingSpecification — TTL memoization
  log.py             # LoggingTranslator — log each translation step
  translator.py      # abstract Translator base
  translators.py     # SqlTranslator, MongoTranslator
  utils.py           # slots_of()
  contrib/
    django.py        # DjangoQTranslator
    sqlalchemy.py    # SqlAlchemyTranslator
    polars.py        # PolarsTranslator
    pandas.py        # PandasTranslator
    elasticsearch.py # ElasticsearchTranslator
    redis.py         # RediSearchTranslator
    pydantic.py      # validate() — use specs as Pydantic validators
```
