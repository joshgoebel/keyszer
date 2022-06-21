import time
from evdev import ecodes
import asyncio

from .lib.key_context import KeyContext
from .models.key import Key
from .models.action import Action
from .models.modifier import Modifier
from .models.combo import Combo, ComboHint
from .models.keystate import Keystate
from .models.keymap import Keymap
from .lib.logger import debug
from .lib import logger
from .output import Output
from .config_api import get_configuration, escape_next_key, ignore_key

_MODMAPS = None
_MULTI_MODMAPS = None
_KEYMAPS = None
_TIMEOUTS = None


def boot_config():
    global _MODMAPS
    global _MULTI_MODMAPS
    global _KEYMAPS
    global _TIMEOUTS
    _MODMAPS, _MULTI_MODMAPS, _KEYMAPS, _TIMEOUTS = \
        get_configuration()


# ============================================================ #


_active_keymaps = None
_output = Output()
_key_states = {}
_sticky = {}


def reset_transform():
    global _active_keymaps
    global _output
    global _key_states
    global _sticky
    _active_keymaps = None
    _output = Output()
    _key_states = {}
    _sticky = {}


def shutdown():
    _output.shutdown()

# ============================================================ #


def none_pressed():
    return len(_key_states) == 0


def get_pressed_mods():
    keys = [x.key for x in _key_states.values() if x.is_pressed()]
    keys = [x for x in keys if Modifier.is_key_modifier(x)]
    return [Modifier.from_key(key) for key in keys]


def get_pressed_states():
    return [x for x in _key_states.values() if x.is_pressed()]


def is_sticky(key):
    for k in _sticky.keys():
        if k == key:
            return True
    return False


def update_pressed_states(keystate):
    # release
    if keystate.action == Action.RELEASE:
        del _key_states[keystate.inkey]

    # press / add
    if keystate.inkey not in _key_states:
        # add state
        if keystate.action == Action.PRESS:
            _key_states[keystate.inkey] = keystate
        return


# ─── SUSPEND AND RESUME INPUT SIDE ──────────────────────────────────────────────


# keep track of how long until we need to resume the input
# and send held keys to the output (that haven't been used
# as part of a combo)
_suspend_timer = None
_last_suspend_timeout = 0


def resume_keys():
    global _last_suspend_timeout
    global _suspend_timer
    if not is_suspended():
        return

    _suspend_timer.cancel()
    _last_suspend_timeout = 0
    _suspend_timer = None

    # keys = get_suspended_mods()
    states = [x for x in _key_states.values() if x.suspended]
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
            ks.key = ks.multikey
            ks.multikey = False
            ks.is_multi = False

        if not ks.exerted_on_output:
            ks.exerted_on_output = True
            _output.send_key_action(ks.key, Action.PRESS)


def is_suspended():
    return _suspend_timer is not None


def resuspend_keys(timeout):
    # we should not be able to resuspend for a shorter timeout, ie
    # a multi timeout of 1s should not be overruled by a shorter timeout
    if is_suspended():
        if timeout < _last_suspend_timeout:
            return
    # TODO: revisit
    # REF: https://github.com/nolar/looptime/issues/3
    # if is_suspended():
    #     loop = asyncio.get_event_loop()
    #     # log("when", _suspend_timer.when())
    #     # log("loop time", loop.time())
    #     until = _suspend_timer.when() - loop.time()
    #     # log("requesting sleep", timeout)
    #     # log(until, "until wake")

    #     if timeout < until:
    #         return

    _suspend_timer.cancel()
    debug("resuspending keys")
    suspend_keys(timeout)


def pressed_mods_not_exerted_on_output():
    return [key for key in get_pressed_mods() if not _output.is_mod_pressed(key)]


def suspend_or_resuspend_keys(timeout):
    if is_suspended():
        resuspend_keys(timeout)
    else:
        suspend_keys(timeout)


def suspend_keys(timeout):
    global _suspend_timer
    global _last_suspend_timeout
    debug("suspending keys", pressed_mods_not_exerted_on_output())
    states = [x for x in _key_states.values() if x.is_pressed()]
    for s in states:
        s.suspended = True
    loop = asyncio.get_event_loop()
    _last_suspend_timeout = timeout
    _suspend_timer = loop.call_later(timeout, resume_keys)

# ─── DUMP DIAGNOTICS ────────────────────────────────────────────────────────


def dump_diagnostics():
    print("*** TRANSFORM  ***")
    print(f"are we suspended: {is_suspended()}")
    print("_suspend_timer:")
    print(_suspend_timer)
    print("_last_key:")
    print(_last_key)
    print("_key_states:")
    print(_key_states)
    print("_sticky:")
    print(_sticky)
    _output.diag()
    print("")


# ─── KEYBOARD INPUT PROCESSING HELPERS ──────────────────────────────────────────


# last key that sent a PRESS event (used to track press/release of multi-keys
# to decide to use their temporary form)
_last_key = None


# translate keycode (like xmodmap)
def apply_modmap(keystate, context):
    inkey = keystate.inkey
    keystate.key = inkey
    # first modmap is always the default, unconditional
    active_modmap = _MODMAPS[0]
    # debug("active", active_modmap)
    conditional_modmaps = _MODMAPS[1:]
    # debug("conditionals", conditional_modmaps)
    if conditional_modmaps:
        for modmap in conditional_modmaps:
            if modmap.conditional(context):
                active_modmap = modmap
                break
    if active_modmap and inkey in active_modmap:
        debug(f"modmap: {inkey} => {active_modmap[inkey]} [{active_modmap.name}]")
        keystate.key = active_modmap[inkey]


def apply_multi_modmap(keystate, context):
    active_multi_modmap = _MULTI_MODMAPS[0]
    conditional_multimaps = _MULTI_MODMAPS[1:]
    if conditional_multimaps:
        for modmap in conditional_multimaps:
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


# from .lib.benchit import *
def find_keystate_or_new(inkey, action):
    if inkey not in _key_states:
        return Keystate(inkey=inkey, action=action)

    ks = _key_states[inkey]
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
    if event.type != ecodes.EV_KEY:
        _output.send_event(event)
        return

    context = KeyContext(device_name)
    action = Action(event.value)
    key = Key(event.code)

    ks = find_keystate_or_new(
        inkey=key,
        action=action
    )

    debug()
    debug(f"in {key} ({action})", ctx="II")


    # if there is an X error (we don't have any window context)
    # then we turn off all mappings until it's resolved and act
    # more or less as a pass thru for all input => output
    if context.x_error:
        ks.key = ks.key or ks.inkey

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

    if Modifier.is_key_modifier(key):
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
                suspend_or_resuspend_keys(_TIMEOUTS["suspend"])

        if not hold_output:
            _output.send_key_action(key, action)
            if action.is_released():
                keystate.exerted_on_output = False

    elif keystate.is_multi and action.just_pressed():
        # debug("multi pressed", key)
        keystate.suspended = True
        update_pressed_states(keystate)
        suspend_keys(_TIMEOUTS["multipurpose"])

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
            resume_keys()
            transform_key(key, action, context)
            update_pressed_states(keystate)
    else:
        # not a modifier or a multi-key, so pass straight to transform
        transform_key(key, action, context)

    if action.just_pressed():
        _last_key = key


def transform_key(key, action, ctx):
    global _active_keymaps
    is_top_level = False

    # if we do have window context information we essentially short-circuit
    # the keymapper, acting in essentially a pass thru mode sending what is
    # typed straight thru from input to output
    if ctx.x_error:
        resume_keys()
        _output.send_key_action(key, action)
        return

    combo = Combo(get_pressed_mods(), key)

    if _active_keymaps is escape_next_key:
        debug(f"Escape key: {combo} => {key}")
        _output.send_key_action(key, action)
        _active_keymaps = None
        return

    # Decide keymap(s)
    if _active_keymaps is None:
        is_top_level = True
        _active_keymaps = [km for km in _KEYMAPS if km.matches(ctx)]

    for keymap in _active_keymaps:
        if combo not in keymap:
            continue

        if logger.VERBOSE:
            keymap_names = [map.name for map in _active_keymaps]
            name_list = ", ".join(keymap_names)
            debug("")
            debug(
                f"WM_CLS '{ctx.wm_class}' | "
                f"DV '{ctx.device_name}' | "
                f"KMAPS = [{name_list}]")
            debug(f"  COMBO: {combo} => {keymap[combo]} [{keymap.name}]")

        held = get_pressed_states()
        for ks in held:
            # if we are triggering a momentary on the output we can mark ourselves
            # spent, but if the key is already asserted on the output then we cannot
            # count it as spent and must hold it so that it's release later will
            # trigger the release on the output
            if not _output.is_mod_pressed(ks.key):
                ks.spent = True
        debug("spent modifiers", [_.key for _ in held if _.spent])
        reset_mode = handle_commands(keymap[combo], key, action, combo)
        if reset_mode:
            _active_keymaps = None
        return

    # Not found in all KEYMAPS
    if is_top_level:
        # need to output any keys we've suspended
        resume_keys()
        # If it's top-level, pass through keys
        _output.send_key_action(key, action)

    _active_keymaps = None


# ─── AUTO BIND AND STICKY KEYS SUPPORT ──────────────────────────────────────────


# binds the first input modifier to the first output modifier
def simple_sticky(combo, output_combo):
    inmods = combo.modifiers
    outmods = output_combo.modifiers
    if len(inmods) == 0 or len(outmods) == 0:
        return {}
    inkey = inmods[0].get_key()
    outkey = outmods[0].get_key()

    if inkey in _key_states:
        ks = _key_states[inkey]
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

    stuck = {inkey: outkey}
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


# ─── COMMAND PROCESSING ───────────────────────────────────────────────────────


def handle_commands(commands, key, action, input_combo=None):
    """
    returns: reset_mode (True/False) if this is True, _active_keymaps will be reset
    """
    global _active_keymaps
    _next_bind = False

    if not isinstance(commands, list):
        commands = [commands]

    # if input_combo and input_combo.hint == ComboHint.BIND:
        # auto_sticky(commands[0], input_combo)

    # resuspend any keys still not exerted on the output, giving
    # them a chance to be lifted or to trigger another macro as-is
    if is_suspended():
        resuspend_keys(_TIMEOUTS["suspend"])

    with _output.suspend_when_lifting():
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
                _active_keymaps = escape_next_key
                return False
            elif command is ComboHint.BIND:
                _next_bind = True
                continue
            elif command is ignore_key:
                debug("ignore_key", key)
                return True
            # Go to next keymap
            elif isinstance(command, Keymap):
                _active_keymaps = [command]
                return False
            elif command is None:
                pass
            else:
                debug(f"unknown command {command}")
            _next_bind = False
        # Reset keymap in ordinary flow
        return True
