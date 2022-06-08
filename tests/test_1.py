# this is pulled in first when running `pytest` on it's own
import sys
sys.modules["keyszer.xorg"] = __import__('lib.xorg_mock',
    None, None, ["get_active_window_wm_class"])