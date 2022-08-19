from ..xorg import get_xorg_context


class KeyContext:
    def __init__(self, device):
        self._X_ctx = None
        self._device = device

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
        return self._device.name

    @property
    def capslock_on(self):
        CL_LED = 1  # evdev puts int 1 in leds() list if Capslock is ON
        return True if CL_LED in self._device.leds() else False

    @property
    def numlock_on(self):
        NL_LED = 0  # evdev puts int 0 in leds() list if Numlock is ON
        return True if NL_LED in self._device.leds() else False
