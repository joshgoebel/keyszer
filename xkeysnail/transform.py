# -*- coding: utf-8 -*-

import itertools
from time import time
from inspect import signature
from evdev import ecodes
import asyncio

from .key import Action, Combo, Key, Modifier
from .output import Output 
from .xorg import get_active_window_wm_class

# ============================================================ #


_pressed_modifier_keys = set()
_output = Output()


def update_pressed_modifier_keys(key, action):
    if action.is_pressed():
        _pressed_modifier_keys.add(key)
    else:
        _pressed_modifier_keys.discard(key)


def get_pressed_modifiers():
    return {Modifier.from_key(key) for key in _pressed_modifier_keys}


# ============================================================ #


_pressed_keys = set()


def update_pressed_keys(key, action):
    if action.is_pressed():
        _pressed_keys.add(key)
    else:
        _pressed_keys.discard(key)


# ============================================================ #
# Mark
# ============================================================ #

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




# ============================================================
# Keymap
# ============================================================


_toplevel_keymaps = []
_mode_maps = None

escape_next_key = {}
pass_through_key = {}


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


# ============================================================
# Key handler
# ============================================================

# keycode translation
# e.g., { Key.CAPSLOCK: Key.LEFT_CTRL }
_mod_map = None
_conditional_mod_map = []

# multipurpose keys
# e.g, {Key.LEFT_CTRL: [Key.ESC, Key.LEFT_CTRL, Action.RELEASE]}
_multipurpose_map = None
_conditional_multipurpose_map = []

# last key that sent a PRESS event or a non-mod or non-multi key that sent a RELEASE
# or REPEAT
_last_key = None

# last key time record time when execute multi press
_last_key_time = time()
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


def multipurpose_handler(multipurpose_map, key, action):

    def maybe_press_modifiers(multipurpose_map):
        """Search the multipurpose map for keys that are pressed. If found and
        we have not yet sent it's modifier translation we do so."""
        for k, [ _, mod_key, state ] in multipurpose_map.items():
            if k in _pressed_keys and mod_key not in _pressed_modifier_keys:
                on_key(mod_key, Action.PRESS)

    # we need to register the last key presses so we know if a multipurpose key
    # was a single press and release
    global _last_key
    global _last_key_time

    if key in multipurpose_map:
        single_key, mod_key, key_state = multipurpose_map[key]
        key_is_down = key in _pressed_keys
        mod_is_down = mod_key in _pressed_modifier_keys
        key_was_last_press = key == _last_key

        update_pressed_keys(key, action)
        if action == Action.RELEASE and key_is_down:
            # it is a single press and release
            if key_was_last_press and _last_key_time + _timeout > time():
                maybe_press_modifiers(multipurpose_map)  # maybe other multipurpose keys are down
                on_key(single_key, Action.PRESS)
                on_key(single_key, Action.RELEASE)
            # it is the modifier in a combo
            elif mod_is_down:
                on_key(mod_key, Action.RELEASE)
        elif action == Action.PRESS and not key_is_down:
            _last_key_time = time()
    # if key is not a multipurpose or mod key we want eventual modifiers down
    elif (key not in Modifier.get_all_keys()) and action == Action.PRESS:
        maybe_press_modifiers(multipurpose_map)

    # we want to register all key-presses
    if action == Action.PRESS:
        _last_key = key


def on_event(event, device_name, quiet):
    # we do not attempt to transform non-key events 
    if event.type != ecodes.EV_KEY:
        _output.send_event(event)
        return

    key = Key(event.code)
    action = Action(event.value)
    wm_class = None
    # translate keycode (like xmodmap)
    active_mod_map = _mod_map
    if _conditional_mod_map:
        wm_class = get_active_window_wm_class()
        for condition, mod_map in _conditional_mod_map:
            params = [wm_class]
            if len(signature(condition).parameters) == 2:
                params = [wm_class, device_name]

            if condition(*params):
                active_mod_map = mod_map
                break
    if active_mod_map and key in active_mod_map:
        key = active_mod_map[key]

    active_multipurpose_map = _multipurpose_map
    if _conditional_multipurpose_map:
        wm_class = get_active_window_wm_class()
        for condition, mod_map in _conditional_multipurpose_map:
            params = [wm_class]
            if len(signature(condition).parameters) == 2:
                params = [wm_class, device_name]

            if condition(*params):
                active_multipurpose_map = mod_map
                break
    if active_multipurpose_map:
        multipurpose_handler(active_multipurpose_map, key, action)
        if key in active_multipurpose_map:
            return

    on_key(key, action, wm_class=wm_class, quiet=quiet)
    update_pressed_keys(key, action)


def none_pressed():
    return not(any(_pressed_keys) or any(_pressed_modifier_keys))

_suspend_timer = None

def resume_keys():
    global _suspend_timer
    if not suspended():
        return

    _suspend_timer.cancel()
    _suspend_timer = None
    print("resuming keys:", _pressed_modifier_keys)
    for mod in _pressed_modifier_keys:
        _output.send_key_action(mod, Action.PRESS)
    

def suspended():
    global _suspend_timer
    return _suspend_timer != None

def resuspend_keys():
    global _suspend_timer
    _suspend_timer.cancel()
    print("resuspending keys")
    suspend_keys(True)

def suspend_keys(quiet=False):
    global _suspend_timer
    if not quiet:
        print("suspending keys")
    loop = asyncio.get_event_loop()
    _suspend_timer = loop.call_later(1, resume_keys)

def is_sticky(key):
    for k in _sticky.keys():
        if k == key:
            return True
    return False

def on_key(key, action, wm_class=None, quiet=False):
    global _suspend_timer

    if key in Modifier.get_all_keys():
        if none_pressed() and action.is_pressed():
            suspend_keys()        

        if action.is_released():
            if is_sticky(key):
                outkey = _sticky[key]
                _output.send_key_action(outkey, Action.RELEASE)    
                del _sticky[key]
            else:     
                resume_keys()

        update_pressed_modifier_keys(key, action)
        if not suspended():
            _output.send_key_action(key, action)
    elif not action.is_pressed():
        if _output.is_pressed(key):
            _output.send_key_action(key, action)
    else:
        transform_key(key, action, wm_class=wm_class, quiet=quiet)


def transform_key(key, action, wm_class=None, quiet=False):
    global _mode_maps
    global _toplevel_keymaps

    combo = Combo(get_pressed_modifiers(), key)

    if _mode_maps is escape_next_key:
        print("Escape key: {}".format(combo))
        _output.send_key_action(key, action)
        _mode_maps = None
        return

    is_top_level = False
    if _mode_maps is None:
        # Decide keymap(s)
        is_top_level = True
        _mode_maps = []
        if wm_class is None:
            wm_class = get_active_window_wm_class()
        keymap_names = []
        for condition, mappings, name in _toplevel_keymaps:
            if (callable(condition) and condition(wm_class)) \
               or (hasattr(condition, "search") and condition.search(wm_class)) \
               or condition is None:
                _mode_maps.append(mappings)
                keymap_names.append(name)
        if not quiet:
            print("WM_CLASS '{}' | active keymaps = [{}]".format(wm_class, ", ".join(keymap_names)))

    if not quiet:
        print(combo)

    # _mode_maps: [global_map, local_1, local_2, ...]
    for mappings in _mode_maps:
        if combo not in mappings:
            continue
        # Found key in "mappings". Execute commands defined for the key.
        reset_mode = handle_commands(mappings[combo], key, action, combo)
        if reset_mode:
            _mode_maps = None
        return

    # Not found in all keymaps
    if is_top_level:
        # need to output any keys we've suspended
        resume_keys()
        # If it's top-level, pass through keys
        _output.send_key_action(key, action)

    _mode_maps = None

# deals with the single modifier mapped to another modifier case
def simple_sticky(combo, output_combo):
    inp = combo.modifiers or {}
    out = output_combo.modifiers or {}
    print("simple_sticky", combo, output_combo)
    if len(inp) != 1 or len(out) != 1:
        return {}
    
    m = {}
    m[next(iter(inp)).get_key()] = next(iter(out)).get_key()
    print("AUTO-STICKY:", m)
    return m

_sticky = {}

def handle_commands(commands, key, action, combo):
    """
    returns: reset_mode (True/False) if this is True, _mode_maps will be reset
    """
    global _mode_maps
    global _sticky

    if not isinstance(commands, list):
        commands = [commands]

    # Execute commands
    for command in commands:
        if callable(command):
            reset_mode = handle_commands(command(), key, action)
            if reset_mode:
                return True

        if isinstance(command, Key):
            _output.send_key(command)
        elif isinstance(command, Combo):
            _sticky = simple_sticky(combo, command)
            if (suspended()):
                resuspend_keys()
            for k in _sticky.values():
                if not _output.is_mod_pressed(k):
                    _output.send_key_action(k, Action.PRESS)
            _output.send_combo(command)
        elif command is escape_next_key:
            _mode_maps = escape_next_key
            return False
        # Go to next keymap
        elif isinstance(command, dict):
            _mode_maps = [command]
            return False
        elif command is pass_through_key:
            _output.send_key_action(key, action)
            return True
    # Reset keymap in ordinary flow
    return True
