from keyszer.lib.env import get_env
from keyszer.config_api import ENVIRONMENT_OVERRIDES
from keyszer.lib.logger import debug, error
import dbus.exceptions


# This module "connects" keycontext.py to the correct window context function for the detected
# environment (if available). 

SESSION_TYPE = ENVIRONMENT_OVERRIDES['override_session_type'] or get_env()['SESSION_TYPE']
DESKTOP_ENV  = ENVIRONMENT_OVERRIDES['override_desktop_env']  or get_env()['DESKTOP_ENV']

get_window_context = None

if SESSION_TYPE == 'wayland' and DESKTOP_ENV == 'gnome':
    try:
        from .wl_gnome_dbus_shell_ext import get_wl_gnome_dbus_shell_ext_context
        get_window_context = get_wl_gnome_dbus_shell_ext_context
        debug(f'CTX: Window context module: Wayland+GNOME D-Bus to shell extension.', ctx="--")
    except Exception as extension_error:
        error(extension_error)
elif SESSION_TYPE == 'x11': # X11/Xorg plus any desktop environment/window manager is good.
    try:
        from .x11_xorg import get_xorg_context
        get_window_context = get_xorg_context
        debug(f'CTX: Window context module: X11/Xorg.', ctx="--")
    except Exception as x_error:
        error(x_error)
else:
    raise EnvironmentError(
        f'Incompatible environment: {SESSION_TYPE = }, {DESKTOP_ENV = }')


# For use with Wayland+sway context module (incomplete, untested)
##########################################################################################
# elif SESSION_TYPE == 'wayland' and DESKTOP_ENV == 'sway':
#     try:
#         from .testing_wl_sway_dbus import get_wl_sway_dbus_context
#         get_window_context = get_wl_sway_dbus_context
#         debug(f'CTX: Window context module: Wayland+sway D-Bus.', ctx="--")
#     except dbus.exceptions.DBusException as dbus_error:
#         error(dbus_error)
#         # raise EnvironmentError(f'CTX: Failure in context module: Wayland+sway D-Bus.')
