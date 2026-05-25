# Translator

A visitor that walks a specification tree and translates it into another form — SQL, JSON, or anything else.

For human-readable rendering, use `str(spec)` and `repr(spec)` directly on specifications.

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

### String rendering with `str()` and `repr()`

Use `str(spec)` for a readable tree representation. Override `__str__` in leaf specifications to customize:

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

## Writing a custom translator

Subclass `Translator[TResult]` and implement four methods:

| Method | Purpose |
|---|---|
| `_translate(spec)` | Convert a leaf specification to TResult |
| `_and(left, right)` | Combine two results with AND |
| `_or(left, right)` | Combine two results with OR |
| `_not(operand)` | Negate a result |
