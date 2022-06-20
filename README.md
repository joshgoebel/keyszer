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

Keyszer works at quite a low-level.  It grabs input directly from the kernel's [`evdev`](https://www.freedesktop.org/wiki/Software/libevdev/) input devices ( `/dev/input/event*`) and then creates an emulated [`uinput`](https://www.kernel.org/doc/html/v4.12/input/uinput.html) device to inject those inputs back into the kernel.  During this process the input stream is transformed on the fly as necessary to remap keys.


**Upgrading from xkeysnail**

- Some small configuration changes will be needed.
- A few command line arguments have changed.
- For xkeysnail 0.4.0 see [UPGRADING_FROM_XKEYSNAIL.md](https://github.com/joshgoebel/keyszer/blob/main/UPGRADE_FROM_XKEYSNAIL.md).
- For xkeysnail (Kinto variety) see [USING_WITH_KINTO.md](https://github.com/joshgoebel/keyszer/blob/main/USING_WITH_KINTO.md) and [Using with Kinto v1.2-13](https://github.com/joshgoebel/keyszer/issues/36).


#### Key Highlights

- Low-level library usage (`evdev` and `uinput`) allows remapping to work from the console all the way into X11.
- High-level and incredibly flexible remapping mechanisms:
    - _per-application keybindings_ - bindings that change depending on the active X11 application or window
    - _multiple stroke keybindings_ - `Ctrl+x Ctrl+c` could map to `Ctrl+q`
    - _very flexible output_ - `Ctrl-s` could type out `:save`, and then hit enter
    - _stateful key combos_ - build Emacs style combos with shift/mark
    - _multipurpose bindings_ - a regular key can become a modifier when held
    - _arbitrary functions_ - a key combo can run custom Python function


**New Features (since xkeysnail 0.4.0)**

- simpler and more flexible configuration scripting APIs
- better debugging tools
  - configurable `EMERGENCY EJECT` hotkey
  - configurable `DIAGNOSTIC` hotkey
- fully supports running as semi-privleged user (using `root` is now deprecated)
- adds `Meta`, Command` and `Cmd` aliases for Super/Meta modifier
- supports custom modifiers via `add_modifier` (such as `Hyper`)
- supports `Fn` as a potential modifier (on hardware where it works)
- adds `bind` helper to support persistent holds across multiple combos
  - most frequently used for persistent Mac OS style `Cmd-tab` app switcher panels
- adds `--check` for checking the config file for issues
- adds `wm_name` context for all conditionals (PR #40)
- adds `device_name` context for all conditionals (including keymaps)
- (fix) `xmodmap` cannot be used until some keys are first pressed on the emulated output
- (fix) ability to avoid unintentional Alt/Super false keypresses in many setups
- (fix) fixes multi-combo nested keymaps (vs Kinto's xkeysnail)
- (fix) properly cleans up pressed keys before termination


---

## Installation

Requires **Python 3**.


_Over time we should add individual instructions for various distros here._

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

Just download the source and install.

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

Keyszer requires read/write access to:

- `/dev/input/event*` - to grab input from your `evdev` input devices
- `/dev/uinput` - to provide an emulated keyboard to the kernel


### Running as a semi-privleged user

It's best to create an entirely isolated user to run the keymapper.  Group or ACL based permissions can be used to provide this user access to the necessary devices.  You'll need only a few `udev` rules to ensure that the input devices are all given correct permissions.


#### ACL based permissions (narrow, more secure)

First, lets make a new user:

    sudo useradd keymapper

...then use udev and ACL to grant our new user access:

*/etc/udev/rules.d/90-keymapper-acl.rules*

    KERNEL=="event*", SUBSYSTEM=="input", RUN+="/usr/bin/setfacl -m user:keymapper:rw /dev/input/%k"
    KERNEL=="uinput", SUBSYSTEM=="misc", RUN+="/usr/bin/setfacl -m user:keymapper:rw /dev/uinput"


#### Group based permissions (slightly wider, less secure)

Many distros already have an input group; if not, you can create one.  Next, add a new user that's a member of that group:

    sudo useradd keymapper -G input


...then use udev to grant our new user access (via the `input` group):

*/etc/udev/rules.d/90-keymapper-input.rules*

    SUBSYSTEM=="input", GROUP="input"
    KERNEL=="uinput", SUBSYSTEM=="misc", GROUP="input"


#### systemd

For a sample systemd service file for running Keyszer as a service please see [keyszer.service](https://github.com/joshgoebel/keyszer/blob/main/keyszer.service).


### Running as the Active Logged in User

This may be appropriate in some limited development scenarios, but is not recommended.  Giving the active, logged in user access to `evdev` and `uinput` potentially allows all keystrokes to be logged and could allow a malicious program to take over (or destroy) your machine by injecting input into a Terminal session or other application.

It would be better to open a terminal, `su` to a dedicated `keymapper` user and then run Keyszer inside that context, as shown earlier.


### Running as `root`

_Don't do this, it's dangerous, and not unnecessary._  A semi-priveleged user with access to only the necessary input devices is a far better choice.


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

The full path or complete device name may be used.  Device name is usually better to avoid USB device numbering jumping around after a reboot, etc...

**Other Options:**

- `-c`, `--config` - location of the configuration file 
- `-w`, `--watch` - watch for new keyboard devices to hot-plug 
- `-v` - increase verbosity greatly (to help with debugging)
- `--list-devices` - list out all available input devices


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


Defaults:

```py
timeouts(
    multipurpose = 1,
    suspend = 1,
)
```

### `dump_diagnostics_key(key)`

Configures a key that when hit will dump additional diagnostic information to STDOUT.

```py
dump_diagnostics_key(Key.F15)  # default
```

### `emergency_eject_key(key)`

Configures a key that when hit will immediately terminate keyszer; useful for development, recovering from bugs, or badly broken configurations.

```py
emergency_eject_key(Key.F16)  # default
```



### `add_modifier(name, aliases, key/keys)`

Allows you to add custom modifiers and then map them to actual keys.

```py
add_modifier("HYPER", aliases = ["Hyper"], key = Key.F24)
```

_Note:_ Just adding `HYPER` doesn't necessarily make it work with your software, you may still need to configure X11 setup to accept the key you choose as the "Hyper" key.


### `wm_class_match(re_str)`

Helper to make matching conditionals (and caching the compiled regex) just a tiny bit simpler.

```py
keymap("Firefox",{
    # ... keymap here
}, when = wm_class_match("^Firefox$"))
```


### `not_wm_class_match(re_str)`

The negation of `wm_class_match`, matches only when the regex does NOT match.


### `modmap(name, mappings, when_conditional = None)`

Maps a single physical key to a different key.  A default modmap will always be overruled by any conditional modmaps that apply.  `when_conditional` can be passed to make the modmap conditional.

```py
modmap("default", {
    # mapping caps lock to left control
    Key.CAPSLOCK: Key.LEFT_CTRL
})
```

If you don't create a default (non-conditional) modmap a blank one is created for you.  For `modmap` sides of the pairing will be `Key` literals (not combos).


### `multipurpose_modmap(name, mappings)`

Used to bestow a key with multiple-purposes, both for regular use and for use as a modifier.

```py
multipurpose_modmap("default",
    # Enter is enter if pressed and immediately released...
    # ...but Right Control if held down and paired with other keys.
    {Key.ENTER: [Key.ENTER, Key.RIGHT_CTRL]}
)
```


### `keymap(name, mappings)`

Defines a keymap of input combos mapped to output equivalents.

```py
keymap("Firefox", {
    # when Cmd-S is input instead send Ctrl-S to the ouput
    C("Cmd-s"): C("Ctrl-s"),
}, when = lambda ctx: ctx.wm_class == "Firefox")
```

Because of the `when` conditional this keymap will only apply for Firefox.


The argument `mappings` is a dictionary in the form of `{ combo: command, ...}` where `combo` and `command` take following forms:

- `combo`: Combo to map, specified by `K(combo_str)`
    - For the syntax of combo specifications, see [Combo Specifications](#combo-specifications).
- `command`: one of the following
    - `K(combo_str)`: Type a specific key combo to the output.
    - `[command1, command2, ...]`: Execute multiple commands sequentially.
    - `{ ... }`: Sub-keymap. Used to define [Multiple Stroke Keys](#multiple-stroke-keys).
    - `escape_next_key`: Escape the next key pressed.
    - `ignore_key`: Ignore the key that is pressed next. (often used to disable native combos)
    - `bind`: Bind an input and ouput modifier together such that the output is not lifted until the input is.
    - arbitrary function: The function is executed and the returned value (if any) is used as a command.

The argument `name` specifies the keymap name. Every keymap has a name - using `default` is suggested for a non-conditional keymap.


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

_Note:_ The same conditional `fn` can always be passed directly to `modmap` using the `when` argument.

---

#### Marks

TODO: need docs (See issue #8)


#### Combo Specifications

The Combo specification in a keymap is written in the form of `C("(<Modifier>-)*<Key>")`.

`<Modifier>` is one of the following:

- `C` or `Ctrl` -> Control key
- `Alt` -> Alt key
- `Shift` -> Shift key
- `Super`, `Win`, `Command`, `Cmd`, `Meta` -> Super/Windows/Command key
- `Fn` -> Function key (on supported keyboards)

You can specify left/right modifiers by adding the prefixes `L` or `R`.

`<Key>` is any key whose name is defined in [`key.py`](https://github.com/joshgoebel/keyszer/blob/main/keyszer/models/key.py).

Some combo examples:

- `C("LC-Alt-j")`: left Control, Alt, `j`
- `C("Ctrl-m")`: Left or Right Control, `m`
- `C("Win-o")`: Cmd/Windows,  `o`
- `C("Alt-Shift-comma")`: Alt, Left or Right Shift, comma


#### Multiple Stroke Keys

To use multiple stroke keys, simply define a nested keymap. For example, the
following example remaps `C-x C-c` to `C-q`.

```python
keymap("multi stroke", {
    C("C-x"): {
      C("C-c"): C("C-q"),
    }
})
```

#### Finding out the proper `Key.NAME` literal for a key on your keyboard

From a terminal session run `evtest` and select your keyboard's input device.  Now hit the key in question.

```
Event: time 1655723568.594844, type 1 (EV_KEY), code 69 (KEY_NUMLOCK), value 1
Event: time 1655723568.594844, -------------- SYN_REPORT ------------
```

Above I've just pressed "clear" on my numpad and see `code 69 (KEY_NUMLOCK)` in the ouput. For Keyszer this would translate to `Key.NUMLOCK`.  You can also browse the [full list of key names](https://github.com/joshgoebel/keyszer/blob/main/src/keyszer/models/key.py) in the source.


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


**Does Keyszer support FreeBSD/NetBSD or other BSDs?**

Not at the moment, perhaps never.  If you're an expert on the BSD kernel's input layers please
[join the discussion](https://github.com/joshgoebel/keyszer/issues/46).  I'm at the very least open to the discussion to find out if this is possible, a good idea, etc...


**Does this work with Wayland?**

[Not yet.](https://github.com/joshgoebel/keyszer/issues/27)  This is desires but seems impossible at the moment until there is a standardized system to *quickly and easily* determine the app/window that has input focus on Wayland, just like we do so easily on X11.


**Is keyszer compatible with [Kinto.sh](https://github.com/rbreaves/kinto)?**


*That is certainly the plan.*   The major reason Kinto.sh required it's own fork [has been resolved](https://github.com/joshgoebel/keyszer/issues/11).  Kinto.sh should simply "just work" with `keyszer` (with a few tiny config changes).  In fact, hopefully it works better than before since many quirks with the Kinto fork should be resolved. (such as nested combos not working, etc)

Reference:

- [Kinto GitHub issue](https://github.com/rbreaves/kinto/issues/718) regarding the transition.
- Instructions on altering your `kinto.py` config slightly. See [USING_WITH_KINTO.md](https://github.com/joshgoebel/keyszer/blob/main/USING_WITH_KINTO.md).


**How can I help or contribute?**

Please open an issue to discuss how you'd like to get involved or respond on one of the existing issues. Also feel free to open new issues for feature requests.  Many issues are tagged [good first issue](https://github.com/joshgoebel/keyszer/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) or [help welcome](https://github.com/joshgoebel/keyszer/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+welcome%22).



## License

`keyszer` is distributed under GPL3.  See [LICENSE](https://github.com/joshgoebel/keyszer/blob/main/LICENSE).

    
