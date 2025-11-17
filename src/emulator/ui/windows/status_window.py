from unicurses import mvwaddstr
from ui.windows.window import Window

class StatusWindow(Window):
    def __init__(self, height, width, y, x, cpu):
        super().__init__(height, width, y, x, title="Status")
        self.border = [
            '├','─','─',
            '│',    ' ',
            '└','─','─',
        ]
        self.cpu = cpu

    def draw_contents(self):
        mvwaddstr(self.win, 1, 2, "Registers:")
        mvwaddstr(self.win, 2, 2, f"r0: {self.cpu.reg[0]:04X}, r1: {self.cpu.reg[1]:04X}")
        mvwaddstr(self.win, 3, 2, f"r2: {self.cpu.reg[2]:04X}, r3: {self.cpu.reg[3]:04X}")
        mvwaddstr(self.win, 4, 2, f"r4: {self.cpu.reg[4]:04X}, r5: {self.cpu.reg[5]:04X}")
        mvwaddstr(self.win, 5, 2, f"r6: {self.cpu.reg[6]:04X}")
        mvwaddstr(self.win, 6, 2, f"SP: {self.cpu.reg[7]:04X}, PC: {self.cpu.reg[8]:04X}")

        mvwaddstr(self.win, 8, 2, "Flags:")
        mvwaddstr(self.win, 9, 2, ", ".join(f"{flag}: {'1' if self.cpu.flags[flag] else '0'}" for flag in self.cpu.flags))

        mvwaddstr(self.win, 11, 2, "Clock Cycle:")
        mvwaddstr(self.win, 12, 2, self.cpu.clock_cycle)