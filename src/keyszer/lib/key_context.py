from ..xorg import get_xorg_context
from ..models.key import Key


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
        return Key.LED_CAPSL in self._device.leds()

    @property
    def numlock_on(self):
        return Key.LED_NUML in self._device.leds()
