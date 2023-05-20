# from ..xorg import get_xorg_context
from ..models.key import Key
from .window_context import WindowContextProvider


class KeyContext:
    def __init__(self, device, session_type, wl_desktop_env):
        self._X_ctx = None
        self._device = device
        self.session_type = session_type
        self.wl_desktop_env = wl_desktop_env
        self._win_ctx_provider = WindowContextProvider(self.session_type, self.wl_desktop_env)

    def _query_window_context(self):
        # cache this,  think it might be expensive
        if self._X_ctx is None:
            # self._X_ctx = get_xorg_context()
            self._X_ctx = self._win_ctx_provider.get_window_context()

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
