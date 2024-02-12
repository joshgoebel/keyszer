import abc
import json
from typing import Dict

from .logger import error, debug

# Provider classes for window context info

# Place new provider classes above the generic class at the end to
# facilitate automatic inclusion in the list of supported environments
# and automatic redirection from the generic provider class to the
# matching specific provider class suitable for the environment.


NO_CONTEXT_WAS_ERROR = {"wm_class": "", "wm_name": "", "x_error": True}


class WindowContextProviderInterface(abc.ABC):
    """Abstract base class for all window context provider classes"""

    @abc.abstractmethod
    def get_window_context(self):
        """
        This method should return the current window's context as a dictionary.

        The returned dictionary should contain the following keys:

        - "wm_class": The class of the window.
        - "wm_name": The name of the window.
        - "x_error": A boolean indicating whether there was an error 
            in obtaining the window's context.

        The "wm_class" and "wm_name" values are expected to be strings.
        The "x_error" value is expected to be a boolean, which should 
        be False if the window's context was successfully obtained, 
        and True otherwise.

        Example of a successful context:

        {
            "wm_class": "ExampleClass",
            "wm_name": "ExampleName",
            "x_error": False
        }

        In case of an error, the method should return NO_CONTEXT_WAS_ERROR, 
        which is a predefined global variable "constant":

        NO_CONTEXT_WAS_ERROR = {"wm_class": "", "wm_name": "", "x_error": True}

        :returns: A dictionary containing window context information.
        """

    @classmethod
    @abc.abstractmethod
    def get_supported_environments(cls):
        """
        This method should return a list of environments that the subclass 
        supports.

        Each environment should be represented as a tuple. For example, if 
        a subclass supports the environments 'x11' and 'wayland', this method 
        would return [('x11',), ('wayland',)].

        If an environment is specific to a certain desktop environment, the 
        desktop environment should be included in the tuple. For example, if 
        a subclass supports the 'wayland' environment specifically on the 
        'gnome' desktop, this method would return [('wayland', 'gnome')].

        :returns: A list of tuples, each representing an environment supported 
        by the subclass.
        """


class Wl_GNOME_WindowContext(WindowContextProviderInterface):
    """Window context provider object for Wayland+GNOME environments"""

    def __init__(self):
        import dbus
        from dbus.exceptions import DBusException

        self.DBusException      = DBusException
        self.session_bus        = dbus.SessionBus()

        self.proxy_focused_wdw  = self.session_bus.get_object(
                                                        "org.gnome.Shell",
                                                        "/org/gnome/shell/extensions/FocusedWindow")
        self.iface_focused_wdw  = dbus.Interface(
                                            self.proxy_focused_wdw,
                                            "org.gnome.shell.extensions.FocusedWindow")

        self.proxy_windowsext   = self.session_bus.get_object(
                                                        "org.gnome.Shell",
                                                        "/org/gnome/Shell/Extensions/WindowsExt")
        self.iface_windowsext   = dbus.Interface(
                                            self.proxy_windowsext,
                                            "org.gnome.Shell.Extensions.WindowsExt")

        self.proxy_xremap       = self.session_bus.get_object(
                                                        "org.gnome.Shell",
                                                        "/com/k0kubun/Xremap")
        self.iface_xremap       = dbus.Interface(
                                            self.proxy_xremap,
                                            "com.k0kubun.Xremap")

        self.last_good_ext_uuid     = None
        self.cycle_count            = 0

        self.ext_uuid_focused_wdw   = 'focused-window-dbus@flexagoon.com'
        self.ext_uuid_windowsext    = 'window-calls-extended@hseliger.eu'
        self.ext_uuid_xremap        = 'xremap@k0kubun.com'

        self.GNOME_SHELL_EXTENSIONS = {
            self.ext_uuid_focused_wdw:  self.get_wl_gnome_dbus_focused_wdw_context,
            self.ext_uuid_windowsext:   self.get_wl_gnome_dbus_windowsext_context,
            self.ext_uuid_xremap:       self.get_wl_gnome_dbus_xremap_context,
        }

    @classmethod
    def get_supported_environments(cls):
        # This class supports the GNOME environment on Wayland
        return [('wayland', 'gnome')]

    def get_window_context(self):
        """
        This function gets the window context from one of the compatible 
        GNOME Shell extensions, via D-Bus.
        
        It attempts to get the window context from the shell extension that 
        was successfully used last time.
        
        If it fails, it tries the others. If all fail, it returns an error.
        """

        # Order of the extensions
        extension_uuids = list(self.GNOME_SHELL_EXTENSIONS.keys())

        # If we have a last successful extension
        if self.last_good_ext_uuid in extension_uuids:
            starting_index = extension_uuids.index(self.last_good_ext_uuid)
        else:
            # We don't have a last successful extension, so start from the first
            starting_index = 0

        # Create a new list that starts with the last successful extension, followed by the others
        ordered_extensions = extension_uuids[starting_index:] + extension_uuids[:starting_index]

        for extension_uuid in ordered_extensions:
            try:
                # Call the function associated with the extension
                context = self.GNOME_SHELL_EXTENSIONS[extension_uuid]()
            # pylint disable=broad-exception-caught
            except self.DBusException as e:
                error(f"Error returned from GNOME Shell extension '{extension_uuid}'\n\t {e}")
                # Continue to the next extension
                continue
            else:
                # No exceptions were thrown, so this extension is now the preferred one
                self.last_good_ext_uuid = extension_uuid
                debug(f"SHELL_EXT: Using '{self.last_good_ext_uuid}' for window context")
                return context

        # If we reach here, it means all extensions have failed
        print()
        error(  f'############################################################################')
        error(  f'SHELL_EXT: No compatible GNOME Shell extension responding via D-Bus.'
                f'\n\tThese extensions are compatible with keyszer:'
                f'\n\t    {self.ext_uuid_focused_wdw}:'
                f'\n\t\t(https://extensions.gnome.org/extension/5592/focused-window-d-bus/)'
                f'\n\t    {self.ext_uuid_windowsext}:'
                f'\n\t\t(https://extensions.gnome.org/extension/4974/window-calls-extended/)'
                f'\n\t    {self.ext_uuid_xremap}:'
                f'\n\t\t(https://extensions.gnome.org/extension/5060/xremap/)')
        error(f'Install "Extension Manager" from Flathub to manage GNOME Shell extensions')
        error(f'############################################################################')
        print()
        return NO_CONTEXT_WAS_ERROR

    def get_wl_gnome_dbus_focused_wdw_context(self):
        wm_class            = ''
        wm_name             = ''
        
        try:
            focused_wdw_dbus    = self.iface_focused_wdw.Get()
            # print(f'{focused_wdw_dbus = }')
            focused_wdw_dct     = json.loads(focused_wdw_dbus)
            # print(f'{focused_wdw_dct = }')

            wm_class            = focused_wdw_dct.get('wm_class', '')
            wm_name             = focused_wdw_dct.get('title', '')
        except self.DBusException as dbus_error:
            # This will be the error if no window info found (e.g., GNOME desktop):
            # org.gnome.gjs.JSError.Error: No window in focus
            if 'No window in focus' in str(dbus_error):
                pass
            else:
                raise   # pass on the original exception if not 'No window in focus'

        return {"wm_class": wm_class, "wm_name": wm_name, "x_error": False}

    def get_wl_gnome_dbus_windowsext_context(self):
        wm_class            = ''
        wm_name             = ''

        wm_class            = str(self.iface_windowsext.FocusClass())
        wm_name             = str(self.iface_windowsext.FocusTitle())

        return {"wm_class": wm_class, "wm_name": wm_name, "x_error": False}

    def get_wl_gnome_dbus_xremap_context(self):
        active_window_dbus  = ''
        active_window_dct   = ''
        wm_class            = ''
        wm_name             = ''

        active_window_dbus  = self.iface_xremap.ActiveWindow()
        active_window_dct   = json.loads(active_window_dbus)

        # use get() with default value to avoid KeyError for 
        # GNOME Shell/desktop lack of properties returned
        active_window_dct: Dict[str:str]
        wm_class            = active_window_dct.get('wm_class', '')
        wm_name             = active_window_dct.get('title', '')

        return {"wm_class": wm_class, "wm_name": wm_name, "x_error": False}


class Xorg_WindowContext(WindowContextProviderInterface):
    """Window context provider object for X11/Xorg environments"""

    def __init__(self):
        self._display = None

        # Import Xlib modules here
        from Xlib.xobject.drawable import Window
        from Xlib.display import Display
        from Xlib.error import (ConnectionClosedError, DisplayConnectionError, DisplayNameError)
        self.Window                 = Window
        self.Display                = Display
        self.ConnectionClosedError  = ConnectionClosedError
        self.DisplayConnectionError = DisplayConnectionError
        self.DisplayNameError       = DisplayNameError

    @classmethod
    def get_supported_environments(cls):
        # This class supports any desktop environment on X11
        return [('x11', None)]

    def get_window_context(self):
        """
        Get window context from Xorg, window name, class,
        whether there is an X error or not
        """
        try:
            self._display = self._display or self.Display()
            wm_class    = ""
            wm_name     = ""

            input_focus = self._display.get_input_focus().focus
            window      = self.get_actual_window(input_focus)
            if window:
                # use _NET_WM_NAME string instead of WM_NAME to 
                # bypass (COMPOUND_TEXT) encoding problems
                wm_name = window.get_full_text_property(self._display.get_atom("_NET_WM_NAME"))
                pair    = window.get_wm_class()
                if pair:
                    wm_class = str(pair[1])

            return {"wm_class": wm_class, "wm_name": wm_name, "x_error": False}

        except self.ConnectionClosedError as xerror:
            error(xerror)
            self._display = None
            return NO_CONTEXT_WAS_ERROR
        # most likely DISPLAY env isn't even set
        except self.DisplayNameError as xerror:
            error(xerror)
            self._display = None
            return NO_CONTEXT_WAS_ERROR
        # seen when we don't have permission to the X display
        except self.DisplayConnectionError as xerror:
            error(xerror)
            self._display = None
            return NO_CONTEXT_WAS_ERROR

    def get_actual_window(self, window):
        if not isinstance(window, self.Window):
            return None

        # use _NET_WM_NAME string instead of WM_NAME to bypass (COMPOUND_TEXT) encoding problems
        wmname = window.get_full_text_property(self._display.get_atom("_NET_WM_NAME"))
        wmclass = window.get_wm_class()
        # workaround for Java app
        # https://github.com/JetBrains/jdk8u_jdk/blob/master/src/solaris/classes/sun/awt/X11/XFocusProxyWindow.java#L35
        if (wmclass is None and wmname is None) or "FocusProxy" in (wmclass or ""):
            parent_window = window.query_tree().parent
            if parent_window:
                return self.get_actual_window(parent_window)
            return None

        return window


###############################################################################################
# ALL SPECIFIC PROVIDER CLASSES MUST BE DEFINED BEFORE/ABOVE THIS GENERIC PROVIDER!!!
# This class is responsible for making a list of the environments supported
# by all the specific provider classes in this module, and redirecting the
# rest of the keymapper code to the correct specific provider. 

# Generic class for the rest of the code to interact with
class WindowContextProvider(WindowContextProviderInterface):
    """generic object to provide correct window context to KeyContext"""
    _instance = None

    # Mapping of environments to provider classes
    environment_class_map = {
        env: cls for cls in WindowContextProviderInterface.__subclasses__()
        for env in cls.get_supported_environments()
    }

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(WindowContextProvider, cls).__new__(cls)
        return cls._instance

    def __init__(self, session_type, wl_desktop_env) -> None:

        env = (session_type, wl_desktop_env)
        if env not in self.environment_class_map:
            raise ValueError(f"Unsupported environment: {env}")

        self._provider = self.environment_class_map[env]()

    def get_window_context(self):
        return self._provider.get_window_context()

    @classmethod
    def get_supported_environments(cls):
        # This generic class does not directly support any environments
        return []

# ALL SPECIFIC PROVIDER CLASSES MUST BE DEFINED BEFORE/ABOVE THIS GENERIC PROVIDER!!!
# This class is responsible for making a list of the environments supported
# by all the specific provider classes in this module, and redirecting the
# rest of the keymapper code to the correct specific provider. 
