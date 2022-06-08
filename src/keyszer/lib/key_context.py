from ..xorg import get_active_window_wm_class

class KeyContext:
    def __init__(self, device_name):
        self._device_name = device_name
        self._wm_class = None

    def get_wm_class(self):
        # cache this,  think it might be expensive
        self._wm_class = self._wm_class or get_active_window_wm_class()
        return self._wm_class

    def get_device_name(self):
        return self._device_name

    wm_class = property(fget=get_wm_class)
    device_name = property(fget=get_device_name)
