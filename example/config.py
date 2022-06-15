# define timeout for multipurpose_modmap
timeout(1)

# [Global modemap] Change modifier keys as in xmodmap
modmap("default", {
    Key.CAPSLOCK: Key.LEFT_CTRL
})

# [Conditional modmap] Change modifier keys in certain applications
modmap("Emacs",{
    Key.RIGHT_CTRL: Key.ESC,
}, when = wm_class_match(r"Emacs"))

# [Multipurpose modmap] Give a key two meanings. A normal key when pressed and
# released, and a modifier key when held down with another key. See Xcape,
# Carabiner and caps2esc for ideas and concept.
multipurpose_modmap("default",
    # Enter is enter when pressed and released. Control when held down.
    {Key.ENTER: [Key.ENTER, Key.RIGHT_CTRL]}

    # Capslock is escape when pressed and released. Control when held down.
    # {Key.CAPSLOCK: [Key.ESC, Key.LEFT_CTRL]
    # To use this example, you can't remap capslock with modmap.
)

# [Conditional multipurpose modmap] Multipurpose modmap in certain conditions,
# such as for a particular device.
multipurpose_modmap("Microsoft keyboard", {
    # Left shift is open paren when pressed and released.
    # Left shift when held down.
    Key.LEFT_SHIFT: [Key.KPLEFTPAREN, Key.LEFT_SHIFT],

    # Right shift is close paren when pressed and released.
    # Right shift when held down.
    Key.RIGHT_SHIFT: [Key.KPRIGHTPAREN, Key.RIGHT_SHIFT]
}, when = lambda ctx: ctx.device_name.startswith("Microsoft"))


# Keybindings for Firefox/Chrome
keymap("Firefox and Chrome", {
    # Ctrl+Alt+j/k to switch next/previous tab
    K("C-Alt-j"): K("C-TAB"),
    K("C-Alt-k"): K("C-Shift-TAB"),
    # Type C-j to focus to the content
    K("C-j"): K("C-f6"),
    # very naive "Edit in editor" feature (just an example)
    K("C-o"): [K("C-a"), K("C-c"), launch(["gedit"]), sleep(0.5), K("C-v")]
}, when = wm_class_match(r"Firefox|Google-chrome"))

# Keybindings for Zeal https://github.com/zealdocs/zeal/
keymap("Zeal", {
    # Ctrl+s to focus search area
    K("C-s"): K("C-k"),
}, when = wm_class_match(r"Zeal"))

# Emacs-like keybindings in non-Emacs applications

keymap("Emacs-like keys", {
    # Cursor
    K("C-b"): with_mark(K("left")),
    K("C-f"): with_mark(K("right")),
    K("C-p"): with_mark(K("up")),
    K("C-n"): with_mark(K("down")),
    K("C-h"): with_mark(K("backspace")),
    # Forward/Backward word
    K("Alt-b"): with_mark(K("C-left")),
    K("Alt-f"): with_mark(K("C-right")),
    # Beginning/End of line
    K("C-a"): with_mark(K("home")),
    K("C-e"): with_mark(K("end")),
    # Page up/down
    K("Alt-v"): with_mark(K("page_up")),
    K("C-v"): with_mark(K("page_down")),
    # Beginning/End of file
    K("Alt-Shift-comma"): with_mark(K("C-home")),
    K("Alt-Shift-dot"): with_mark(K("C-end")),
    # Newline
    K("C-m"): K("enter"),
    K("C-j"): K("enter"),
    K("C-o"): [K("enter"), K("left")],
    # Copy
    K("C-w"): [K("C-x"), set_mark(False)],
    K("Alt-w"): [K("C-c"), set_mark(False)],
    K("C-y"): [K("C-v"), set_mark(False)],
    # Delete
    K("C-d"): [K("delete"), set_mark(False)],
    K("Alt-d"): [K("C-delete"), set_mark(False)],
    # Kill line
    K("C-k"): [K("Shift-end"), K("C-x"), set_mark(False)],
    # Undo
    K("C-slash"): [K("C-z"), set_mark(False)],
    K("C-Shift-ro"): K("C-z"),
    # Mark
    K("C-space"): set_mark(True),
    K("C-Alt-space"): with_or_set_mark(K("C-right")),
    # Search
    K("C-s"): K("F3"),
    K("C-r"): K("Shift-F3"),
    K("Alt-Shift-key_5"): K("C-h"),
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
        K("C-c"): K("C-q"),
        # cancel
        K("C-g"): ignore_key,
        # C-x u (undo)
        K("u"): [K("C-z"), set_mark(False)],
    }
}, when = lambda ctx: ctx.wm_class not in ("Emacs", "URxvt"))

