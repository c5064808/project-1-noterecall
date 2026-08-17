# Dataclasses, frozen and otherwise

`@dataclass` writes `__init__`, `__repr__` and `__eq__` from the annotated class
attributes. That is most of what I would have typed by hand and all of what I would have
got subtly wrong.

`frozen=True` blocks attribute assignment after construction and gives the class a
`__hash__`, so instances can go in sets and be dictionary keys. For record types that pass
between modules, freezing them means I never have to wonder whether a function quietly
mutated the thing I handed it. Everything in this project that represents a note, a chunk
or a search hit is frozen.

The mutable default trap:

```python
@dataclass
class Note:
    tags: list[str] = []          # TypeError at class definition time
    tags: list[str] = field(default_factory=list)   # this is the one
```

Python catches the list case for you, which is kinder than the equivalent bug in a plain
function signature where it silently shares one list across every call.

`slots=True` from 3.10 drops the instance `__dict__`. Less memory, faster attribute
access, but it breaks anything that assigns unexpected attributes and it interacts badly
with multiple inheritance. Not needed at our scale.

`order=True` adds comparison operators based on field order. Convenient and dangerous:
the ordering is by the tuple of all fields in declaration order, so adding a field at the
top silently changes how everything sorts. I prefer an explicit `key=` in the sort call.

When not to use one. If the type has behaviour rather than data, write a normal class. If
it is a bag of configuration read from the environment, a frozen dataclass is exactly
right, and building it in one place makes it obvious what the program can be configured
with. `NamedTuple` is the lighter alternative but it is still a tuple, so it unpacks and
compares in ways that occasionally surprise a reader.
