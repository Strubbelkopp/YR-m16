from devices.device import Device

class Bus():
    def __init__(self, devices):
        self.devices = devices
        for device in devices:
            setattr(self, device.name, device)

    def get_device(self, addr):
        for device in self.devices:
            if device.min_address <= addr <= device.max_address:
                return device
        raise RuntimeError(f"No device mapped to address: {addr:04X}")

    def read_byte(self, addr):
        addr &= 0xFFFF
        device = self.get_device(addr)
        return device.read_byte(addr)

    def write_byte(self, addr, value):
        addr &= 0xFFFF
        device = self.get_device(addr)
        device.write_byte(addr, value & 0xFF)

    def read_word(self, addr):
        hi = self.read_byte(addr)
        lo = self.read_byte(addr + 1)
        return (hi << 8) | lo

    def write_word(self, addr, value):
        self.write_byte(addr, value >> 8)
        self.write_byte(addr + 1, value)