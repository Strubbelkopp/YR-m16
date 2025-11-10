from devices.device import Device

class MemoryDevice(Device):
    def __init__(self, name, min_address, max_address, read_only=False):
        super().__init__(name, min_address, max_address)
        self.size = self.max_address - self.min_address + 1
        self.data = bytearray(self.size)
        self.read_only = read_only

    def read_byte(self, addr):
        return self.data[addr]

    def write_byte(self, addr, value):
        if not self.read_only:
            self.data[addr] = value

    def load_program(self, program, base_addr=0x0000):
        for i, byte in enumerate(program):
            addr = base_addr + i
            self.write_byte(addr, byte)

    def write_bytes(self, addr, data: bytes):
        if not self.read_only:
            self.data[addr : addr + len(data)] = data

    def dump(self, start=0, end=None):
        if end is None:
            end = len(self.data)
        for addr in range(start, end, 16):
            chunk = self.data[addr:addr+16]
            hex_bytes = ' '.join(f'{b:02X}' for b in chunk)
            ascii_repr = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            print(f"{addr+self.min_address:04X}: {hex_bytes:<48} {ascii_repr}")