from enum import unique, IntEnum


@unique
class Action(IntEnum):

    RELEASE, PRESS, REPEAT = range(3)

    def is_pressed(self):
        return self == Action.PRESS or self == Action.REPEAT

    def just_pressed(self):
        return self == Action.PRESS

    def is_released(self):
        return self == Action.RELEASE

    def __str__(self):
        return self.name.lower()
