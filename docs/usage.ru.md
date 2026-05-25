# Использование

## Определение спецификации

Унаследуйтесь от `Specification[T]` и реализуйте `is_satisfied_by`:

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

## Операторы композиции

### И (`&`)

```python
class EmailVerified(Specification[User]):
    def is_satisfied_by(self, user: User) -> bool:
        return user.email_verified

can_register = Adult() & EmailVerified()
```

### ИЛИ (`|`)

```python
class Admin(Specification[User]):
    def is_satisfied_by(self, user: User) -> bool:
        return user.role == "admin"

can_edit = Admin() | Moderator()
```

### НЕ (`~`)

```python
is_banned = Banned()
is_active = ~is_banned
```

### XOR (`^`)

Истинно, когда **ровно одна** из двух спецификаций истинна:

```python
either_or = Admin() ^ Moderator()
# истинно только если одна роль совпадает, ложно если обе или ни одна
```

## Массовые комбинаторы

### `all_of`

Истинно, когда **каждая** спецификация в коллекции истинна.
Возвращает `None` для пустой коллекции.

```python
spec = Specification.all_of([
    Adult(),
    EmailVerified(),
    HasTwoFactor(),
])
```

### `any_of`

Истинно, когда **хотя бы одна** спецификация в коллекции истинна.
Возвращает `None` для пустой коллекции.

```python
spec = Specification.any_of([
    Admin(),
    Moderator(),
    Owner(),
])
```

## Вызов спецификации

Обе формы эквивалентны:

```python
spec = Adult()
spec(user)          # __call__
spec.is_satisfied_by(user)  # явный метод
```

## Строковое представление

`str(spec)` — читаемое дерево. Переопределите `__str__` в листовых спецификациях:

```python
class MinAge(Specification[Any]):
    def __init__(self, age: int) -> None:
        self.age = age

    def is_satisfied_by(self, candidate: object) -> bool:
        return True

    def __str__(self) -> str:
        return f"age >= {self.age}"


spec = MinAge(18) & MinAge(21)
print(str(spec))   # (age >= 18 AND age >= 21)
print(repr(spec))  # AndSpecification(left=MinAge(age=18), right=MinAge(age=21))
```

## Фабрика: `Specification.of()`

Для простых проверок — без boilerplate-класса:

```python
adult = Specification.of(lambda u: u.age >= 18)
active = Specification.of(lambda u: u.is_active)

# полностью совместимо с операторами
eligible = adult & active
```

## Фильтрация коллекций

`spec.filter(iterable)` — ленивая фильтрация:

```python
even = Specification.of(lambda x: x % 2 == 0)
list(even.filter([1, 2, 3, 4]))  # [2, 4]

# работает с генераторами
result = even.filter(range(10**6))
next(result)  # 0 — только один элемент за раз
```

## Отбрасывание неподходящих

`reject()` — инверсный `filter()`, возвращает только неподходящие:

```python
even = Specification.of(lambda x: x % 2 == 0)
list(even.reject([1, 2, 3, 4]))  # [1, 3]
```

## Разделение коллекций

`partition()` — за один проход делит на `(подходящие, неподходящие)`:

```python
even = Specification.of(lambda x: x % 2 == 0)
passed, failed = even.partition([1, 2, 3, 4])
# passed = [2, 4], failed = [1, 3]
```

## Константные спецификации

`Specification.true()` и `Specification.false()` — для динамической композиции:

```python
spec = Specification.true()  # нейтральный старт
if min_price:
    spec = spec & MinPrice(min_price)
if in_stock_only:
    spec = spec & InStock()
```

## Отладка с `explain()`

Используйте `explain(spec, candidate)` чтобы понять **почему** спецификация прошла или нет:

```python
from zspec import explain

result = explain(adult & verified, user)
print(result.passed)   # False
for child in result.children:
    print(child.spec, child.passed)
# Adult True
# EmailVerified False
```

Возвращает дерево `ExplainNode` с полями `passed`, `spec` и `children`.

## Типобезопасность

`Specification[T]` сохраняет тип кандидата при композиции:

```python
user_spec: Specification[User] = Adult() & EmailVerified()
# ^^ User сохранён

order_spec: Specification[Order] = Paid() & MinimumAmount(500)
# ^^ Order сохранён
```

## Вложенная композиция

Операторы работают на любых спецификациях, включая составные:

```python
complex_spec = (Adult() & EmailVerified()) | Admin()
# эквивалентно: (adult И verified) ИЛИ admin
```
