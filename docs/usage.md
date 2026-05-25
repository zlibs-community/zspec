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
Returns `None` for an empty iterable.

```python
spec = Specification.all_of([
    Adult(),
    EmailVerified(),
    HasTwoFactor(),
])
```

### `any_of`

Satisfied when **at least one** specification in the iterable is satisfied.
Returns `None` for an empty iterable.

```python
spec = Specification.any_of([
    Admin(),
    Moderator(),
    Owner(),
])
```

## Calling a specification

Both forms are equivalent:

```python
spec = Adult()
spec(user)          # __call__
spec.is_satisfied_by(user)  # explicit method
```

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
