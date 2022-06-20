import sys
sys.path.append("..")
sys.modules["keyszer.xorg"] = __import__('lib.xorg_mock',
    None, None, ["get_active_window_wm_class"])

# from lib.uinput_stub import UInputStub
from keyszer.output import setup_uinput
from keyszer.models.key import Key
from keyszer.models.action import Action
from lib.xorg_mock import set_window
from keyszer.transform import boot_config, on_event, reset_transform
from keyszer import transform
from keyszer.config_api import *
import time
from evdev import InputEvent
from evdev.ecodes import EV_KEY, EV_REL

CONFIG_HEADER = b"""
import re
#from keyszer.config_api import *
"""

class UInputStub:
    def __init__(self):
        self.queue = []

    def syn(self):
        pass
        # self.write(EV_SYN,0,0)

    def write_event(self, event):
        pass
        # self.write(event.type, event.code, event.value)

    def write(self, type, code, value):
        pass
        # self.queue.append((type, code, value))

    def keys(self):
        return [(x[2], x[1]) for x in self.queue if x[0] == EV_KEY]

    def close(self):
        pass # NOP

def eval_config(path):
    with open(path, "rb") as file:
        config_code = CONFIG_HEADER + file.read()
        exec(compile(config_code, path, 'exec'), globals())

def setup():
    global _out
    _out = UInputStub()
    setup_uinput(_out)
    reset_configuration()

def test_typing():
    set_window("Sublime_text")
    REPEAT = 10
    keys = "QWERTYUIOPASDFGHJKLZXCVBNM"
    keys = [getattr(Key, key) for key in keys]
    bunch = keys * 100
    start = time.time()
    press = InputEvent(0,0,EV_KEY,0,Action.PRESS)
    release = InputEvent(0,0,EV_KEY,0,Action.RELEASE)
    for n in range(1, REPEAT):
        for key in bunch:
            press.code = key
            on_event(press, "fake")
            release.code = key
            on_event(release, "fake")
    finish = time.time()
    diff = finish - start
    # print(diff)
    print("[A-Z] keys", len(bunch) * REPEAT / diff, "/s")
    print(round(diff/ (len(bunch) * REPEAT)*1000*1000,3), "us per key")

def test_non_keys():
    REPEAT = 1000000
    start = time.time()
    event = InputEvent(0,0,0,0,0)
    for n in range(1, REPEAT):
        event.type = EV_REL
        event.code = 2
        event.value = n
        on_event(event, "fake")
    finish = time.time()
    diff = finish - start
    # print(diff)
    print("non-key events", REPEAT / diff, "/s")
    print(round(diff/ REPEAT*1000*1000,3), "us per non-key")


def main():
    setup()
    reset_transform()

    eval_config("./kinto.py")
    boot_config()
    print("keymaps", len(transform._KEYMAPS))

    test_non_keys()
    test_typing()



main()
