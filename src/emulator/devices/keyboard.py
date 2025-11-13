import queue
import threading
import sys
from devices.device import Device
try: # Platform-specific imports
    import msvcrt
except ImportError:
    pass

# Internal registers
KEYBRD_DATA = 0
KEYBRD_STATUS = 1
# Status flags
DATA_READY = 0b00000001

class KeyboardDevice(Device):
    def __init__(self, name, min_address, max_address):
        super().__init__(name, min_address, max_address, io_type="ro")
        self.input_buffer = queue.Queue()
        self.status = 0 # Status register
        self.thread = threading.Thread(name="keyboard_input_thread", target=self.input_thread, daemon=True)
        self.lock = threading.Lock()
        self.thread.start()

    def read_byte(self, addr):
        index = addr - self.min_address
        if index == KEYBRD_DATA:
            data = self.input_buffer.get_nowait()
            with self.lock:
                if self.input_buffer.empty() and (self.status & DATA_READY):
                    self.status ^= DATA_READY # Clear data ready flag, if set
            return data
        elif index == KEYBRD_STATUS:
            with self.lock:
                return self.status

    def input_thread(self):
        if sys.platform == "win32":
            while True:
                self.input_windows()

    def input_windows(self):
        if msvcrt.kbhit():
            char = msvcrt.getch()
            self.input_buffer.put(ord(char))
            with self.lock:
                self.status |= DATA_READY # Set data ready flag
