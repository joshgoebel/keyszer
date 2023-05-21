import itertools
import re
import string
import sys
import time
import os
import inspect
from inspect import signature
from pprint import pformat as ppf
from pprint import pprint as pp

from .lib.logger import error, debug
from .lib import window_context
from .models.action import Action
from .models.combo import Combo, ComboHint
from .models.trigger import Trigger
from .models.key import Key, ASCII_TO_KEY
from .models.keymap import Keymap
from .models.modifier import Modifier
from .models.modmap import Modmap, MultiModmap

# GLOBALS
bind = ComboHint.BIND
escape_next_key = ComboHint.ESCAPE_NEXT
ignore_key = ComboHint.IGNORE

immediately = Trigger.IMMEDIATELY

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
    "post_combo": 0.5,
}

# multipurpose timeout
_TIMEOUTS = TIMEOUT_DEFAULTS


_ENVIRON = {
        'session_type'  : 'x11',
        'wl_desktop_env': None
}


# make window_context provider classes self-documenting
def get_all_supported_environments():
    supported_environments = []

    # Get all classes in the window context module
    all_classes = inspect.getmembers(window_context, inspect.isclass)

    # Iterate through each class
    for name, obj in all_classes:
        # If the class is a subclass of WindowContextProviderInterface
        # (but not the base class itself)
        if (issubclass(obj, window_context.WindowContextProviderInterface) and 
            obj is not window_context.WindowContextProviderInterface):
            # Add the environments that this provider supports to the list
            supported_environments.extend(obj.get_supported_environments())

    # debug(f'get_all_supported_environments: {supported_environments = }')
    return supported_environments


def environ_api(session_type='x11', wl_desktop_env=None):
    """
    API function to specify the session type (X11/Xorg or Wayland)
    and if Wayland, which desktop environment, to be used to try 
    to instantiate the correct window context provider object.

    Default session type is 'x11' for backwards compatibility
    with existing configs not using the API.
    """

    # reset wl_desktop_env to None if session is X11/Xorg
    # desktop only relevant for Wayland session
    if session_type == 'x11':
        wl_desktop_env = None

    # disregard any capitalization mistakes by user
    if isinstance(session_type, str):
        session_type = session_type.casefold()
    if isinstance(wl_desktop_env, str):
        wl_desktop_env = wl_desktop_env.casefold()

    # Get the currently supported environments
    supported_environments = get_all_supported_environments()

    # Construct the environment tuple based on the provided values
    provided_environment_tup = (session_type, wl_desktop_env)

    if provided_environment_tup not in supported_environments:
        error(f'Unsupported environment: Session type: {session_type}, Desktop env: {wl_desktop_env}')
        debug(f"Supported environments for keyszer: ('session_type', 'desktop_env')\n\t" +
                '\n\t'.join(ppf(item) for item in supported_environments) + '\n')
        sys.exit(1)

    _ENVIRON.update({
        'session_type': session_type,
        'wl_desktop_env' : wl_desktop_env
    })
    debug(f"ENVIRON: Session type: '{session_type}', Desktop env: '{wl_desktop_env}'")


# global dict of delay values used to mitigate Unicode entry sequence and macro or combo failures
THROTTLE_DELAY_DEFAULTS = {
    'key_pre_delay_ms': 0,
    'key_post_delay_ms': 0,
}
_THROTTLES = THROTTLE_DELAY_DEFAULTS


def clamp(num, min_value, max_value):
    return max(min(num, max_value), min_value)


def throttle_delays(key_pre_delay_ms=0, key_post_delay_ms=0):
    ms_min, ms_max = 0.0, 150.0
    if any([not(ms_min <= e <= ms_max) for e in [key_pre_delay_ms, key_post_delay_ms]]):
        error(f'Throttle delay value out of range. Clamping to valid range: {ms_min} to {ms_max}.')
    _THROTTLES.update({ 'key_pre_delay_ms' : clamp(key_pre_delay_ms, ms_min, ms_max), 
                        'key_post_delay_ms': clamp(key_post_delay_ms, ms_min, ms_max) })
    debug(  f'THROTTLES: Pre-key: {_THROTTLES["key_pre_delay_ms"]}ms, '
            f'Post-key: {_THROTTLES["key_post_delay_ms"]}ms')


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
    default = [mm for mm in _MODMAPS if not mm.conditional] or [
        Modmap("default", {})
    ]
    if len(default) > 1:
        error(
            "You may only have a single default (non-conditional modmap),"
            f"you have {len(default)} currently."
        )
        sys.exit(0)
    _MODMAPS = default + conditionals

    # setup multi-modmaps
    conditionals = [mm for mm in _MULTI_MODMAPS if mm.conditional]
    default = [mm for mm in _MULTI_MODMAPS if not mm.conditional] or [
        MultiModmap("default", {})
    ]
    if len(default) > 1:
        error(
            "You may only have a single default (non-conditional multi-modmap),"
            f" you have {len(default)} currently."
        )
        sys.exit(0)
    _MULTI_MODMAPS = default + conditionals

    return (_MODMAPS, _MULTI_MODMAPS, _KEYMAPS, _TIMEOUTS)


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


class CharacterNotSupported(Exception):
    pass


class TypingTooLong(Exception):
    pass


class UnicodeNumberToolarge(Exception):
    pass


def to_US_keystrokes(s):
    """
    Turn alphanumeric string (with spaces and some ASCII) up to length 
    of 100 characters into keystroke commands

    Warn: Almost certainly not going to work with non-US keymaps.
    """
    if len(s) > 100:
        raise TypingTooLong("`to_keystrokes` only supports strings of 100 characters or less")
    def _to_keystrokes(ctx):
        combo_list = []
        for c in s:
            if ord(c) > 127:
                combo_list.append(unicode_keystrokes(ord(c)))
            elif c.isupper():
                if ctx.capslock_on: combo_list.append(combo(c))
                else: combo_list.append(combo("Shift-" + c))
            elif (str.isdigit(c)):
                combo_list.append(Key[c.upper()])
            elif (str.isalpha(c)):
                if ctx.capslock_on: combo_list.append(combo("Shift-" + c))
                else: combo_list.append(Key[c.upper()])
            elif c in ASCII_TO_KEY:
                combo_list.append(ASCII_TO_KEY[c])
            elif c in ASCII_WITH_SHIFT:
                combo_list.append(ASCII_WITH_SHIFT[c])
            else:
                raise CharacterNotSupported(f"The character {c} is not supported by `to_keystrokes` yet.")
        return combo_list

    return _to_keystrokes


def _digits(n, base):
    digits = []
    while n > 0:
        digits.insert(0, n%base)
        n //= base
    return digits


def unicode_keystrokes(n):
    """Turn Unicode number into keystroke commands"""
    if (n > 0x10ffff):
        raise UnicodeNumberToolarge(f"{hex(n)} too large for Unicode keyboard entry.")
    def _unicode_keystrokes(ctx):
        combo_list = [
            combo("Shift-Ctrl-u"),  # requires "ibus" or "fctix" as input manager?
            *[Key[hexdigit]
                for digit in _digits(n, 16)
                for hexdigit in hex(digit)[2:].upper()
                ],
            Key.ENTER,
        ]
        if ctx.capslock_on:
            combo_list.insert(0, Key.CAPSLOCK)
            combo_list.append(Key.CAPSLOCK)
        return combo_list

    return _unicode_keystrokes


def combo(exp):  # pylint: disable=invalid-name
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
    key = Key[key_str]
    return Combo(_create_modifiers_from_strings(modifier_strs), key)


# legacy helper name
K = combo
# short form for most common used helper
C = combo


def _create_modifiers_from_strings(modifier_strs):
    modifiers = []
    for modifier_str in modifier_strs:
        key = Modifier.from_alias(modifier_str)
        if key not in modifiers:
            modifiers.append(key)
    return modifiers


ASCII_WITH_SHIFT = {
    "~":    combo("Shift-Grave"),
    "!":    combo("Shift-1"),
    "@":    combo("Shift-2"),
    "#":    combo("Shift-3"),
    "$":    combo("Shift-4"),
    "%":    combo("Shift-5"),
    "^":    combo("Shift-6"),
    "&":    combo("Shift-7"),
    "*":    combo("Shift-8"),
    "(":    combo("Shift-9"),
    ")":    combo("Shift-0"),
    "_":    combo("Shift-Minus"),
    "+":    combo("Shift-Equal"),
    "{":    combo("Shift-Left_Brace"),
    "}":    combo("Shift-Right_Brace"),
    "|":    combo("Shift-Backslash"),
    ":":    combo("Shift-Semicolon"),
    "\"":   combo("Shift-Apostrophe"),
    "<":    combo("Shift-Comma"),
    ">":    combo("Shift-Dot"),
    "?":    combo("Shift-Slash")
}


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


def include(file):
    config_globals = inspect.stack()[1][0].f_globals
    dirname = os.path.dirname(config_globals["__config__"])
    name = os.path.join(dirname, file)
    with open(name, "rb") as file:
        code = file.read()
    exec(compile(code, name, "exec"), config_globals)  # nosec


def timeouts(multipurpose=1, suspend=1):
    global _TIMEOUTS
    _TIMEOUTS = {"multipurpose": multipurpose, "suspend": suspend}


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
        raise ValueError("condition must be a function or compiled regexp")

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

    if hasattr(condition, "search"):
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
        raise ValueError("condition must be a function or compiled regexp")

    return conditional(condition_fn, modmap(name, mappings))
    # _conditional_mod_map.append((condition, mod_remappings))
