_window = None


def get_xorg_context():
    return {
        "wm_class": _window or "",
        "context_error": False
    }


def set_window(x):
    global _window
    _window = x
