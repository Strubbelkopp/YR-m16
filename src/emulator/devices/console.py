from time import time
from devices.device import Device
from unicurses import addstr, refresh, move

class ConsoleDevice(Device):
    def __init__(self, name, min_address, max_address, cpu, width=80, height=24, refresh_rate=30):
        super().__init__(name, min_address, max_address, io_type="wo")
        self.base_addr = 0xC000
        self.memory = cpu.bus.memory
        self.width = width
        self.height = height
        self.refresh_rate = refresh_rate
        self.last_refresh = time()

    def write_byte(self, addr, value):
        index = addr - self.min_address
        if index == 0:
            self.base_addr = (self.base_addr & 0x00FF) | (value << 8)
        elif index == 1:
            self.base_addr = (self.base_addr & 0xFF00) | value

    def refresh_screen(self):
        screen_data = self.memory.data[ # Extract the screen data
            self.base_addr - self.memory.min_address:
            self.base_addr - self.memory.min_address + self.width * self.height
        ]
        # Build all lines into a single string
        lines = []
        for i in range(0, len(screen_data), self.width):
            # Convert bytes to printable chars
            line = ''.join(chr(c) if c >= 32 else ' ' for c in screen_data[i:i+self.width])
            lines.append(line)

        move(0, 0)
        addstr('\n'.join(lines) + '\n')
        refresh()

    def tick(self):
        now = time()
        if now - self.last_refresh >= 1.0 / self.refresh_rate:
            self.refresh_screen()
            self.last_refresh = now
        super().tick()