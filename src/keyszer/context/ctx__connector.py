from keyszer.lib.env import get_env
from keyszer.lib.logger import debug
import dbus.exceptions
# Window context modules:
from .ctx_xorg import get_xorg_context
try: from .ctx_wl_gnome_dbus import get_wl_gnome_dbus_context
except dbus.exceptions.DBusException as dbus_error: pass
try: from .ctx_wl_sway_dbus import get_wl_sway_dbus_context
except dbus.exceptions.DBusException as dbus_error: pass


SESSION_TYPE = get_env()['SESSION_TYPE']
DESKTOP_ENV  = get_env()['DESKTOP_ENV']
DISTRO_NAME  = get_env()['DISTRO_NAME']

get_window_context = None

if SESSION_TYPE.casefold() in ['x11', 'xorg']:
    get_window_context = get_xorg_context
    debug(f'CTX: Using X11 context function.')
elif SESSION_TYPE == 'wayland' and DESKTOP_ENV == 'gnome':
    get_window_context = get_wl_gnome_dbus_context
    debug(f'CTX: Using Wayland+GNOME(DBus) context function.')
elif SESSION_TYPE == 'wayland' and DESKTOP_ENV == 'sway':
    get_window_context = get_wl_sway_dbus_context
    debug(f'CTX: Using Wayland+sway(DBus) context function.')
else:
    raise EnvironmentError(
        f'Incompatible display server or desktop environment: {SESSION_TYPE}, {DESKTOP_ENV}')
