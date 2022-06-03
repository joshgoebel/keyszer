
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

import sys
sys.modules["xkeysnail.xorg"] = __import__('lib.xorg_mock',
    None, None, ["get_active_window_wm_class"])
from xkeysnail.output import setup_uinput
from xkeysnail.key import Key, Action
from xkeysnail.config_api import *
from xkeysnail.transform import boot_config, on_event, reset_transform
from lib.uinput_stub import UInputStub
from lib.api import *

from evdev.ecodes import EV_KEY, EV_SYN
from evdev.events import InputEvent
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

@pytest.mark.looptime(False)
async def test_multiple_keys_at_once():

    window("Firefox")
    keymap(re.compile("Firefox"),{
        K("C-M-j"): K("C-TAB"),
        K("C-M-k"): K("C-Shift-TAB"),
    })

    boot_config()

    press(Key.LEFT_CTRL)
    press(Key.LEFT_ALT)
    press(Key.J)    
    release(Key.J)
    release(Key.LEFT_ALT)
    release(Key.LEFT_CTRL)
    assert _out.keys() == [
        (PRESS, Key.LEFT_CTRL),
        (PRESS, Key.TAB),
        (RELEASE, Key.TAB),
        (RELEASE, Key.LEFT_CTRL),
    ]

@pytest.mark.looptime(False)
async def test_multiple_combos_without_releasing_all_nonsticky():
    # NOTE: if we were sticky then techcanily the C on the output
    # should probalby be held without release
    window("Firefox")
    keymap(re.compile("Firefox"),{
        K("C-M-j"): K("C-TAB"),
        K("C-M-k"): K("C-Shift-TAB"),
    })

    boot_config()

    press(Key.LEFT_CTRL)
    press(Key.LEFT_ALT)
    press(Key.J)    
    release(Key.J)
    press(Key.K)            
    release(Key.K)
    release(Key.LEFT_ALT)
    release(Key.LEFT_CTRL)

    assert _out.keys() == [
        (PRESS, Key.LEFT_CTRL),
        (PRESS, Key.TAB),
        (RELEASE, Key.TAB),
        (RELEASE, Key.LEFT_CTRL),
        
        (PRESS, Key.LEFT_CTRL),
        (PRESS, Key.LEFT_SHIFT),
        (PRESS, Key.TAB),
        (RELEASE, Key.TAB),
        (RELEASE, Key.LEFT_SHIFT),
        (RELEASE, Key.LEFT_CTRL),
    ]
