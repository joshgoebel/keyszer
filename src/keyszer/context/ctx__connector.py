from keyszer.lib.env import get_env
from keyszer.lib.logger import debug, error
import dbus.exceptions


SESSION_TYPE = get_env()['SESSION_TYPE']
DESKTOP_ENV  = get_env()['DESKTOP_ENV']
DISTRO_NAME  = get_env()['DISTRO_NAME']

get_window_context = None


if SESSION_TYPE.casefold() in ['x11', 'xorg']:
    try:
        from .ctx_xorg import get_xorg_context
        get_window_context = get_xorg_context
        debug(f'CTX: Using X11 context function.')
    except Exception as x_error:
        error(x_error)
        raise EnvironmentError(f'Tried to use X11 context. Failed.')
elif SESSION_TYPE == 'wayland' and DESKTOP_ENV == 'gnome':
    try:
        from .ctx_wl_gnome_dbus import get_wl_gnome_dbus_context
        get_window_context = get_wl_gnome_dbus_context
        debug(f'CTX: Using Wayland+GNOME(DBus) context function.')
    except dbus.exceptions.DBusException as dbus_error:
        error(dbus_error)
        raise EnvironmentError(f'Tried to use Wayland+GNOME(DBus) context. Failed.')
elif SESSION_TYPE == 'wayland' and DESKTOP_ENV == 'sway':
    try:
        from .ctx_wl_sway_dbus import get_wl_sway_dbus_context
        get_window_context = get_wl_sway_dbus_context
        debug(f'CTX: Using Wayland+sway(DBus) context function.')
    except dbus.exceptions.DBusException as dbus_error:
        error(dbus_error)
        raise EnvironmentError(f'Tried to use Wayland+sway(DBus) context. Failed.')
else:
    raise EnvironmentError(
        f'Incompatible display server or desktop environment: {SESSION_TYPE}, {DESKTOP_ENV}')
