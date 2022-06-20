from dataclasses import dataclass, field, replace
from .key import Key
from .action import Action
import time as _time


@dataclass
class Keystate:
    # the actual REAL key pressed
    inkey: Key
    action: Action
    prior: "Keystate" = None
    time: float = field(default_factory=_time.time)
    # the key we modmapped to
    key: Key = None
    # the modifier we may modmap to (multi-key) if used
    # as part of a combo or held for a certain time period
    multikey: Key = None
    # whether this key is currently suspended inside the
    # transform engine waiting for other input
    suspended: bool = False
    is_multi: bool = False
    exerted_on_output: bool = False
    # if this keystate was spent by executing a combo
    spent: bool = False

    def copy(self):
        return replace(self)

    def is_pressed(self):
        return self.action == Action.PRESS \
            or self.action == Action.REPEAT

    def resolve_as_momentary(self):
        # self.key = self.key # NOP
        self.is_multi = False
        self.multikey = False

    def resolve_as_modifier(self):
        self.key = self.multikey
        self.is_multi = False
        self.multikey = False
