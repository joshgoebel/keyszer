from ..lib.logger import debug, error

# to make "import dbus" work (on Ubuntu): 
# pip install dbus-python
# sudo apt install build-essential libpython3-dev libdbus-1-dev libglib2.0-dev
# 
import dbus
import dbus.mainloop.glib

# to make "import pydbus" work (on Ubuntu): 
# do everything from making "import dbus" work (above), then:
# pip install pydbus
# 
import pydbus
from pydbus import SessionBus

# to make "from gi.repository" work (on Ubuntu):
# sudo apt install python3-gi libgirepository1.0-dev libcairo2-dev
# pip install pycairo pygobject
# 
# from gi.repository import GLib


NO_CONTEXT_WAS_ERROR = {"wm_class": "", "wm_name": "", "context_error": True}

# start the mainloop
# dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
# loop = GLib.MainLoop()

# Connect to the session bus
bus = pydbus.SessionBus()
session_bus = SessionBus() # alternate form for testing

# Get the object for the GNOME shell extension
# 
# shell = bus.get_object("org.gnome.Shell", "/org/gnome/Shell")

# Call the function you want to call in the GNOME shell extension
# shell.some_function(some_arguments, dbus_interface="org.gnome.Shell")
# 
# gnome_shell = bus.get_object("org.gnome.Shell", "/org/gnome/Shell")
# gnome_shell_interface = dbus.Interface(gnome_shell, "org.gnome.Shell")


# def get_active_window_attributes():
#     active_window = gnome_shell_interface.GetActiveWindow()
#     window_props = bus.get_object("org.gnome.Shell.WindowTracker", active_window).GetAll("org.gnome.Shell.WindowProperties")
#     window_title = window_props["title"]
#     window_class = window_props["application"]
#     return (window_title, window_class)

# debug(f'### ### ### {get_active_window_attributes() = }')

# GNOME extension to make this work: 
# https://extensions.gnome.org/extension/4974/window-calls-extended/
# https://github.com/hseliger/window-calls-extended
# 
# To get the focused window: 
# gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell/Extensions/WindowsExt --method org.gnome.Shell.Extensions.WindowsExt.FocusTitle
# 
gnome_ext = bus.get("org.gnome.Shell.Extensions.WindowsExt", "/org/gnome/Shell/Extensions/WindowsExt")
proxy = session_bus.get("org.gnome.Shell.Extensions.WindowsExt", "FocusTitle")
help(proxy)
debug(f'### gnome_dbus.py:\n\t{gnome_ext = }')

def get_gnome_dbus_context():
    try:
        wm_class = ""
        wm_name = ""
        wm_class = gnome_ext.FocusClass()
        wm_name = gnome_ext.FocusTitle()
        debug(f'### ### ###  get_gnome_dbus_context:\n\t{wm_class = }, {wm_name = }')
        return {"wm_class": wm_class, "wm_name": wm_name, "context_error": False}

    except Exception as gnome_dbus_error:
        error(f'#### {gnome_dbus_error = }')
        return NO_CONTEXT_WAS_ERROR


# Run the mainloop
# loop.run()
