"""Internal utilities for zspec."""


def slots_of(obj: object) -> list[str]:
    """Collect all ``__slots__`` entries across the MRO of *obj*."""
    slots: list[str] = []
    for c in type(obj).__mro__:
        for s in getattr(c, "__slots__", ()):
            if s not in slots:
                slots.append(s)
    return slots
