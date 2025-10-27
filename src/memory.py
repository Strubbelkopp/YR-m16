class Memory:
    def __init__(self, size):
        self.size = size
        self.data = bytearray(size)

    def read_byte(self, addr):
        self.validate_address(addr)
        return self.data[addr]

    def write_byte(self, addr, value):
        self.validate_address(addr)
        self.data[addr] = value & 0xFF

    def read_word(self, addr):
        self.validate_address(addr)
        self.validate_address(addr + 1)
        hi = self.data[addr]
        lo = self.data[addr + 1]
        return (hi << 8) | lo

    def write_word(self, addr, value):
        self.validate_address(addr)
        self.validate_address(addr + 1)
        self.data[addr] = (value >> 8) & 0xFF
        self.data[addr + 1] = value & 0xFF

    def validate_address(self, addr):
        if addr < 0 or addr >= self.size:
            raise IndexError(f"Memory address out of range: 0x{addr:04x}")

    def load_program(self, program, base_addr=0x0000):
        for i, instr in enumerate(program):
            addr = base_addr + 2*i
            self.write_word(addr, instr)

    def dump(self, start=0, end=None):
        if end is None:
            end = self.size - 1
        return self.data[start:end+1]