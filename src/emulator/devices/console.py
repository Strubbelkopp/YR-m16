from devices.device import Device

class ConsoleDevice(Device):
    def __init__(self, name, min_address, max_address):
        super().__init__(name, min_address, max_address, io_type="wo")
        self.base_addr = 0x0000

    def write_byte(self, addr, value):
        index = addr - self.min_address
        if index == 0:
            self.base_addr = (self.base_addr & 0x00FF) | (value << 8)
        elif index == 1:
            self.base_addr = (self.base_addr & 0xFF00) | value