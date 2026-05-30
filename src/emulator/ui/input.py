import threading

from ..devices.keyboard import get_key_code, DATA_READY

class InputThread(threading.Thread):
    def __init__(self, cpu):
        super().__init__(daemon=True)
        self.cpu = cpu
        self.term = cpu.term
        self.keyboard = cpu.bus.keyboard

    def run(self):
        while not self.cpu.stop:
            key = self.term.inkey(timeout=0.1)
            if key:
                if key.name == "KEY_F3":
                    self.cpu.stop = True
                elif key.name == "KEY_F4":
                    self.cpu.paused = True
                elif key.name == "KEY_F5":
                    self.cpu.paused = False
                elif key.name == "KEY_F6" and self.cpu.paused:
                    self.cpu.step_once = True
                else:
                    with self.keyboard.lock:
                        for byte in get_key_code(key):
                            self.keyboard.input_buffer.put(byte)
                        self.keyboard.status |= DATA_READY