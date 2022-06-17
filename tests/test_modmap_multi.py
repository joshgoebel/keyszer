import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

import sys
sys.modules["keyszer.xorg"] = __import__('lib.xorg_mock',
    None, None, ["get_active_window_wm_class"])
from keyszer.output import setup_uinput
from keyszer.models.key import Key
from keyszer.models.action import Action
from keyszer.config_api import *
from keyszer.transform import suspend_keys, \
    resume_keys, \
    boot_config, \
    on_event, \
    is_suspended, \
    reset_transform
from lib.uinput_stub import UInputStub
from lib.api import *

from evdev.ecodes import EV_KEY, EV_SYN
from evdev.events import InputEvent
from keyszer.lib import logger
logger.VERBOSE = True
import asyncio
import pytest
import pytest_asyncio
import re


_out = None

def setup_function(module):
    global _out
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _out = UInputStub()
    setup_uinput(_out)
    reset_configuration()
    reset_transform()

async def test_weird_abc_to_ctrl_alt_del():
    multipurpose_modmap("default",{
        Key.A: [Key.A, Key.LEFT_CTRL],
        Key.B: [Key.B, Key.LEFT_ALT],
    })
    modmap("default",
        {Key.C : Key.DELETE}
    )

    boot_config()

    press(Key.A) # ctrl
    press(Key.B) # alt
    press(Key.C) # del
    release(Key.C)
    release(Key.B)
    release(Key.A)
    assert _out.keys() == [
        (PRESS, Key.LEFT_CTRL),
        (PRESS, Key.LEFT_ALT),
        (PRESS, Key.DELETE),
        (RELEASE, Key.DELETE),
        (RELEASE, Key.LEFT_ALT),
        (RELEASE, Key.LEFT_CTRL)
    ]  


async def test_enter_is_enter_and_control():
    multipurpose_modmap("default",
        # Enter is enter when pressed and released. Control when held down.
        {Key.ENTER: [Key.ENTER, Key.RIGHT_CTRL]}
    )

    boot_config()

    hit(Key.ENTER)
    #
    press(Key.ENTER)
    press(Key.F)
    release(Key.F)
    release(Key.ENTER)

    assert _out.keys() == [
        # first enter should register as enter
        (PRESS, Key.ENTER),
        (RELEASE, Key.ENTER),
        # next is a control sequence
        (PRESS, Key.RIGHT_CTRL),
        (PRESS, Key.F),
        (RELEASE, Key.F),
        (RELEASE, Key.RIGHT_CTRL),
    ]  

@pytest.mark.looptime
async def test_held_enter_is_mod_after_timeout():

    multipurpose_modmap("default",
        # Enter is enter when pressed and released. Control when held down.
        {Key.ENTER: [Key.ENTER, Key.RIGHT_CTRL]}
    )

    boot_config()

    press(Key.ENTER)
    await asyncio.sleep(2)
    release(Key.ENTER)

    assert _out.keys() == [
        (PRESS, Key.RIGHT_CTRL),
        (RELEASE, Key.RIGHT_CTRL),
    ]  
