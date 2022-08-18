from ..xorg import get_xorg_context


class KeyContext:
    def __init__(self, device):
        self._X_ctx = None
        self.device = device

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
        self._device_name = self.device.name
        return self._device_name

    @property
    def capslock_on(self):
        self._capslock_on = True if 1 in self.device.leds() else False
        return self._capslock_on

    @property
    def numlock_on(self):
        self._numlock_on = True if 0 in self.device.leds() else False
        return self._numlock_on
