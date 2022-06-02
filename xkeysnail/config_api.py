import itertools

from .key import Action, Combo, Key, Modifier

# GLOBALS

escape_next_key = {}
pass_through_key = {}

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

# ============================================================ #


def K(exp):
    "Helper function to specify keymap"
    import re
    modifier_strs = []
    while True:
        m = re.match(r"\A(LC|LCtrl|RC|RCtrl|C|Ctrl|LM|LAlt|RM|RAlt|M|Alt|LShift|RShift|Shift|LSuper|LWin|RSuper|RWin|Super|Win)-", exp)
        if m is None:
            break
        modifier = m.group(1)
        modifier_strs.append(modifier)
        exp = re.sub(r"\A{}-".format(modifier), "", exp)
    key_str = exp.upper()
    key = getattr(Key, key_str)
    return Combo(_create_modifiers_from_strings(modifier_strs), key)


def _create_modifiers_from_strings(modifier_strs):
    modifiers = set()
    for modifier_str in modifier_strs:
        if modifier_str == 'LC' or modifier_str == 'LCtrl':
            modifiers.add(Modifier.L_CONTROL)
        elif modifier_str == 'RC' or modifier_str == 'RCtrl':
            modifiers.add(Modifier.R_CONTROL)
        elif modifier_str == 'C' or modifier_str == 'Ctrl':
            modifiers.add(Modifier.CONTROL)
        elif modifier_str == 'LM' or modifier_str == 'LAlt':
            modifiers.add(Modifier.L_ALT)
        elif modifier_str == 'RM' or modifier_str == 'RAlt':
            modifiers.add(Modifier.R_ALT)
        elif modifier_str == 'M' or modifier_str == 'Alt':
            modifiers.add(Modifier.ALT)
        elif modifier_str == 'LSuper' or modifier_str == 'LWin':
            modifiers.add(Modifier.L_SUPER)
            pass
        elif modifier_str == 'RSuper' or modifier_str == 'RWin':
            modifiers.add(Modifier.R_SUPER)
            pass
        elif modifier_str == 'Super' or modifier_str == 'Win':
            modifiers.add(Modifier.SUPER)
            pass
        elif modifier_str == 'LShift':
            modifiers.add(Modifier.L_SHIFT)
        elif modifier_str == 'RShift':
            modifiers.add(Modifier.R_SHIFT)
        elif modifier_str == 'Shift':
            modifiers.add(Modifier.SHIFT)
    return modifiers


# ============================================================ #


# keycode translation
# e.g., { Key.CAPSLOCK: Key.LEFT_CTRL }
_mod_map = {}
_conditional_mod_map = []

# multipurpose keys
# e.g, {Key.LEFT_CTRL: [Key.ESC, Key.LEFT_CTRL, Action.RELEASE]}
_multipurpose_map = None
_conditional_multipurpose_map = []

_timeout = 1


def define_timeout(seconds=1):
    global _timeout
    _timeout = seconds


def define_modmap(mod_remappings):
    """Defines modmap (keycode translation)

    Example:

    define_modmap({
        Key.CAPSLOCK: Key.LEFT_CTRL
    })
    """
    global _mod_map
    _mod_map = mod_remappings


def define_conditional_modmap(condition, mod_remappings):
    """Defines conditional modmap (keycode translation)

    Example:

    define_conditional_modmap(re.compile(r'Emacs'), {
        Key.CAPSLOCK: Key.LEFT_CTRL
    })
    """
    if hasattr(condition, 'search'):
        condition = condition.search
    if not callable(condition):
        raise ValueError('condition must be a function or compiled regexp')
    _conditional_mod_map.append((condition, mod_remappings))


def define_multipurpose_modmap(multipurpose_remappings):
    """Defines multipurpose modmap (multi-key translations)

    Give a key two different meanings. One when pressed and released alone and
    one when it's held down together with another key (making it a modifier
    key).

    Example:

    define_multipurpose_modmap(
        {Key.CAPSLOCK: [Key.ESC, Key.LEFT_CTRL]
    })
    """
    global _multipurpose_map
    for key, value in multipurpose_remappings.items():
        value.append(Action.RELEASE)
    _multipurpose_map = multipurpose_remappings


def define_conditional_multipurpose_modmap(condition, multipurpose_remappings):
    """Defines conditional multipurpose modmap (multi-key translation)

    Example:

    define_conditional_multipurpose_modmap(lambda wm_class, device_name: device_name.startswith("Microsoft"), {
        {Key.CAPSLOCK: [Key.ESC, Key.LEFT_CTRL]
    })
    """
    if hasattr(condition, 'search'):
        condition = condition.search
    if not callable(condition):
        raise ValueError('condition must be a function or compiled regexp')
    for key, value in multipurpose_remappings.items():
        value.append(Action.RELEASE)
    _conditional_multipurpose_map.append((condition, multipurpose_remappings))


# ============================================================ #

_toplevel_keymaps = []

def define_keymap(condition, mappings, name="Anonymous keymap"):
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
        if isinstance(target, dict):
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

    _toplevel_keymaps.append((condition, mappings, name))
    return mappings

timeout = define_timeout
keymap = define_keymap
modmap = define_modmap
conditional_modmap = define_conditional_modmap
multipurpose_modmap = define_multipurpose_modmap
conditional_multipurpose_modmap = define_conditional_multipurpose_modmap

def get_configuration():
    return (
        _mod_map,
        _conditional_mod_map,
        _multipurpose_map,
        _conditional_multipurpose_map,
        _toplevel_keymaps,
        _timeout
    )

