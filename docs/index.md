# Composable specifications for Python

Turn business rules into objects. Combine them. Reuse everywhere.

[Get Started](usage.md){ .md-button .md-button--primary }
[Cookbook](cookbook.md){ .md-button }

---

## The problem

Business rules scatter across your codebase. A check like *"is this order eligible
for free shipping?"* lives in a service, copied to a view, slightly different in
validation. When requirements change, you hunt down every copy.

**zspec** turns each rule into a single, testable object. Combine them with
`&`, `|`, `^`, `~` to express complex logic without writing new classes.

## Five minutes

```python
from dataclasses import dataclass
from zspec import Specification


@dataclass
class Order:
    total: int
    is_paid: bool


class Paid(Specification[Order]):
    def is_satisfied_by(self, order: Order) -> bool:
        return order.is_paid


class MinimumAmount(Specification[Order]):
    def __init__(self, amount: int) -> None:
        self.amount = amount

    def is_satisfied_by(self, order: Order) -> bool:
        return order.total >= self.amount


# Compose with &, |, ~
free_shipping = Paid() & MinimumAmount(500)

order = Order(total=600, is_paid=True)
assert free_shipping(order)
```

## Why zspec?

| | |
|---|---|
| :material-puzzle: **Composable** | `&` `\|` `^` `~` — build complex rules from simple ones. No new classes needed. |
| :material-package-variant-closed: **Zero dependencies** | Standard library only. Optional extras for SQLAlchemy, Django, Polars, and Pandas. |
| :material-shield-check: **Type-safe** | Generic `Specification[T]` preserves candidate types. Full pyrefly strict mode. |
| :material-database: **Database translators** | One spec → in-memory check, SQL, MongoDB, Django Q, Polars, or Pandas expression. |
| :material-file-code: **Serializable** | Serialize rules to JSON. Store in configs, databases, or send over API. |
| :material-bug: **Debuggable** | `explain()` shows which rules passed and failed — as an ASCII tree. |

## Operators

| Operator | Expression | Reads as |
|---|---|---|
| `&` | `a & b` | Both `a` AND `b` |
| <code>&#124;</code> | <code>a &#124; b</code> | At least one |
| `^` | `a ^ b` | Exactly one |
| `~` | `~a` | NOT `a` |
| `()` | `spec(c)` | `is_satisfied_by(c)` |

## What else?

```python
# One spec — filter in memory AND query databases
matches = list(eligible.filter(products))
sql = MySql().translate(eligible)
df.filter(MyPolars().translate(eligible))

# Debug why a rule failed
from zspec import explain
print(explain(eligible, order))
# AND FAIL
# ├── Paid PASS
# └── amount >= 500 FAIL

# Build specs from config files
from zspec import from_dict
spec = from_dict(json.loads(config))

# Quick field comparisons — no subclass needed
spec = Specification[Product].matching(price__gte=100, in_stock=True)
```

[:fontawesome-solid-book: Full usage guide](usage.md){ .md-button }
[:fontawesome-solid-kitchen-set: Cookbook](cookbook.md){ .md-button }
