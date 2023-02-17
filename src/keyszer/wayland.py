import pywayland.server
import pywayland.protocol

from .lib.logger import debug, error

# to make "import dbus" work: 
# pip install dbus-python
# sudo apt install build-essential libpython3-dev libdbus-1-dev libglib2.0-dev

NO_CONTEXT_WAS_ERROR = {"wm_class": "", "wm_name": "", "context_error": True}
display = None


def focus_handler(surface, event):
    # Get the WM_NAME and WM_CLASS properties of the focused surface
    wm_name = surface.get_label("WM_NAME")
    debug(f'### wayland.py - focus_handler:\n\t{wm_name = }')
    wm_class = surface.get_label("WM_CLASS")
    debug(f'### wayland.py - focus_handler:\n\t{wm_class = }')

    # Handle the focus event here, using the wm_name and wm_class variables
    pass


def get_wayland_context():
    """
    Get window context from Wayland, window name, class,
    whether there is a Wayland error or not
    """
    try:
        display = pywayland.server.Display()
        debug(f'### wayland.py - get_wayland_context:\n\t{display = }')
        focused_window = display.get_focused_window()

        wm_class = ""
        wm_name = ""

        input_focus = display(pywayland.server.Listener(focus_handler))
        debug(f'### wayland.py - get_wayland_context:\n\t{input_focus = }')
        window = get_actual_window(input_focus)
        debug(f'### wayland.py - get_wayland_context:\n\t{window = }')
        if window:
            wm_name = window.get_label("WM_NAME")
            debug(f'### wayland.py - get_wayland_context:\n\t{wm_name = }')
            pair = window.get_label("WM_CLASS")
            debug(f'### wayland.py - get_wayland_context:\n\t{pair = }')
            if pair:
                wm_class = str(pair[1])
            debug(f'### wayland.py - get_wayland_context:\n\t{wm_class = }')

        return {"wm_class": wm_class, "wm_name": wm_name, "context_error": False}

    except Exception as wayland_error:
        error(f'### wayland.py - get_wayland_context:\n\t{wayland_error = }')
        display = None
        return NO_CONTEXT_WAS_ERROR


def get_actual_window(window):
    try:
        wmname = window.get_label("WM_NAME")
        debug(f'### wayland.py - get_wayland_context:\n\t{wmclass = }')
        wmclass = window.get_label("WM_CLASS")
        debug(f'### wayland.py - get_wayland_context:\n\t{wmclass = }')
        # workaround for Java app
        # https://github.com/JetBrains/jdk8u_jdk/blob/master/src/solaris/classes/sun/awt/X11/XFocusProxyWindow.java#L35
        if (wmclass is None and wmname is None) or "FocusProxy" in wmclass:
            parent_window = window.parent
            if parent_window:
                return get_actual_window(parent_window)
            return None

        return window
    # TODO: more specific rescue here
    except Exception:
        return None
