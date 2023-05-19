from ..lib.logger import debug, error
import dbus
import dbus.exceptions
import json


# This module handles attempting to connect to and retrieve window context
# information using any available compatible GNOME Shell extension. 

NO_CONTEXT_WAS_ERROR    = {"wm_class": "", "wm_name": "", "context_error": True}
last_shell_ext_uuid     = None
cycle_count             = 0

# Only need one session bus object for multiple D-Bus interfaces
session_bus             = dbus.SessionBus()        # Bus() also seems to work.

# Set up interface for extension "xremap@k0kubun.com"
proxy_xremap            = session_bus.get_object("org.gnome.Shell", "/com/k0kubun/Xremap")
iface_xremap            = dbus.Interface(proxy_xremap, "com.k0kubun.Xremap")

# Set up interface for extension "window-calls-extended@hseliger.eu"
proxy_windowsext        = session_bus.get_object("org.gnome.Shell", "/org/gnome/Shell/Extensions/WindowsExt")
iface_windowsext        = dbus.Interface(proxy_windowsext, "org.gnome.Shell.Extensions.WindowsExt")


def get_wl_gnome_dbus_shell_ext_context():
    """
    Abstraction interface so the user doesn't need to manually specify
    which compatible GNOME Shell extension they are using, or can switch
    between multiple extensions on-the-fly if one stops working. 

    Compatible extensions as of 2023-02-22:

    "Window Calls Extended", uuid: 'window-calls-extended@hseliger.eu'
    "Xremap", uuid: 'xremap@k0kubun.com'

    """

    global last_shell_ext_uuid
    global cycle_count
    ext_name_windowsext     = 'window-calls-extended@hseliger.eu'
    ext_name_xremap         = 'xremap@k0kubun.com'

    if last_shell_ext_uuid in [None, ext_name_windowsext]:
        try:
            get_wl_gnome_dbus_windowsext_context()
        except Exception as e:
            # Indicate the attempt to use this extension didn't work this cycle
            last_shell_ext_uuid = None
            error(f'Error returned from GNOME Shell extension {ext_name_windowsext}\n\t {e}')
        else:
            last_shell_ext_uuid = ext_name_windowsext
            debug(f"SHELL_EXT: Using '{last_shell_ext_uuid}' for window context")
            return get_wl_gnome_dbus_windowsext_context()

    if last_shell_ext_uuid in [None, ext_name_xremap]:
        try:
            get_wl_gnome_dbus_xremap_context()
        except Exception as e:
            # Indicate the attempt to use this extension didn't work this cycle
            last_shell_ext_uuid = None
            error(f'Error returned from GNOME Shell extension {ext_name_xremap}\n\t {e}')
        else:
            last_shell_ext_uuid = ext_name_xremap
            debug(f"SHELL_EXT: Using '{last_shell_ext_uuid}' for window context")
            return get_wl_gnome_dbus_xremap_context()

    if not cycle_count:
        # Come back through here (once only) if previous cycle failed
        # This will evaluate all compatible extensions on each key press
        # until one starts working again. 
        cycle_count += 1
        return get_wl_gnome_dbus_shell_ext_context()
    else:
        # Already been through? Reset cycle and show problem in log
        cycle_count = 0
        print()
        error(f'############################################################################')
        error(f'SHELL_EXT: No compatible GNOME Shell extension responding via D-Bus.')
        error(f'Compatible GNOME Shell extensions: \
            \n       {ext_name_windowsext}: \
            \n\t\t(https://extensions.gnome.org/extension/4974/window-calls-extended/)\
            \n       {ext_name_xremap}: \
            \n\t\t(https://extensions.gnome.org/extension/5060/xremap/) \
            ')
        error(f'Install "Extension Manager" from Flathub to manage GNOME Shell extensions')
        error(f'############################################################################')
        print()
        return NO_CONTEXT_WAS_ERROR


def get_wl_gnome_dbus_xremap_context():
    """"
    This function connects to GNOME Shell extension: "Xremap"
    
    The extension exposes a D-Bus interface with the name:
    com.k0kubun.Xremap
    
    ActiveWindow(): returns a JSON object with the window's WM class and title.
    WMClass(): returns the WM class of the currently focused window.
    WMClasses(): returns a JSON array of all unique WM classes of the currently open windows.
    
    https://extensions.gnome.org/extension/5060/xremap/
    https://github.com/xremap/xremap-gnome
    """
    active_window_dbus  = ""
    active_window_dct   = ""
    wm_class            = ""
    wm_name             = ""

    active_window_dbus  = iface_xremap.ActiveWindow()
    # Convert from D-Bus to Python dict format
    active_window_dct   = json.loads(active_window_dbus)

    wm_class            = active_window_dct['wm_class']
    wm_name             = active_window_dct['title']

    return {"wm_class": wm_class, "wm_name": wm_name, "context_error": False}


def get_wl_gnome_dbus_windowsext_context():
    """
    This function connects to GNOME Shell extension: "Window Calls Extended"
    
    The extension exposes a D-Bus interface with the name: 
    org.gnome.Shell.Extensions.WindowsExt
    
    - The List() method returns a JSON string with information about all 
        windows currently open, including their window class, process ID, 
        window ID, title, and whether they are maximized and focused.
    - The FocusTitle() method returns the title of the currently focused window.
    - The FocusPID() method returns the process ID of the currently focused window.
    - The FocusClass() method returns the class of the currently focused window.    
    
    https://extensions.gnome.org/extension/4974/window-calls-extended/
    https://github.com/hseliger/window-calls-extended
    """
    wm_class = ""
    wm_name = ""

    wm_class = str(iface_windowsext.FocusClass())
    wm_name = str(iface_windowsext.FocusTitle())

    return {"wm_class": wm_class, "wm_name": wm_name, "context_error": False}
