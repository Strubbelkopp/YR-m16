from src.memory import Memory

class CPU:
    def __init__(self):
        self.reg = [0] * 9 # R0 - R6, SP, PC (16-bit)
        self.sp = 0xFFFF # Stack grows downwards
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
                instr = self.fetch_word()
                self.decode_execute(instr)
                if dump_state:
                    self.dump_state()
                if steps > 0:
                    steps -= 1
        except StopIteration: # Exit on HALT instruction
            return
        except Exception:
            raise

    def decode_execute(self, instr):
        instr_type = get_bits(instr, 14, 15)
        opcode = get_bits(instr, 10, 13)
        reg = get_bits(instr, 7, 9) # Source register A / destination register (3 bits)
        operand = get_bits(instr, 3, 6) # Source register B / small immediate (4 bits)
        addressing_mode = get_bits(instr, 0, 2)

        if instr_type == 0b00: # General instructions
            if opcode == 0b0000: # NOP
                return
            elif opcode == 0b0001: # HALT
                raise StopIteration("CPU halted!")
            elif opcode == 0b0010: # RET
                return_addr = self.pop_word()
                self.update_program_counter(return_addr)
            elif opcode == 0b0011: # MOV
                b = self.apply_addressing_mode(addressing_mode, operand)
                self.write_register(reg, b)
        elif instr_type == 0b01: # ALU operations
            self.exec_alu(opcode, reg, operand, addressing_mode)
        elif instr_type == 0b10 and (opcode & 0b1000) == 0: # Jump operations
            opcode &= 0b111
            self.exec_jump(opcode, operand, addressing_mode)
        elif instr_type == 0b10 and (opcode & 0b1000) != 0: # Memory/stack operations
            opcode &= 0b111
            self.exec_mem_stack(opcode, reg, operand, addressing_mode)

    def exec_alu(self, opcode, rA, b, addressing_mode):
        a = self.read_register(rA)
        b = self.apply_addressing_mode(addressing_mode, b)

        if opcode == 0x0: # ADD
            res = a + b
            self.flags["C"] = int(res > 0xFFFF)
            self.write_register(rA, res)
        elif opcode == 0x1: # SUB
            res = a - b
            self.flags["C"] = int(a < b)
            self.write_register(rA, res)
        elif opcode == 0x2: # MUL
            res = a * b
            self.flags["C"] = int(res > 0xFFFF)
            self.write_register(rA, res)
        elif opcode == 0x3: # MULH
            res = (a * b) >> 16
            self.write_register(rA, res)
        elif opcode == 0x4: # AND
            res = a & b
            self.write_register(rA, res)
        elif opcode == 0x5: # OR
            res = a | b
            self.write_register(rA, res)
        elif opcode == 0x6: # XOR
            res = a ^ b
            self.write_register(rA, res)
        elif opcode == 0x7: # SHL
            shift = b & 0xF # Limit shifts to 0-15
            res = a << shift
            self.flags["C"] = (a >> (16 - shift)) & 1
            self.write_register(rA, res)
        elif opcode == 0x8: # ROL
            shift = b & 0xF # Limit shifts to 0-15
            res = (a << shift) | (a >> (16 - shift))
            self.flags["C"] = res & 1
            self.write_register(rA, res)
        elif opcode == 0x9: # SHR
            shift = b & 0xF # Limit shifts to 0-15
            res = a >> shift
            self.flags["C"] = (a >> (shift - 1)) & 1
            self.write_register(rA, res)
        elif opcode == 0xA: # ASR
            shift = b & 0xF # Limit shifts to 0-15
            sign = (a >> 15) & 1
            res = (a >> shift) | ((0xFFFF << (16 - shift)) if sign else 0)
            self.flags["C"] = (a >> (shift - 1)) & 1
            self.write_register(rA, res)
        elif opcode == 0xB: # ROR
            shift = b & 0xF # Limit shifts to 0-15
            res = (a >> shift) | (a << (16 - shift))
            self.flags["C"] = (res >> 15) & 1
            self.write_register(rA, res)
        elif opcode == 0xC: # CMP
            res = a - b
            self.update_status_flags(res)
        elif opcode == 0xD: # NOT
            res = ~a
            self.write_register(rA, res)
        elif opcode == 0xE: # NEG
            res = -a
            self.write_register(rA, res)

    def exec_jump(self, opcode, operand, addressing_mode):
        addr = self.apply_addressing_mode(addressing_mode, operand, fetch_addr=True)

        if opcode == 0x0: # JMP
            self.update_program_counter(addr)
        elif opcode == 0x1 and self.flags["Z"]: # JZ/JEQ
            self.update_program_counter(addr)
        elif opcode == 0x2 and not self.flags["Z"]: # JNZ/JNE
            self.update_program_counter(addr)
        elif opcode == 0x3 and self.flags["N"]: # JLT
            self.update_program_counter(addr)
        elif opcode == 0x4 and not self.flags["N"]: # JGT
            self.update_program_counter(addr)
        elif opcode == 0x5 and self.flags["C"]: # JC
            self.update_program_counter(addr)
        elif opcode == 0x6 and not self.flags["C"]: # JNC
            self.update_program_counter(addr)
        elif opcode == 0x7: # CALL
            self.push_word(self.pc)
            self.update_program_counter(addr)

    def exec_mem_stack(self, opcode, rA, operand, addressing_mode):
        addr = self.apply_addressing_mode(addressing_mode, operand, fetch_addr=True)

        if opcode == 0x0: # LOADB
            self.write_register(rA, self.mem.read_byte(addr))
        elif opcode == 0x1: # LOAD
            self.write_register(rA, self.mem.read_word(addr))
        elif opcode == 0x2: # STOREB
            self.mem.write_byte(addr, self.read_register(rA) & 0xFF)
        elif opcode == 0x3: # STORE
            self.mem.write_word(addr, self.read_register(rA))
        elif opcode == 0x4: # POPB
            self.write_register(rA, self.pop_byte())
        elif opcode == 0x5: # POP
            self.write_register(rA, self.pop_word())
        elif opcode == 0x6: # PUSHB
            self.push_byte(self.read_register(rA) & 0xFF)
        elif opcode == 0x7: # PUSH
            self.push_word(self.read_register(rA))
        else:
            raise NotImplementedError(f"Memory/Move operation {opcode:03b} not implemented!")

    def apply_addressing_mode(self, addressing_mode, operand, fetch_addr=False):
        if addressing_mode == 0x0: # Imm4
            return operand
        elif addressing_mode == 0x1: # Imm8
            return self.fetch_byte()
        elif addressing_mode == 0x2: # Imm16
            return self.fetch_word()
        elif addressing_mode == 0x3: # Reg
            return self.read_register(operand)
        elif addressing_mode == 0x4: # Indirect Reg
            addr = self.read_register(operand)
            return self.mem.read_word(addr) if not fetch_addr else addr
        elif addressing_mode == 0x5: # Reg + Imm16(signed)
            offset = self.fetch_word()
            addr = self.read_register(operand) + to_signed(offset, 16)
            return self.mem.read_word(addr) if not fetch_addr else addr
        elif addressing_mode == 0x6: # Indirect Imm16
            addr = self.fetch_word()
            return self.mem.read_word(addr) if not fetch_addr else addr
        else:
            raise NotImplementedError(f"Addressing mode {addressing_mode:03b} not implemented!")

    def read_register(self, rN):
        if (rN > min(len(self.reg) - 1, 0b1111)): # Special registers (PC, Status register) also readable
            raise ValueError(f"Can't read from register: {rN}")
        return self.reg[rN]

    def write_register(self, rN, value):
        if (rN > 0b111):
            raise ValueError(f"Can't write to register: {rN}")
        value &= 0xFFFF
        self.update_status_flags(value)
        self.reg[rN] = value

    def update_status_flags(self, value):
        value &= 0xFFFF
        self.flags["Z"] = int(value == 0)
        self.flags["N"] = int(value >= 0x8000)

    def update_program_counter(self, addr):
        self.pc = addr & 0xFFFF

    def fetch_byte(self):
        value = self.mem.read_byte(self.pc)
        self.update_program_counter(self.pc + 1)
        self.cycles += 1
        return value

    def fetch_word(self):
        value = self.mem.read_word(self.pc)
        self.update_program_counter(self.pc + 2)
        self.cycles += 1
        return value

    def update_stack_addr(self, offset):
        # TODO: How to deal with stack overflow? Should I wrap around, throw an exception or something else?
        return (self.sp + offset) | 0xE000 # For now wrap around, by keeping SP address in stack region (0xE000-0xFFFF)

    def pop_byte(self):
        self.sp = self.update_stack_addr(offset=1)
        return self.mem.read_byte(self.sp)

    def pop_word(self):
        self.sp = self.update_stack_addr(offset=2)
        return self.mem.read_word(self.sp-1)

    def push_byte(self, byte):
        self.mem.write_byte(self.sp, byte)
        self.sp = self.update_stack_addr(offset=-1)

    def push_word(self, word):
        self.mem.write_word(self.sp-1, word)
        self.sp = self.update_stack_addr(offset=-2)

    def dump_state(self, data_format="hex"):
        print("Cycle:", self.cycles)
        print("Registers:", [f"{get_reg_name(rN)}: {format_num(r, data_format)}" for rN, r in enumerate(self.reg)])
        print("Flags:", self.flags)
        print("Next PC:", format_num(self.pc, "hex")) # PC after running the instruction (points to the instruction that gets executed next)
        print("---------------------------------------")

    @property
    def sp(self):
        return self.reg[7]
    @sp.setter
    def sp(self, value):
        self.reg[7] = value

    @property
    def pc(self):
        return self.reg[8]
    @pc.setter
    def pc(self, value):
        self.reg[8] = value

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

def format_num(num, data_format):
    if data_format == "hex":
        return f"0x{num:04X}"
    elif data_format == "bin":
        return f"0b{num:016b}"
    elif data_format == "signed":
        return to_signed(num, 16)
    else:
        return num

def get_reg_name(rN):
    REG_NAMES = {
        0: "R0", 1: "R1", 2: "R2", 3: "R3", 4: "R4",
        5: "R5", 6: "R6", 7: "SP", 8: "PC"
    }
    return REG_NAMES.get(rN)