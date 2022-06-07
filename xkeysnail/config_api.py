import itertools

from .key import Key 
from .models.action import Action
from .models.combo import Combo
from .models.modifier import Modifier
from .lib.modmap import Modmap, MultiModmap
from .lib.keymap import Keymap
from sys import exit
from inspect import signature
from .logger import *

# GLOBALS

escape_next_key = {}
pass_through_key = {}
ignore_key = {}

# keycode translation
# e.g., { Key.CAPSLOCK: Key.LEFT_CTRL }
_modmaps = []

# multipurpose keys
# e.g, {Key.LEFT_CTRL: [Key.ESC, Key.LEFT_CTRL, Action.RELEASE]}
_multi_modmaps = []

# multipurpose timeout
_timeout = 1

# keymaps
_toplevel_keymaps = []


# needed for testing teardowns
def reset_configuration():
    global _modmaps
    global _multi_modmaps
    global _toplevel_keymaps
    global _timeout

    _modmaps = []
    _multi_modmaps = []
    _toplevel_keymaps = []
    _timeout = 1

# how transform hooks into the configuration
def get_configuration():
    global _modmaps
    global _multi_modmaps

    # setup modmaps
    conditional = [mm for mm in _modmaps if mm.conditional]
    default = [mm for mm in _modmaps if not mm.conditional] or [Modmap("default", {})]
    if len(default) > 1:
        error(f"You may only have a single default (non-conditional modmap), you have {len(default)} currently.")
        exit(0)
    _modmaps = default + conditional

    # setup multi-modmaps
    conditional = [mm for mm in _multi_modmaps if mm.conditional]
    default = [mm for mm in _multi_modmaps if not mm.conditional] or [MultiModmap("default", {})]
    if len(default) > 1:
        error(f"You may only have a single default (non-conditional multi-modmap), you have {len(default)} currently.")
        exit(0)
    _multi_modmaps = default + conditional

    return (
        _modmaps,
        _multi_modmaps,
        _toplevel_keymaps,
        _timeout
    )


# ============================================================ #
# Utility functions for keymap
# ============================================================ #


def launch(command):
    """Launch command"""
    def launcher():
        from subprocess import Popen
        Popen(command)
    return launcher


def sleep(sec):
    """Sleep sec in commands"""
    def sleeper():
        import time
        time.sleep(sec)
    return sleeper


def usleep(usec):
    """Sleep usec in commands"""
    def sleeper():
        import time
        time.sleep(usec/1000)
    return sleeper

# ============================================================ #


def K(exp):
    "Helper function to specify keymap"
    import re
    modifier_strs = []
    while True:
        aliases = "|".join(Modifier.all_aliases())
        m = re.match(f"\\A({aliases})-", exp)
        if m is None:
            break
        modifier = m.group(1)
        modifier_strs.append(modifier)
        exp = re.sub(r"\A{}-".format(modifier), "", exp)
    key_str = exp.upper()
    key = getattr(Key, key_str)
    return Combo(_create_modifiers_from_strings(modifier_strs), key)

def _create_modifiers_from_strings(modifier_strs):
    modifiers = []
    for modifier_str in modifier_strs:
        key = Modifier.from_alias(modifier_str)
        if not key in modifiers:
            modifiers.append(key)
    return modifiers


# ============================================================ #



def define_timeout(seconds=1):
    global _timeout
    _timeout = seconds


def conditional(fn, what): 
    # TODO: check that fn is a valid conditional
    what.conditional = fn
    return what


# old API, takes name as an optional param
def define_modmap(mappings, name = "unnamed"):
    return modmap(name, mappings)


# new API, requires name
def modmap(name, mappings):
    """Defines modmap (keycode translation)

    Example:

    define_modmap({
        Key.CAPSLOCK: Key.LEFT_CTRL
    })
    """
    global _modmaps
    mm = Modmap(name, mappings)
    _modmaps.append(mm)
    return mm


def old_style_condition_to_fn(condition):
    condition_fn = None
    def re_search(re):
        def fn(ctx):
            return re.search(ctx.wm_class)
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


def multipurpose_modmap(name, mappings):
    for key, value in mappings.items():
        # TODO: why, we don't use this anywhere???
        value.append(Action.RELEASE)
    mmm = MultiModmap(name, mappings)
    _multi_modmaps.append(mmm)
    return mmm

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

    define_conditional_multipurpose_modmap(lambda wm_class, device_name: device_name.startswith("Microsoft"), {
        {Key.CAPSLOCK: [Key.ESC, Key.LEFT_CTRL]
    })
    """
    condition_fn = old_style_condition_to_fn(condition)
    if not callable(condition_fn):
        raise ValueError('condition must be a function or compiled regexp')
 
    name = "anonymous multipurpose map (old API)"
    return conditional(condition_fn, multipurpose_modmap(name, mappings))


# ============================================================ #

def keymap(name, mappings):
    global _toplevel_keymaps

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
    def expand(target):
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
                    if not modifier.is_specified():
                        expanded_modifiers.append([modifier.to_left(), modifier.to_right()])
                    else:
                        expanded_modifiers.append([modifier])

                # Create a Cartesian product of expanded modifiers
                expanded_modifier_lists = itertools.product(*expanded_modifiers)
                # Create expanded mappings
                for modifiers in expanded_modifier_lists:
                    expanded_mappings[Combo(set(modifiers), k.key)] = v
                keys_for_deletion.append(k)

        # Delete original mappings whose key was expanded into expanded_mappings
        for key in keys_for_deletion:
            del target[key]
        # Merge expanded mappings into original mappings
        target.update(expanded_mappings)

    expand(mappings)

    km = Keymap(name, mappings)
    _toplevel_keymaps.append(km)
    return km

def define_keymap(condition, mappings, name="Anonymous keymap"):
    condition_fn = old_style_condition_to_fn(condition)
    return conditional(condition_fn, keymap(name, mappings))

# aliases

timeout = define_timeout
conditional_modmap = define_conditional_modmap
# multipurpose_modmap = define_multipurpose_modmap
# conditional_multipurpose_modmap = define_conditional_multipurpose_modmap
    
