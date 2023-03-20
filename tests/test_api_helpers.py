import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from evdev.ecodes import EV_KEY, EV_SYN
from evdev.events import InputEvent
from lib.api import *
from lib.uinput_stub import UInputStub

from keyszer import input
from keyszer.config_api import *
from keyszer.lib import logger
from keyszer.models.action import Action
from keyszer.models.key import Key
from keyszer.output import setup_uinput
from keyszer.transform import (
    boot_config,
    is_suspended,
    on_event,
    reset_transform,
    resume_keys,
    suspend_keys,
)

logger.VERBOSE = True
import asyncio

import pytest
import pytest_asyncio

_out = None


class Context_with_CapsL_OFF:
    def __init__(self):
        self.capslock_on = False

ctx = Context_with_CapsL_OFF()

class Context_with_CapsL_ON:
    def __init__(self):
        self.capslock_on = True

ctx_ON = Context_with_CapsL_ON()


def setup_function(module):
    global _out
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _out = UInputStub()
    setup_uinput(_out)
    reset_transform()
    reset_configuration()

def test_combo_single_letter():
    combo = C("A")
    assert Key.A == combo.key
    assert [] == combo.modifiers

def test_combo_single_simple_number():
    combo = C("1")
    assert Key.KEY_1 == combo.key
    assert [] == combo.modifiers

def test_combo_simple():
    combo = C("Alt-A")
    assert Key.A == combo.key
    assert [Modifier.ALT] == combo.modifiers

def test_to_US_keystrokes_simple():
    out = to_US_keystrokes("hello5")(ctx)
    assert [Key.H, Key.E, Key.L, Key.L, Key.O, Key.KEY_5] == out

def test_to_US_keystrokes_simple_with_shift():
    out = to_US_keystrokes("Hello")(ctx)
    assert [C("Shift-H"), Key.E, Key.L, Key.L, Key.O] == out

def test_to_US_keystrokes_simple_with_CapsL_ON():
    out = to_US_keystrokes("Hello")(ctx_ON)
    assert [C("h"), C("Shift-e"), C("Shift-l"), C("Shift-l"), C("Shift-o")] == out

# TODO: it wasn't clear what to use here since we support
# - most all ASCII now so we went with BELL but this may
# - just be better to remove in the future
def test_to_US_keystrokes_unsupported_character():
    with pytest.raises(CharacterNotSupported) as e:
        out_fn = to_US_keystrokes("\u0007")
        out_inner = out_fn(ctx)[0]
        out = out_inner(ctx)
        assert e == "The character \u0007 is not supported by `to_US_keystrokes` yet"

def test_to_US_keystrokes_too_long():
    with pytest.raises(TypingTooLong) as e:
        out = to_US_keystrokes("lasdjlkad jlkasjd laksjdlkasj dlkasj dlk ajlkd jaldkjal"
            "asdkjhasdkjahkjdhaskjdhakjdhkjadh kajhdkjashdkashdkjajhdajksd")
        assert e == "`to_US_keystrokes` only supports strings of 100 characters or less"

def test_to_US_keystrokes_extended_ascii():
    out_fn = to_US_keystrokes("\u00ff")
    out_inner = out_fn(ctx)[0]
    out = out_inner(ctx)
    assert [    C("Shift-Ctrl-U"),
                Key.F, Key.F,
                Key.ENTER   ] == out

def test_ascii_keys():
    out = to_US_keystrokes("`-=[]\\;',./")(ctx)
    assert [    Key.GRAVE, Key.MINUS, Key.EQUAL, Key.LEFT_BRACE,
                Key.RIGHT_BRACE, Key.BACKSLASH, Key.SEMICOLON,
                Key.APOSTROPHE, Key.COMMA, Key.DOT, Key.SLASH   ] == out

def test_ascii_with_shift_keys():
    out = to_US_keystrokes('~!@#$%^&*()_+{}|:"<>?')(ctx)
    assert [C("Shift-Grave"),C("Shift-1"),C("Shift-2"),C("Shift-3"),C("Shift-4"),
            C("Shift-5"),C("Shift-6"),C("Shift-7"),C("Shift-8"),C("Shift-9"),
            C("Shift-0"),C("Shift-Minus"),C("Shift-Equal"),C("Shift-Left_Brace"),
            C("Shift-Right_Brace"),C("Shift-Backslash"),C("Shift-Semicolon"),
            C("Shift-Apostrophe"),C("Shift-Comma"),C("Shift-Dot"),C("Shift-Slash")
    ] == out

def test_to_US_keystrokes_unicode():

    # with CapsLock OFF

    out_fn = to_US_keystrokes("🎉")
    out_inner = out_fn(ctx)[0]
    out = out_inner(ctx)
    assert [    C("Shift-Ctrl-U"),
                Key.KEY_1, Key.F, Key.KEY_3, Key.KEY_8, Key.KEY_9,
                Key.ENTER   ] == out

    out_fn = to_US_keystrokes("\U0001f389")
    out_inner = out_fn(ctx)[0]
    out = out_inner(ctx)
    assert [    C("Shift-Ctrl-U"),
                Key.KEY_1, Key.F, Key.KEY_3, Key.KEY_8, Key.KEY_9,
                Key.ENTER   ] == out

    # with CapsLock ON

    out_fn = to_US_keystrokes("🎉")
    out_inner = out_fn(ctx_ON)[0]
    out = out_inner(ctx_ON)
    assert [    Key.CAPSLOCK, C("Shift-Ctrl-U"),
                Key.KEY_1, Key.F, Key.KEY_3, Key.KEY_8, Key.KEY_9,
                Key.ENTER, Key.CAPSLOCK   ] == out

    out_fn = to_US_keystrokes("\U0001f389")
    out_inner = out_fn(ctx_ON)[0]
    out = out_inner(ctx_ON)
    assert [    Key.CAPSLOCK, C("Shift-Ctrl-U"),
                Key.KEY_1, Key.F, Key.KEY_3, Key.KEY_8, Key.KEY_9,
                Key.ENTER, Key.CAPSLOCK   ] == out

def test_unicode_keystrokes():
    ctx_OFF = Context_with_CapsL_OFF()

    # with CapsLock OFF

    with pytest.raises(UnicodeNumberToolarge) as e:
        out = unicode_keystrokes(0x110000)(ctx_OFF)
        assert e == "too large for Unicode keyboard entry."

    out = unicode_keystrokes(0x00ff)(ctx_OFF)
    assert [    C("Shift-Ctrl-U"),
                Key.F, Key.F,
                Key.ENTER   ] == out

    out = unicode_keystrokes(0x10fad)(ctx_OFF)
    assert [    C("Shift-Ctrl-U"),
                Key.KEY_1, Key.KEY_0, Key.F, Key.A, Key.D,
                Key.ENTER   ] == out

    # with CapsLock ON

    out = unicode_keystrokes(0x00ff)(ctx_ON)
    assert [    Key.CAPSLOCK, C("Shift-Ctrl-U"),
                Key.F, Key.F,
                Key.ENTER, Key.CAPSLOCK   ] == out

    out = unicode_keystrokes(0x10fad)(ctx_ON)
    assert [    Key.CAPSLOCK, C("Shift-Ctrl-U"),
                Key.KEY_1, Key.KEY_0, Key.F, Key.A, Key.D,
                Key.ENTER, Key.CAPSLOCK   ] == out
