from keyszer.lib.logger import debug, error
import dbus

NO_CONTEXT_WAS_ERROR = {"wm_class": "", "wm_name": "", "x_error": True}

session_bus = dbus.SessionBus()        # Bus() also works.
proxy = session_bus.get_object(
    "org.gnome.Shell",
    "/org/gnome/Shell/Extensions/WindowsExt"
)
extension = dbus.Interface(
    proxy,
    "org.gnome.Shell.Extensions.WindowsExt"
)

def get_gnome_dbus_context():
    try:
        window_id = ""
        wm_class = ""
        wm_name = ""

        window_id = str(extension.FocusPID())   # probably not the ID we need to get parent
        wm_class = str(extension.FocusClass())
        wm_name = str(extension.FocusTitle())
        debug(f'######### ## ###  ctx_gnome_dbus_test.py:\n\t{wm_class = }\n\t{wm_name = }\n')

        return {"wm_class": wm_class, "wm_name": wm_name, "x_error": False}

    except Exception as xerror:
        error(f'####  Something went wrong in get_gnome_dbus_context().  ####')
        error(xerror)
        return NO_CONTEXT_WAS_ERROR
