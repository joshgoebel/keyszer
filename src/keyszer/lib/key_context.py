from .logger import debug, error
from ..models.key import Key
from ..context.ctx__connector import get_window_context


class KeyContext:
    def __init__(self, device):
        self._X_ctx = None
        self._device = device

    def _query_window_context(self):
        # cache this,  think it might be expensive
        if self._X_ctx is None:
            self._X_ctx = get_window_context()

    @property
    def wm_class(self):
        self._query_window_context()
        return self._X_ctx["wm_class"]

    @property
    def wm_name(self):
        self._query_window_context()
        return self._X_ctx["wm_name"]

    # generic context error, covering both X11 and Wayland
    @property
    def context_error(self):
        self._query_window_context()
        return self._X_ctx["context_error"]

    @property
    def device_name(self):
        return self._device.name

    @property
    def capslock_on(self):
        return Key.LED_CAPSL in self._device.leds()

    @property
    def numlock_on(self):
        return Key.LED_NUML in self._device.leds()
