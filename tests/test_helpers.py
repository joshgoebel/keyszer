
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import sys

sys.modules["keyszer.xorg"] = __import__('lib.xorg_mock',
    None, None, ["get_active_window_wm_class"])
from lib.api import *
from lib.uinput_stub import UInputStub

from keyszer.config_api import *
from keyszer.lib import logger
from keyszer.models.action import Action
from keyszer.models.key import Key
from keyszer.output import setup_uinput
from keyszer.transform import boot_config, on_event, reset_transform

logger.VERBOSE = True
import asyncio
import re

import pytest
import pytest_asyncio
from evdev.ecodes import EV_KEY, EV_SYN
from evdev.events import InputEvent

_out = None

def setup_function(module):
    global _out
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _out = UInputStub()
    setup_uinput(_out)
    reset_configuration()
    reset_transform()

@pytest.mark.looptime(False)
async def test_wm_class_match_and_inverse():

    conditional(wm_class_match("Firefox"),
        keymap("Firefox",{
            K("a"): K("b"),
        }))
    conditional(not_wm_class_match("Firefox"),
        keymap("not firefox",{
            K("a"): K("c"),
        }))

    boot_config()

    window("Firefox")
    hit(Key.A)

    window("shell")
    hit(Key.A)

    assert _out.keys() == [
        (PRESS, Key.B),
        (RELEASE, Key.B),
        (PRESS, Key.C),
        (RELEASE, Key.C),
    ]
