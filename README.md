# keyszer - a smart key remapper for Linux

![work in progress](https://badgen.net/badge/status/beta?color=orange&scale=2)
[![discord](https://badgen.net/badge/icon/discord?icon=discord&label&color=pink&scale=2)](https://discord.gg/nX6qSC8mer)


**So this is a fork of xkeysnail?**

Yes, this is a fork/reboot of the popular [xkeysnail](https://github.com/mooz/xkeysnail) project.  The xkeysnail project seems largely unmaintained since it's last release in Fall 2020;  by unmaintained I mean that the author no longer seems involved (no commits, no releases, no comms on issues, no response to emails, no GitHub activity, etc).


**Is it ready for me to use/test?**

Certainly.  I've been using it myself full time with a 99% stock Kinto.sh config file.  If you're comfortable running from source and sending detailed bug reports we'd love to have your help.  If you're comfortable hacking on the source, even better!

See [UPGRADING_FROM_XKEYSNAIL.md](https://github.com/joshgoebel/keyszer/blob/exerted/UPGRADE_FROM_XKEYSNAIL.md) to get started with your upgrade.


**Is this compatible with [Kinto.sh](https://github.com/rbreaves/kinto)?**

**That is the plan.**  The major reason that Kinto.sh is using a fork has been resolved. Kinto.sh should simply "just work" with `keyszer`. In fact it should work better than before since many quirks with the Kinto version of xkeysnail are resolved. (such as nested combos not working, etc)

Note: If you want to get ahead of the curve you will need to alter your `kinto.py` config file just slightly. [USING_WITH_KINTO.md](https://github.com/joshgoebel/keyszer/blob/exerted/USING_WITH_KINTO.md)


**What features/fixes does it already have or have plans for in the near future?**

- [x] Slightly simpler configuration API
- [x] more debugging logging
- [x] initial tests framework
- [ ] more tests, tests, tests
- [x] entirely rewritten multi-modmap support
- [x] better conditional support (keymaps can now be conditional based on device name)
- [x] [#10](https://github.com/joshgoebel/keyszer/issues/10) No more running as root `root`
- [x] [#9](https://github.com/joshgoebel/keyszer/issues/9) `Alt`/`Super` wrongly trigger other non-combos when used as part of a combo
- [x] [#7](https://github.com/joshgoebel/keyszer/issues/7) Support for `Hyper` as a modifier
- [ ] [#2](https://github.com/joshgoebel/keyszer/issues/2) Support for `WM_NAME` conditionals
- [x] [#11](https://github.com/joshgoebel/keyszer/issues/11) Support "sticky" `Command-TAB` to proper support [Kinto.sh](https://github.com/rbreaves/kinto)


**Can I help/contribute?**

Sure.  Just open an issue to discuss how you'd like to get involved or respond on one of the existing issues. Or feel free to open new issues for feature requests.


---

# keyszer - a smart key remapper for Linux

<!-- [![latest version](https://badgen.net/pypi/v/keyszer?label=latest)]() -->
[![latest version](https://badgen.net/badge/version/0.5.0?color=orange)](https://github.com/joshgoebel/keyszer/releases)
[![](https://badgen.net/badge/python/3.10%20|%20%3F/blue)]()
[![license](https://badgen.net/badge/license/GPL3/keyszer?color=cyan)](https://github.com/joshgoebel/keyszer/blob/main/LICENSE)

<!-- ![build and CI status](https://badgen.net/github/checks/joshgoebel/keyszer/main?label=build) -->
<!-- [![code quality](https://badgen.net/lgtm/grade/g/joshgoebel/keyszer/js?label=code+quality)](https://lgtm.com/projects/g/joshgoebel/keyszer/?mode=list) -->
<!-- [![vulnerabilities](https://badgen.net/snyk/joshgoebel/keyszer)](https://snyk.io/test/github/joshgoebel/keyszer?targetFile=package.json) -->


[![discord](https://badgen.net/badge/icon/discord?icon=discord&label&color=pink)](https://discord.gg/nX6qSC8mer)
[![open issues](https://badgen.net/github/open-issues/joshgoebel/keyszer?label=issues)](https://github.com/joshgoebel/keyszer/issues)
[![help welcome issues](https://badgen.net/github/label-issues/joshgoebel/keyszer/help%20welcome/open)](https://github.com/joshgoebel/keyszer/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+welcome%22)
[![good first issue](https://badgen.net/github/label-issues/joshgoebel/keyszer/good%20first%20issue/open)](https://github.com/joshgoebel/keyszer/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22)

`keyszer` is a keyboard remapping tool for the X environment written in Python. It's similar `xmodmap` but allows more flexible remappings.

#### Features

- High-level and flexible remapping mechanisms:
    - **per-application keybindings**
    - **multiple stroke keybindings** such as `Ctrl+x Ctrl+c` to `Ctrl+q`
    - **multipurpose bindings** a regular key can become a modifier when held 
- Uses low-level libraries (`evdev` and `uinput`), making remapping work almost everywhere


This project was forked from [keyszer](https://github.com/mooz/keyszer) which itself was based on the older [pykeymacs](https://github.com/DreaminginCodeZH/pykeymacs).



## Installation

Requires **Python 3**.

<!--
### Ubuntu

    sudo apt install python3-pip
    sudo pip3 install keyszer
    
    # If you plan to compile from source
    sudo apt install python3-dev

### Fedora

    sudo dnf install python3-pip
    sudo pip3 install keyszer
    # Add your user to input group if you don't want to run keyszer
    # with sudo (log out and log in again to apply group change)
    sudo usermod -a -G input $USER
    
    # If you plan to compile from source
    sudo dnf install python3-devel
    
### Manjaro/Arch

    # Some distros will need to compile evdev components 
    # and may fail to do so if gcc is not installed.
    sudo pacman -Syy
    sudo pacman -S gcc
    
### Solus

    # Some distros will need to compile evdev components 
    # and may fail to do so if gcc is not installed.
    sudo eopkg install gcc
    sudo eopkg install -c system.devel
-->

### From source

    git clone https://github.com/joshgoebel/keyszer.git
    cd keyszer
    sudo pip3 install --upgrade .


### For testing/hacking/contributing

    git clone https://github.com/joshgoebel/keyszer.git
    cd keyszer
    python -m venv .venv
    source .venv/bin/activate
    pip3 install -e .
    ./bin/keyszer -c config_file


## Setup Requirements

We will need read/write access to:

- `/dev/input/event*` - to capture input from actual hardware input devices
- `/dev/uinput` - to present a pretend keyboard to the kernel

### Running as a user in the `input` group (most secure)

Some distros already have an input group, or you can create one.  You'll just need a few `udev` rules to make sure that the input devices are all given read/write access to that group.

`/etc/udev/rules.d/90-custom-input.rules`:

    SUBSYSTEM=="input", GROUP="input"
    KERNEL=="uinput", SUBSYSTEM=="misc", GROUP="input"

...and a new user that is a member of that group.


    sudo useradd keymapper -G input


#### systemd

For a sample systemd service file please see [keyszer.service](https://github.com/joshgoebel/keyszer/blob/main/keyszer.service).


### Running as Your Logged in User

#### Caveats / Security Concerns

- any running programs can potentially log all your keystrokes (including your passwords!) simply by monitoring the input devices

#### udev rules:

`/etc/udev/rules.d/90-custom-input.rules`:

```
SUBSYSTEM=="input", GROUP="input"
KERNEL=="uinput", SUBSYSTEM=="misc", OPTIONS+="static_node=uinput", TAG+="uaccess"
```

#### With Systemd

Would it make sense to use systemd here also?


#### With a graphical display manager?

HOW?


#### With `.xinitrc`

If you're using a minimal setup you can simply add us to your `.xinitrc`. For example to start us up and then start Awesome WM.

```
keyszer &
exec awesome
```


### Running as root (most insecure)

#### Caveats / Security Concerns

_Don't do this, it's bad, dangerous, and wholly unnecessary._


## Usage

    keyszer 


A successful startup will look a bit like:

    keyszer v0.4.99
    (--) CONFIG: /home/jgoebel/.config/keyszer/config.py
    (+K) Grabbing Apple, Inc Apple Keyboard (/dev/input/event3)
    (--) Ready to process input.

**Limiting Devices**

Limit remapping to specify devices with `--devices`:

    keyszer --devices /dev/input/event3 'Topre Corporation HHKB Professional'

The path or full device name can be used.

**Other Options:**

- `-c`, `--config` - location of the configuration file 
- `-w`, `--watch` - watch for new keyboard devices to hot-plug 
- `-v` - much increased verbosity to help with debugging
- `--list-devices` - list all available input devices


## Configuration

By default we will look for the configuration in `~/.config/keyszer/config.py` but you can override this location with the `-c`/`--config` switch.  The configuration file is a Python script that defines modmaps, keymaps, and other configuration details. 
For an example configuration please see [`example/config.py`](https://github.com/joshgoebel/keyszer/blob/main/example/config.py).




The configuration API:

- `timeout(s)`
- `add_modifier(name, aliases, key/keys)`
- `keymap(name, map, when)`
- `modmap(name, map)`
- `multipurpose_modmap(name, map)`
- `conditional(condition_fn, map)` - used to wrap maps and only apply them conditionally

### `timeout(s)`

Sets the number of seconds before multi-purpose modmaps timeout... ie, how long you have to press and release a key before it's instead assuming it's part of a combo.

### `add_modifier(name, aliases, key/keys)`

Allows you to add custom modifiers and then map them to actual keys.

```py
add_modifier("HYPER", aliases = ["Hyper"], key = Key.F24)
```

### `wm_class_match(re_str)`

Helper to make matching conditionals a tiny bit simpler.

```py
conditional(wm_class_match("^Firefox$"),
    keymap("Firefox",{
        # ... keymap here
    }))
```


### `not_wm_class_match(re_str)`

The opposite of `wm_class_match`, matches only when the regex is NOT a match.


### `modmap(name, mappings, when)`

Entirely maps one key to a different key, in all contexts.  Note that the default modmap will be overruled by any conditional modmaps that apply.  `when` can optionally be passed to make the modmap conditional.

```py
modmap("default", {
    # mapping caps lock to left control
    Key.CAPSLOCK: Key.LEFT_CTRL
})
```

### `multipurpose_modmap(name, mappings)`

Used to map a key with multiple-purposes, both for regular usage and use as a modifier (when held down).

```py
multipurpose_modmap("default",
    # Enter is enter when pressed and released. Control when held down.
    {Key.ENTER: [Key.ENTER, Key.RIGHT_CTRL]}
)
```


### `keymap(name, mappings)`

Defines a keymap consisting of `mappings` of the input combos mapped to output equivalents.

```py
keymap("Firefox", {
    # when Cmd-S is hit instead send Ctrl-S
    K("Cmd-s"): K("Ctrl-s"),
}, when = lambda ctx: ctx.wm_class == "Firefox")
```

Argument `mappings` is a dictionary in the form of `{key: command, key2:
command2, ...}` where `key` and `command` take following forms:
- `key`: Key to override specified by `K("YYY")`
    - For the syntax of key specification, please refer to the [key specification section](#key-specification).
- `command`: one of the followings
    - `K("YYY")`: Dispatch custom key to the application.
    - `[command1, command2, ...]`: Execute commands sequentially.
    - `{ ... }`: Sub-keymap. Used to define multiple stroke keybindings. See [multiple stroke keys](#multiple-stroke-keys) for details.
    - `escape_next_key`: Escape next key.
    - arbitrary function: The function is executed and the returned value is used as a command.

Argument `name` specifies the keymap name. Every keymap should have a name.  `default` is suggested for non-conditional keymaps.


### `conditional(fn, map)`

Applies a map conditionally only when the `fn` function evaluates `True`.  The below example is a modmap that is only active when the current `WM_CLASS` is `Terminal`.

```py
conditional(
    lambda ctx: ctx.wm_class == "Terminal",
    modmap({
        # ...
    })
)
```

The `context` object passed to the `fn` function has several attributes:

- `wm_class` - the WM_CLASS of the currently focused X11 window
- `device_name` - the name of the device an input event originated on

---

#### Key Specification

Key specification in a keymap is in a form of `K("(<Modifier>-)*<Key>")` where

`<Modifier>` is one of the following:

- `C` or `Ctrl` -> Control key
- `Alt` -> Alt key
- `Shift` -> Shift key
- `Super` or `Win` or `Cmd` -> Super/Windows/Command key

You can specify left/right modifiers by adding any one of prefixes `L`/`R`.

`<Key>` is a key whose name is defined
in [`key.py`](https://github.com/joshgoebel/keyszer/blob/main/keyszer/key.py).

Here is a list of key specification examples:

- `K("LC-Alt-j")`: `Left Ctrl` + `Alt` + `j`
- `K("Ctrl-m")`: `Ctrl` + `m`
- `K("Win-o")`: `Super/Windows` + `o`
- `K("Alt-Shift-comma")`: `Alt` + `Shift` + `comma`


#### Multiple Stroke Keys

When you needs multiple stroke keys, define a nested keymap. For example, the
following example remaps `C-x C-c` to `C-q`.

```python
keymap(None, {
    K("C-x"): {
      K("C-c"): K("C-q"),
    }
})
```


#### Finding an Application's `WM_CLASS` with `xprop`

To check `WM_CLASS` of the application you want to have custom keymap, use
`xprop` command:

    xprop WM_CLASS

and then click the application. `xprop` tells `WM_CLASS` of the application as follows.

    WM_CLASS(STRING) = "Navigator", "Firefox"

Use the second value (in this case `Firefox`) when matching `context.wm_class` when using a `conditional`.


#### Example of Case Insensitivity Matching

```py
terminals = ["gnome-terminal","konsole","io.elementary.terminal","sakura"]
terminals = [term.casefold() for term in terminals]
termStr = "|".join(str(x) for x in terminals)

conditional(
    lambda ctx: ctx.wm_class.casefold() not in terminals,
    modmap({
        Key.LEFT_ALT: Key.RIGHT_CTRL,   # WinMac
        # ... 
    }))

conditional(
    lambda ctx: re.compile(termStr, re.IGNORECASE).search(ctx.wm_class),
    modmap("default", {
        Key.LEFT_ALT: Key.RIGHT_CTRL,   # WinMac
        # ... 
    }))
```

## FAQ

*Can I remap the `Fn` key?*

Most laptops do not allow this as the `Fn` key is not directly exposed to the operating system.  On some keyboards it's just another key.  To find out you can run `evtest`.  Point it to your keyboard device and then hit a few keys; then try `Fn`.  If you get output, then you can map `Fn`.  If not, you can't.

Here is an example from a full size Apple keyboard I have:

```
Event: time 1654948033.572989, type 1 (EV_KEY), code 464 (KEY_FN), value 1
Event: time 1654948033.572989, -------------- SYN_REPORT ------------
Event: time 1654948033.636611, type 1 (EV_KEY), code 464 (KEY_FN), value 0
Event: time 1654948033.636611, -------------- SYN_REPORT ------------
```

## License

`keyszer` is distributed under GPL.  See our [LICENSE](https://github.com/joshgoebel/keyszer/blob/main/LICENSE).

    
