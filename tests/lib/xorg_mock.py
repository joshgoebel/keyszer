_window = None

def get_active_window_wm_class(display=None):
    return _window or ""

def set_window(x):
    global _window
    _window = x