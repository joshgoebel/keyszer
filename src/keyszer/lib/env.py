from . import logger
from .logger import debug, error, info
from os import environ
import re


# ─── GLOBALS ─────────────────────────────────────────────────────────────────

DISTRO_NAME  = ""
SESSION_TYPE = environ.get("XDG_SESSION_TYPE") or ""
DESKTOP_ENV  = ""
_desktop_env = environ.get("XDG_SESSION_DESKTOP") or environ.get("XDG_CURRENT_DESKTOP")


# ─── ENVIRONMENT ─────────────────────────────────────────────────────────────────

# Get distro name
with open('/etc/os-release', 'r') as f:
    for line in f:
        if line.startswith('NAME='):
            DISTRO_NAME = line.split('=')[1].strip().strip('"')
            break
if not DISTRO_NAME:
    debug(f"ENV: Distro name couldn't be found in /etc/os-release.")

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

# Produce a simplified desktop environment name
de_names = {
    'Budgie':                   'budgie',
    'Cinnamon':                 'cinnamon',
    'Deepin':                   'deepin',
    'Enlightenment':            'enlightenment',
    'GNOME':                    'gnome',
    'IceWM':                    'icewm',
    'KDE':                      'kde',
    'LXDE':                     'lxde',
    'LXQt':                     'lxqt',
    'MATE':                     'mate',
    'Neon':                     'kde_neon',
    'Pantheon':                 'pantheon',
    'Plasma':                   'kde',
    'Ubuntu':                   'gnome',    # "Ubuntu" in XDG_CURRENT_DESKTOP, but DE is GNOME
    'Unity':                    'unity',
    'Xfce':                     'xfce',
}
for k, v in de_names.items():
    # debug(f'{k = :<10} {v = :<10}')
    if re.search(k, _desktop_env, re.I):
        DESKTOP_ENV = v
    if DESKTOP_ENV == 'kde' and re.search('neon', _desktop_env, re.I):
        DESKTOP_ENV = 'kde_neon'         # override 'kde' for KDE Neon
        break
    if DESKTOP_ENV:
        break
if not DESKTOP_ENV:
    debug(
        f'Desktop Environment not in de_names list! Should fix this.\n\t{_desktop_env = }', ctx="EE")

import psutil

# Doublecheck the desktop env by checking for running processes
for proc in psutil.process_iter(['name']):
    if proc.info['name'] == 'gnome-shell':
        DESKTOP_ENV = 'gnome'
        break
    if proc.info['name'] == 'sway':
        DESKTOP_ENV = 'sway'
        break


debug(f'ENV: {SESSION_TYPE = }')
debug(f'ENV: {DISTRO_NAME  = }')
debug(f'ENV: {DESKTOP_ENV  = }')


def get_env():
    return {"SESSION_TYPE": SESSION_TYPE, "DISTRO_NAME": DISTRO_NAME, "DESKTOP_ENV": DESKTOP_ENV}
