from keyszer.lib.env import get_env
from keyszer.lib.logger import debug, error
import dbus.exceptions


SESSION_TYPE = get_env()['SESSION_TYPE']
DESKTOP_ENV  = get_env()['DESKTOP_ENV']
DISTRO_NAME  = get_env()['DISTRO_NAME']

get_window_context = None


if SESSION_TYPE.casefold() in ['x11', 'xorg']:
    try:
        from .x11_xorg import get_xorg_context
        get_window_context = get_xorg_context
        debug(f'CTX: Window attribute module: X11/Xorg.')
    except Exception as x_error:
        error(x_error)
        raise EnvironmentError(f'CTX: Failure in module: X11/Xorg.')

elif SESSION_TYPE.casefold() == 'wayland' and DESKTOP_ENV == 'gnome':
    try:
        from .wl_gnome_dbus_shell_ext import get_wl_gnome_dbus_shell_ext_context
        get_window_context = get_wl_gnome_dbus_shell_ext_context
        debug(f'CTX: Window attribute module: Wayland+GNOME D-Bus to shell extension.')
    except Exception as extension_error:
        error(extension_error)

# elif SESSION_TYPE.casefold() == 'wayland' and DESKTOP_ENV == 'gnome':
#     try:
#         from .wl_gnome_dbus_xremap import get_wl_gnome_dbus_xremap_context
#         get_window_context = get_wl_gnome_dbus_xremap_context
#         debug(f'CTX: Window attribute module: Wayland+GNOME D-Bus to "Xremap" extension.')
#     except dbus.exceptions.DBusException as dbus_error:
#         error(dbus_error)
#         raise EnvironmentError(f'CTX: Failure in module: Wayland+GNOME D-Bus to "Xremap" extension".')
# elif SESSION_TYPE.casefold() == 'wayland' and DESKTOP_ENV == 'gnome':
#     try:
#         from .wl_gnome_dbus_windowsext import get_wl_gnome_dbus_windowsext_context
#         get_window_context = get_wl_gnome_dbus_windowsext_context
#         debug(f'CTX: Window attribute module: Wayland+GNOME D-Bus to "Window Calls Extended" extension.')
#     except dbus.exceptions.DBusException as dbus_error:
#         error(dbus_error)
#         raise EnvironmentError(f'CTX: Failure in module: Wayland+GNOME D-Bus to "Window Calls Extended" extension.')
elif SESSION_TYPE.casefold() == 'wayland' and DESKTOP_ENV == 'sway':
    try:
        from .test_wl_sway_dbus import get_wl_sway_dbus_context
        get_window_context = get_wl_sway_dbus_context
        debug(f'CTX: Window attribute module: Wayland+sway D-Bus.')
    except dbus.exceptions.DBusException as dbus_error:
        error(dbus_error)
        raise EnvironmentError(f'CTX: Failure in module: Wayland+sway D-Bus.')
else:
    raise EnvironmentError(
        f'Incompatible display server or desktop environment: {SESSION_TYPE}, {DESKTOP_ENV}')
