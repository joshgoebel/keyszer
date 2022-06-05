from ..key import Key
from enum import Enum, unique, IntEnum

@unique
class Modifier(Enum):

    L_CONTROL, R_CONTROL, CONTROL, \
        L_ALT, R_ALT, ALT, \
        L_SHIFT, R_SHIFT, SHIFT, \
        L_SUPER, R_SUPER, SUPER = range(12)

    @classmethod
    def _get_modifier_map(cls):
        return {
            cls.L_CONTROL: [Key.LEFT_CTRL],
            cls.R_CONTROL: [Key.RIGHT_CTRL],
            cls.CONTROL: [Key.LEFT_CTRL, Key.RIGHT_CTRL],
            cls.L_ALT: [Key.LEFT_ALT],
            cls.R_ALT: [Key.RIGHT_ALT],
            cls.ALT: [Key.LEFT_ALT, Key.RIGHT_ALT],
            cls.L_SHIFT: [Key.LEFT_SHIFT],
            cls.R_SHIFT: [Key.RIGHT_SHIFT],
            cls.SHIFT: [Key.LEFT_SHIFT, Key.RIGHT_SHIFT],
            cls.L_SUPER: [Key.LEFT_META],
            cls.R_SUPER: [Key.RIGHT_META],
            cls.SUPER: [Key.LEFT_META, Key.RIGHT_META],
        }

    def __str__(self):
        to_str = {
            self.L_CONTROL: "LC",
            self.R_CONTROL: "RC",
            self.CONTROL: "C",
            self.L_ALT: "LAlt",
            self.R_ALT: "RAlt",
            self.ALT: "Alt",
            self.L_SHIFT: "LShift",
            self.R_SHIFT: "RShift",
            self.SHIFT: "Shift",
            self.L_SUPER: "LSuper",
            self.R_SUPER: "RSuper",
            self.SUPER: "Super"
        }
        return to_str.get(self)

    def is_specified(self):
        prefix = self.name[0:2]
        return prefix == "L_" or prefix == "R_"

    def to_left(self):
        try:
            return Modifier["L_" + self.name]
        except KeyError:
            return None

    def to_right(self):
        try:
            return Modifier["R_" + self.name]
        except KeyError:
            return None

    def get_keys(self):
        return self._get_modifier_map()[self]

    def get_key(self):
        return next(iter(self.get_keys()))

    @classmethod
    def get_all_keys(cls):
        return {key for keys in cls._get_modifier_map().values() for key in keys}

    @staticmethod
    def from_key(key):
        key_to_modifier = {
            Key.LEFT_CTRL: Modifier.L_CONTROL, 
            Key.RIGHT_CTRL: Modifier.R_CONTROL,
            Key.LEFT_ALT: Modifier.L_ALT,
            Key.RIGHT_ALT: Modifier.R_ALT,
            Key.LEFT_SHIFT: Modifier.L_SHIFT,
            Key.RIGHT_SHIFT: Modifier.R_SHIFT,
            Key.LEFT_META: Modifier.L_SUPER,
            Key.RIGHT_META: Modifier.R_SUPER
        }
        return key_to_modifier.get(key)

