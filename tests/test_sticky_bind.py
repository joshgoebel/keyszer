import asyncio
import warnings

import pytest
import pytest_asyncio
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
