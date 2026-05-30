import sys

from .windows.console_window import ConsoleWindow
from .windows.status_window import StatusWindow
from .windows.memory_window import MemoryWindow
from .windows.action_window import ActionWindow

CONSOLE_H = 24 + 1
CONSOLE_W = 80 + 4
CONSOLE_Y = 0
CONSOLE_X = 0
MEMORY_W = 53 + 4
STATUS_H = 12 + 2
STATUS_W = CONSOLE_W - MEMORY_W
STATUS_Y = CONSOLE_Y + CONSOLE_H
STATUS_X = 0
MEMORY_H = STATUS_H - 3
MEMORY_Y = STATUS_Y
MEMORY_X = STATUS_X + STATUS_W
ACTION_H = 3
ACTION_W = MEMORY_W
ACTION_Y = MEMORY_Y + MEMORY_H
ACTION_X = MEMORY_X

class UI():
    def __init__(self, program_name, cpu, refresh_rate=60):
        self.term = cpu.term
        self.refresh_rate = refresh_rate
        self.console_win = ConsoleWindow(self.term, CONSOLE_H, CONSOLE_W, CONSOLE_Y, CONSOLE_X, program_name, cpu)
        self.status_win = StatusWindow(self.term, STATUS_H, STATUS_W, STATUS_Y, STATUS_X, cpu)
        self.memory_win = MemoryWindow(self.term, MEMORY_H, MEMORY_W, MEMORY_Y, MEMORY_X, cpu)
        self.action_win = ActionWindow(self.term, ACTION_H, ACTION_W, ACTION_Y, ACTION_X)
        self.windows = [self.console_win, self.status_win, self.memory_win, self.action_win]

        for window in self.windows:
            window.draw_border()
            window.flush()

    def refresh(self):
        for window in self.windows:
            window.draw_contents()
            window.flush()