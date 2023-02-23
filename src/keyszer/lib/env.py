import re
import psutil
import dbus
import dbus.exceptions
from os import environ
from .logger import debug, error
from ..config_api import _ENVIRONMENT

# ─── GLOBALS ─────────────────────────────────────────────────────────────────

DISTRO_NAME     = ""
SESSION_TYPE    = environ.get("XDG_SESSION_TYPE") or ""
DESKTOP_ENV     = ""
_desktop_env    = environ.get("XDG_SESSION_DESKTOP") or environ.get("XDG_CURRENT_DESKTOP")
SHELL_EXT       = ""


# ─── ENVIRONMENT ─────────────────────────────────────────────────────────────────

# Get distro name
with open('/etc/os-release', 'r') as f:
    for line in f:
        if line.startswith('NAME='):
            DISTRO_NAME = line.split('=')[1].strip().strip('"')
            break
if not DISTRO_NAME:
    DISTRO_NAME = 'Unidentified'
    error(f"ENV: Distro name couldn't be found in /etc/os-release.")

if not SESSION_TYPE:  # Why isn't XDG_SESSION_TYPE set? This shouldn't happen.
    debug(f'ENV: XDG_SESSION_TYPE should really be set. Are you in a graphical environment?')
    SESSION_TYPE = environ.get("WAYLAND_DISPLAY")
    if not SESSION_TYPE:
        raise EnvironmentError(
            f'\n\nENV: Detecting session type from XDG_SESSION_TYPE or WAYLAND_DISPLAY failed.\n')
if SESSION_TYPE.casefold() not in ['x11', 'xorg', 'wayland']:
    raise EnvironmentError(f'\n\nENV: Unknown session type: {SESSION_TYPE}.\n')

if not _desktop_env:
    _desktop_env = None
    debug("ENV ERROR: Desktop Environment not found in XDG_SESSION_DESKTOP or XDG_CURRENT_DESKTOP.")
    debug("ENV ERROR: Config file will not be able to adapt automatically to Desktop Environment.")

# Produce a simplified desktop environment name
de_names = {
    'Budgie':                   'budgie',
    'Cinnamon':                 'cinnamon',
    'Deepin':                   'deepin',
    'Enlightenment':            'enlightenment',
    'GNOME':                    'gnome',
    'Hyprland':                 'hypr',
    'IceWM':                    'icewm',
    'KDE':                      'kde',
    'LXDE':                     'lxde',
    'LXQt':                     'lxqt',
    'MATE':                     'mate',
    'Neon':                     'kde_neon',
    'Pantheon':                 'pantheon',
    'Plasma':                   'kde',
    'SwayWM':                   'sway',
    'Ubuntu':                   'gnome',    # "Ubuntu" in XDG_CURRENT_DESKTOP, but DE is GNOME
    'Unity':                    'unity',
    'Xfce':                     'xfce',
}
for k, v in de_names.items():
    # debug(f'{k = :<10} {v = :<10}')
    if re.search(k, _desktop_env, re.I):
        DESKTOP_ENV = v
    if DESKTOP_ENV == 'kde' and re.search('neon', _desktop_env, re.I):
        DESKTOP_ENV = 'kde_neon'         # override 'kde' for KDE Neon
        break
    if DESKTOP_ENV:
        break
if not DESKTOP_ENV:
    error(f'ENV: Desktop Environment not in de_names list! Should fix this.\n\t{_desktop_env = }')

# Doublecheck the desktop env by checking for running processes
for proc in psutil.process_iter(['name']):
    if proc.info['name'] == 'gnome-shell':
        DESKTOP_ENV = 'gnome'
        break
    if proc.info['name'] == 'sway':
        DESKTOP_ENV = 'sway'
        break

RUN_THIS_TEST_STUFF = False

# Build list of available GNOME shell extensions, if applicable
if DESKTOP_ENV == 'gnome' and RUN_THIS_TEST_STUFF:
    bus = dbus.SessionBus()
    # Get the org.gnome.Shell.Extensions interface
    proxy = bus.get_object("org.gnome.Shell.Extensions", "/org/gnome/Shell/Extensions")
    # Alternate proxy that also seems to work:
    # proxy = bus.get_object("org.gnome.Shell", "/org/gnome/Shell")
    iface = dbus.Interface(proxy, "org.gnome.Shell.Extensions")
    # # Retrieve the list of enabled extensions
    extensions_dbus_dict = iface.ListExtensions()

    # print()
    # print("Printing extensions_dbus_dict contents, line by line:")
    # print("######################################################")
    # for k, v in extensions_dbus_dict.items():
    #     print(f'{k}: {v}')


    def dbus_to_py(obj):
        if isinstance(obj, dbus.ByteArray):
            return bytes(obj)
        elif isinstance(obj, dbus.String):
            return str(obj)
        elif isinstance(obj, dbus.Int16) or isinstance(obj, dbus.UInt16) \
                or isinstance(obj, dbus.Int32) or isinstance(obj, dbus.UInt32) \
                or isinstance(obj, dbus.Int64) or isinstance(obj, dbus.UInt64):
            return int(obj)
        elif isinstance(obj, dbus.Boolean):
            return bool(obj)
        elif isinstance(obj, dbus.Double):
            return float(obj)
        elif isinstance(obj, dbus.Array):
            return [dbus_to_py(elem) for elem in obj]
        elif isinstance(obj, dbus.Dictionary):
            return dict([(dbus_to_py(k), dbus_to_py(v)) for k, v in obj.items()])
        elif isinstance(obj, dbus.Struct):
            return tuple([dbus_to_py(elem) for elem in obj])
        elif isinstance(obj, dbus.Byte):
            return int(obj)
        else:
            return obj

    # Assuming you have a D-Bus dictionary object named 'enabled_extensions'
    # First, get the keys and values from the D-Bus dictionary object
    extensions_dbus_keys = extensions_dbus_dict.keys()
    extensions_dbus_values = extensions_dbus_dict.values()

    # Next, convert the keys and values to Python objects
    extensions_py_keys = [dbus_to_py(k) for k in extensions_dbus_keys]
    extensions_py_values = [dbus_to_py(v) for v in extensions_dbus_values]

    # Finally, create a Python dictionary from the keys and values
    extensions_py_dict = dict(zip(extensions_py_keys, extensions_py_values))

    # print()
    # print("Printing extensions_py_dict contents, line by line:")
    # print("######################################################")
    # for k, v in extensions_py_dict.items():
    #     print(f'{k}: {v}')

    extensions_dct = {}
    for k, v in extensions_py_dict.items():
        extensions_dct.update({k: {'uuid': v['uuid'], 'name': v['name'], 'state': v['state']}})
        # extension_info.update({k: {'name': v['name'], 'uuid': v['uuid'], 'state': v['state']}})
        # print(f"name: {v['name']}")
        # print(f"uuid: {v['uuid']}")
        # print(f"state: {v['state']}")
        # for _k, _v in v.items():
        #     print(f'    {_k}: {_v}')
        # print("########")

    # state 1.0 == (enabled), state 2.0 == (disabled?), state 6.0 (disabled?)

    print()
    print("Printing extensions_dct contents, line by line:")
    print("######################################################")
    for k, v in extensions_dct.items():
        print(f'{k}: {v}')

    print()
    print("Printing only the keys (extension uuids) from extensions_dct, line by line:")
    print("######################################################")
    for e in extensions_dct:
        print(e)

    print()
    print("Printing the values attached to the keys for the GNOME extensions:")
    print("######################################################")
    print(extensions_dct['window-calls-extended@hseliger.eu'])
    print(extensions_dct['xremap@k0kubun.com'])


debug("")
debug(f'ENV: {DISTRO_NAME  = }')
debug(f'ENV: {SESSION_TYPE = }')
debug(f'ENV: {DESKTOP_ENV  = }')
debug(f'ENV: {SHELL_EXT    = }')


def get_env():
    return {
                "DISTRO_NAME"   : DISTRO_NAME,
                "SESSION_TYPE"  : SESSION_TYPE,
                "DESKTOP_ENV"   : DESKTOP_ENV,
                "SHELL_EXT"     : SHELL_EXT,
            }

