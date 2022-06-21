from evdev import ecodes
from evdev.uinput import UInput
from .models.action import Action
from .models.combo import Combo
from .models.modifier import Modifier
from .lib.logger import debug

VIRT_DEVICE_PREFIX = "Keyszer VIRTUAL"

# Remove all buttons so udev doesn't think keyszer is a joystick
_KEYBOARD_KEYS = ecodes.keys.keys() - ecodes.BTN

# But we want mouse buttons, so let's enumerate those and add them
# back into the set of buttons we'll watch and use
_MOUSE_BUTTONS = {256: ['BTN_0', 'BTN_MISC'],
                  257: 'BTN_1',
                  258: 'BTN_2',
                  259: 'BTN_3',
                  260: 'BTN_4',
                  261: 'BTN_5',
                  262: 'BTN_6',
                  263: 'BTN_7',
                  264: 'BTN_8',
                  265: 'BTN_9',
                  272: ['BTN_LEFT', 'BTN_MOUSE'],
                  274: 'BTN_MIDDLE',
                  273: 'BTN_RIGHT'}
_KEYBOARD_KEYS.update(_MOUSE_BUTTONS)

_uinput = None


def real_uinput():
    return UInput(name=f"{VIRT_DEVICE_PREFIX} Keyboard",
                  events={ecodes.EV_KEY: _KEYBOARD_KEYS,
                          ecodes.EV_REL: set([0, 1, 6, 8, 9])})


# TODO: improve injection?
def setup_uinput(uinput=None):
    global _uinput
    _uinput = uinput or real_uinput()


class Output:

    def __init__(self):
        self._pressed_modifier_keys = set()
        self._pressed_keys = set()
        self._suspended_mod_keys = []
        self._suspend_depth = 0

    def __update_pressed_modifier_keys(self, key, action):
        if not Modifier.is_key_modifier(key):
            return

        if action.is_pressed():
            self._pressed_modifier_keys.add(key)
        else:
            self._pressed_modifier_keys.discard(key)

    def __update_pressed_keys(self, key, action):
        if action.is_pressed():
            self._pressed_keys.add(key)
        else:
            self._pressed_keys.discard(key)

    def diag(self):
        print("*** OUTPUT ***")
        print("_pressed_modifier_keys:")
        print(self._pressed_modifier_keys)
        print("_pressed_keys")
        print(self._pressed_keys)
        print("_suspended_mod_keys")
        print(self._suspended_mod_keys)
        print("_suspend_depth", self._suspend_depth)

    def __send_sync(self):
        _uinput.syn()

    def is_mod_pressed(self, key):
        return key in self._pressed_modifier_keys

    def is_pressed(self, key):
        return key in self._pressed_keys

    def send_event(self, event):
        _uinput.write_event(event)
        # TODO: do we need this? I think not.
        # self.__send_sync()

    def send_key_action(self, key, action):
        self.__update_pressed_modifier_keys(key, action)
        self.__update_pressed_keys(key, action)
        _uinput.write(ecodes.EV_KEY, key, action)
        debug(action, key, ctx="OO")
        self.__send_sync()

    def send_combo(self, combo):
        released_modifiers_keys = []

        extra_modifier_keys = self._pressed_modifier_keys.copy()
        missing_modifiers = combo.modifiers.copy()
        for pressed_key in self._pressed_modifier_keys:
            for modifier in combo.modifiers:
                if pressed_key in modifier.get_keys():
                    extra_modifier_keys.remove(pressed_key)
                    missing_modifiers.remove(modifier)

        for modifier_key in extra_modifier_keys:
            self.send_key_action(modifier_key, Action.RELEASE)
            released_modifiers_keys.append(modifier_key)

        pressed_modifier_keys = []
        for modifier in missing_modifiers:
            modifier_key = modifier.get_key()
            self.send_key_action(modifier_key, Action.PRESS)
            pressed_modifier_keys.append(modifier_key)

        # normal key portion of the combo
        self.send_key_action(combo.key, Action.PRESS)
        self.send_key_action(combo.key, Action.RELEASE)

        for modifier in reversed(pressed_modifier_keys):
            self.send_key_action(modifier, Action.RELEASE)

        if self.__is_suspending():  # sleep the keys
            self._suspended_mod_keys.extend(released_modifiers_keys)
        else:  # reassert the keys
            for modifier in reversed(released_modifiers_keys):
                self.send_key_action(modifier, Action.PRESS)

    def send_key(self, key):
        self.send_combo(Combo(None, key))

    def shutdown(self):
        # raise all keys for shutdown so that we have a clean state
        # on uninput with any watching apps as we're exiting
        for key in self._pressed_keys.copy():
            self.send_key_action(key, Action.RELEASE)
        for key in self._pressed_modifier_keys.copy():
            self.send_key_action(key, Action.RELEASE)
        _uinput.close()

    # ─── SUSPEND ──────────────────────────────────────────────────────────────────

    # self._suspended_mod_keys : list
    # self._suspend_depth : int

    def suspend_when_lifting(self):
        return SuspendWhenLifting(self)

    def __is_suspending(self):
        return self._suspend_depth > 0

    def __reexert(self, key):
        self.send_key_action(key, Action.PRESS)

    # the function that calls this is re-entrant so we need to make sure
    # we can suspend/resume to multiple depths without losing track of
    # where we are, though this SHOULD be more of a theoretical concern
    def allow_suspend(self):
        self._suspend_depth += 1

    def disallow_suspend(self):
        self._suspend_depth -= 1

        if not self.__is_suspending():
            for mod in self._suspended_mod_keys:
                self.__reexert(mod)
            self._suspended_mod_keys.clear()


class SuspendWhenLifting:
    """
    wraps the suspending pattern for output

    When output release keys it doesn't need for the current combo instead
    of re-exerting them immediatley after it will hold them until it is
    unsuspended (which is currently immediately when a sequence ends)
    """
    def __init__(self, output):
        self._output = output

    def __enter__(self):
        self._output.allow_suspend()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._output.disallow_suspend()
        return False
