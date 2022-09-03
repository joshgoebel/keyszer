from enum import IntEnum, unique


@unique
class Action(IntEnum):

    RELEASE, PRESS, REPEAT = range(3)

    def is_pressed(self):
        return self == Action.PRESS or self == Action.REPEAT

    def just_pressed(self):
        return self == Action.PRESS

    def is_released(self):
        return self == Action.RELEASE

    @property
    def is_repeat(self):
        return self == Action.REPEAT

    def __str__(self):
        return self.name.lower()


PRESS = Action.PRESS
RELEASE = Action.RELEASE
REPEAT = Action.REPEAT
