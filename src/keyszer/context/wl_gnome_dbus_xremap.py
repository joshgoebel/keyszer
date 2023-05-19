from keyszer.lib.logger import debug, error
import dbus
import dbus.exceptions
import json


# This module connects to GNOME Shell extension: "Window Calls Extended"
#
# This extension exposes a D-Bus interface with the name com.k0kubun.Xremap 
# and three methods: ActiveWindow, WMClass, and WMClasses.
# 
# https://extensions.gnome.org/extension/5060/xremap/
# https://github.com/xremap/xremap-gnome
# 

NO_CONTEXT_WAS_ERROR = {"wm_class": "", "wm_name": "", "context_error": True}

session_bus = dbus.SessionBus()        # Bus() also works.
proxy = session_bus.get_object(
    "org.gnome.Shell",
    "/com/k0kubun/Xremap"
)
extension = dbus.Interface(
    proxy,
    "com.k0kubun.Xremap"
)

def get_wl_gnome_dbus_xremap_context():
    try:
        active_window_dbus  = ""
        active_window_dct   = ""
        wm_class            = ""
        wm_name             = ""

        active_window_dbus  = extension.ActiveWindow()
        active_window_dct   = json.loads(active_window_dbus)
        
        wm_class            = active_window_dct['wm_class']
        wm_name             = active_window_dct['title']

        return {"wm_class": wm_class, "wm_name": wm_name, "context_error": False}

    except dbus.exceptions.DBusException as _dbus_error:
        error(f'####  Something went wrong in get_gnome_dbus_xremap_context().  ####')
        error(_dbus_error)
        return NO_CONTEXT_WAS_ERROR
    except Exception as _context_error:
        error(f'####  Something went wrong in get_gnome_dbus_xremap_context().  ####')
        error(_context_error)
        return NO_CONTEXT_WAS_ERROR
