
###  ALL CODE IN THIS MODULE IS COMPLETELY UNTESTED AND PROBABLY DOESN'T WORK

import dbus

def get_focused_window_info():
    bus = dbus.SessionBus()
    kwin = bus.get_object('org.kde.KWin', '/KWin')
    window_id = kwin.activeWindow()
    window = bus.get_object('org.kde.KWin', window_id)
    title = window.title()
    class_name = window.windowClassClass()

    return title, class_name

title, class_name = get_focused_window_info()
print("Window title:", title)
print("Window class:", class_name)
