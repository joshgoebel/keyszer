from evdev.ecodes import EV_KEY
from evdev.events import InputEvent
from lib.xorg_mock import set_window

from keyszer.models.action import PRESS, RELEASE, REPEAT
from keyszer.transform import on_event

class MockKeyboard:
    name = "generic keyboard"


_kb = MockKeyboard()

def using_keyboard(name):
    global _kb
    _kb.name = name


def window(name):
    set_window(name)


def press(key):
    ev = InputEvent(0, 0, EV_KEY, key, PRESS)
    on_event(ev, _kb)


def release(key):
    ev = InputEvent(0, 0, EV_KEY, key, RELEASE)
    on_event(ev, _kb)

def repeat(key):
    ev = InputEvent(0, 0, EV_KEY, key, REPEAT)
    on_event(ev, _kb)


def hit(key):
    press(key)
    release(key)
