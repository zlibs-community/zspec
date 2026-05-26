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

can_edit = Admin() | Moderator()
```

### NOT (`~`)

```python
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
    HasTwoFactor(),
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
    Owner(),
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

Generate a specification directly from attribute comparisons — no subclass needed:

```python
from dataclasses import dataclass
from zspec import Specification


@dataclass
class Product:
    price: int
    in_stock: bool


spec = Specification[Product].matching(price__gte=100, in_stock=True)
spec(Product(price=100, in_stock=True))   # True
spec(Product(price=50, in_stock=True))    # False
```

### Operator suffixes

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
available = Specification[Product].matching(in_stock=True)
bargain = cheap & available
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
spec = Specification.true()  # neutral start
if min_price:
    spec = spec & MinPrice(min_price)
if in_stock_only:
    spec = spec & InStock()
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
class MinPrice(Specification[Product]):
    def __init__(self, price: int) -> None:
        self.price = price

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

result = explain(adult & verified, user)
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

order_spec: Specification[Order] = Paid() & MinimumAmount(500)
# ^^ Order preserved
```

## Nested composition

Operators work on any specification, including composed ones:

```python
complex_spec = (Adult() & EmailVerified()) | Admin()
# equivalent to: (adult AND verified) OR admin
```
