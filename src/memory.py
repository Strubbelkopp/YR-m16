class Memory:
    def __init__(self, size):
        self.size = size
        self.data = bytearray(size)

    def read_byte(self, addr):
        return self.data[addr & 0xFFFF]

    def write_byte(self, addr, value):
        self.data[addr & 0xFFFF] = value & 0xFF

    def read_word(self, addr):
        hi = self.data[addr & 0xFFFF]
        lo = self.data[(addr + 1) & 0xFFFF]
        return (hi << 8) | lo

    def write_word(self, addr, value):
        self.data[addr & 0xFFFF] = (value >> 8) & 0xFF
        self.data[(addr + 1) & 0xFFFF] = value & 0xFF

    def load_program(self, program, base_addr=0x0000):
        for i, instr in enumerate(program):
            addr = base_addr + 2*i
            self.write_word(addr, instr)

    def dump(self, start=0, end=None):
        if end is None:
            end = self.size - 1
        return self.data[start:end+1]