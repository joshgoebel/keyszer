# keyszer - a smart key remapper for Linux/X11

[![latest version](https://badgen.net/pypi/v/keyszer?label=latest)](https://github.com/joshgoebel/keyszer/releases)
[![](https://badgen.net/badge/python/3.10/blue)]()
[![license](https://badgen.net/badge/license/GPL3/keyszer?color=cyan)](https://github.com/joshgoebel/keyszer/blob/main/LICENSE)
[![discord](https://badgen.net/badge/icon/discord?icon=discord&label&color=pink)](https://discord.gg/nX6qSC8mer)

<!-- ![build and CI status](https://badgen.net/github/checks/joshgoebel/keyszer/main?label=build) -->
<!-- [![code quality](https://badgen.net/lgtm/grade/g/joshgoebel/keyszer/js?label=code+quality)](https://lgtm.com/projects/g/joshgoebel/keyszer/?mode=list) -->
<!-- [![vulnerabilities](https://badgen.net/snyk/joshgoebel/keyszer)](https://snyk.io/test/github/joshgoebel/keyszer?targetFile=package.json) -->


[![open issues](https://badgen.net/github/open-issues/joshgoebel/keyszer?label=issues)](https://github.com/joshgoebel/keyszer/issues)
[![help welcome issues](https://badgen.net/github/label-issues/joshgoebel/keyszer/help%20welcome/open)](https://github.com/joshgoebel/keyszer/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+welcome%22)
[![good first issue](https://badgen.net/github/label-issues/joshgoebel/keyszer/good%20first%20issue/open)](https://github.com/joshgoebel/keyszer/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22)


Keyszer is a smart key remapper for Linux (and X11) written in Python. It's similar to `xmodmap` but allows far more flexible remappings.  Keyszer was forked from [xkeysnail](https://github.com/mooz/xkeysnail) which no longer seems actively maintained.


### How does it work?

Keyszer works at quite a low-level.  It grabs input directly from the kernel's input devices (`/dev/input/event*`) and then creates an emulated device ([uinput](https://www.kernel.org/doc/html/v4.12/input/uinput.html)) to inject those inputs back into the kernel.  During this process the input stream is transformed on the fly as necessary to remap keys.


**Upgrading from xkeysnail**

- Some small config changes will be necessary.
- A few command line arguments have changed.
- For xkeysnail 0.4.0 see [UPGRADING_FROM_XKEYSNAIL.md](https://github.com/joshgoebel/keyszer/blob/main/UPGRADE_FROM_XKEYSNAIL.md).
- For xkeysnail (Kinto fork) see [USING_WITH_KINTO.md](https://github.com/joshgoebel/keyszer/blob/main/USING_WITH_KINTO.md) and [Using with Kinto v1.2-13](https://github.com/joshgoebel/keyszer/issues/36).


#### Primary Highlights

- Low-level library usage (`evdev` and `uinput`) allows remapping to work from the console all the way into X11.
- High-level and incredibly flexible remapping mechanisms:
    - _per-application keybindings_ - bindings that change depending on the active X11 application or window
    - _multiple stroke keybindings_ - `Ctrl+x Ctrl+c` could map to `Ctrl+q`
    - _very flexible output_ - `Ctrl-s` could type out `:save`, then hit enter
    - _multipurpose bindings_ - a regular key can become a modifier when held
    - _arbitrary functions_ - a key combo can run custom Python function


**New Features (since xkeysnail 0.4.0)**

- simpler and more flexible configuration scripting APIs
- better debugging tools
  - configurable `EMERGENCY EJECT` hotkey
  - configurable `DIAGNOSTIC` hotkey
- fully supports running as non-privleged user (using `root` is now deprecated)
- adds `Command` and `Cmd` aliases for Super/Meta
- supports custom modifiers via `add_modifier`, such as `Hyper`
- supports `Fn` as a modifier (on hardware where it works)
- `bind` helper supports persistent holds for Mac OS style Cmd-tab, etc.
- adds checking config file for issues with --check
- adds `wm_name` conditionals (open PR)
- adds `device_name` for all conditionals (including keymaps)
- (fix) `xmodmap` cannot be used until some keys are pressed on the output
- (fix) ability to avoid unintentional Alt/Super mis-triggers in many setups
- (fix) fixes multi-combo nested keymaps (vs Kinto's xkeysnail)
- (fix) properly cleans up `uinput` pressed keys before termination


---

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

Just downloading the source and install.

    git clone https://github.com/joshgoebel/keyszer.git
    cd keyszer
    pip3 install --user --upgrade .


### For testing/hacking/contributing

Using a Python `venv` might be the simplest way to get started:

    git clone https://github.com/joshgoebel/keyszer.git
    cd keyszer
    python -m venv .venv
    source .venv/bin/activate
    pip3 install -e .
    ./bin/keyszer -c config_file


## System Requirements

keyszer requires read/write access to all of:

- `/dev/input/event*` - to grab input from actual input devices
- `/dev/uinput` - to provide an emulated keyboard to the kernel


### Running as a semi-privleged user

It's best to create an entirely isolated user to run the keymapper.  Group or ACL based permissions can be used to give this user access to the necessary devices.  You'll need only a few `udev` rules to ensure that the input devices are all given correct permissions.


#### ACL based permissions (narrow, more secure)

First, lets make a new user:

    sudo useradd keymapper

...then ask udev to use ACL to give our new user access to everything:

*/etc/udev/rules.d/90-keymapper-acl.rules*

    KERNEL=="event*", SUBSYSTEM=="input", RUN+="/usr/bin/setfacl -m user:keymapper:rw /dev/input/%k"
    KERNEL=="uinput", SUBSYSTEM=="misc", RUN+="/usr/bin/setfacl -m user:keymapper:rw /dev/uinput"


#### Group based permissions (wider, less secure)

Some distros already have an input group; if not, you can create one.  Next, add a new user that's a member of said group:

    sudo useradd keymapper -G input

...then ask udev to make sure our user has access to everything (via the input group):

*/etc/udev/rules.d/90-keymapper-input.rules*

    SUBSYSTEM=="input", GROUP="input"
    KERNEL=="uinput", SUBSYSTEM=="misc", GROUP="input"


#### systemd

For a sample systemd service file for running keyszer as a service please see [keyszer.service](https://github.com/joshgoebel/keyszer/blob/main/keyszer.service).


### Running as the Logged in User

_TODO: remove this section entirely?_


#### Caveats / Security Concerns

- running programs could potentially log all your keystrokes (including your passwords!) simply by monitoring the input devices (that you must give yourself access to for this to work)

Add your yourself to the input group:

    usermod -a -G input [username]

#### udev rules:

`/etc/udev/rules.d/90-custom-input.rules`:

```
SUBSYSTEM=="input", GROUP="input"
KERNEL=="uinput", SUBSYSTEM=="misc", OPTIONS+="static_node=uinput", TAG+="uaccess"
```



#### With a graphical display manager?

_HOW? Shouldn't systemd cover this already?_


#### With `.xinitrc`

When using a very minimal setup you can simply add us to your `.xinitrc`. For example to start us up and then start Awesome WM.

```
keyszer --watch &
exec awesome
```


### Running as root (most insecure)

_Don't do this, it's bad, dangerous, and wholly unnecessary._  A semi-priveleged user is always better.


## Usage

    keyszer 


A successful startup should resemble:

    keyszer v0.5.0
    (--) CONFIG: /home/jgoebel/.config/keyszer/config.py
    (+K) Grabbing Apple, Inc Apple Keyboard (/dev/input/event3)
    (--) Ready to process input.

**Limiting Devices**

Limit remapping to specify devices with `--devices`:

    keyszer --devices /dev/input/event3 'Topre Corporation HHKB Professional'

The full path or completee device name may be used.

**Other Options:**

- `-c`, `--config` - location of the configuration file 
- `-w`, `--watch` - watch for new keyboard devices to hot-plug 
- `-v` - increase verbosity greatly (to help with debugging)
- `--list-devices` - list all available input devices


## Configuration

By default we look for the configuration in `~/.config/keyszer/config.py`. You can override this location using the `-c`/`--config` switch.  The configuration file is written in Python.
For an example configuration please see [`example/config.py`](https://github.com/joshgoebel/keyszer/blob/main/example/config.py).


The configuration API:

- `timeouts(multipurpose, suspend)`
- `wm_class_match(re_str)`
- `not_wm_class_match(re_str)`
- `add_modifier(name, aliases, key/keys)`
- `modmap(name, map, when_conditional)`
- `multipurpose_modmap(name, map, when_conditional)`
- `keymap(name, map, when_conditional)`
- `conditional(condition_fn, map)` - used to wrap maps, applying them conditionally
- `dump_diagnostics_key(key)`
- `emergency_eject_key(key)`


### `timeouts(...)`

Configures the timing behavior of various aspects of the keymapper.

- `multipurpose` - The number of seconds before a held multi-purpose key is assumed to be a modifier (evne in the absense of other keys).
- `suspend` - The number of seconds modifiers are "suspended" and withheld from the output waiting to see whether if they are part of a combo or if they may be the actual intended output.


### `dump_diagnostics_key(key)`

Configures a key that when hit will dump additional diagnostic information to STDOUT.


### `emergency_eject_key(key)`

Configures a key that when hit will immediately terminate keyszer; useful for development, recovering from bugs, or badly broken configurations.


### `add_modifier(name, aliases, key/keys)`

Allows you to add custom modifiers and then map them to actual keys.

```py
add_modifier("HYPER", aliases = ["Hyper"], key = Key.F24)
```


### `wm_class_match(re_str)`

Helper to make matching conditionals a tiny bit simpler.

```py
keymap("Firefox",{
    # ... keymap here
}, when = m_class_match("^Firefox$"))
```


### `not_wm_class_match(re_str)`

The opposite of `wm_class_match`, matches only when the regex is NOT a match.


### `modmap(name, mappings, when_conditional = None)`

Maps a singel physicl key to an entirely different key.  A default modmap will be overruled by any conditional modmaps that apply.  `when_conditional` can be passed to make the modmap conditional.

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

Argument `mappings` is a dictionary in the form of `{combo: command, combo2:
command2, ...}` where `combo` and `command` take following forms:
- `combo`: Combo to map, specified by `K(combo_string)`
    - For the syntax of combo specifications, see [Combo Specifications](#combo-specifications).
- `command`: one of the following
    - `K("YYY")`: Type a specific key combo to the output.
    - `[command1, command2, ...]`: Execute multiple commands sequentially.
    - `{ ... }`: Sub-keymap. Used to define multiple stroke keybindings. See [Multiple Stroke Keys](#multiple-stroke-keys) for details.
    - `escape_next_key`: Escape the next key.
    - `ignore_key`: Ignore the key combo entirely.
    - `bind`: Bind input and ouput modifier together such that the output is not lifted until the input is.
    - arbitrary function: The function is executed and the returned value (if any) is used as a command.

Argument `name` specifies the keymap name. Every keymap should have a name.  `default` is suggested for non-conditional keymaps.


### `conditional(fn, map)`

Applies a map conditionally, only when the `fn` function evaluates `True`.  The below example is a modmap that is only active when the current `WM_CLASS` is `Terminal`.

```py
conditional(
    lambda ctx: ctx.wm_class == "Terminal",
    modmap({
        # ...
    })
)
```

The `context` object passed to the `fn` function has several attributes:

- `wm_class` - the WM_CLASS of the [input] focused X11 window
- `wm_name` - the WM_NAME of the [input] focused X11 window
- `device_name` - name of the device where an input originated

---

#### Marks

TODO: need docs (See #8)


#### Combo Specifications

The Combo specification in a keymap is written in the form of `K("(<Modifier>-)*<Key>")`.

`<Modifier>` is one of the following:

- `C` or `Ctrl` -> Control key
- `Alt` -> Alt key
- `Shift` -> Shift key
- `Super`, `Win`, `Command`, `Cmd`, `Meta` -> Super/Windows/Command key
- `Fn` -> Function key (on supported keyboards)

You can specify left/right modifiers by adding the prefixes `L` or `R`.

`<Key>` is any key whose name is defined in [`key.py`](https://github.com/joshgoebel/keyszer/blob/main/keyszer/models/key.py).

Some combo examples:

- `K("LC-Alt-j")`: left Control, Alt, `j`
- `K("Ctrl-m")`: Left or Right Control, `m`
- `K("Win-o")`: Cmd/Windows,  `o`
- `K("Alt-Shift-comma")`: Alt, Left or Right Shift, comma


#### Multiple Stroke Keys

To use multiple stroke keys, simply define a nested keymap. For example, the
following example remaps `C-x C-c` to `C-q`.

```python
keymap("multi stroke", {
    K("C-x"): {
      K("C-c"): K("C-q"),
    }
})
```


#### Finding an Application's `WM_CLASS`  and `WM_NAME` using `xprop`

Use the `xprop` command from a terminal:

    xprop WM_CLASS WM_NAME

...then click an application window.  Let's try it with Google Chrome:

    WM_CLASS(STRING) = "google-chrome", "Google-chrome"
    WM_NAME(UTF8_STRING) = "README - Google Chrome"

Use the second `WM_CLASS` value (in this case `Google-chrome`) when matching `context.wm_class`.


#### Example of Case Insensitive Matching

```py
terminals = ["gnome-terminal","konsole","io.elementary.terminal","sakura"]
terminals = [term.casefold() for term in terminals]
USING_TERMINAL_RE = re.compile("|".join(terminals), re.IGNORECASE)

modmap("not in terminal", {
    Key.LEFT_ALT: Key.RIGHT_CTRL,
    # ...
    }, when = lambda ctx: ctx.wm_class.casefold() not in terminals
)

modmap("terminals", {
    Key.RIGHT_ALT: Key.RIGHT_CTRL,
    # ...
    }, when = lambda ctx: USING_TERMINAL_RE.search(ctx.wm_class)
)
```


## FAQ


**Can I remap the keyboard's `Fn` key?**

_It depends._  Most laptops do not allow this as the `Fn` keypress events are not _directly_ exposed to the operating system.  On some keyboards, it's just another key.  To find out you can run `evtest`.  Point it to your keyboard device and then hit a few keys; then try `Fn`.  If you get output, then you can map `Fn`.  If not, you can't.

Here is an example from a full size Apple keyboard I have:

```
Event: time 1654948033.572989, type 1 (EV_KEY), code 464 (KEY_FN), value 1
Event: time 1654948033.572989, -------------- SYN_REPORT ------------
Event: time 1654948033.636611, type 1 (EV_KEY), code 464 (KEY_FN), value 0
Event: time 1654948033.636611, -------------- SYN_REPORT ------------
```


**Is keyszer compatible with [Kinto.sh](https://github.com/rbreaves/kinto)?**


*That is certainly the plan.*   The major reason Kinto.sh required it's own fork [has been resolved](https://github.com/joshgoebel/keyszer/issues/11).  Kinto.sh should simply "just work" with `keyszer` (with a few tiny config changes).  In fact, hopefully it works better than before since many quirks with the Kinto fork should be resolved. (such as nested combos not working, etc)

Reference:

- [Kinto GitHub issue](https://github.com/rbreaves/kinto/issues/718) regarding the transition.
- Instructions on altering your `kinto.py` config slightly. See [USING_WITH_KINTO.md](https://github.com/joshgoebel/keyszer/blob/main/USING_WITH_KINTO.md).


**How can I help or contribute?**

Please open an issue to discuss how you'd like to get involved or respond on one of the existing issues. Also feel free to open new issues for feature requests.  Many issues are tagged [good first issue](https://github.com/joshgoebel/keyszer/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) or [help welcome](https://github.com/joshgoebel/keyszer/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+welcome%22).



## License

`keyszer` is distributed under GPL3.  See [LICENSE](https://github.com/joshgoebel/keyszer/blob/main/LICENSE).

    
