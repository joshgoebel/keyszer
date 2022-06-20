from enum import unique, IntEnum
from collections.abc import Iterable

from .key import Key
from .modifier import Modifier
from ordered_set import OrderedSet


@unique
class ComboHint(IntEnum):
    BIND = 1
    ESCAPE_NEXT = 2
    IGNORE = 3


class Combo:

    def __init__(self, modifiers, key):
        modifiers = modifiers or []

        if isinstance(modifiers, set):
            raise ValueError("modifiers needs ordered sequence, not a set")
        if isinstance(modifiers, Iterable):
            modifiers = OrderedSet(modifiers)
        elif isinstance(modifiers, Modifier):
            modifiers = OrderedSet([modifiers])
        else:
            raise ValueError("modifiers should be Iterable")

        if not isinstance(key, Key):
            raise ValueError("key should be a Key")

        self._modifiers = modifiers
        self._key = key

    @property
    def modifiers(self):
        return self._modifiers

    @property
    def key(self):
        return self._key

    def __eq__(self, other):
        if isinstance(other, Combo):
            return set(self.modifiers) == set(other.modifiers) and \
                self.key == other.key
        else:
            return NotImplemented

    def __hash__(self):
        return hash((frozenset(self.modifiers), self.key))

    def __str__(self):
        return "-".join([str(mod) for mod in self.modifiers] + [self.key.name])

    def __repr__(self):
        return self.__str__()

    def with_modifier(self, modifiers):
        if isinstance(modifiers, Modifier):
            modifiers = {modifiers}
        return Combo(self.modifiers | modifiers, self.key)
