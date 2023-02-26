import re
import psutil
import dbus
import dbus.exceptions
from os import environ
from .logger import debug, error
from ..config_api import ENVIRONMENT_OVERRIDES

# ─── GLOBALS ─────────────────────────────────────────────────────────────────

DISTRO_NAME         = None
_os_distro_name     = None
_lsb_distro_name    = None

SESSION_TYPE        = None

DESKTOP_ENV         = None
_desktop_env        = None


# ─── ENVIRONMENT ─────────────────────────────────────────────────────────────────


########################################################################
##  Get distro name
##  We don't provide a "simplified" distro name
##  Just pull it from /etc/os-release or /etc/lsb-release
try:
    with open('/etc/os-release', 'r') as f:
        for line in f:
            if line.startswith('NAME='):
                _os_distro_name = line.split('=')[1].strip().strip('"')
                break
except FileNotFoundError as file_error:
    error(file_error)

try:
        with open('/etc/lsb-release', 'r') as f:
            for line in f:
                if line.startswith('DISTRIB_ID='):
                    _lsb_distro_name = line.split('=')[1].strip().strip('"')
                    break
except FileNotFoundError as file_error:
    error(file_error)

if not _os_distro_name and not _lsb_distro_name:
        DISTRO_NAME = 'Unidentified'
        error(f"ENV: Distro name couldn't be found in /etc/os-release or /etc/lsb-release.")
else:
    DISTRO_NAME = _os_distro_name or _lsb_distro_name


########################################################################
##  Get session type
SESSION_TYPE = environ.get("XDG_SESSION_TYPE") or None

if not SESSION_TYPE:  # Why isn't XDG_SESSION_TYPE set? This shouldn't happen.
    error(f'ENV: XDG_SESSION_TYPE should really be set. Are you in a graphical environment?')
    SESSION_TYPE = environ.get("WAYLAND_DISPLAY")
    if not SESSION_TYPE:
        raise EnvironmentError(
            f'\n\nENV: Detecting session type from XDG_SESSION_TYPE or WAYLAND_DISPLAY failed.\n')
if SESSION_TYPE.casefold() not in ['x11', 'xorg', 'wayland']:
    raise EnvironmentError(f'\n\nENV: Unknown session type: {SESSION_TYPE}.\n')


########################################################################
##  Get desktop environment
_desktop_env = environ.get("XDG_SESSION_DESKTOP") or environ.get("XDG_CURRENT_DESKTOP") or None

if not _desktop_env:
    error("ENV: Desktop Environment not found in XDG_SESSION_DESKTOP or XDG_CURRENT_DESKTOP.")

# Produce a simplified desktop environment name
de_names = {
    'Budgie':                   'budgie',
    'Cinnamon':                 'cinnamon',
    'Deepin':                   'deepin',
    'Enlightenment':            'enlightenment',
    'GNOME':                    'gnome',
    'i3':                       'i3',
    'IceWM':                    'icewm',
    'KDE':                      'kde',
    'LXDE':                     'lxde',
    'LXQt':                     'lxqt',
    'MATE':                     'mate',
    'Pantheon':                 'pantheon',
    'Plasma':                   'kde',
    'SwayWM':                   'sway',
    'Ubuntu':                   'gnome',    # "Ubuntu" in XDG_CURRENT_DESKTOP, but DE is GNOME
    'Unity':                    'unity',
    'Xfce':                     'xfce',
}

if _desktop_env:
    for k, v in de_names.items():
        # debug(f'{k = :<18} {v = :<10}')
        if re.search(k, _desktop_env, re.I):
            DESKTOP_ENV = v
            break
if not DESKTOP_ENV:
    DESKTOP_ENV = _desktop_env or "Unidentified"
    error(f'ENV: Desktop Environment not in de_names list! Should fix this.\n\t{_desktop_env = }')

# Doublecheck the desktop environment by checking for identifiable running processes
for proc in psutil.process_iter(['name']):
    if proc.info['name'] in ['plasmashell', 'kwin_ft', 'kwin_x11']:
        if DESKTOP_ENV != 'kde':
            error(f'Desktop may have been misidentified: {DESKTOP_ENV = }. KWin detected.')
            DESKTOP_ENV = 'kde'
            break
    if proc.info['name'] == 'gnome-shell':
        if DESKTOP_ENV != 'gnome':
            error(f'Desktop may have been misidentified: {DESKTOP_ENV = }. GNOME Shell detected.')
            DESKTOP_ENV = 'gnome'
            break
    if proc.info['name'] == 'sway':
        if DESKTOP_ENV != 'sway':
            error(f'Desktop may have been misidentified: {DESKTOP_ENV = }. SwayWM detected.')
            DESKTOP_ENV = 'sway'
            break


debug("")
debug(f'ENV: {DISTRO_NAME  = }')
debug(f'ENV: {SESSION_TYPE = }')
debug(f'ENV: {DESKTOP_ENV  = }')

def get_env():
    return {
                "DISTRO_NAME"   : DISTRO_NAME,
                "SESSION_TYPE"  : SESSION_TYPE,
                "DESKTOP_ENV"   : DESKTOP_ENV,
            }
