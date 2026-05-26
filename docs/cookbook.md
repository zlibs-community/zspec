# Cookbook

## Filter a collection

**Without zspec** — inline condition, not reusable:

```python
expensive = [p for p in products if p.price > 100 and p.in_stock]
```

**With zspec** — one spec, used everywhere:

```python
eligible = InStock() & MinPrice(100)
expensive = list(eligible.filter(products))
```

Works on generators too — memory-efficient for large datasets:

```python
first = next(eligible.filter(stream), None)
```

## Build rules from config

Store business rules in JSON. Add new rules without touching code:

```python
import json
from zspec import to_dict, from_dict

# Save
with open("rules.json", "w") as f:
    json.dump(to_dict(InStock() & MinPrice(100)), f)

# Load — weeks later
data = json.load(open("rules.json"))
spec = from_dict(data)
results = list(spec.filter(products))
```

## Conditional composition

Build a spec dynamically based on user input:

```python
spec = Specification.true()

if filters.get("min_price"):
    spec = spec & MinPrice(filters["min_price"])
if filters.get("in_stock_only"):
    spec = spec & InStock()

results = list(spec.filter(products))
```

`spec.true()` is a neutral starting point — `spec & A` when `spec` is `true()` just returns `A`.

## Debug a failing rule

Use `explain()` to see WHY a candidate was rejected:

```python
from zspec import explain

print(explain(eligible, product))
# AND FAIL
# ├── InStock PASS
# └── price >= 100 FAIL
```

Or visualize the spec structure itself:

```python
from zspec import to_ascii

print(to_ascii(eligible))
# AND
# ├── InStock
# └── price >= 100
```

## Validate in a service layer

Raise an error with a readable message when business rules fail:

```python
def ship(order: Order) -> None:
    if not eligible(order):
        raise ValueError(f"Order not eligible:\n{explain(eligible, order)}")
    # ... proceed with shipping
```

## Translate to database queries

One spec — filter in memory AND in the database. Translators produce
filter fragments, you control joins and projections:

```python
# In-memory
eligible.is_satisfied_by(product)

# Same spec → SQL WHERE clause
fragment = SqlTranslator().translate(eligible)
cursor.execute(
    f"SELECT * FROM products WHERE {fragment.sql}",
    fragment.params,
)

# Same spec → MongoDB $match
collection.find(MongoTranslator().translate(eligible))

# Same spec → Django Q
Product.objects.filter(DjangoQTranslator().translate(eligible))

# Same spec → Polars / Pandas filter
df.filter(PolarsTranslator().translate(eligible))
df.query(PandasTranslator().translate(eligible))
```

## Negate a set of rules

Exclude anything that matches, accept everything else:

```python
# Accept all products EXCEPT those that are too expensive and out of stock
valid = Specification[Product].excluding(
    price__gt=1000,
    in_stock=False,
)
```

## Quick field comparisons

Skip the subclass boilerplate for simple attribute checks:

```python
# Instead of writing a MinPrice class
eligible = Specification[Product].matching(
    price__gte=100,     # price >= 100
    in_stock=True,       # in_stock == True
)

# With field proxies for type-safe comparisons
F = fields(Product)
eligible = Specification[Product].matching(
    F.price >= 100,
    F.in_stock == True,
)

# With lambda predicates
eligible = Specification[Product].matching(
    lambda p: p.price >= 100,
    lambda p: p.in_stock,
)
```

## Equality and deduplication

Specs support `==` and `hash` — use them in sets and dicts:

```python
seen: set[Specification] = set()
if eligible not in seen:
    seen.add(eligible)
    # expensive operation, cached per spec
    cache[eligible] = list(eligible.filter(products))
```
