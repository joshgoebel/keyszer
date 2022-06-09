import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

from keyszer.output import setup_uinput
from keyszer.key import Key
from keyszer.models.action import Action
from keyszer import input
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
from keyszer import logger
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

@pytest.mark.looptime
async def test_suspended():
    suspend_keys()
    await asyncio.sleep(0.1)
    assert is_suspended()

@pytest.mark.looptime
async def test_unsuspend_after_second():
    suspend_keys()
    await asyncio.sleep(2)
    assert not is_suspended()

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

async def test_terminate_should_release_keys():
    boot_config()

    press(Key.LEFT_CTRL)
    press(Key.LEFT_SHIFT)
    press(Key.F)

    with pytest.raises(SystemExit):
        input.sig_term()

    assert _out.keys() == [
        (PRESS, Key.LEFT_CTRL),
        (PRESS, Key.LEFT_SHIFT),
        (PRESS, Key.F),
        # sig term should ensure the releases happen before we terminate
        (RELEASE, Key.F),
        (RELEASE, Key.LEFT_SHIFT),
        (RELEASE, Key.LEFT_CTRL),
    ]