# ZSpec

Паттерн Спецификация для Python 3.14+.

Определяйте бизнес-правила как объекты и комбинируйте их через `&`, `|`, `~` для выражения сложной логики.

[Быстрый старт :material-arrow-right:](usage.md){ .md-button }
[GitHub :fontawesome-brands-github:](https://github.com/oek1ng/zspec){ .md-button }

## Почему ZSpec?

| | |
|---|---|
| **Композиция** | Комбинируйте спецификации через `&`, `|`, `^`, `~` — сложные правила из простых, без новых классов. |
| **Без зависимостей** | Только стандартная библиотека. Опциональные расширения для SQLAlchemy и Django. |
| **Типобезопасность** | `Specification[T]` сохраняет тип кандидата при композиции. Полная поддержка pyrefly strict mode. |

## Установка

```bash
pip install zspec
```

## Пример за пять минут

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


# Композиция
free_shipping = Paid() & MinimumAmount(500)

order = Order(total=600, is_paid=True)
assert free_shipping(order)
```

## Операторы

| Оператор | Описание |
|---|---|
| `spec & other` | Оба истинны (И) |
| `spec \| other` | Хотя бы одно истинно (ИЛИ) |
| `spec ^ other` | Ровно одно истинно (XOR) |
| `~spec` | Отрицание (НЕ) |
| `spec(candidate)` | Сокращение для `is_satisfied_by` |
