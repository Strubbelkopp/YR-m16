from queue import Queue
import threading
from .device import Device

# Internal registers
KEYBRD_DATA = 0
KEYBRD_STATUS = 1
# Status flags
DATA_READY = 0b00000001

class KeyboardDevice(Device):
    def __init__(self, name, min_address, max_address):
        super().__init__(name, min_address, max_address, io_type="ro")
        self.input_buffer = Queue()
        self.status = 0  # Status register
        self.lock = threading.Lock()

    def read_byte(self, addr):
        index = addr - self.min_address
        if index == KEYBRD_DATA:
            with self.lock:
                data = self.input_buffer.get_nowait()
                if self.input_buffer.empty():
                    self.status &= ~DATA_READY # Clear data ready flag
            return data
        elif index == KEYBRD_STATUS:
            with self.lock:
                return self.status


def get_key_code(key):
    if key.is_sequence:
        EXTENDED_KEY_MAP = {
            'KEY_UP': 0x48,
            'KEY_DOWN': 0x50,
            'KEY_LEFT': 0x4B,
            'KEY_RIGHT': 0x4D,
            'KEY_BACKSPACE': 0x08,
            'KEY_DELETE': 0x53,
        }
        code = EXTENDED_KEY_MAP.get(key.name)
        if code is not None:
            return bytes([0xE0, code])
        return b''
    else:
        return bytes([ord(key.value)])