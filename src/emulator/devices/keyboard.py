from queue import Queue
from devices.device import Device
from unicurses import getch

# Internal registers
KEYBRD_DATA = 0
KEYBRD_STATUS = 1
# Status flags
DATA_READY = 0b00000001

class KeyboardDevice(Device):
    def __init__(self, name, min_address, max_address):
        super().__init__(name, min_address, max_address, io_type="ro")
        self.input_buffer = Queue()
        self.status = 0 # Status register

    def read_byte(self, addr):
        index = addr - self.min_address
        if index == KEYBRD_DATA:
            data = self.input_buffer.get_nowait()
            if self.input_buffer.empty() and (self.status & DATA_READY):
                self.status ^= DATA_READY # Clear data ready flag, if set
            return data
        elif index == KEYBRD_STATUS:
            return self.status

    def tick(self):
        ch = getch()
        if ch != -1:
            for byte in get_key_code(self, ch):
                self.input_buffer.put(byte)
            self.status |= DATA_READY # Set data ready flag
        super().tick()

def get_key_code(self, key):
    if 0 <= key <= 255:
        return bytes([key])
    else:
        EXTENDED_KEY_MAP = {
            3:  0x48,  # Up Arrow
            2:  0x50,  # Down Arrow
            4:  0x4B,  # Left Arrow
            5:  0x4D,  # Right Arrow
            7:  0x08,  # Backspace
            74: 0x53,  # Delete
        }
        return bytes([0xE0, EXTENDED_KEY_MAP.get(key & 0xFF, 0x00)])