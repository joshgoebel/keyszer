from enum import Enum, unique, IntEnum

@unique
class Action(IntEnum):

    RELEASE, PRESS, REPEAT = range(3)

    def is_pressed(self):
        return self == Action.PRESS or self == Action.REPEAT

    def is_released(self):
        return self == Action.RELEASE

    def __str__(self):
        return self.name.lower()

