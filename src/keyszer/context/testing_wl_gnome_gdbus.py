
# This works but seems pretty slow to return, using gdbus commands to the shell

import subprocess
from keyszer.lib.logger import debug, error

print(f'#### running ctx_gnome_dbus_test.py ####')


NO_CONTEXT_WAS_ERROR = {"wm_class": "", "wm_name": "", "context_error": True}


def get_gnome_dbus_context():
    try:
        gdbus_class_result = subprocess.run(
            ["gdbus", "call", "--session", "--dest", "org.gnome.Shell",
            "--object-path", "/org/gnome/Shell/Extensions/WindowsExt",
            "--method", "org.gnome.Shell.Extensions.WindowsExt.FocusClass"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
        )
        gdbus_name_result = subprocess.run(
            ["gdbus", "call", "--session", "--dest", "org.gnome.Shell",
            "--object-path", "/org/gnome/Shell/Extensions/WindowsExt",
            "--method", "org.gnome.Shell.Extensions.WindowsExt.FocusTitle"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
        )

        if gdbus_class_result.returncode == 0:
            focused_window_class = gdbus_class_result.stdout.strip()
            wm_class = focused_window_class[2:-3]
            debug("### ### ### Focused window class:", f'{wm_class = }')
        else:
            error("Error running gdbus command:", gdbus_class_result.stderr.strip())

        if gdbus_name_result.returncode == 0:
            focused_window_name = gdbus_name_result.stdout.strip()
            wm_name = focused_window_name[2:-3]
            debug("### ### ### Focused window title:", f'{wm_name = }')
        else:
            error("Error running gdbus command:", gdbus_name_result.stderr.strip())

        return {"wm_class": wm_class, "wm_name": wm_name, "context_error": False}

    except Exception as gnome_dbus_error:
        error(f'#### {gnome_dbus_error = }')
        return NO_CONTEXT_WAS_ERROR

print(f"{get_gnome_dbus_context() = }")