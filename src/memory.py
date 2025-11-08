class Memory:
    def __init__(self, size):
        self.size = size
        self.data = bytearray(size)

    def read_byte(self, addr):
        return self.data[addr & 0xFFFF] & 0xFF

    def write_byte(self, addr, value):
        self.data[addr & 0xFFFF] = value & 0xFF

    def read_word(self, addr):
        hi = self.read_byte(addr)
        lo = self.read_byte(addr + 1)
        return (hi << 8) | lo

    def write_word(self, addr, value):
        self.write_byte(addr, value >> 8)
        self.write_byte(addr + 1, value)

    def load_program(self, program, base_addr=0x0000):
        for i, byte in enumerate(program):
            addr = base_addr + i
            self.write_byte(addr, byte)

    def dump(self, start=0, end=None):
        if end is None:
            end = self.size - 1
        mem_region = self.data[start:end+1]
        for addr in range(start, end + 1, 16):
            chunk = mem_region[addr - start:addr - start + 16]
            hex_bytes = ' '.join(f'{b:02X}' for b in chunk)
            print(f'{addr:04X}: {hex_bytes}')