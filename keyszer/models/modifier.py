from ..key import Key

class Modifier:
    _BY_KEY = {}
    _MODIFIERS = {}
    _IDS = iter(range(100))

    def __init__(self, name, aliases, key = None, keys = None):
        cls = type(self)
        self._id = next(cls._IDS)
        self.name = name
        self.aliases = aliases
        keys = key or keys
        if isinstance(keys, Key):
            keys = [keys]
        self.keys = keys
        # TODO: prevent duplicates
        if len(self.keys) == 1:
            cls._BY_KEY[self.keys[0]] = self
        cls._MODIFIERS[name] = self
        setattr(Modifier, name, self)

    def __str__(self):
        return self.aliases[0]

    def __eq__(self, other):
        return self._id == other._id
    
    def __hash__(self):
        return self._id

    def is_specified(self):
        prefix = self.name[0:2]
        return prefix == "L_" or prefix == "R_"

    def get_keys(self):
        return self.keys

    def get_key(self):
        return self.keys[0]

    def to_left(self):
        try:
            return getattr(Modifier,"L_" + self.name)
        except AttributeError:
            return None

    def to_right(self):
        try:
            return getattr(Modifier,"R_" + self.name)
        except AttributeError:
            return None

    @classmethod
    def get_all_keys(cls):
        return cls._BY_KEY.keys()

    @classmethod
    def from_key(cls, key):
        return cls._BY_KEY[key]

    @classmethod
    def all_aliases(cls):
        mods = cls._MODIFIERS.values()
        return [alias for mod in mods for alias in mod.aliases]
    
    @classmethod
    def from_alias(cls, alias):
        for mod in cls._MODIFIERS.values():
            if alias in mod.aliases:
                return mod
        return None


# create all the default modifiers we ship with
Modifier("R_CONTROL", aliases = ["RCtrl", "RC"], key = Key.RIGHT_CTRL)
Modifier("L_CONTROL", aliases = ["LCtrl", "LC"], key = Key.LEFT_CTRL)
Modifier("CONTROL", aliases = ["Ctrl", "C"], keys = [Key.LEFT_CTRL, Key.RIGHT_CTRL])
Modifier("R_ALT", aliases = ["RAlt", "RM"], key = Key.RIGHT_ALT)
Modifier("L_ALT", aliases = ["LAlt", "LM"], key = Key.LEFT_ALT)
Modifier("ALT", aliases = ["Alt", "M"], keys = [Key.LEFT_ALT, Key.RIGHT_ALT])
Modifier("R_SHIFT", aliases = ["RShift"], key = Key.RIGHT_SHIFT)
Modifier("L_SHIFT", aliases = ["LShift"], key = Key.LEFT_SHIFT)
Modifier("SHIFT", aliases = ["Shift"], keys = [Key.LEFT_SHIFT, Key.RIGHT_SHIFT])
Modifier("R_SUPER", aliases = ["RSuper", "RWin"], key = Key.RIGHT_META)
Modifier("L_SUPER", aliases = ["LSuper", "LWin"], key = Key.LEFT_META)
Modifier("SUPER", aliases = ["Super", "Win"], keys = [Key.LEFT_META, Key.RIGHT_META])







