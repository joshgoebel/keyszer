from .lib.logger import log, error, info, debug
from .lib import logger
from .version import __version__, __name__, __description__

CONFIG_HEADER = b"""
import re
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
        from keyszer.output import setup_uinput  # noqa: F401
        setup_uinput()
        return True
    except UInputError:
        return False


def main():
    # Parse args
    import argparse
    from appdirs import user_config_dir
    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument('-c', '--config', dest="config", metavar="config.py",
                        type=str,
                        default=user_config_dir('keyszer/config.py'),
                        help='use custom configuration file')
    parser.add_argument('-d', '--devices', dest="devices", metavar='device',
                        type=str, nargs='+',
                        help='manually specify devices to remap')
    parser.add_argument('-w', '--watch', dest='watch', action='store_true',
                        help='watch for new hot-plugged devices')
    parser.add_argument('-v', dest='verbose', action='store_true',
                        help='increase debug logging')
    parser.add_argument('--list-devices', dest='list_devices',
                        action='store_true', help="")
    parser.add_argument('--check', dest='check_config', action='store_true',
                        help="evaluate config script, check for syntax errors")
    parser.add_argument('--version', dest='show_version', action='store_true',
                        help='')
    parser.add_argument('--very-bad-idea', dest='run_as_root',
                        action='store_true',
                        help="(deprecated: run as root)")
    args = parser.parse_args()

    if args.show_version:
        print(f"{__name__} v{__version__}")
        exit(0)

    if args.verbose:
        logger.VERBOSE = True

    print(f"{__name__} v{__version__}")

    import os
    if os.getuid() == 0:
        if not args.run_as_root:
            log("ROOT: All your base are belong to us! ;-)")
            error(
                "Please don't run me as root.  "
                "It's a --very-bad-idea, seriously.")
            info(
                "Running as root is deprecated, prefer running "
                "as a semi-priveleged user.")
            exit(0)
        else:
            log("ROOT: Yes, I am.  --very-bad-idea acknowledged.")

    if args.list_devices:
        from .input import Devices
        Devices.print_list()
        exit(0)

    if args.check_config:
        config_good = False
        try:
            eval_config(args.config)
            log("CONFIG: Looks good to me.")
            config_good = True
        except:  # noqa: E722
            import traceback
            error("CONFIG: No bueno, we have a problem...")
            traceback.print_exc()
        exit(0) if config_good else exit(1)

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

    debug(f"CONFIG: {args.config}")

    # Load configuration file
    eval_config(args.config)

    if args.watch:
        log("WATCH: Watching for new devices to hot-plug.")

    # Enter event loop
    from keyszer.input import main_loop
    main_loop(args.devices, args.watch)
