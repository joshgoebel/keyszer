from ..lib.logger import debug, error
import dbus


# This module connects to GNOME Shell extension: "Window Calls Extended"
# https://extensions.gnome.org/extension/4974/window-calls-extended/
# https://github.com/hseliger/window-calls-extended
#


NO_CONTEXT_WAS_ERROR = {"wm_class": "", "wm_name": "", "context_error": True}

session_bus = dbus.SessionBus()        # Bus() also works.
proxy = session_bus.get_object(
    "org.gnome.Shell",
    "/org/gnome/Shell/Extensions/WindowsExt"
)
extension = dbus.Interface(
    proxy,
    "org.gnome.Shell.Extensions.WindowsExt"
)

def get_wl_gnome_dbus_windowsext_context():
    try:
        # window_pid = ""
        wm_class = ""
        wm_name = ""

        # window_pid = str(extension.FocusPID())   # just process ID, not window ID
        wm_class = str(extension.FocusClass())
        wm_name = str(extension.FocusTitle())

        return {"wm_class": wm_class, "wm_name": wm_name, "context_error": False}

    except Exception as _context_error:
        error(f'####  Something went wrong in get_gnome_dbus_context().  ####')
        error(_context_error)
        return NO_CONTEXT_WAS_ERROR
