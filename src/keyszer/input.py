from evdev import ecodes, InputDevice, InputEvent
from .models.action import Action
from .models.key import Key
from sys import exit
from .transform import on_event, boot_config, dump_diagnostics
from . import transform
from . import config_api
from .devices import DeviceRegistry, DeviceFilter, DeviceGrabError
from .lib.logger import info, error, debug
import asyncio
import signal


CONFIG = config_api


def shutdown():
    loop = asyncio.get_event_loop()
    loop.stop()
    transform.shutdown()


def sig_term():
    print("signal TERM received", flush=True)
    shutdown()
    exit(0)


def sig_int():
    print("signal INT received", flush=True)
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
    down = InputEvent(0, 0, ecodes.EV_KEY, Key.LEFT_SHIFT, Action.PRESS)
    up = InputEvent(0, 0, ecodes.EV_KEY, Key.LEFT_SHIFT, Action.RELEASE)
    for ev in [down, up]:
        on_event(ev, "")


def main_loop(arg_devices, device_watch):
    inotify = None

    boot_config()
    wakeup_output()

    if device_watch:
        inotify = watch_dev_input()

    try:
        loop = asyncio.get_event_loop()
        registry = DeviceRegistry(
            loop, input_cb=receive_input, filterer=DeviceFilter(arg_devices)
        )
        registry.autodetect()

        if device_watch:
            loop.add_reader(inotify.fd, _inotify_handler, registry, inotify)

        _sup = loop.create_task(supervisor())  # noqa: F841
        loop.add_signal_handler(signal.SIGINT, sig_int)
        loop.add_signal_handler(signal.SIGTERM, sig_term)
        info("Ready to process input.")
        loop.run_forever()
    except DeviceGrabError:
        loop.stop()
    finally:
        shutdown()
        registry.ungrab_all()
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


def receive_input(device):
    for event in device.read():
        if event.type == ecodes.EV_KEY:
            if event.code == CONFIG.EMERGENCY_EJECT_KEY:
                error("BAIL OUT: Emergency eject - shutting down.")
                shutdown()
                exit(0)
            if event.code == CONFIG.DUMP_DIAGNOSTICS_KEY:
                debug("DIAG: Diagnostics requested.")
                action = Action(event.value)
                if action.just_pressed():
                    dump_diagnostics()

        on_event(event, device.name)


_add_timer = None
_notify_events = []


def _inotify_handler(registry, inotify):
    global _add_timer
    global _notify_events

    events = inotify.read(0)
    _notify_events.extend(events)

    if _add_timer:
        _add_timer.cancel()

    def device_change_task():
        task = loop.create_task(device_change(registry, _notify_events))
        _tasks.append(task)

    loop = asyncio.get_running_loop()
    # slow the roll a bit to allow for udev to change permissions, etc...
    _add_timer = loop.call_later(0.5, device_change_task)


async def device_change(registry, events):
    while events:
        event = events.pop(0)
        # ignore mouse, mice, etc, non-event devices
        if not event.name.startswith("event"):
            continue

        filename = f"/dev/input/{event.name}"
        device = InputDevice(filename)

        # unplugging
        from inotify_simple import flags

        if event.mask == flags.DELETE:
            if device in registry:
                registry.ungrab(device)
            continue

        # potential new device
        try:
            if device not in registry:
                if registry.cares_about(device):
                    registry.grab(device)
        except FileNotFoundError:
            # likely received ATTR right before a DELETE, so we ignore
            continue
