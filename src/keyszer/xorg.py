import Xlib.display
from Xlib.display import Display
from Xlib.error import ConnectionClosedError, DisplayConnectionError, DisplayNameError

from .logger import error

# https://github.com/python-xlib/python-xlib/blob/master/Xlib/display.py#L153
# https://stackoverflow.com/questions/23786289/how-to-correctly-detect-application-name-when-changing-focus-event-occurs-with

# TODO: keep tabs on active window vs constant querying?


NO_CONTEXT_WAS_ERROR = {
    "wm_class": "",
    "wm_name": "",
    "x_error": True
}


def get_xorg_context():
    """Get window context from Xorg, window name, class, whether there is an X error"""
    try:
        display = Display()

        wm_class = ""
        wm_name = ""

        input_focus_window = display.get_input_focus().focus
        wm_name = input_focus_window.get_wm_name()
        # (process name, class name)
        pair = get_class_name(input_focus_window)
        #TODO: is this sometomes not a pair, but a string???
        if pair:
            wm_class = str(pair[1])

        return {
            "wm_class": wm_class,
            "wm_name": wm_name,
            "x_error": False
        }

    except ConnectionClosedError as xerror:
        error(xerror)
        return NO_CONTEXT_WAS_ERROR
    # seen when we don't have permission to the X display
    except (DisplayConnectionError, DisplayNameError) as xerror:
        error(xerror)
        return NO_CONTEXT_WAS_ERROR


def get_class_name(window):
    """Get window's class name (recursively checks parents)"""
    try:
        wmname = window.get_wm_name()
        wmclass = window.get_wm_class()
        # workaround for Java app
        # https://github.com/JetBrains/jdk8u_jdk/blob/master/src/solaris/classes/sun/awt/X11/XFocusProxyWindow.java#L35
        if (wmclass is None and wmname is None) or "FocusProxy" in wmclass:
            parent_window = window.query_tree().parent
            if parent_window:
                return get_class_name(parent_window)
            return None
        return wmclass
    except:
        return None
