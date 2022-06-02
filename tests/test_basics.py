import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

from xkeysnail.output import setup_uinput
from xkeysnail.key import Key, Action
from xkeysnail.config_api import *
from xkeysnail.transform import suspend_keys, \
    resume_keys, \
    boot_config, \
    on_event, \
    suspended
from lib.uinput_stub import UInputStub
from lib.api import *

from evdev.ecodes import EV_KEY, EV_SYN
from evdev.events import InputEvent
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
    reset_configutation()

@pytest.mark.looptime
async def test_suspended():
    suspend_keys()
    await asyncio.sleep(0.1)
    assert suspended()

@pytest.mark.looptime
async def test_unsuspend_after_second():
    suspend_keys()
    await asyncio.sleep(2)
    assert not suspended()

async def test_plain_keys():
    boot_config()

    hit(Key.J)
    hit(Key.ESC)
    assert _out.keys() == [
        (PRESS, Key.J),
        (RELEASE, Key.J),
        (PRESS, Key.ESC),
        (RELEASE, Key.ESC),
    ]

async def test_multiple_keys_at_once():
    boot_config()

    press(Key.J)
    press(Key.K)
    release(Key.K)
    release(Key.J)
    assert _out.keys() == [
        (PRESS, Key.J),
        (PRESS, Key.K),
        (RELEASE, Key.K),
        (RELEASE, Key.J),
    ]

async def test_unmapped_combo():
    boot_config()

    press(Key.LEFT_CTRL)
    press(Key.LEFT_SHIFT)
    press(Key.F)
    release(Key.F)
    release(Key.LEFT_SHIFT)
    release(Key.LEFT_CTRL)
    assert _out.keys() == [
        (PRESS, Key.LEFT_CTRL),
        (PRESS, Key.LEFT_SHIFT),
        (PRESS, Key.F),
        (RELEASE, Key.F),
        (RELEASE, Key.LEFT_SHIFT),
        (RELEASE, Key.LEFT_CTRL),
    ]