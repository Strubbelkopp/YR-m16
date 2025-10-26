class CPU:
    def __init__(self, mem_size=pow(2, 16)):
        self.reg = [0] * 8 # R0 - R6, SP (16-bit)
        self.pc = 0
        self.mem = [0] * mem_size # Byte-addressable memory
        self.flags = {
            "Z": 0, # Zero
            "N": 0, # Negative
            "C": 0, # Carry
            "V": 0  # Overflow
        }
        self.cycles = 0

    def run(self, max_cycles=10_000_000, dump_state=False):
        try:
            while True:
                if self.cycles >= max_cycles:
                    raise RuntimeError("Max cycles exceeded!")
                self.step(1, dump_state)
        except StopIteration:
            return
        except Exception:
            raise

    def step(self, steps=1, dump_state=False):
        remaining_steps = steps
        while remaining_steps > 0:
            instr = self.fetch()
            self.decode_execute(instr)
            if dump_state:
                print("Cycle:", self.cycles)
                self.dump_state()
            remaining_steps -= 1

    def fetch(self):
        if self.pc < 0 or self.pc + 1 >= len(self.mem):
            raise IndexError(f"PC out of memory range: 0x{self.pc:04x}")
        hi = self.mem[self.pc]
        lo = self.mem[self.pc + 1]
        instr = (hi << 8) | lo
        self.pc +=2
        self.cycles += 1
        return instr

    def decode_execute(self, instr):
        opcode = get_bits(instr, 12, 15)

        if opcode == 0b0000: # ALU (reg/reg)
            rD = get_bits(instr, 9, 11)
            rA = get_bits(instr, 6, 8)
            rB = get_bits(instr, 3, 5)
            alu_func = get_bits(instr, 0, 2)
            self.alu(alu_func, rD, self.reg[rA], self.reg[rB])
        elif opcode == 0b0001: # ALU (reg/imm)
            rD = get_bits(instr, 9, 11)
            rA = rD
            imm = get_bits(instr, 3, 8)
            alu_func = get_bits(instr, 0, 2)
            self.alu(alu_func, rD, self.reg[rA], imm)
        elif opcode == 0b0010: # Relative jump
            jmp_func = get_bits(instr, 9, 11)
            offset = to_signed(get_bits(instr, 0, 8), bits=9)
            self.jmp_relative(jmp_func, offset)
        elif opcode == 0b0110: # Move
            rD = get_bits(instr, 9, 11)
            imm = to_signed(get_bits(instr, 0, 8), bits=9)
            self.reg[rD] = imm
            self.flags["Z"] = int((imm & 0xFFFF) == 0)
            self.flags["N"] = int((imm & 0x8000) != 0)
        elif opcode == 0b0111:
            raise StopIteration("CPU halted!")
        elif opcode == 0b1000 or opcode == 0b1010: # Load (imm)
            data_size = get_bits(instr, 13) # Byte/Word
            rD = get_bits(instr, 9, 11)
            imm = get_bits(instr, 0, 8)
            if data_size == 0:
                self.reg[rD] = self.mem[imm]
            elif data_size == 1:
                self.reg[rD] = self.load_word(imm)
        elif opcode == 0b1001 or opcode == 0b1011: # Store (imm)
            data_size = get_bits(instr, 13) # Byte/Word
            rA = get_bits(instr, 9, 11)
            imm = get_bits(instr, 0, 8)
            if data_size == 0:
                self.mem[imm] = self.reg[rA]
            elif data_size == 1:
                self.store_word(imm, self.reg[rA])

    def alu(self, alu_func, rD, a, b):
        res = 0
        if alu_func == 0x0: # ADD
            res = a + b
        elif alu_func == 0x1: # SUB
            res = a - b
        elif alu_func == 0x2: # AND
            res = a & b
        elif alu_func == 0x3: # OR
            res = a | b
        elif alu_func == 0x4: # XOR
            res = a ^ b
        elif alu_func == 0x5: # SHL
            res = a << b
            self.flags["C"] = int((res & 0x10000) != 0)  # bit 16 is carry
        elif alu_func == 0x6: # SHR
            res = a >> (b & 0xFF)
        elif alu_func == 0x7: # CMP
            res = a - b

        if alu_func != 0x7: # Write result to destination register, except for CMP
            self.reg[rD] = res & 0xFFFF
        self.flags["Z"] = int((res & 0xFFFF) == 0)
        self.flags["N"] = int((res & 0x8000) != 0)

    def jmp_relative(self, jmp_func, offset):
        cond = False
        if jmp_func == 0x0: # JMP
            cond = True
        elif jmp_func == 0x1: # JZ
            cond = bool(self.flags["Z"])
        elif jmp_func == 0x2: # JNZ
            cond = not bool(self.flags["Z"])
        elif jmp_func == 0x3: # JLT
            cond = bool(self.flags["N"])
        elif jmp_func == 0x4: # JGT
            cond = not bool(self.flags["N"])

        if cond:
            addr = self.pc + ((offset - 1) * 2) # -1, since PC already was incremented
            if addr < 0 or addr + 1 >= len(self.mem):
                raise IndexError(f"Calculated jump address out of memory range: 0x{addr:04x}")
            self.pc = addr

    def load_word(self, addr):
        """Load a 16-Bit word from memory at the specified address"""
        hi = self.mem[addr]
        lo = self.mem[addr + 1]
        return (hi << 8) | lo

    def store_word(self, addr, word):
        """Stores a 16-Bit word in memory at the specified address"""
        self.mem[addr]     = get_bits(word, 8, 15) # MSB
        self.mem[addr + 1] = get_bits(word, 0, 7) # LSB

    def load_program(self, program, base_addr=0x0000):
        """Load assembled program (list of 16-bit words) into memory at addr (default = 0)"""
        for i, instr in enumerate(program):
            addr = base_addr + 2*i
            self.store_word(addr, instr)

    def dump_state(self):
        print("Registers:", [r for r in self.reg])
        print("Flags:", self.flags)
        print("Next PC:", self.pc) # PC after running the instruction (points to the instruction that gets executed next)
        print("---------------------------------------")

def get_bits(value, start, end=None):
    """Extract bits from start..end (inclusive, 0 = LSB)."""
    if end == None:
        end = start
    range = end - start + 1
    mask = (1 << range) - 1
    return (value >> start) & mask

# TODO: understand this
def to_signed(value, bits):
    """Interpret value (unsigned) as signed with `bits` bits."""
    sign = 1 << (bits - 1)
    return (value ^ sign) - sign