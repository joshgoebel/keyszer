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


async def test_nested_keymaps():
    keymap("Firefox",{
        K("C-a"): {
            K("C-b"): {
                K("C-c"): K("Alt-KEY_9")
            }
        }
    })

    boot_config()

    press(Key.LEFT_CTRL)
    press(Key.A)
    release(Key.A)
    press(Key.B)
    release(Key.B)
    press(Key.C)
    release(Key.C)
    release(Key.LEFT_CTRL)

    # thanks to escaping with just get a B rather
    # than the C-b combo
    assert _out.keys() == [
        (PRESS, Key.LEFT_ALT),
        (PRESS, Key.KEY_9),
        (RELEASE, Key.KEY_9),
        (RELEASE, Key.LEFT_ALT),
    ]


async def test_trigger_immediately():
    keymap("Firefox",{
        K("C-a"): {
            immediately: K("8"),
            K("C-b"): K("Alt-KEY_9")
        }
    })

    boot_config()

    press(Key.LEFT_CTRL)
    press(Key.A)
    release(Key.A)
    press(Key.B)
    release(Key.B)
    release(Key.LEFT_CTRL)

    # the 8 (as the immediate effect of the C-a combo) is pressed
    # first, and without any modifiers
    assert _out.keys() == [
        (PRESS, Key.KEY_8),
        (RELEASE, Key.KEY_8),
        (PRESS, Key.LEFT_ALT),
        (PRESS, Key.KEY_9),
        (RELEASE, Key.KEY_9),
        (RELEASE, Key.LEFT_ALT),
    ]
