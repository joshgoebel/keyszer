from enum import Enum, unique, IntEnum

from .key import Key
from .modifier import Modifier
from ..logger import *

@unique
class ComboHint(IntEnum):
    BIND = 1


class Combo:

    def __init__(self, modifiers, key):
        ordered_mods = None

        if isinstance(modifiers, list):
            # raise ValueError("modifiers should be a set instead of a list")
            ordered_mods = modifiers
            modifiers = set(modifiers)
        elif modifiers is None:
            modifiers = set()
        elif isinstance(modifiers, Modifier):
            modifiers = {modifiers}
        elif not isinstance(modifiers, set):
            raise ValueError("modifiers should be a set")

        if not isinstance(key, Key):
            raise ValueError("key should be a Key")

        self.ordered_mods = ordered_mods or list(modifiers)
        self.modifiers = modifiers
        self.key = key
        if len(self.modifiers) != len(self.ordered_mods):
            debug('mismatch in', self)
            debug("mods", self.modifiers)
            debug("ordered mods", self.ordered_mods)

    def __eq__(self, other):
        if isinstance(other, Combo):
            return self.modifiers == other.modifiers and self.key == other.key
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
        # TODO: preserve order of ordered_mods
        return Combo(self.modifiers | modifiers, self.key)
