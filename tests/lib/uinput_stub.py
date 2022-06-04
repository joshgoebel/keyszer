from evdev.ecodes import EV_KEY, EV_SYN
from evdev.events import InputEvent

class UInputStub:
    def __init__(self):
        self.queue = []

    def syn(self):
        self.write(EV_SYN,0,0)
    
    def write_event(self, event):
        self.write(event.type, event.code, event.value)
    
    def write(self, type, code, value):
        self.queue.append((type, code, value))

    def keys(self):
        return [(x[2], x[1]) for x in self.queue if x[0] == EV_KEY]

    def close(self):
        pass # NOP