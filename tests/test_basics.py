import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

from keyszer.output import setup_uinput
from keyszer.models.key import Key
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
from keyszer.lib import logger
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
    suspend_keys(1)
    await asyncio.sleep(0.1)
    assert is_suspended()

@pytest.mark.looptime
async def test_unsuspend_after_second():
    suspend_keys(1)
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

async def test_escape_next_key():
    keymap("Firefox",{
        K("C-j"): escape_next_key,
        K("C-b"): K("Alt-TAB"),
    })

    boot_config()

    press(Key.LEFT_CTRL)
    press(Key.J)
    release(Key.J)
    press(Key.B)
    release(Key.B)
    release(Key.LEFT_CTRL)

    # thanks to escaping with just get a B rather
    # than the C-b combo
    assert _out.keys() == [
        (PRESS, Key.B),
        (RELEASE, Key.B),
    ]

@pytest.mark.looptime
async def test_after_combo_should_lift_exerted_keys():
    keymap("Firefox",{
        K("C-j"): K("Alt-TAB"),
    })

    boot_config()

    press(Key.LEFT_CTRL)
    await asyncio.sleep(2)
    press(Key.J)
    release(Key.J)
    release(Key.LEFT_CTRL)

    assert _out.keys() == [
        (PRESS, Key.LEFT_CTRL),
        # beginning of combo will release left ctrl since it's not part of combo
        (RELEASE, Key.LEFT_CTRL),
        (PRESS, Key.LEFT_ALT),
        (PRESS, Key.TAB),
        (RELEASE, Key.TAB),
        (RELEASE, Key.LEFT_ALT),
        # but now we reassert left ctrl
        (PRESS, Key.LEFT_CTRL),
        # and finally we release it
        (RELEASE, Key.LEFT_CTRL),
    ]

@pytest.mark.looptime
async def test_sticky_combo_should_lift_exerted_keys_before_combo():
    keymap("Firefox",{
        K("C-j"): [bind, K("Alt-TAB")],
    })

    boot_config()

    press(Key.LEFT_CTRL)
    await asyncio.sleep(2)
    press(Key.J)
    release(Key.J)
    release(Key.LEFT_CTRL)

    assert _out.keys() == [
        (PRESS, Key.LEFT_CTRL),
        # beginning of combo will release left ctrl since it's the inkey
        # sticky and no longer needed once we assert the outkey sticky (alt)
        (RELEASE, Key.LEFT_CTRL),
        (PRESS, Key.LEFT_ALT),
        (PRESS, Key.TAB),
        (RELEASE, Key.TAB),
        (RELEASE, Key.LEFT_ALT),
    ]

@pytest.mark.looptime
async def test_sticky_combo_with_sticky_inkey_in_output_combo():
    keymap("Firefox",{
        K("C-j"): [bind, K("Alt-C-TAB")],
    })

    boot_config()

    press(Key.LEFT_CTRL)
    await asyncio.sleep(2)
    press(Key.J)
    release(Key.J)
    release(Key.LEFT_CTRL)

    assert _out.keys() == [
        (PRESS, Key.LEFT_CTRL),
        # we never lift left control (that was held)
        # because it's part of the output combo
        (PRESS, Key.LEFT_ALT),
        (PRESS, Key.TAB),
        (RELEASE, Key.TAB),
        (RELEASE, Key.LEFT_ALT),
        (RELEASE, Key.LEFT_CTRL),
    ]


@pytest.mark.looptime
async def test_real_inputs_do_not_reexert_during_combo_sequence():
    keymap("default",{
        K("C-Alt-j"): [
            K("C-Alt-X"),
            K("C-Y"),
            K("Z"),
            K("A"),
        ],
    })

    boot_config()

    press(Key.LEFT_CTRL)
    press(Key.LEFT_ALT)
    # we want to get past suspend so these keys
    # are actually pushed to the ouput
    await asyncio.sleep(2)
    press(Key.J)
    release(Key.J)
    release(Key.LEFT_CTRL)
    release(Key.LEFT_ALT)

    assert _out.keys() == [
        (PRESS, Key.LEFT_CTRL),
        (PRESS, Key.LEFT_ALT),
        (PRESS, Key.X),
        (RELEASE, Key.X),
        # next combo - K("C-Y"),
        (RELEASE, Key.LEFT_ALT), # alt isn't needed, lifted
        (PRESS, Key.Y),
        (RELEASE, Key.Y),
        # last combo - K("Z"),
        (RELEASE, Key.LEFT_CTRL), # ctrl isn't needed, lifted
        (PRESS, Key.Z),
        (RELEASE, Key.Z),
        (PRESS, Key.A),
        (RELEASE, Key.A),
        # done with the sequence output will re-exert
        (PRESS, Key.LEFT_ALT),
        (PRESS, Key.LEFT_CTRL),
        # and finally the releases
        (RELEASE, Key.LEFT_CTRL),
        (RELEASE, Key.LEFT_ALT),
    ]
