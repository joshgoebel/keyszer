import re
import psutil
import dbus
import dbus.exceptions
from os import environ
from .logger import debug, error
from ..config_api import _ENVIRONMENT

# ─── GLOBALS ─────────────────────────────────────────────────────────────────

DISTRO_NAME     = ""
OS_DISTRO_NAME  = None
LSB_DISTRO_NAME = None

SESSION_TYPE    = environ.get("XDG_SESSION_TYPE") or ""
DESKTOP_ENV     = ""
_desktop_env    = environ.get("XDG_SESSION_DESKTOP") or environ.get("XDG_CURRENT_DESKTOP")


def get_env():
    return {
                "DISTRO_NAME"   : DISTRO_NAME,
                "SESSION_TYPE"  : SESSION_TYPE,
                "DESKTOP_ENV"   : DESKTOP_ENV,
            }


# ─── ENVIRONMENT ─────────────────────────────────────────────────────────────────


####################################
##  Get distro name
try:
    with open('/etc/os-release', 'r') as f:
        for line in f:
            if line.startswith('NAME='):
                OS_DISTRO_NAME = line.split('=')[1].strip().strip('"')
                break
except FileNotFoundError as file_error:
    error(file_error)

try:
        with open('/etc/lsb-release', 'r') as f:
            for line in f:
                if line.startswith('DISTRIB_ID='):
                    LSB_DISTRO_NAME = line.split('=')[1].strip().strip('"')
                    break
except FileNotFoundError as file_error:
    error(file_error)

if not OS_DISTRO_NAME and not LSB_DISTRO_NAME:
        DISTRO_NAME = 'Unidentified'
        error(f"ENV: Distro name couldn't be found in /etc/os-release or /etc/lsb-release.")
else:
    DISTRO_NAME = OS_DISTRO_NAME or LSB_DISTRO_NAME


####################################
##  Get session type
if not SESSION_TYPE:  # Why isn't XDG_SESSION_TYPE set? This shouldn't happen.
    debug(f'ENV: XDG_SESSION_TYPE should really be set. Are you in a graphical environment?')
    SESSION_TYPE = environ.get("WAYLAND_DISPLAY")
    if not SESSION_TYPE:
        raise EnvironmentError(
            f'\n\nENV: Detecting session type from XDG_SESSION_TYPE or WAYLAND_DISPLAY failed.\n')
if SESSION_TYPE.casefold() not in ['x11', 'xorg', 'wayland']:
    raise EnvironmentError(f'\n\nENV: Unknown session type: {SESSION_TYPE}.\n')

if not _desktop_env:
    _desktop_env = None
    debug("ENV ERROR: Desktop Environment not found in XDG_SESSION_DESKTOP or XDG_CURRENT_DESKTOP.")
    debug("ENV ERROR: Config file will not be able to adapt automatically to Desktop Environment.")


####################################
##  Get desktop environment

# Produce a simplified desktop environment name
de_names = {
    'Budgie':                   'budgie',
    'Cinnamon':                 'cinnamon',
    'Deepin':                   'deepin',
    'Enlightenment':            'enlightenment',
    'GNOME':                    'gnome',
    'Hyprland':                 'hypr',
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
for k, v in de_names.items():
    # debug(f'{k = :<10} {v = :<10}')
    if re.search(_desktop_env, k, re.I):
        DESKTOP_ENV = v
if not DESKTOP_ENV:
    DESKTOP_ENV = _desktop_env
    error(f'ENV: Desktop Environment not in de_names list! Should fix this.\n\t{_desktop_env = }')

# Doublecheck the desktop env by checking for running processes
for proc in psutil.process_iter(['name']):
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
    if proc.info['name'] in ['plasmashell', 'kwin_ft', 'kwin_x11']:
        if DESKTOP_ENV != 'kde':
            error(f'Desktop may have been misidentified: {DESKTOP_ENV = }. KWin detected.')
        DESKTOP_ENV = 'kde'
        break

from distro import name as dname

print(f'## ### testing distro module: {dname() = }')
debug("")
debug(f'ENV: {DISTRO_NAME  = }')
debug(f'ENV: {SESSION_TYPE = }')
debug(f'ENV: {DESKTOP_ENV  = }')
