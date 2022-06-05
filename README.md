# keyszer - a smart key remapper for Linux/X11

![work in progress](https://badgen.net/badge/status/alpha?color=red&scale=2)
[![discord](https://badgen.net/badge/icon/discord?icon=discord&label&color=pink&scale=2)](https://discord.gg/nX6qSC8mer)


**So this is a fork of xkeysnail?**

Yes, this is a fork/reboot of the popular [xkeysnail](https://github.com/mooz/xkeysnail) project.  The xkeysnail project seems largely unmaintained since it's last release in Fall 2020;  by unmaintained I mean that the author no longer seems involved (no commits, no releases, no comms on issues, no response to emails, no GitHub activity, etc).

**Why is the xkeysnail name still in so many places?**

I've reached out to the author of `xkeysnail` to see if I might simply take over the maintainership... I'm not expecting a response (at this point) but I haven't entirely given up yet.  Becoming maintainer of the existing project would simplify several things, responding to older issues, avoiding the need to rename, etc.

Sometime next week I'll likely change the name completely (and then release a beta on PyPi) if I haven't heard anything more.

**Is it ready to use/test?**

Maybe.  _I'd call it late alpha or early beta._  I've been code refactoring (and adding much needed tests) more than directly using, but that is now changing.  If you're comfortable running from the source and sending detailed bug reports I'd love to have your help.  If you're comfortable hacking on the source, even better!


**Is this compatible with [Kinto.sh](https://github.com/rbreaves/kinto)?**

That is the goal.  I haves plans to address the one major reason that kinto is using a fork with "sticky" modifier keys (for some combos)... at that point kinto should work just fine with `keyszer` - in fact even better since nested keymaps will start working again.


**What features/fixes does it already have or have plans for in the near future?**

- [x] Slightly simpler configuration API
- [x] more debugging logging
- [x] initial tests framework
- [ ] more tests, tests, tests
- [x] better conditional support (keymaps can now be conditional based on device name)
- [ ] #10 No more running as root `root`
- [x] #9 `Alt`/`Super` wrongly trigger other non-combos when used as part of a combo
- [ ] #7 Support for `Hyper` as a modifier
- [ ] #2 Support for `WM_NAME` conditionals
- [ ] #11 Support "sticky" `Command-TAB` to proper support [Kinto.sh](https://github.com/rbreaves/kinto)


**Can I help/contribute?**

Sure.  Just open an issue to discuss how you'd like to get involved or respond on one of the existing issues. Or feel free to open new issues for feature requests.


---

# keyszer

<!-- [![latest version](https://badgen.net/pypi/v/xkeysnail?label=latest)]() -->
[![latest version](https://badgen.net/badge/version/0.4.99?color=orange)](https://github.com/joshgoebel/xkeysnail/releases) 
[![](https://badgen.net/badge/python/3.10%20|%20%3F/blue)]()
[![license](https://badgen.net/badge/license/GPL3/xkeysnail?color=cyan)](https://github.com/joshgoebel/xkeysnail/blob/main/LICENSE)

<!-- ![build and CI status](https://badgen.net/github/checks/joshgoebel/xkeysnail/main?label=build) -->
<!-- [![code quality](https://badgen.net/lgtm/grade/g/joshgoebel/xkeysnail/js?label=code+quality)](https://lgtm.com/projects/g/joshgoebel/xkeysnail/?mode=list) -->
<!-- [![vulnerabilities](https://badgen.net/snyk/joshgoebel/xkeysnail)](https://snyk.io/test/github/joshgoebel/xkeysnail?targetFile=package.json) -->


[![discord](https://badgen.net/badge/icon/discord?icon=discord&label&color=pink)](https://discord.gg/nX6qSC8mer)
[![open issues](https://badgen.net/github/open-issues/joshgoebel/xkeysnail?label=issues)](https://github.com/joshgoebel/xkeysnail/issues)
[![help welcome issues](https://badgen.net/github/label-issues/joshgoebel/xkeysnail/help%20welcome/open)](https://github.com/joshgoebel/xkeysnail/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+welcome%22)
[![good first issue](https://badgen.net/github/label-issues/joshgoebel/xkeysnail/good%20first%20issue/open)](https://github.com/joshgoebel/xkeysnail/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22)

`keyszer` is a keyboard remapping tool for X environment written in Python. It's similar `xmodmap` but allows more flexible remappings.

#### Features

- High-level and flexible remapping mechanisms:
    - **per-application keybindings**
    - **multiple stroke keybindings** such as `Ctrl+x Ctrl+c` to `Ctrl+q`
    - **multipurpose bindings** a regular key can become a modifier when held 
- Uses low-level libraries (`evdev` and `uinput`), making remapping work almost everywhere


This project was originally forked from [xkeysnail](https://github.com/mooz/xkeysnail) which itself was based on the older [pykeymacs](https://github.com/DreaminginCodeZH/pykeymacs). The primary goals are to once again have an active maintainer and focus on improved reliability and security (no more root!).



## Installation

**These instructions are not correct yet.**

Requires **Python 3**.

<!--
### Ubuntu

    sudo apt install python3-pip
    sudo pip3 install xkeysnail
    
    # If you plan to compile from source
    sudo apt install python3-dev

### Fedora

    sudo dnf install python3-pip
    sudo pip3 install xkeysnail
    # Add your user to input group if you don't want to run xkeysnail
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

    git clone https://github.com/joshgoebel/xkeysnail.git
    cd xkeysnail
    sudo pip3 install --upgrade .

## Requirements

We will need read/write access to:

- `/dev/input/event*` - to capture input from actual hardware keyboards
- `/dev/uinput` - to present ourselves as a pretend keyboard to the kernel

### Running as a user in the `input` group (most secure)

Some distros already have an input group, or you can create one.  You'll just need `udev` rules to make sure that the input devices are all given read/write access to that group.

`/etc/udev/rules.d/90-input.rules`:

```
SUBSYSTEM=="input", GROUP="input"
KERNEL=="uinput", SUBSYSTEM=="misc", GROUP="input"
```

Now create a new user that is a member of that group.  We'll name them `xkeysnail`.

```
sudo useradd xkeysnail -G input
```

#### systemd

Then lets have a systemd service to run:

```
[Unit]
Description=xkeysnail

[Service]
Type=simple
KillMode=process
ExecStart=xkeysnail --quiet --watch
Restart=on-failure
RestartSec=3
Environment=DISPLAY=:0
User=xkeysnail
Group=input

[Install]
WantedBy=graphical.target
```

### Running under own user account 

#### udev rules:

`/etc/udev/rules.d/90-input.rules`:

```
SUBSYSTEM=="input", GROUP="input"
KERNEL=="uinput", SUBSYSTEM=="misc", OPTIONS+="static_node=uinput", TAG+="uaccess"
```

#### systemd

Would it make sense to use systemd here also?


#### With a graphical display manager?

HOW?


#### with `.xinitrc`

If you're using a minimal setup you can simply add us to your `.xinitrc`. For example to start us up and then start Awesome WM.

```
xkeysnail &
exec awesome
```


### Running as root (most insecure)

_Don't do this, it's bad, and wholly unnecessary._

## Usage

    xkeysnail

To specify the location of a config file (otherwise the default  `~/.config/xkeysnail/config.py` will be used):

    xkeysnail -c config.py

If you want to limit to only specify keyboard devices, use `--devices`:

    xkeysnail --devices /dev/input/event3 'Topre Corporation HHKB Professional'

If you have hot-plugging keyboards, use `--watch` option.

If you want to suppress output of key events, use `-q` / `--quiet` option especially when running as a daemon.


## Configuration

By default we will look for the configuration in `~/.config/xkeysnail/config.py` but you can override this location with the `-c` switch.  The configuration file is a Python script that defines modmaps, keymaps, and other configuration details. 

The configuration API:

- `timeout`
- `keymap`
- `modmap`
- `conditional_modmap`
- `multipurpose_modmap`
- `conditional_multipurpose_modmap`

### `modmap`



### `conditional_modmap`

### `multipurpose_modmap`

### `conditional_multipurpose_modmap`

### `keymap(condition, mappings, name)`

Defines a keymap consists of `mappings`, which is activated when the `condition`
is satisfied.

Argument `condition` specifies the condition of activating the `mappings` on an
application and takes one of the following forms:
- Regular expression (e.g., `re.compile("YYY")`)
    - Activates the `mappings` if the pattern `YYY` matches the `WM_CLASS` of the application.
    - Case Insensitivity matching against `WM_CLASS` via `re.IGNORECASE` (e.g. `re.compile('Gnome-terminal', re.IGNORECASE)`)
- `lambda wm_class: some_condition(wm_class)`
    - Activates the `mappings` if the `WM_CLASS` of the application satisfies the condition specified by the `lambda` function.
    - Case Insensitivity matching via `casefold()` or `lambda wm_class: wm_class.casefold()` (see example below to see how to compare to a list of names)
- `None`: Refers to no condition. `None`-specified keymap will be a global keymap and is always enabled.

Argument `mappings` is a dictionary in the form of `{key: command, key2:
command2, ...}` where `key` and `command` take following forms:
- `key`: Key to override specified by `K("YYY")`
    - For the syntax of key specification, please refer to the [key specification section](#key-specification).
- `command`: one of the followings
    - `K("YYY")`: Dispatch custom key to the application.
    - `[command1, command2, ...]`: Execute commands sequentially.
    - `{ ... }`: Sub-keymap. Used to define multiple stroke keybindings. See [multiple stroke keys](#multiple-stroke-keys) for details.
    - `pass_through_key`: Pass through `key` to the application. Useful to override the global mappings behavior on certain applications.
    - `escape_next_key`: Escape next key.
    - Arbitrary function: The function is executed and the returned value is used as a command.
        - Can be used to invoke UNIX commands.

Argument `name` specifies the keymap name. This is an optional argument.

#### Key Specification

Key specification in a keymap is in a form of `K("(<Modifier>-)*<Key>")` where

`<Modifier>` is one of the followings
- `C` or `Ctrl` -> Control key
- `M` or `Alt` -> Alt key
- `Shift` -> Shift key
- `Super` or `Win` -> Super/Windows key

You can specify left/right modifiers by adding any one of prefixes `L`/`R`.

And `<Key>` is a key whose name is defined
in [`key.py`](https://github.com/joshgoebel/xkeysnail/blob/main/xkeysnail/key.py).

Here is a list of key specification examples:

- `K("C-M-j")`: `Ctrl` + `Alt` + `j`
- `K("Ctrl-m")`: `Ctrl` + `m`
- `K("Win-o")`: `Super/Windows` + `o`
- `K("M-Shift-comma")`: `Alt` + `Shift` + `comma` (= `Alt` + `>`)

#### Multiple stroke keys

When you needs multiple stroke keys, define a nested keymap. For example, the
following example remaps `C-x C-c` to `C-q`.

```python
define_keymap(None, {
    K("C-x"): {
      K("C-c"): K("C-q"),
      K("C-f"): K("C-q"),
    }
})
```

#### Checking an application's `WM_CLASS` with `xprop`

To check `WM_CLASS` of the application you want to have custom keymap, use
`xprop` command:

    xprop WM_CLASS

and then click the application. `xprop` tells `WM_CLASS` of the application as follows.

    WM_CLASS(STRING) = "Navigator", "Firefox"

Use the second value (in this case `Firefox`) as the `WM_CLASS` value in your
`config.py`.

### Example `config.py`

See [`example/config.py`](https://github.com/joshgoebel/xkeysnail/blob/main/example/config.py).

Here is an excerpt of `example/config.py`.

```python
define_keymap(re.compile("Firefox|Google-chrome"), {
    # Ctrl+Alt+j/k to switch next/previous tab
    K("C-M-j"): K("C-TAB"),
    K("C-M-k"): K("C-Shift-TAB"),
}, "Firefox and Chrome")

define_keymap(re.compile("Zeal"), {
    # Ctrl+s to focus search area
    K("C-s"): K("C-k"),
}, "Zeal")

define_keymap(lambda wm_class: wm_class not in ("Emacs", "URxvt"), {
    # Cancel
    K("C-g"): [K("esc"), set_mark(False)],
    # Escape
    K("C-q"): escape_next_key,
    # C-x YYY
    K("C-x"): {
        # C-x h (select all)
        K("h"): [K("C-home"), K("C-a"), set_mark(True)],
        # C-x C-f (open)
        K("C-f"): K("C-o"),
        # C-x C-s (save)
        K("C-s"): K("C-s"),
        # C-x k (kill tab)
        K("k"): K("C-f4"),
        # C-x C-c (exit)
        K("C-c"): K("M-f4"),
        # cancel
        K("C-g"): pass_through_key,
        # C-x u (undo)
        K("u"): [K("C-z"), set_mark(False)],
    }
}, "Emacs-like keys")
```

### Example of Case Insensitivity Matching

```py
terminals = ["gnome-terminal","konsole","io.elementary.terminal","sakura"]
terminals = [term.casefold() for term in terminals]
termStr = "|".join(str(x) for x in terminals)

# [Conditional modmap] Change modifier keys in certain applications
define_conditional_modmap(lambda wm_class: wm_class.casefold() not in terminals,{
    # Default Mac/Win
    Key.LEFT_ALT: Key.RIGHT_CTRL,   # WinMac
    Key.LEFT_META: Key.LEFT_ALT,    # WinMac
    Key.LEFT_CTRL: Key.LEFT_META,   # WinMac
    Key.RIGHT_ALT: Key.RIGHT_CTRL,  # WinMac
    Key.RIGHT_META: Key.RIGHT_ALT,  # WinMac
    Key.RIGHT_CTRL: Key.RIGHT_META, # WinMac
})

# [Conditional modmap] Change modifier keys in certain applications
define_conditional_modmap(re.compile(termStr, re.IGNORECASE), {

    # Default Mac/Win
    Key.LEFT_ALT: Key.RIGHT_CTRL,   # WinMac
    Key.LEFT_META: Key.LEFT_ALT,    # WinMac
    Key.LEFT_CTRL: Key.LEFT_CTRL,   # WinMac
    Key.RIGHT_ALT: Key.RIGHT_CTRL,  # WinMac
    Key.RIGHT_META: Key.RIGHT_ALT,  # WinMac
    Key.RIGHT_CTRL: Key.LEFT_CTRL,  # WinMac
})
```

## FAQ

None yet.

## License

`keyszer` is distributed under GPL.  See our [LICENSE](https://github.com/joshgoebel/xkeysnail/blob/main/LICENSE).

    