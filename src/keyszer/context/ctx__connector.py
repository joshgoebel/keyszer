from keyszer.lib.env import get_env
from keyszer.lib.logger import debug, error
import dbus.exceptions


SESSION_TYPE = get_env()['SESSION_TYPE']
DESKTOP_ENV  = get_env()['DESKTOP_ENV']

get_window_context = None


if SESSION_TYPE.casefold() in ['x11', 'xorg']:
    try:
        from .x11_xorg import get_xorg_context
        get_window_context = get_xorg_context
        debug(f'CTX: Window context module: X11/Xorg.', ctx="--")
    except Exception as x_error:
        error(x_error)
        raise EnvironmentError(f'CTX: Failure in context module: X11/Xorg.')
elif SESSION_TYPE.casefold() == 'wayland' and DESKTOP_ENV.casefold() == 'gnome':
    try:
        from .wl_gnome_dbus_shell_ext import get_wl_gnome_dbus_shell_ext_context
        get_window_context = get_wl_gnome_dbus_shell_ext_context
        debug(f'CTX: Window context module: Wayland+GNOME D-Bus to shell extension.', ctx="--")
    except Exception as extension_error:
        error(extension_error)
elif SESSION_TYPE.casefold() == 'wayland' and DESKTOP_ENV.casefold() == 'sway':
    try:
        from .test_wl_sway_dbus import get_wl_sway_dbus_context
        get_window_context = get_wl_sway_dbus_context
        debug(f'CTX: Window context module: Wayland+sway D-Bus.', ctx="--")
    except dbus.exceptions.DBusException as dbus_error:
        error(dbus_error)
        raise EnvironmentError(f'CTX: Failure in context module: Wayland+sway D-Bus.')
else:
    raise EnvironmentError(
        f'Incompatible display server or desktop environment: {SESSION_TYPE}, {DESKTOP_ENV}')
