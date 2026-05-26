# Usage

## Defining a specification

Subclass `Specification[T]` and implement `is_satisfied_by`:

```python
from zspec import Specification
from dataclasses import dataclass


@dataclass
class User:
    age: int
    email_verified: bool


class Adult(Specification[User]):
    def is_satisfied_by(self, user: User) -> bool:
        return user.age >= 18
```

## Composition operators

### AND (`&`)

```python
class EmailVerified(Specification[User]):
    def is_satisfied_by(self, user: User) -> bool:
        return user.email_verified

can_register = Adult() & EmailVerified()
```

### OR (`|`)

```python
class Admin(Specification[User]):
    def is_satisfied_by(self, user: User) -> bool:
        return user.role == "admin"

class Moderator(Specification[User]):
    def is_satisfied_by(self, user: User) -> bool:
        return user.role == "moderator"

can_edit = Admin() | Moderator()
```

### NOT (`~`)

```python
class Banned(Specification[User]):
    def is_satisfied_by(self, user: User) -> bool:
        return user.banned

is_banned = Banned()
is_active = ~is_banned
```

## Bulk combinators

### `all_of`

Satisfied when **every** specification in the iterable is satisfied.
Returns `None` for an empty iterable. Pass ``default`` to avoid null checks:

```python
spec = Specification.all_of([
    Adult(),
    EmailVerified(),
])

# With a default for empty input
spec = Specification.all_of(filters, default=Specification.true())
```

### `any_of`

Satisfied when **at least one** specification in the iterable is satisfied.
Returns `None` for an empty iterable. Pass ``default`` to avoid null checks:

```python
spec = Specification.any_of([
    Admin(),
    Moderator(),
])

# With a default for empty input
spec = Specification.any_of(filters, default=Specification.false())
```

## Calling a specification

Both forms are equivalent:

```python
spec = Adult()
spec(user)          # __call__
spec.is_satisfied_by(user)  # explicit method
```

## String rendering with `str()` and `repr()`

Use `str(spec)` for a readable tree. Override `__str__` in leaf specs:

```python
from dataclasses import dataclass
from zspec import Specification


@dataclass
class Person:
    age: int


class MinAge(Specification[Person]):
    def __init__(self, age: int) -> None:
        self.age = age

    def is_satisfied_by(self, candidate: Person) -> bool:
        return candidate.age >= self.age

    def __str__(self) -> str:
        return f"age >= {self.age}"


spec = MinAge(18) & MinAge(21)
print(str(spec))   # (age >= 18 AND age >= 21)
print(repr(spec))  # AndSpecification(left=MinAge(age=18), right=MinAge(age=21))
```

## Quick factory: `Specification.of()`

For simple checks, skip the subclass boilerplate:

```python
adult = Specification.of(lambda u: u.age >= 18)
active = Specification.of(lambda u: u.is_active)

# fully composable
eligible = adult & active
```

The lambda name is preserved in `repr()`.

## Attribute factory: `Specification.matching()`

Generate a specification directly from field comparisons and predicates:

```python
from dataclasses import dataclass
from zspec import Specification, fields


@dataclass
class Product:
    price: int
    in_stock: bool


class InStock(Specification[Product]):
    def is_satisfied_by(self, p: Product) -> bool:
        return p.in_stock


class MinPrice(Specification[Product]):
    def __init__(self, threshold: int) -> None:
        self.threshold = threshold

    def is_satisfied_by(self, p: Product) -> bool:
        return p.price >= self.threshold


F = fields(Product)

# Field proxies with comparison operators
spec = Specification[Product].matching(
    F.price >= 100,
    F.in_stock == True,
)

# Keyword arguments with operator suffixes
spec = Specification[Product].matching(price__gte=100, in_stock=True)

# Lambda predicates
spec = Specification[Product].matching(
    lambda p: p.price > 100,
    lambda p: p.in_stock,
)

# Mix and match
spec = Specification[Product].matching(
    F.price >= 100,
    lambda p: p.in_stock,
    in_stock=True,
)
```

### Field proxies via `fields()`

`fields(Model)` returns a namespace where each attribute access produces a
proxy that overloads comparison operators:

```python
F = fields(Product)
F.price >= 100         # Specification[Product]
F.price != 200         # Specification[Product]
F.in_stock == True     # Specification[Product]
```

These are composable directly:

```python
spec = (F.price >= 100) & (F.in_stock == True)
```

### Keyword operator suffixes

Append `__op` to the field name. A bare field name defaults to `eq`:

| Suffix | Meaning |
|--------|---------|
| *(no suffix)* | `==` |
| `__eq` | `==` |
| `__ne` | `!=` |
| `__gt` | `>` |
| `__gte` | `>=` |
| `__lt` | `<` |
| `__lte` | `<=` |

### Combining with operators

`matching()` returns a full specification — use `&`, `|`, `~` as usual:

```python
cheap = Specification[Product].matching(price__lt=50)
bargain = cheap & F.in_stock
```

## Negation factory: `Specification.excluding()`

Inverse of :meth:`~zspec.Specification.matching` — exclude anything that matches:

```python
# Exclude products that are too expensive or out of stock
available = Specification[Product].excluding(
    price__gt=1000,
    in_stock=False,
)
```

Empty ``excluding()`` returns ``true()`` (nothing excluded = accept everything).

## Serialization: `to_dict` / `from_dict`

Convert specification trees to plain dictionaries and back:

```python
from zspec import to_dict, from_dict

# Serialize
spec = Specification[Product].matching(price__gte=100, in_stock=True)
data = to_dict(spec)
# {
#     "type": "AndSpecification",
#     "left": {"type": "FieldSpec", "field": "price", "op": "gte", "value": 100},
#     "right": {"type": "FieldSpec", "field": "in_stock", "op": "eq", "value": True},
# }

# Deserialize — identical spec, identical behavior
spec2 = from_dict(data)
assert spec == spec2
```

### Registering custom specs

Decorate your ``Specification`` subclasses with :func:`~zspec.registered`
to make them auto-discoverable by ``from_dict``:

```python
from zspec import registered

@registered
class InStock(Specification[Product]):
    ...

@registered
class MinPrice(Specification[Product]):
    ...

# No registry dict needed
spec = from_dict({"type": "MinPrice", "threshold": 100})
```

Pass a ``registry`` dict only when the class name in JSON
differs from the Python class name.

### Use case: rules stored as data

When rules live in a config file or database, serialize them so
they can be loaded and applied at runtime:

```python
import json
from zspec import to_dict, from_dict

# Save a rule
rule = InStock() & MinPrice(100)
with open("rules/eligible.json", "w") as f:
    json.dump(to_dict(rule), f)

# Load and apply — months later, without touching code
data = json.load(open("rules/eligible.json"))
spec = from_dict(data)
results = list(spec.filter(products))
```

## XOR (`^`)

Satisfied when **exactly one** of two specifications is true:

```python
either_or = Admin() ^ Moderator()
# true only if one role matches, false if both or neither
```

## Filtering collections

Use `spec.filter(iterable)` for lazy, memory-efficient filtering:

```python
even = Specification.of(lambda x: x % 2 == 0)
list(even.filter([1, 2, 3, 4]))  # [2, 4]

# works with generators
result = even.filter(range(10**6))
next(result)  # 0 — only evaluates one element at a time
```

## Rejecting candidates

`reject()` is the inverse of `filter()` — yield only non-matching candidates:

```python
even = Specification.of(lambda x: x % 2 == 0)
list(even.reject([1, 2, 3, 4]))  # [1, 3]
```

Lazy, works with large iterables.

## Partitioning collections

`partition()` splits an iterable into `(passed, failed)` in one pass:

```python
even = Specification.of(lambda x: x % 2 == 0)
passed, failed = even.partition([1, 2, 3, 4])
# passed = [2, 4], failed = [1, 3]
```

## Constant specifications

`Specification.true()` and `Specification.false()` for dynamic composition:

```python
spec = Specification[Product].true()  # neutral start
if min_price is not None:
    spec = spec & Specification[Product].matching(price__gte=min_price)
if in_stock_only:
    spec = spec & Specification[Product].matching(in_stock=True)
```

These constants are singletons — `Specification.true() is Specification.true()`.
They fold away during composition so your spec trees stay clean:

| Expression | Simplifies to |
|------------|---------------|
| `spec & true()` | `spec` |
| `spec \| false()` | `spec` |
| `~true()` | `false()` |
| `~~spec` | `spec` |

This means translators never see constant nodes — they only process your
actual business rules.

## Equality and hashing

Specifications compare by type and slot values:

```python
MinPrice(100) == MinPrice(100)   # True
MinPrice(100) == MinPrice(200)   # False
```

Composite specs compare recursively:

```python
a = InStock() & MinPrice(100)
b = InStock() & MinPrice(100)
assert a == b
assert hash(a) == hash(b)
```

This means specs work in sets and as dict keys:

```python
seen: set[Specification[Product]] = {InStock(), MinPrice(100)}
unique = list({InStock(), InStock(), MinPrice(100)})  # 2 items
```

## Debugging with `explain()`

Use `explain(spec, candidate)` to see **why** a specification passed or failed:

```python
from zspec import explain

result = explain(Adult() & EmailVerified(), user)
print(result.passed)   # False
for child in result.children:
    print(child.spec, child.passed)
# Adult True
# EmailVerified False
```

Returns an `ExplainNode` tree with `passed`, `spec`, and `children` fields.

## Type safety

`Specification[T]` preserves the candidate type through composition:

```python
user_spec: Specification[User] = Adult() & EmailVerified()
# ^^ User preserved

product_spec: Specification[Product] = InStock() & MinPrice(100)
# ^^ Product preserved
```

## Nested composition

Operators work on any specification, including composed ones:

```python
complex_spec = (Adult() & EmailVerified()) | Admin()
# equivalent to: (Adult AND EmailVerified) OR Admin
```
