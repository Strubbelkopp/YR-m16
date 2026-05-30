from .window import Window

class MemoryWindow(Window):
    def __init__(self, term, height, width, y, x, cpu):
        super().__init__(term, height, width, y, x, title="Memory View (F2)")
        self.border = [
            '┬','─','┤',
            '│',    '│',
            '│',' ','│',
        ]
        self.memory = cpu.bus.memory

        self.observe_addr = 0xC000

    def draw_contents(self):
        start_addr = min(self.observe_addr, self.memory.max_address+1)
        end_addr = min(self.observe_addr + (self.height - 2) * 16, self.memory.max_address+1)
        self.print_str(1, 2, f"Address: {start_addr:04X} - {end_addr-1:04X}")
        line_num = 0
        for addr in range(start_addr, end_addr, 16):
            chunk = self.memory.data[addr:addr+16]
            hex_bytes = ' '.join(f'{b:02X}' for b in chunk)
            self.print_str(2 + line_num, 2, f"{addr:04X}: {hex_bytes}")
            line_num += 1