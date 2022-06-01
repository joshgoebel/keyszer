from .key import Action, Combo, Key, Modifier

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