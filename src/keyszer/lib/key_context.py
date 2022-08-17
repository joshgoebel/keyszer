from ..xorg import get_xorg_context


class KeyContext:
    def __init__(self, device):
        self._X_ctx = None
        leds_list = []

        # Must declare these here or app will crash if keyboard device hasn't been "grabbed" yet
        self._capslock_state = ""
        self._numlock_state = ""

        # Check for actual device name being present before using evdev's ".leds()" method
        # or device.name (doesn't like strings)
        if not device == "":
            self._device_name = device.name
            leds_list = device.leds()
            self._capslock_state = "ON" if 1 in leds_list else "OFF"
            self._numlock_state = "ON" if 0 in leds_list else "OFF"

    def _query_window_context(self):
        # cache this,  think it might be expensive
        if self._X_ctx is None:
            self._X_ctx = get_xorg_context()

    @property
    def wm_class(self):
        self._query_window_context()
        return self._X_ctx["wm_class"]

    @property
    def wm_name(self):
        self._query_window_context()
        return self._X_ctx["wm_name"]

    @property
    def x_error(self):
        self._query_window_context()
        return self._X_ctx["x_error"]

    @property
    def device_name(self):
        return self._device_name

    @property
    def capslock_state(self):
        return self._capslock_state

    @property
    def numlock_state(self):
        return self._numlock_state
