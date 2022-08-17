from ..xorg import get_xorg_context


class KeyContext:
    def __init__(self, device_name):
        self._device_name = device_name
        self._X_ctx = None

        # Must declare these here or app will crash if keyboard device hasn't been "grabbed" yet
        self._capslock_state = ""
        self._numlock_state = ""

        leds_list = []

        # Check for actual device name being present before using evdev's ".leds()" method
        if not device == "":
            leds_list = device.leds()
            if 1 in leds_list:
                self._capslock_state = "ON"
            else:
                self._capslock_state = "OFF"
            if 0 in leds_list:
                self._numlock_state = "ON"
            else:
                self._numlock_state = "OFF"

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
