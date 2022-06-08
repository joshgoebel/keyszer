# -*- coding: utf-8 -*-

import itertools
import time
from inspect import signature
from evdev import ecodes
from ordered_set import OrderedSet
import asyncio

import evdev

from .lib.key_context import KeyContext
from .key import Key 
from .models.action import Action
from .models.combo import Combo
from .models.modifier import Modifier
from .logger import *
from .output import Output 
from .xorg import get_active_window_wm_class
from .config_api import get_configuration,escape_next_key, pass_through_key, ignore_key

def boot_config():
    global _modmaps
    global _multi_modmaps
    global _toplevel_keymaps
    global _timeout
    _modmaps, _multi_modmaps, _toplevel_keymaps, _timeout = \
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
    if (len(_pressed_modifier_keys) > 1):
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
    debug("resuspending keys (after output combo)")
    suspend_keys(True)

def pressed_mods_not_exerted_on_output():
    return [key for key in _pressed_modifier_keys if not _output.is_mod_pressed(key)]

def suspend_keys(quiet=False):
    global _suspend_timer
    if not quiet:
        debug("suspending keys", pressed_mods_not_exerted_on_output())
    loop = asyncio.get_event_loop()
    _suspend_timer = loop.call_later(1, resume_keys)


# ============================================================
# Key handler
# ============================================================


# last key that sent a PRESS event or a non-mod or non-multi key that sent a RELEASE
# or REPEAT
_last_key = None

# last key time record time when execute multi press
_last_key_time = time.time()


def multipurpose_handler(multipurpose_map, key, action, context):
    # debug("multipurple_handler", key, action)
    def maybe_press_modifiers(multipurpose_map):
        """Search the multipurpose map for keys that are pressed. If found and
        we have not yet sent it's modifier translation we do so."""
        for k, [ _, mod_key, state ] in multipurpose_map.items():
            if k in _pressed_keys and mod_key not in _pressed_modifier_keys:
                on_key(mod_key, Action.PRESS, context)

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
                on_key(single_key, Action.PRESS, context)
                on_key(single_key, Action.RELEASE, context)
            # it is the modifier in a combo
            elif mod_is_down:
                on_key(mod_key, Action.RELEASE, context)
        elif action == Action.PRESS and not key_is_down:
            _last_key_time = time()
    # if key is not a multipurpose or mod key we want eventual modifiers down
    elif (key not in Modifier.get_all_keys()) and action == Action.PRESS:
        maybe_press_modifiers(multipurpose_map)

    # we want to register all key-presses
    if action == Action.PRESS:
        _last_key = key


# translate keycode (like xmodmap)
def apply_modmap(key, context):
    # first modmap is always the default, unconditional
    active_modmap = _modmaps[0] 
    #print("active", active_modmap)
    conditional_modmaps = _modmaps[1:]
    #print("conditionals", conditional_modmaps)
    if conditional_modmaps:
        for modmap in conditional_modmaps:
            if modmap.conditional(context):
                active_modmap = modmap
                break
    if active_modmap and key in active_modmap:
        debug(f"modmap: {key} => {active_modmap[key]} [{active_modmap.name}]")
        key = active_modmap[key]

    return key


def apply_multi_modmap(key, action, context):
    active_multi_modmap = _multi_modmaps[0]
    conditional_multi_modmaps = _multi_modmaps[1:]
    if conditional_multi_modmaps:
        for modmap in conditional_multi_modmaps:
            if modmap.conditional(context):
                active_multi_modmap = modmap
                break
    if active_multi_modmap:
        multipurpose_handler(active_multi_modmap, key, action, context)
        if key in active_multi_modmap:
            return True

    return False


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

    context = KeyContext(device_name)
    action = Action(event.value)
    key = Key(event.code)

    # debug(f"in {key} ({action})", ctx = "II")

    key = apply_modmap(key, context)
    # multipurpose modmaps fire their own on_key and do their own
    # pressed key updating, so if a multi-modmap decides to apply
    # then we stop here and do not proceed with normal processing
    if apply_multi_modmap(key, action, context):
        return

    on_key(key, action, context, quiet=quiet)
    update_pressed_keys(key, action)


def is_sticky(key):
    for k in _sticky.keys():
        if k == key:
            return True
    return False

def on_key(key, action, context, quiet=False):
    need_suspend = False
    # debug("on_key", key, action)
    if key in Modifier.get_all_keys():
        if none_pressed() and action.is_pressed():
            need_suspend = True

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
        if need_suspend:
            suspend_keys()
        if not suspended():
            _output.send_key_action(key, action)
    elif not action.is_pressed():
        if _output.is_pressed(key):
            _output.send_key_action(key, action)
    else:
        transform_key(key, action, context, quiet=quiet)


def transform_key(key, action, context, quiet=False):
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
        keymap_names = []
        for keymap in _toplevel_keymaps:
            if keymap.conditional == None or keymap.conditional(context):
                _mode_maps.append(keymap)
                keymap_names.append(keymap.name)

    # _mode_maps: [global_map, local_1, local_2, ...]
    for mappings in _mode_maps:
        if combo not in mappings:
            continue

        if not quiet:
            print("")
            debug("WM_CLS '{}' | DEV '{}' | KMAPS = [{}]".format(context.wm_class, context.device_name, ", ".join(keymap_names)))
            debug("  COMBO:", combo, "=>", mappings[combo], f"  [{mappings.name}]")

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
    # debug("simple_sticky (one mod => one mod)", combo, output_combo)

    m = {}
    m[next(iter(inp)).get_key()] = next(iter(out)).get_key()
    debug("AUTO-STICKY:", m)
    return m

_sticky = {}

def handle_commands(commands, key, action, input_combo = None):
    """
    returns: reset_mode (True/False) if this is True, _mode_maps will be reset
    """
    global _mode_maps
    global _sticky

    if not isinstance(commands, list):
        commands = [commands]

    # sticky only applies to 1 => 1 mappings
    if len(commands)==1 and input_combo:
        if isinstance(commands[0], Combo):
            command = commands[0]
            _sticky = simple_sticky(input_combo, command)
            for k in _sticky.values():
                if not _output.is_mod_pressed(k):
                    _output.send_key_action(k, Action.PRESS)

    if (suspended()):
        resuspend_keys()

    # Execute commands
    for command in commands:
        if callable(command):
            commands = command()
            # very likely we're given None though which 
            # means we can just do nothing at all and
            # assume that running the command was the
            # actual operation we care about
            if commands:
                handle_commands(commands, key, action)
        elif isinstance(command, Combo):
            _output.send_combo(command)
        elif isinstance(command, Key):
            _output.send_key(command)
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
