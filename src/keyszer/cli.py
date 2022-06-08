# -*- coding: utf-8 -*-
from .logger import *
from .info import __version__, __name__, __description__

CONFIG_HEADER = b"""
# -*- coding: utf-8 -*-
import re
from keyszer.transform import with_mark, set_mark, with_or_set_mark
from keyszer.config_api import *
"""

def eval_config(path):
    with open(path, "rb") as file:
        config_code = CONFIG_HEADER + file.read()
        exec(compile(config_code, path, 'exec'), globals())


def uinput_device_exists():
    from os.path import exists
    return exists('/dev/uinput')


def has_access_to_uinput():
    from evdev.uinput import UInputError
    try:
        from keyszer.output import _uinput  # noqa: F401
        return True
    except UInputError:
        return False


def main():
    # Parse args
    import argparse
    from appdirs import user_config_dir
    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument('-c', '--config', dest="config", metavar="config.py", type=str, 
                        default=user_config_dir('keyszer/config.py'),
                        help='use custom configuration file')
    parser.add_argument('-d', '--devices', dest="devices", metavar='device', type=str, nargs='+',
                        help='manually specify devices to remap')
    parser.add_argument('-w', '--watch', dest='watch', action='store_true',
                        help='watch for new hot-plugged devices')
    parser.add_argument('-q', '--quiet', dest='quiet', action='store_true',
                        help='suppress output of key events')
    parser.add_argument('--list-devices', dest='list_devices', action='store_true',
                        help="")
    parser.add_argument('--version', dest='show_version', action='store_true',
                        help='')
    parser.add_argument('--very-bad-idea', dest='run_as_root', action='store_true',
                        help="(deprecated: run as root, don't do this)")
    args = parser.parse_args()

    if args.show_version:
        print(f"{__name__} v{__version__}")
        exit(0)

    print(f"{__name__} v{__version__}")

    import os
    if os.getuid()==0:
        if not args.run_as_root:
            log("ROOT: All your base are belong to us! ;-)")
            error("Please don't run me as root.  It's a --very-bad-idea, seriously.")
            info("Running as root is deprecated, prefer running as a semi-priveleged user.")
            exit(0)
        else:
            log("ROOT: Yes, I am.  --very-bad-idea received and acknowledged.")

    if args.list_devices:
        from .input import get_devices_list, print_device_list
        print_device_list(get_devices_list())
        exit(0)

    # Make sure that the /dev/uinput device exists
    if not uinput_device_exists():
        error("""The '/dev/uinput' device does not exist.
Please check kernel configuration.""")
        import sys
        sys.exit(1)

    # Make sure that user have root privilege
    if not has_access_to_uinput():
        error("""Failed to open `uinput` in write mode.
Please check access permissions for /dev/uinput.""")
        import sys
        sys.exit(1)

    

    # Load configuration file
    eval_config(args.config)

    log(f"CONFIG: {args.config}")

    if args.quiet:
        log("QUIET: key output supressed.")

    if args.watch:
        log("WATCH: Watching for new devices to hot-plug.")

    # Enter event loop
    from keyszer.input import main_loop
    main_loop(args.devices, args.watch, args.quiet)
