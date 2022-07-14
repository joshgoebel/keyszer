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

def test_type_simple():
    out = to_US_keystrokes("hello5")
    assert [Key.H, Key.E, Key.L, Key.L, Key.O, Key.KEY_5] == out

def test_type_simple_with_shift():
    out = to_US_keystrokes("Hello")
    assert [C("Shift-H"), Key.E, Key.L, Key.L, Key.O] == out

def test_type_unsupported_character():
    with pytest.raises(CharacterNotSupported) as e:
        out = to_US_keystrokes("{")
        assert e.message == "The character { is not supported by `type` yet"

def test_type_too_long():
    with pytest.raises(TypingTooLong) as e:
        out = to_US_keystrokes("lasdjlkad jlkasjd laksjdlkasj dlkasj dlk ajlkd jaldkjal"
            "asdkjhasdkjahkjdhaskjdhakjdhkjadh kajhdkjashdkashdkjajhdajksd")
        assert e.message == "`type` only supports strings of 100 characters or less"

def test_type_extended_ascii():
    out = to_US_keystrokes("\u00ff")
    assert [ C("Shift-Ctrl-U"),
             Key.F, Key.F,
             Key.ENTER] == out

def test_ascii_keys():
    out = to_US_keystrokes("`-=[]\\;',./")
    assert [ Key.GRAVE, Key.MINUS, Key.EQUAL, Key.LEFT_BRACE,
             Key.RIGHT_BRACE, Key.BACKSLASH, Key.SEMICOLON,
             Key.APOSTROPHE, Key.COMMA, Key.DOT, Key.SLASH
             ] == out

def test_ascii_with_shift_keys():
    out = to_US_keystrokes('~!@#$%^&*()_+{}|:"<>?')
    assert [C("Shift-Grave"),C("Shift-1"),C("Shift-2"),C("Shift-3"),C("Shift-4"),
            C("Shift-5"),C("Shift-6"),C("Shift-7"),C("Shift-8"),C("Shift-9"),
            C("Shift-0"),C("Shift-Minus"),C("Shift-Equal"),C("Shift-Left_Brace"),
            C("Shift-Right_Brace"),C("Shift-Backslash"),C("Shift-Semicolon"),
            C("Shift-Apostrophe"),C("Shift-Comma"),C("Shift-Dot"),C("Shift-Slash")
             ] == out

def test_type_unicode():
    out = to_US_keystrokes("🎉")
    assert [ C("Shift-Ctrl-U"),
             Key.KEY_1, Key.F, Key.KEY_3, Key.KEY_8, Key.KEY_9,
             Key.ENTER] == out

    out = to_US_keystrokes("\U0001f389")
    assert [ C("Shift-Ctrl-U"),
             Key.KEY_1, Key.F, Key.KEY_3, Key.KEY_8, Key.KEY_9,
             Key.ENTER] == out

def test_uncode_keystrokes():
    out = unicode_keystrokes(0x00ff)
    assert [ C("Shift-Ctrl-U"),
             Key.F, Key.F,
             Key.ENTER] == out

    out = unicode_keystrokes(0x10fad)
    assert [ C("Shift-Ctrl-U"),
             Key.KEY_1, Key.KEY_0, Key.F, Key.A, Key.D,
             Key.ENTER] == out

    with pytest.raises(UnicodeNumberToolarge) as e:
        out = unicode_keystrokes(0x110000)
        assert e.message == "too large for Unicode keyboard entry."
