from src.memory import Memory

class CPU:
    def __init__(self):
        self.reg = [0] * 8 # R0 - R6, SP (16-bit)
        self.sp = 0xFFFF # SP
        self.pc = 0
        self.mem = Memory(pow(2, 16)) # Byte-addressable memory
        self.flags = {
            "Z": 0, # Zero
            "N": 0, # Negative
            "C": 0, # Carry
            "V": 0  # Overflow
        }
        self.cycles = 0

    def run(self, steps=-1, max_cycles=10_000_000, dump_state=False):
        try:
            while steps != 0:
                if self.cycles >= max_cycles:
                    raise RuntimeError("Max cycles exceeded!")
                instr = self.fetch()
                self.decode_execute(instr)
                if dump_state:
                    self.dump_state()
                if steps > 0:
                    steps -= 1
        except StopIteration: # Exit on HALT instruction
            return
        except Exception:
            raise

    def fetch(self):
        instr = self.mem.read_word(self.pc)
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
            source_mode = get_bits(instr, 0) # Imm/Reg
            rD = get_bits(instr, 9, 11)
            if source_mode == 0: # Reg
                rA = get_bits(instr, 6, 8)
                self.reg[rD] = self.reg[rA]
            elif source_mode == 1: # Imm
                imm = get_bits(instr, 1, 8)
                self.reg[rD] = imm
            self.flags["Z"] = int((self.reg[rD] & 0xFFFF) == 0)
            self.flags["N"] = int((self.reg[rD] & 0x8000) != 0)
        elif opcode == 0b0111:
            raise StopIteration("CPU halted!")
        elif opcode == 0b1000 or opcode == 0b1010: # Load (imm)
            data_size = get_bits(instr, 13) # Byte/Word
            rD = get_bits(instr, 9, 11)
            imm = get_bits(instr, 0, 8)
            if data_size == 0:
                self.reg[rD] = self.mem.read_byte(imm)
            elif data_size == 1:
                self.reg[rD] = self.mem.read_word(imm)
        elif opcode == 0b1001 or opcode == 0b1011: # Store (imm)
            data_size = get_bits(instr, 13) # Byte/Word
            rA = get_bits(instr, 9, 11)
            imm = get_bits(instr, 0, 8)
            if data_size == 0:
                self.mem.write_byte(imm, self.reg[rA])
            elif data_size == 1:
                self.mem.write_word(imm, self.reg[rA])
        elif opcode == 0b1100 or opcode == 0b1110: # Load (reg) / Pop
            data_size = get_bits(instr, 13) # Byte/Word
            is_stack_op = get_bits(instr, 0)
            rD = get_bits(instr, 9, 11)
            if is_stack_op:
                if data_size == 0:
                    self.reg[rD] = self.pop_byte()
                elif data_size == 1:
                    self.reg[rD] = self.pop_word()
            else:
                rAddr = get_bits(instr, 6, 8)
                offset = to_signed(get_bits(instr, 1, 5), 5)
                addr = self.reg[rAddr] + offset
                if data_size == 0:
                    self.reg[rD] = self.mem.read_byte(addr)
                elif data_size == 1:
                    self.reg[rD] = self.mem.read_word(addr)
        elif opcode == 0b1101 or opcode == 0b1111: # Store (reg) / Push
            data_size = get_bits(instr, 13) # Byte/Word
            is_stack_op = get_bits(instr, 0)
            rA = get_bits(instr, 9, 11)
            if is_stack_op:
                if data_size == 0:
                    self.push_byte(self.reg[rA] & 0xFF)
                elif data_size == 1:
                    self.push_word(self.reg[rA])
            else:
                rAddr = get_bits(instr, 6, 8)
                offset = to_signed(get_bits(instr, 1, 5), 5)
                addr = self.reg[rAddr] + offset
                if data_size == 0:
                    self.mem.write_byte(addr, self.reg[rA])
                elif data_size == 1:
                    self.mem.write_word(addr, self.reg[rA])

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
            self.mem.validate_address(addr)
            self.pc = addr

    def pop_byte(self):
        """Pops an 8-Bit byte from the stack"""
        self.sp += 1
        value = self.mem.read_byte(self.sp)
        return value

    def pop_word(self):
        """Pops a 16-Bit word from the stack"""
        self.sp += 2
        value = self.mem.read_word(self.sp-1)
        return value

    def push_byte(self, byte):
        """Pushes an 8-Bit byte to the stack"""
        self.mem.write_byte(self.sp, byte)
        self.sp -= 1

    def push_word(self, word):
        """Pushes a 16-Bit word to the stack"""
        self.mem.write_word(self.sp-1, word)
        self.sp -= 2

    def dump_state(self):
        print("Cycle:", self.cycles)
        print("Registers:", [r for r in self.reg])
        print("Flags:", self.flags)
        print("Next PC:", self.pc) # PC after running the instruction (points to the instruction that gets executed next)
        print("---------------------------------------")

    @property
    def sp(self):
        """Return the stack pointer (R7)."""
        return self.reg[7]

    @sp.setter
    def sp(self, value):
        """Set the stack pointer (R7)."""
        self.reg[7] = value

def get_bits(value, start, end=None):
    """Extract bits from start..end (inclusive, 0 = LSB)."""
    if end == None:
        end = start
    range = end - start + 1
    mask = (1 << range) - 1
    return (value >> start) & mask

def to_signed(value, bits):
    """Interpret value (unsigned) as signed with `bits` bits."""
    sign = 1 << (bits - 1)
    return (value ^ sign) - sign