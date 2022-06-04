# -*- coding: utf-8 -*-

import itertools
from time import time
from inspect import signature
from evdev import ecodes
from ordered_set import OrderedSet
import asyncio

import evdev

from .key import Action, Combo, Key, Modifier
from .logger import *
from .output import Output 
from .xorg import get_active_window_wm_class
from .config_api import get_configuration,escape_next_key, pass_through_key, ignore_key

def boot_config():
    global _modmaps
    global _multipurpose_map
    global _conditional_multipurpose_map
    global _toplevel_keymaps
    global _timeout
    _modmaps, _multipurpose_map, \
        _conditional_multipurpose_map, _toplevel_keymaps, _timeout = \
            get_configuration()


# ============================================================ #


_spent_modifiers_keys = set()
_pressed_modifier_keys = OrderedSet()
_mode_maps = None
_output = Output()
_pressed_keys = set()

def reset_transform():
    global _spent_modifiers_keys
    global _pressed_modifier_keys
    global _mode_maps
    global _pressed_keys
    global _output
    _mode_maps = None
    _pressed_keys = set()
    _spent_modifiers_keys = set()
    _pressed_modifier_keys = OrderedSet()
    _output = Output()


def shutdown():
    _output.shutdown()

# ============================================================ #


def update_pressed_modifier_keys(key, action):
    if action.is_pressed():
        _pressed_modifier_keys.add(key)
    else:
        _pressed_modifier_keys.discard(key)


def get_pressed_modifiers():
    return {Modifier.from_key(key) for key in _pressed_modifier_keys}


def none_pressed():
    return not(any(_pressed_keys) or any(_pressed_modifier_keys))


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


# ============================================================ #
# Suspend / Resume input side
# ============================================================ #

# keep track of how long until we need to resume the input
# and send held keys to the output (that haven't been used
# as part of a combo)
_suspend_timer = None

def resume_keys():
    global _suspend_timer
    if not suspended():
        return

    _suspend_timer.cancel()
    _suspend_timer = None
    debug("resuming keys:", _pressed_modifier_keys)
    _spent_modifiers_keys = {}
    for mod in _pressed_modifier_keys:
        # sticky keys (input side) remain silently held
        # and are only lifted when they are lifted from the input
        if mod in _sticky:
            continue
        _output.send_key_action(mod, Action.PRESS)
    

def suspended():
    global _suspend_timer
    return _suspend_timer != None

def resuspend_keys():
    global _suspend_timer
    _suspend_timer.cancel()
    debug("resuspending keys")
    suspend_keys(True)

def suspend_keys(quiet=False):
    global _suspend_timer
    if not quiet:
        debug("suspending keys")
    loop = asyncio.get_event_loop()
    _suspend_timer = loop.call_later(1, resume_keys)


# ============================================================
# Key handler
# ============================================================


# last key that sent a PRESS event or a non-mod or non-multi key that sent a RELEASE
# or REPEAT
_last_key = None

# last key time record time when execute multi press
_last_key_time = time()


def multipurpose_handler(multipurpose_map, key, action):
    debug("multipurple_handler", key, action)
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


# translate keycode (like xmodmap)
def apply_modmap(key, device_name):
    # first modmap is always the default, unconditional
    active_modmap = _modmaps[0] 
    print("active", active_modmap)
    conditional_modmaps = _modmaps[1:]
    print("conditionals", conditional_modmaps)
    if conditional_modmaps:
        ctx = {
            "wm_class": get_active_window_wm_class(),
            "device_name": device_name
        }
        for modmap in conditional_modmaps:
            if modmap.conditional(ctx):
                active_modmap = modmap
                break
    if active_modmap and key in active_modmap:
        key = active_modmap[key]

    return key

JUST_KEYS = []
JUST_KEYS.extend([Key[x] for x in "QWERTYUIOPASDFGHJKLZXCVBNM"])

#from .lib.benchit import *

# @benchit
def on_event(event, device_name, quiet):
    # we do not attempt to transform non-key events 
    #debug(evdev.util.categorize(event))
    if event.type != ecodes.EV_KEY:
        _output.send_event(event)
        return
        
    # if len(_pressed_modifier_keys) == 0 and event.code in JUST_KEYS:
    #     _output.send_event(event)
    #     return

    action = Action(event.value)
    key = apply_modmap(Key(event.code), device_name)

    wm_class = None
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


def is_sticky(key):
    for k in _sticky.keys():
        if k == key:
            return True
    return False

def on_key(key, action, wm_class=None, quiet=False):
    # debug("on_key", key, action)
    if key in Modifier.get_all_keys():
        if none_pressed() and action.is_pressed():
            suspend_keys()        

        if action.is_released():
            if is_sticky(key):
                outkey = _sticky[key]
                _output.send_key_action(outkey, Action.RELEASE)    
                del _sticky[key]
            elif key in _spent_modifiers_keys:
                debug("silent lift of spent modifier", key)
                # allow a silent release inside the tranform
                _spent_modifiers_keys.remove(key)
            else:     
                debug("resume because of mod release")
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
    # global _toplevel_keymaps
    global _spent_modifiers_keys

    combo = Combo(get_pressed_modifiers(), key)

    if _mode_maps is escape_next_key:
        debug("Escape key: {}".format(combo))
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
            debug("WM_CLASS '{}' | active keymaps = [{}]".format(wm_class, ", ".join(keymap_names)))

    if not quiet:
        debug("COMBO:", combo)

    # _mode_maps: [global_map, local_1, local_2, ...]
    for mappings in _mode_maps:
        if combo not in mappings:
            continue
        _spent_modifiers_keys |= _pressed_modifier_keys
        debug("spent modifiers", _spent_modifiers_keys)
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
    if len(inp) != 1 or len(out) != 1:
        return {}
    debug("simple_sticky (one mod => one mod)", combo, output_combo)

    m = {}
    m[next(iter(inp)).get_key()] = next(iter(out)).get_key()
    debug("AUTO-STICKY:", m)
    return m

_sticky = {}

def handle_commands(commands, key, action, input_combo):
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
            _sticky = simple_sticky(input_combo, command)
            if (suspended()):
                resuspend_keys()
            for k in _sticky.values():
                if not _output.is_mod_pressed(k):
                    _output.send_key_action(k, Action.PRESS)
            _output.send_combo(command)
        elif command is escape_next_key:
            _mode_maps = escape_next_key
            return False
        elif command is ignore_key:
            debug("ignore_key", key)
            return True
        elif command is pass_through_key:
            debug("pass_thru_key", key)
            _output.send_key_action(key, action)
            return True
        # Go to next keymap
        elif isinstance(command, dict):
            _mode_maps = [command]
            return False
        else:
            debug("unknown command")
    # Reset keymap in ordinary flow
    return True
