from devices.device import Device

class ConsoleDevice(Device):
    def __init__(self, name, min_address, max_address, width=80, height=24):
        super().__init__(name, min_address, max_address, io_type="rw")
        self.base_addr = 0x0000
        self.width = width
        self.height = height

    def write_byte(self, addr, value):
        index = addr - self.min_address
        if index == 0:
            self.base_addr = (self.base_addr & 0x00FF) | (value << 8)
        elif index == 1:
            self.base_addr = (self.base_addr & 0xFF00) | value

    def read_byte(self, addr):
        index = addr - self.min_address
        if index == 2:
            return self.width
        elif index == 3:
            return self.height