import pytest_asyncio
import pytest
import asyncio
from keyszer.lib import logger
from evdev.events import InputEvent
from evdev.ecodes import EV_KEY, EV_SYN
from lib.api import *
from lib.uinput_stub import UInputStub
from keyszer.transform import suspend_keys, \
    resume_keys, \
    boot_config, \
    on_event, \
    is_suspended, \
    reset_transform
from keyszer.config_api import *
from keyszer import input
from keyszer.models.action import Action
from keyszer.models.key import Key
from keyszer.output import setup_uinput
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


logger.VERBOSE = True

_out = None


def setup_function(module):
    global _out
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _out = UInputStub()
    setup_uinput(_out)
    reset_transform()
    reset_configuration()


async def test_single_key_auto_sticky():

    keymap("default", {
        K("Super-TAB"): [bind, K("C-TAB") ],
        K("Super-Shift-Tab"): K("C-Shift-TAB"),
    })

    boot_config()

    press(Key.LEFT_META)
    hit(Key.TAB)
    hit(Key.TAB)
    # shift doesn't do anything magical here, this all still works just because
    # LEFT_META is still sticky because we're still asserting it
    press(Key.LEFT_SHIFT)
    hit(Key.TAB)
    hit(Key.TAB)
    release(Key.LEFT_SHIFT)
    hit(Key.TAB)
    hit(Key.TAB)
    release(Key.LEFT_META)

    assert _out.keys() == [
        (PRESS, Key.LEFT_CTRL),
        (PRESS, Key.TAB),
        (RELEASE, Key.TAB),
        (PRESS, Key.TAB),
        (RELEASE, Key.TAB),

        (PRESS, Key.LEFT_SHIFT),
        (PRESS, Key.TAB),
        (RELEASE, Key.TAB),
        (RELEASE, Key.LEFT_SHIFT),

        (PRESS, Key.LEFT_SHIFT),
        (PRESS, Key.TAB),
        (RELEASE, Key.TAB),
        (RELEASE, Key.LEFT_SHIFT),

        (PRESS, Key.TAB),
        (RELEASE, Key.TAB),
        (PRESS, Key.TAB),
        (RELEASE, Key.TAB),
        (RELEASE, Key.LEFT_CTRL)

    ]
