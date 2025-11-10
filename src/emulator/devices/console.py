import os
import sys
from devices.device import Device

class ConsoleDevice(Device):
    def __init__(self, name, min_address, max_address, memory, width=80, height=24):
        super().__init__(name, min_address, max_address)
        self.base_addr = 0xC000
        self.memory = memory
        self.width = width
        self.height = height

    def read_byte(self, addr):
        raise RuntimeError(f"Can't read from address: {addr}")

    def write_byte(self, addr, value):
        device_addr = addr - self.min_address
        if device_addr == 0:
            self.base_addr = (self.base_addr & 0x00FF) | (value << 8)
        elif device_addr == 1:
            self.base_addr = (self.base_addr & 0xFF00) | value

    def refresh_screen(self):
        # Clear the console
        sys.stdout.write("\033[H\033[J")  # Move cursor to top-left, clear screen
        sys.stdout.flush()

        screen_data = self.memory.data[
            self.base_addr - self.memory.min_address:
            self.base_addr - self.memory.min_address + self.width * self.height
        ]
        lines = [screen_data[i:i+self.width] for i in range(0, len(screen_data), self.width)]

        for line in lines:
            print(''.join(chr(c) for c in line))

    def tick(self, cycles=1):
        pass
        self.refresh_screen()