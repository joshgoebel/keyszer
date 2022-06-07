# -*- coding: utf-8 -*-

from evdev import ecodes, InputDevice, list_devices, InputEvent
from .models.action import Action
from select import select
from sys import exit
from .transform import on_event, boot_config
from . import transform
from .output import setup_uinput
from .logger import *
from .key import Key
import asyncio
import signal


QWERTY = [Key.Q, Key.W, Key.E, Key.R, Key.T, Key.Y]
A_Z_SPACE = [Key.SPACE, Key.A, Key.Z]


def is_keyboard_device(device):
    """Guess the device is a keyboard or not"""
    capabilities = device.capabilities(verbose=False)
    if 1 not in capabilities:
        return False
    supported_keys = capabilities[1]

    qwerty = all(k in supported_keys for k in QWERTY)
    az = all(k in supported_keys for k in A_Z_SPACE)
    if qwerty and az:
        return True
    # Otherwise, its not a keyboard!
    return False


def print_device_list(devices):
    device_format = '{1.fn:<20} {1.name:<35} {1.phys}'
    device_lines = [device_format.format(n, d) for n, d in enumerate(devices)]
    print('-' * len(max(device_lines, key=len)))
    print('{:<20} {:<35} {}'.format('Device', 'Name', 'Phys'))
    print('-' * len(max(device_lines, key=len)))
    print('\n'.join(device_lines))
    print('')


def get_devices_list():
    return [InputDevice(device_fn) for device_fn in reversed(list_devices())]


class DeviceFilter(object):
    def __init__(self, matches):
        self.matches = matches

    def __call__(self, device):
        # Match by device path or name, if no keyboard devices specified, picks up keyboard-ish devices.
        if self.matches:
            for match in self.matches:
                if device.fn == match or device.name == match:
                    return True
            return False
        # Exclude evdev device, we use for output emulation, from input monitoring list
        if device.name == "py-evdev-uinput":
            return False
        # Exclude none keyboard devices
        return is_keyboard_device(device)


def select_devices(device_filter=None):
    """Select a device from the list of accessible input devices."""
    devices = get_devices_list()

    if not device_filter:
        info("(--) Autodetecting keyboards (--device not specified)")

    devices = list(filter(device_filter, devices))

    if not devices:
        info('error: no input devices found (do you have rw permission on /dev/input/*?)')
        exit(1)

    return devices


def in_device_list(filename, devices):
    return any([device for device in devices if device.fn == filename])


def shutdown():
    loop = asyncio.get_event_loop()
    loop.stop()
    transform.shutdown()


def sig_term():
    print("signal TERM received", flush = True)
    shutdown()
    exit(0)


def sig_int():
    print("signal INT received", flush = True)
    shutdown()
    exit(0)


def watch_dev_input():
    from inotify_simple import INotify, flags
    inotify = INotify()
    inotify.add_watch("/dev/input", flags.CREATE | flags.ATTRIB | flags.DELETE)
    return inotify


# Why? xmodmap won't persist mapping changes until it's seen at least
# one keystroke on a new device, so we need to give it something that
# won't do any harm, but is still an actual keypress, hence shift.
def wakeup_output():
    down=InputEvent(0, 0, ecodes.EV_KEY, Key.LEFT_SHIFT, Action.PRESS)
    up=InputEvent(0, 0, ecodes.EV_KEY, Key.LEFT_SHIFT, Action.RELEASE)
    for ev in [down, up]:
        on_event(ev, "", True)


def main_loop(device_matches, device_watch, quiet):
    devices = []
    inotify = None

    boot_config()
    setup_uinput()
    wakeup_output()

    # fake=InputEvent(0, 0, ecodes.EV_SYN, 0,0)
    device_filter = DeviceFilter(device_matches)
    selected_devices = select_devices(device_filter)
    for device in selected_devices:
        add_device(devices, device)

    if device_watch:
        inotify = watch_dev_input()

    try:
        loop = asyncio.get_event_loop()

        for device in devices:
            loop.add_reader(device, receive_input, device, quiet)
        if device_watch:
            loop.add_reader(inotify.fd, _inotify_handler, devices, device_filter, inotify)
        
        _sup = loop.create_task(supervisor())
        loop.add_signal_handler(signal.SIGINT, sig_int)
        loop.add_signal_handler(signal.SIGTERM, sig_term)
        info("Ready to process input.")
        loop.run_forever()
    finally:
        for device in devices:
            try:
                device.ungrab()
            except OSError as e:
                pass
        if device_watch:
            inotify.close()


_tasks = []
_sup = None


async def supervisor():
    while True:
        await asyncio.sleep(5)
        for task in _tasks:
            if task.done():
                if task.exception():
                    import traceback
                    traceback.print_exception(task.exception())
                _tasks.remove(task)


def receive_input(device, quiet):
    for event in device.read():
        if (event.type == ecodes.EV_KEY and event.code == Key.F16):
            error("BAIL: Emergency shutdown requested.")
            shutdown()
            exit(0)
        on_event(event, device.name, quiet)


_add_timer = None
_notify_events = []

def _inotify_handler(devices, device_filter, inotify):
    global _add_timer
    global _notify_events

    events = inotify.read(0)
    _notify_events.extend(events)

    if _add_timer:
        _add_timer.cancel()
    
    def device_change_task():
        task = loop.create_task(device_change(devices, device_filter, _notify_events))
        _tasks.append(task)

    loop = asyncio.get_running_loop()
    # slow the roll a bit to allow for udev to change permissions, etc...
    _add_timer = loop.call_later(0.5, device_change_task)

async def device_change(devices, device_filter, events):
    while events:
        event = events.pop(0)
        # ignore mouse, mice, etc, non-event devices
        if not event.name.startswith("event"):
            continue

        filename = f"/dev/input/{event.name}"

        # unplugging
        from inotify_simple import flags
        if (event.mask == flags.DELETE):
            device, = [d for d in devices if d.fn == filename] or [None]
            if device:
                remove_device(devices, device)
            continue

        # new device, do we care about it?
        try:
            new_device = InputDevice(filename)
            if device_filter(new_device) and not in_device_list(new_device.fn, devices):
                add_device(devices, device)
        except FileNotFoundError:
            # likely we've recieved a ATTR right before a DELETE, so we just ignore it
            continue

def remove_device(devices, device):
    info(f"Ungrabbing: {device.name} (removed)", ctx = "-K")
    loop = asyncio.get_running_loop()
    loop.remove_reader(device)
    devices.remove(device)
    try:
        device.ungrab()
    except OSError:
        pass

def add_device(devices, device):
    info(f"Grabbing {device.name} ({device.fn})", ctx = "+K")
    devices.append(device)
    try:
        device.grab()
    except IOError:
        print("IOError when grabbing keyboard. Maybe, another instance is running?")
        shutdown()
        exit(1)
    # except IOError:
    #     # Ignore errors on new devices
    #     print("IOError when grabbing new device: " + str(new_device.name))
    #     continue
