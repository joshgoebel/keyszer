import itertools
import sys
import re
import time
from inspect import signature

from .models.key import Key
from .models.action import Action
from .models.combo import Combo, ComboHint
from .models.modifier import Modifier
from .models.modmap import Modmap, MultiModmap
from .models.keymap import Keymap
from .lib.logger import error

# GLOBALS
bind = ComboHint.BIND
escape_next_key = ComboHint.ESCAPE_NEXT
ignore_key = ComboHint.IGNORE

# keycode translation
# e.g., { Key.CAPSLOCK: Key.LEFT_CTRL }
_MODMAPS = []

# multipurpose keys
# e.g, {Key.LEFT_CTRL: [Key.ESC, Key.LEFT_CTRL, Action.RELEASE]}
_MULTI_MODMAPS = []

TIMEOUT_DEFAULTS = {
    "multipurpose": 1,
    "suspend": 1,
    # TODO: not implemented yet
    "post_combo": 0.5
}

# multipurpose timeout
_TIMEOUTS = TIMEOUT_DEFAULTS

# keymaps
_KEYMAPS = []

# hotkeys for debugging
DUMP_DIAGNOSTICS_KEY = Key.F15
EMERGENCY_EJECT_KEY = Key.F16


# needed for testing teardowns
def reset_configuration():
    """reset configuration settings completely"""
    global _MODMAPS
    global _MULTI_MODMAPS
    global _KEYMAPS
    global _TIMEOUTS

    _MODMAPS = []
    _MULTI_MODMAPS = []
    _KEYMAPS = []
    _TIMEOUTS = TIMEOUT_DEFAULTS


# how transform hooks into the configuration
def get_configuration():
    """API for exporting the current configuration"""
    global _MODMAPS
    global _MULTI_MODMAPS

    # setup modmaps
    conditionals = [mm for mm in _MODMAPS if mm.conditional]
    default = [mm for mm in _MODMAPS if not mm.conditional] or \
        [Modmap("default", {})]
    if len(default) > 1:
        error(
            "You may only have a single default (non-conditional modmap),"
            f"you have {len(default)} currently.")
        sys.exit(0)
    _MODMAPS = default + conditionals

    # setup multi-modmaps
    conditionals = [mm for mm in _MULTI_MODMAPS if mm.conditional]
    default = [mm for mm in _MULTI_MODMAPS if not mm.conditional] or \
        [MultiModmap("default", {})]
    if len(default) > 1:
        error(
            "You may only have a single default (non-conditional multi-modmap),"
            f" you have {len(default)} currently.")
        sys.exit(0)
    _MULTI_MODMAPS = default + conditionals

    return (
        _MODMAPS,
        _MULTI_MODMAPS,
        _KEYMAPS,
        _TIMEOUTS
    )


# ─── HOTKEYS ─────────────────────────────────────────────────────────────────

def dump_diagnostics_key(key):
    global DUMP_DIAGNOSTICS_KEY
    if isinstance(key, Key):
        DUMP_DIAGNOSTICS_KEY = key


def emergency_eject_key(key):
    global EMERGENCY_EJECT_KEY
    if isinstance(key, Key):
        EMERGENCY_EJECT_KEY = key

# ============================================================ #
# Utility functions for keymap
# ============================================================ #


def sleep(sec):
    """Sleep sec in commands"""
    def sleeper():
        time.sleep(sec)
    return sleeper


def usleep(usec):
    """Sleep usec in commands"""
    def sleeper():
        time.sleep(usec / 1000)
    return sleeper

# ============================================================ #


def C(exp):  # pylint: disable=invalid-name
    "Helper function to specify keymap"
    modifier_strs = []
    while True:
        aliases = "|".join(Modifier.all_aliases())
        m = re.match(f"\\A({aliases})-", exp)
        if m is None:
            break
        modifier = m.group(1)
        modifier_strs.append(modifier)
        exp = re.sub(rf"\A{modifier}-", "", exp)
    key_str = exp.upper()
    key = getattr(Key, key_str)
    return Combo(_create_modifiers_from_strings(modifier_strs), key)


# legacy helper name
K = C


def _create_modifiers_from_strings(modifier_strs):
    modifiers = []
    for modifier_str in modifier_strs:
        key = Modifier.from_alias(modifier_str)
        if key not in modifiers:
            modifiers.append(key)
    return modifiers


# ─── MARKS ──────────────────────────────────────────────────────────────────


_mark_set = False


def with_mark(combo):
    if isinstance(combo, Key):
        combo = Combo(None, combo)

    def _with_mark():
        return combo.with_modifier(Modifier.SHIFT) if _mark_set else combo

    return _with_mark


def set_mark(mark_set):
    def _set_mark():
        global _mark_set
        _mark_set = mark_set
    return _set_mark


def with_or_set_mark(combo):
    if isinstance(combo, Key):
        combo = Combo(None, combo)

    def _with_or_set_mark():
        global _mark_set
        _mark_set = True
        return combo.with_modifier(Modifier.SHIFT)

    return _with_or_set_mark


# ─── STANDARD API ───────────────────────────────────────────────────────────


def timeouts(multipurpose=1, suspend=1):
    global _TIMEOUTS
    _TIMEOUTS = {
        "multipurpose": multipurpose,
        "suspend": suspend
    }


def add_modifier(name, aliases, key=None, keys=None):
    """
    Creates a new modifier and binds it to a key (or keys)

    After creation this modifier can be used in combos by using
    it's alias just like any of the built-in modifiers.

    add_modifier("HYPER", aliases = ["Hyper"], key = Key.F24)
    """
    return Modifier(name, aliases, key=key, keys=keys)


def wm_class_match(re_str):
    rgx = re.compile(re_str)

    def cond(ctx):
        return rgx.search(ctx.wm_class)
    return cond


def not_wm_class_match(re_str):
    rgx = re.compile(re_str)

    def cond(ctx):
        return not rgx.search(ctx.wm_class)
    return cond


def conditional(fn, what):
    """apply a conditional function to a keymap or modmap"""
    # TODO: check that fn is a valid conditional
    what.conditional = fn
    return what


# new API, requires name
def modmap(name, mappings, when=None):
    """Defines modmap (keycode translation)

    Example:

    define_modmap({
        Key.CAPSLOCK: Key.LEFT_CTRL
    })
    """
    mm = Modmap(name, mappings, when=when)
    _MODMAPS.append(mm)
    return mm


def multipurpose_modmap(name, mappings, when=None):
    """new API for declaring multipurpose modmaps"""
    for _, value in mappings.items():
        # TODO: why, we don't use this anywhere???
        value.append(Action.RELEASE)
    mmm = MultiModmap(name, mappings, when=when)
    _MULTI_MODMAPS.append(mmm)
    return mmm


# ─── KEYMAPS ────────────────────────────────────────────────────────────────


def keymap(name, mappings, when=None):
    """define and register a new keymap"""

    def expand(target):
        # Expand not L/R-specified modifiers
        # Suppose a nesting is not so deep
        # {K("C-a"): Key.A,
        #  K("C-b"): {
        #      K("LC-c"): Key.B,
        #      K("C-d"): Key.C}}
        # ->
        # {K("LC-a"): Key.A, K("RC-a"): Key.A,
        #  K("LC-b"): {
        #      K("LC-c"): Key.B,
        #      K("LC-d"): Key.C,
        #      K("RC-d"): Key.C},
        #  K("RC-b"): {
        #      K("LC-c"): Key.B,
        #      K("LC-d"): Key.C,
        #      K("RC-d"): Key.C}}
        if not isinstance(target, dict):
            return None
        expanded_mappings = {}
        keys_for_deletion = []
        for k, v in target.items():
            # Expand children
            expand(v)

            if isinstance(k, Combo):
                expanded_modifiers = []
                for modifier in k.modifiers:
                    if not modifier.is_specific():
                        variants = [modifier.to_left(), modifier.to_right()]
                        expanded_modifiers.append(variants)
                    else:
                        expanded_modifiers.append([modifier])

                # Create a Cartesian product of expanded modifiers
                expanded_modifier_lists = itertools.product(*expanded_modifiers)
                # Create expanded mappings
                for modifiers in expanded_modifier_lists:
                    expanded_mappings[Combo(modifiers, k.key)] = v
                keys_for_deletion.append(k)

        # Delete original keys that were expanded into expanded_mappings
        for key in keys_for_deletion:
            del target[key]
        # Merge expanded mappings into original mappings
        target.update(expanded_mappings)

    def wrap_keymap(name, mappings, depth=0):
        """convert naked dict objects into proper named keymaps"""
        if depth > 0:
            name = f"{name} (" * depth + " nested" + ")" * depth
        for k, v in mappings.items():
            if isinstance(v, dict):
                mappings[k] = wrap_keymap(name, v, depth + 1)
        return Keymap(name, mappings)

    expand(mappings)

    km = wrap_keymap(name, mappings)
    km.conditional = when
    _KEYMAPS.append(km)
    return km


# ─── OLD DEPRECATED API ─────────────────────────────────────────────────────


def define_timeout(seconds=1):
    """define timeout for suspending keys and resolving multimods"""
    global _TIMEOUTS
    _TIMEOUTS["multipurpose"] = seconds


# old API, takes name as an optional param
def define_modmap(mappings, name="anonymous modmap"):
    """old style API for defining modmaps"""
    return modmap(name, mappings)


def define_keymap(condition, mappings, name="anonymous keymap"):
    """old API for defining keymaps"""
    condition_fn = old_style_condition_to_fn(condition)
    return conditional(condition_fn, keymap(name, mappings))


def define_multipurpose_modmap(mappings):
    """Defines multipurpose modmap (multi-key translations)

    Give a key two different meanings. One when pressed and released alone and
    one when it's held down together with another key (making it a modifier
    key).

    Example:

    define_multipurpose_modmap(
        {Key.CAPSLOCK: [Key.ESC, Key.LEFT_CTRL]
    })
    """
    return multipurpose_modmap("default", mappings)


def define_conditional_multipurpose_modmap(condition, mappings):
    """Defines conditional multipurpose modmap (multi-key translation)

    Example:

    define_conditional_multipurpose_modmap(
        lambda wm_class, device_name: device_name.startswith("Microsoft"
    ), {
        {Key.CAPSLOCK: [Key.ESC, Key.LEFT_CTRL]
    })
    """
    condition_fn = old_style_condition_to_fn(condition)
    if not callable(condition_fn):
        raise ValueError('condition must be a function or compiled regexp')

    name = "anonymous multipurpose map (old API)"
    return conditional(condition_fn, multipurpose_modmap(name, mappings))


def old_style_condition_to_fn(condition):
    """converts old API style condition into a new style conditional"""
    condition_fn = None

    def re_search(regex):
        def fn(ctx):
            return regex.search(ctx.wm_class)
        return fn

    def wm_class(wm_class_fn):
        def fn(ctx):
            return wm_class_fn(ctx.wm_class)
        return fn

    def wm_class_and_device(cond_fn):
        def fn(ctx):
            return cond_fn(ctx.wm_class, ctx.device_name)
        return fn

    if hasattr(condition, 'search'):
        condition_fn = re_search(condition)
    elif callable(condition):
        if len(signature(condition).parameters) == 1:
            condition_fn = wm_class(condition)
        elif len(signature(condition).parameters) == 2:
            condition_fn = wm_class_and_device(condition)

    return condition_fn


def define_conditional_modmap(condition, mappings):
    """Defines conditional modmap (keycode translation)

    Example:

    define_conditional_modmap(re.compile(r'Emacs'), {
        Key.CAPSLOCK: Key.LEFT_CTRL
    })
    """

    condition_fn = old_style_condition_to_fn(condition)
    name = "define_conditional_modmap (old API)"

    if not callable(condition_fn):
        raise ValueError('condition must be a function or compiled regexp')

    return conditional(condition_fn, modmap(name, mappings))
    # _conditional_mod_map.append((condition, mod_remappings))
