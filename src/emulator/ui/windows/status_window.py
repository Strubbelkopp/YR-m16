from .window import Window

class StatusWindow(Window):
    def __init__(self, term, height, width, y, x, cpu):
        super().__init__(term, height, width, y, x, title="Status")
        self.border = [
            '├','─','─',
            '│',    ' ',
            '└','─','─',
        ]
        self.cpu = cpu
        self.cycle = 0

    def draw_contents(self):
        self.print_str(1, 2, "Registers:")
        self.print_str(2, 2, f"r0: {self.cpu.reg[0]:04X}, r1: {self.cpu.reg[1]:04X}")
        self.print_str(3, 2, f"r2: {self.cpu.reg[2]:04X}, r3: {self.cpu.reg[3]:04X}")
        self.print_str(4, 2, f"r4: {self.cpu.reg[4]:04X}, r5: {self.cpu.reg[5]:04X}")
        self.print_str(5, 2, f"r6: {self.cpu.reg[6]:04X}")
        self.print_str(6, 2, f"SP: {self.cpu.reg[7]:04X}, PC: {self.cpu.reg[8]:04X}")

        self.print_str(8, 2, "Flags:")
        self.print_str(9, 2, ", ".join(f"{flag}: {'1' if self.cpu.flags[flag] else '0'}" for flag in self.cpu.flags))

        self.print_str(11, 2, "Clock Cycle:")
        self.print_str(12, 2, self.cpu.clock_cycle)