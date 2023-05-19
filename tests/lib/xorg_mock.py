_window = None
_wm_name = None

def get_xorg_context():
    return {
        "wm_class": _window or "",
        "wm_name": _wm_name or "",
        "context_error": False
    }


def set_window(x):
    global _window
    global _wm_name
    _window = x
    _wm_name = x
