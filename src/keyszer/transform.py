# -*- coding: utf-8 -*-

import itertools
import time
from inspect import signature
from evdev import ecodes
from ordered_set import OrderedSet
import asyncio

import evdev

from .lib.key_context import KeyContext
from .models.key import Key
from .models.action import Action
from .models.modifier import Modifier
from .models.combo import Combo, ComboHint
from .models.keystate import Keystate
from .lib.keymap import Keymap
from .logger import *
from . import logger
from .output import Output
from .xorg import get_active_window_wm_class
from .config_api import get_configuration,escape_next_key, ignore_key

_modmaps = None
_multi_modmaps = None
_keymaps = None
_timeout = None

def boot_config():
    global _modmaps
    global _multi_modmaps
    global _keymaps
    global _timeout
    _modmaps, _multi_modmaps, _keymaps, _timeout = \
            get_configuration()


# ============================================================ #


_mode_maps = None
_output = Output()
_pressed_keys = set()
_states = {}
_sticky = {}

def reset_transform():
    global _mode_maps
    global _pressed_keys
    global _output
    global _states
    global _sticky
    _mode_maps = None
    _pressed_keys = set()
    _output = Output()
    _states = {}
    _sticky = {}


def shutdown():
    _output.shutdown()

# ============================================================ #

def none_pressed():
    return len(_states) == 0


def get_pressed_mods():
    keys = [x.key for x in _states.values() if x.is_pressed()]
    keys = [x for x in keys if Modifier.is_modifier(x)]
    return [Modifier.from_key(key) for key in keys]


def get_pressed_states():
    return [x for x in _states.values() if x.is_pressed()]


def is_sticky(key):
    for k in _sticky.keys():
        if k == key:
            return True
    return False


def update_pressed_states(keystate):
    # release
    if keystate.action == Action.RELEASE:
        del _states[keystate.inkey]

    # press / add
    if not keystate.inkey in _states:
        # add state
        if keystate.action == Action.PRESS:
            _states[keystate.inkey] = keystate
        return


# ─── MARK ───────────────────────────────────────────────────────────────────────


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


# ─── SUSPEND AND RESUME INPUT SIDE ──────────────────────────────────────────────



# keep track of how long until we need to resume the input
# and send held keys to the output (that haven't been used
# as part of a combo)
_suspend_timer = None

def resume_keys():
    global _suspend_timer
    if not is_suspended():
        return

    _suspend_timer.cancel()
    _suspend_timer = None

    # keys = get_suspended_mods()
    states = [x for x in _states.values() if x.suspended]
    if len(states) > 0:
        debug("resuming keys:", [x.key for x in states])

    for ks in states:
        # spent keys that are held long enough to resume
        # no longer count as spent
        ks.spent = False
        # sticky keys (input side) remain silently held
        # and are only lifted when they are lifted from the input
        ks.suspended = False
        if ks.key in _sticky:
            continue
        # if some other key is waking us up then we must be a modifier (we know
        # because if we were waking ourself it would happen in on_key)
        if ks.is_multi:
            ks.key=ks.multikey
            ks.multikey=False
            ks.is_multi=False

        if not ks.exerted_on_output:
            ks.exerted_on_output = True
            _output.send_key_action(ks.key, Action.PRESS)


def resume_state(keystate):
    resume_keys()

def is_suspended():
    return _suspend_timer != None

def resuspend_keys():
    _suspend_timer.cancel()
    debug("resuspending keys")
    suspend_keys()

def pressed_mods_not_exerted_on_output():
    return [key for key in get_pressed_mods() if not _output.is_mod_pressed(key)]

def suspend_or_resuspend_keys():
    if is_suspended():
        resuspend_keys()
    else:
        suspend_keys()

def suspend_keys():
    global _suspend_timer
    debug("suspending keys", pressed_mods_not_exerted_on_output())
    states = [x for x in _states.values() if x.is_pressed()]
    for s in states:
        s.suspended = True
    loop = asyncio.get_event_loop()
    _suspend_timer = loop.call_later(1, resume_keys)

# --- DUMP DIAGNOTICS ----

def dump_diagnostics():
    print("*** TRANSFORM  ***")
    print(f"are we suspended: {is_suspended()}")
    print("_suspend_timer:")
    print(_suspend_timer)
    print("_last_key:")
    print(_last_key)
    print("_states:")
    print(_states)
    print("_sticky:")
    print(_sticky)
    _output.diag()
    print("")


# ─── KEYBOARD INPUT PROCESSING HELPERS ──────────────────────────────────────────


# last key that sent a PRESS event (used to track press/release of multi-keys
# to decide to use their temporary form)
_last_key = None

# last key time record time when execute multi press
# _last_key_time = time.time()


# def multipurpose_handler(multipurpose_map, key, action, context):
#     # debug("multipurple_handler", key, action)
#     def maybe_press_modifiers(multipurpose_map):
#         """Search the multipurpose map for keys that are pressed. If found and
#         we have not yet sent it's modifier translation we do so."""
#         for k, [ _, mod_key, state ] in multipurpose_map.items():
#             if k in _pressed_keys and mod_key not in _pressed_modifier_keys:
#                 on_key(mod_key, Action.PRESS, context)

#     # we need to register the last key presses so we know if a multipurpose key
#     # was a single press and release
#     global _last_key
#     global _last_key_time

#     if key in multipurpose_map:
#         single_key, mod_key, key_state = multipurpose_map[key]
#         key_is_down = key in _pressed_keys
#         mod_is_down = mod_key in _pressed_modifier_keys
#         key_was_last_press = key == _last_key

#         update_pressed_keys(key, action)
#         if action == Action.RELEASE and key_is_down:
#             # it is a single press and release
#             if key_was_last_press and _last_key_time + _timeout > time.time():
#                 maybe_press_modifiers(multipurpose_map)  # maybe other multipurpose keys are down
#                 on_key(single_key, Action.PRESS, context)
#                 on_key(single_key, Action.RELEASE, context)
#             # it is the modifier in a combo
#             elif mod_is_down:
#                 on_key(mod_key, Action.RELEASE, context)
#         elif action == Action.PRESS and not key_is_down:
#             _last_key_time = time.time()
#     # if key is not a multipurpose or mod key we want eventual modifiers down
#     elif (key not in Modifier.get_all_keys()) and action == Action.PRESS:
#         maybe_press_modifiers(multipurpose_map)

#     # we want to register all key-presses
#     if action == Action.PRESS:
#         _last_key = key


# translate keycode (like xmodmap)
def apply_modmap(keystate, context):
    inkey = keystate.inkey
    keystate.key = inkey
    # first modmap is always the default, unconditional
    active_modmap = _modmaps[0]
    #debug("active", active_modmap)
    conditional_modmaps = _modmaps[1:]
    #debug("conditionals", conditional_modmaps)
    if conditional_modmaps:
        for modmap in conditional_modmaps:
            if modmap.conditional(context):
                active_modmap = modmap
                break
    if active_modmap:
        if inkey in active_modmap:
            debug(f"modmap: {inkey} => {active_modmap[inkey]} [{active_modmap.name}]")
            keystate.key = active_modmap[inkey]


def apply_multi_modmap(keystate, context):
    active_multi_modmap = _multi_modmaps[0]
    conditional_multi_modmaps = _multi_modmaps[1:]
    if conditional_multi_modmaps:
        for modmap in conditional_multi_modmaps:
            if modmap.conditional(context):
                active_multi_modmap = modmap
                break

    if active_multi_modmap:
        if keystate.key in active_multi_modmap:
            momentary, held, _ = active_multi_modmap[keystate.key]
            keystate.key = momentary
            keystate.multikey = held
            keystate.is_multi = True


JUST_KEYS = []
JUST_KEYS.extend([Key[x] for x in "QWERTYUIOPASDFGHJKLZXCVBNM"])

#from .lib.benchit import *

def find_keystate_or_new(inkey, action):
    if not inkey in _states:
        return Keystate(inkey = inkey, action = action)

    ks = _states[inkey]
    ks.prior = ks.copy()
    delattr(ks.prior, "prior")
    ks.action = action
    ks.time = time
    return ks


# ─── KEYBOARD INPUT PROCESSING PIPELINE ─────────────────────────────────────────

# The input processing pipeline:
#
# - on_event
#   - forward non key events
#   - modmapping
#   - multi-mapping
# - on_key
#   - suspend/resume, etc
# - transform_key
# - handle_commands
#   - process the actual combos, commands



# @benchit
def on_event(event, device_name):
    # we do not attempt to transform non-key events 
    #debug(evdev.util.categorize(event))
    if event.type != ecodes.EV_KEY:
        _output.send_event(event)
        return
    
    # if none pressed and not a modifier and not used in any 
    # modmap or multi-modmaps

    # if len(_pressed_modifier_keys) == 0 and event.code in JUST_KEYS:
    #     _output.send_event(event)
    #     return

    context = KeyContext(device_name)
    action = Action(event.value)
    key = Key(event.code)

    ks = find_keystate_or_new(
        inkey = key,
        action = action
    )

    debug()
    debug(f"in {key} ({action})", ctx = "II")

    # we only do modmap on the PRESS pass, keys may not
    # redefine themselves midstream while repeating or
    # as they are lifted
    if not ks.key:
        apply_modmap(ks, context)
        apply_multi_modmap(ks, context)

    on_key(ks, context)


def on_key(keystate, context):
    global _last_key
    hold_output = False
    should_suspend = False

    key, action = (keystate.key, keystate.action)
    debug("on_key", key, action)

    if Modifier.is_modifier(key):
        if action.is_pressed():
            if none_pressed():
                should_suspend = True

        elif action.is_released():
            if is_sticky(key):
                outkey = _sticky[key]
                debug(f"lift of BIND {key} => {outkey}")
                _output.send_key_action(outkey, Action.RELEASE)
                del _sticky[key]
                hold_output = not keystate.exerted_on_output
            elif keystate.spent:
                # if we are being released (after spent) before we can be resumed
                # then our press (as far as output is concerned) should be silent
                debug("silent lift of spent mod", key)
                hold_output = not keystate.exerted_on_output
            else:
                debug("resume because of mod release")
                resume_keys()

        update_pressed_states(keystate)

        if should_suspend or is_suspended():
            keystate.suspended = True
            hold_output = True
            if action.just_pressed():
                suspend_or_resuspend_keys()

        if not hold_output:
            _output.send_key_action(key, action)
            if action.is_released():
                keystate.exerted_on_output = False

    elif keystate.is_multi and action.just_pressed():
        # debug("multi pressed", key)
        keystate.suspended = True
        update_pressed_states(keystate)
        suspend_keys()

    # regular key releases, not modifiers (though possibly a multi-mod)
    elif action.is_released():
        if _output.is_pressed(key):
            _output.send_key_action(key, action)
        if keystate.is_multi:
            debug("multi released early", key)
            # we've triggered ourself with our own key (lifting)
            # before the timeout, so we are a normal momentary
            # input
            if _last_key == key:
                keystate.resolve_as_momentary()
            else:
                keystate.resolve_as_modifier()
            resume_state(keystate)
            transform_key(key, action, context)
            update_pressed_states(keystate)
    else:
        # not a modifier or a multi-key, so pass straight to transform
        transform_key(key, action, context)

    if action.just_pressed():
        _last_key = key


def transform_key(key, action, ctx):
    global _mode_maps
    is_top_level = False

    combo = Combo(get_pressed_mods(), key)

    if _mode_maps is escape_next_key:
        debug(f"Escape key: {combo} => {key}")
        _output.send_key_action(key, action)
        _mode_maps = None
        return

    # Decide keymap(s)
    if _mode_maps is None:
        is_top_level = True
        _mode_maps = [km for km in _keymaps if km.matches(ctx)]

    for keymap in _mode_maps:
        if combo not in keymap:
            continue

        if logger.VERBOSE:
            keymap_names = [map.name for map in _mode_maps]
            name_list = ", ".join(keymap_names)
            debug("")
            debug(
                f"WM_CLS '{ctx.wm_class}' | "
                f"DV '{ctx.device_name}' | "
                f"KMAPS = [{name_list}]")
            debug(f"  COMBO: {combo} => {keymap[combo]} [{keymap.name}]")

        held = get_pressed_states()
        for ks in held:
            # if we are triggering a momentary on the output then we can mark ourselves
            # spent, but if the key is already asserted on the output then we cannot
            # count it as spent and must hold it so that it's release later will
            # trigger the release on the output
            if not _output.is_mod_pressed(ks.key):
                ks.spent = True
        debug("spent modifiers", [_.key for _ in held if _.spent])
        reset_mode = handle_commands(keymap[combo], key, action, combo)
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


# ─── AUTO BIND AND STICKY KEYS SUPPORT ──────────────────────────────────────────


# binds the first input modifier to the first output modifier
def simple_sticky(combo, output_combo):
    inmods = combo.ordered_mods
    outmods = output_combo.ordered_mods
    if len(inmods) == 0 or len(outmods) == 0:
        return {}
    inkey = inmods[0].get_key()
    outkey = outmods[0].get_key()

    if inkey in _states:
        ks = _states[inkey]
        if ks.exerted_on_output:
            key_in_output = any([inkey in mod.keys for mod in outmods])
            if not key_in_output:
                # we are replacing the input key with the bound outkey, so if
                # the input key is exerted on the output we should lift it
                _output.send_key_action(inkey, Action.RELEASE)
                # it's release later will still need to result in us lifting
                # the sticky out key from output, but that is currently handled
                # by `_sticky` in `on_key`
                # TODO: this state info should likely move into `KeyState`
                ks.exerted_on_output = False

    stuck = { inkey: outkey }
    debug("BIND:", stuck)
    return stuck


def auto_sticky(combo, input_combo):
    global _sticky

    # can not engage a second sticky over top of a first
    if len(_sticky) > 0:
        debug("refusing to engage second sticky bind over existing sticky bind")
        return

    _sticky = simple_sticky(input_combo, combo)
    for k in _sticky.values():
        if not _output.is_mod_pressed(k):
            _output.send_key_action(k, Action.PRESS)


# ─── COMMAND PROCESSING ─────────────────────────────────────────────────────────


def handle_commands(commands, key, action, input_combo = None):
    """
    returns: reset_mode (True/False) if this is True, _mode_maps will be reset
    """
    global _mode_maps
    _next_bind = False

    if not isinstance(commands, list):
        commands = [commands]

    # if input_combo and input_combo.hint == ComboHint.BIND:
        # auto_sticky(commands[0], input_combo)

    # resuspend any keys still not exerted on the output, giving
    # them a chance to be lifted or to trigger another macro as-is
    if is_suspended():
        resuspend_keys()

    # Execute commands
    for command in commands:
        if callable(command):
            # very likely we're just passing None forwards here but that OK
            reset_mode = handle_commands(command(), key, action)
            # if the command wants to disable reset, lets propogate that
            if reset_mode is False:
                return False
        elif isinstance(command, Combo):
            if _next_bind:
                auto_sticky(command, input_combo)
            _output.send_combo(command)
        elif isinstance(command, Key):
            _output.send_key(command)
        elif command is escape_next_key:
            _mode_maps = escape_next_key
            return False
        elif command is ComboHint.BIND:
            _next_bind = True
            continue
        elif command is ignore_key:
            debug("ignore_key", key)
            return True
        # Go to next keymap
        elif isinstance(command, dict):
            # TODO: we should really handle this at startup so we have a
            # proper name here such as "Firefox (nested)" or something
            _mode_maps = [Keymap("nested (anon)", command)]
            return False
        else:
            debug("unknown command")
        _next_bind = False
    # Reset keymap in ordinary flow
    return True
