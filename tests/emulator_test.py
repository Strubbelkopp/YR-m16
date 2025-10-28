from src.cpu import CPU

import pytest

@pytest.fixture
def cpu():
    return CPU()

def test_halt(cpu):
    program = [
        0b0111_000000000000,  # HALT
        0b0110_001_000010001,  # MOV r1, 17
    ]
    cpu.mem.load_program(program)

    cpu.run(max_cycles=10)
    assert cpu.cycles == 1
    assert cpu.reg[1] == 0

def test_mov_immediate_byte(cpu):
    cpu.flags["Z"] = 1
    cpu.flags["N"] = 1
    program = [
        0b0110_001_00010001_1,  # MOV r1, 17
    ]
    cpu.mem.load_program(program)

    cpu.run(1)
    assert cpu.reg[1] == 17
    assert cpu.flags["Z"] == 0
    assert cpu.flags["N"] == 0

def test_mov_immediate_word(cpu):
    cpu.flags["Z"] = 1
    cpu.flags["N"] = 0
    program = [
        0b0110_000_11111110_1,  # MOV r0, 0xFE
        0b0001_000_01000_0111,  # SHL r0, 8
        0b0110_001_01110011_1,  # MOV r1, 0x73
        0b0000_000_001_00_0000, # ADD r0, r1
    ]
    cpu.mem.load_program(program)

    cpu.run(4)
    assert cpu.reg[0] == 0xFE73
    assert cpu.flags["Z"] == 0
    assert cpu.flags["N"] == 1

def test_add_immediate(cpu):
    cpu.reg[0] = 5
    cpu.flags["Z"] = 1
    cpu.flags["N"] = 1
    program = [
        0b0001_000_01010_0000,   # ADD r0, 10
    ]
    cpu.mem.load_program(program)

    cpu.run(1)
    assert cpu.reg[0] == 15
    assert cpu.flags["Z"] == 0
    assert cpu.flags["N"] == 0

@pytest.mark.parametrize("instruction, r0, r1, expected_value, zero_flag, negative_flag", [
    (0b0000_000_001_00_0000, 5, 10, 15,               False, False), # ADD r0, r1
    (0b0000_000_001_00_0010, 5, 8,  (5 - 8) & 0xFFFF, False, True),  # SUB r0, r1
], ids=["add", "sub"])
def test_arithmetic_ops(cpu, instruction, r0, r1, expected_value, zero_flag, negative_flag):
    cpu.reg[0] = r0
    cpu.reg[1] = r1
    cpu.flags["Z"] = int(not zero_flag)
    cpu.flags["N"] = int(not negative_flag)
    cpu.mem.load_program([instruction])

    cpu.run(1)
    assert cpu.reg[0] == expected_value
    assert cpu.flags["Z"] == int(zero_flag)
    assert cpu.flags["N"] == int(negative_flag)

@pytest.mark.parametrize("instruction, r0, r1, expected_value, zero_flag, negative_flag", [
    (0b0000_000_001_00_0100, 0b10101010, 0b11001100, 0b10001000, False, False), # AND r0, r1
    (0b0000_000_001_00_0101, 0b10101010, 0b11001100, 0b11101110, False, False), # OR r0, r1
    (0b0000_000_001_00_0110, 0b10101010, 0b11001100, 0b01100110, False, False), # XOR r0, r1
], ids=["and", "or", "xor"])
def test_logic_ops(cpu, instruction, r0, r1, expected_value, zero_flag, negative_flag):
    cpu.reg[0] = r0
    cpu.reg[1] = r1
    cpu.flags["Z"] = int(not zero_flag)
    cpu.flags["N"] = int(not negative_flag)
    cpu.mem.load_program([instruction])

    cpu.run(1)
    assert cpu.reg[0] == expected_value
    assert cpu.flags["Z"] == int(zero_flag)
    assert cpu.flags["N"] == int(negative_flag)

@pytest.mark.parametrize("instruction, r0, expected_value, carry_flag", [
    (0b0001_000_00001_0111, 0x00FF, 0x01FE, False), # SHL r0, 1
    (0b0001_000_01000_0111, 0x01FE, 0xFE00, True),  # SHL r0, 8
    (0b0001_000_00001_1001, 0x0100, 0x0080, False), # SHR r0, 1
    (0b0001_000_01000_1001, 0x0080, 0x0000, True),  # SHR r0, 8
    (0b0001_000_00101_1010, 0x8000, 0xFC00, False), # ASR r0, 5
    (0b0001_000_00011_1010, 0xAD76, 0xF5AE, True),  # ASR r0, 3
    (0b0001_000_00001_1000, 0x5555, 0xAAAA, False), # ROL r0, 1
    (0b0001_000_00001_1000, 0xAAAA, 0x5555, True),  # ROL r0, 1
    (0b0001_000_00110_1011, 0xA29A, 0x6A8A, False), # ROR r0, 6
    (0b0001_000_01101_1011, 0x908E, 0x8474, True),  # ROR r0, 13
], ids=["shl", "shl_carry", "shr", "shr_carry", "asr", "asr_carry", "rol", "rol_carry", "ror", "ror_carry"])
def test_shift_ops(cpu, instruction, r0, expected_value, carry_flag):
    cpu.reg[0] = r0
    cpu.flags["C"] = int(not carry_flag)
    cpu.mem.load_program([instruction])

    cpu.run(1)
    assert cpu.reg[0] == expected_value
    assert cpu.flags["C"] == int(carry_flag)

def test_relative_jump_forward(cpu):
    cpu.flags["Z"] = 1
    program = [
        0b0010_001_000000010, # JZ +2
        0b0110_000_000000101, # MOV r0, 5 (should be skipped)
        0b0111_000000000000,  # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run(1)
    assert cpu.pc == 4
    cpu.run(1)
    assert cpu.reg[0] == 0

def test_relative_jump_backward(cpu):
    cpu.flags["N"] = 1
    cpu.pc = 2
    program = [
        0b0111_000000000000,  # HALT
        0b0010_011_111111111, # JLT -1
        0b0110_000_000000101, # MOV r0, 5 (should be skipped)
    ]
    cpu.mem.load_program(program)

    cpu.run(1)
    assert cpu.pc == 0
    cpu.run(1)
    assert cpu.reg[0] == 0

def test_cmp_flags(cpu):
    cpu.reg[0] = 2
    cpu.reg[1] = 3
    cpu.reg[2] = 3
    cpu.flags["Z"] = 1
    cpu.flags["N"] = 0
    program = [
        0b0000_000_001_00_1100, # CMP r0, r1
        0b0000_001_010_00_1100, # CMP r1, r2
    ]
    cpu.mem.load_program(program)

    cpu.run(1)
    assert cpu.flags["Z"] == 0
    assert cpu.flags["N"] == 1
    cpu.run(1)
    assert cpu.flags["Z"] == 1
    assert cpu.flags["N"] == 0

def test_load_immediate_byte(cpu):
    cpu.flags["Z"] = 1
    cpu.flags["N"] = 1
    cpu.mem.data[0x72] = 69
    program = [
        0b1000_011_001110010, # LOADB r3, 0x72
    ]
    cpu.mem.load_program(program)

    cpu.run(1)
    assert cpu.reg[3] == 69
    assert cpu.reg[3] < 0xFF # Should fit into a byte
    assert cpu.flags["Z"] == 0
    assert cpu.flags["N"] == 0

def test_store_immediate_byte(cpu):
    cpu.reg[3] = 0x4A69
    program = [
        0b1001_011_001110010, # STOREB r3, 0x72
    ]
    cpu.mem.load_program(program)

    cpu.run(1)
    assert cpu.mem.data[0x72] == 0x69 # Only lower byte should be stored
    assert cpu.mem.data[0x72] < 0xFF # Should fit into a byte

def test_load_immediate_word(cpu):
    cpu.flags["Z"] = 1
    cpu.flags["N"] = 0
    cpu.mem.data[0x52] = 0xFE
    cpu.mem.data[0x53] = 0x73
    program = [
        0b1010_011_001010010, # LOAD r3, 0x52
    ]
    cpu.mem.load_program(program)

    cpu.run(1)
    assert cpu.reg[3] == 0xFE73
    assert cpu.flags["Z"] == 0
    assert cpu.flags["N"] == 1

def test_store_immediate_word(cpu):
    cpu.reg[3] = 0xFE73
    program = [
        0b1011_011_001010010, # STORE r3, 0x72
    ]
    cpu.mem.load_program(program)

    cpu.run(1)
    assert cpu.mem.data[0x52] == 0xFE
    assert cpu.mem.data[0x53] == 0x73

@pytest.mark.parametrize("instruction, addr, offset, value, zero_flag, negative_flag", [
    (0b1100_011_010_00000_0, 0xA070,  0, 0,   True,  False), # LOADB r3, [r2]
    (0b1100_011_010_00010_0, 0xA070,  2, 25,  False, False), # LOADB r3, [r2 + 2]
    (0b1100_011_010_11011_0, 0xA070, -5, 123, False, False), # LOADB r3, [r2 - 5]
    (0b1100_011_010_00001_0, 0xFFFF,  1, 42,  False, False), # LOADB r3, [0xFFFF + 1] (wraps to 0x0000)
    (0b1100_011_010_11111_0, 0x0000, -1, 99,  False, False), # LOADB r3, [0x0000 - 1] (wraps to 0xFFFF)
], ids=["no_offset", "positive_offset", "negative_offset", "crosses_lower_boundary", "crosses_upper_boundary"])
def test_load_indirect_byte(cpu, instruction, addr, offset, value, zero_flag, negative_flag):
    cpu.reg[2] = addr # Holds base address
    cpu.reg[3] = 0xABCD # Initial value should be overwritten
    cpu.flags["Z"] = int(not zero_flag)
    cpu.flags["N"] = int(not negative_flag)
    cpu.mem.data[(addr + offset) & 0xFFFF] = value
    cpu.mem.load_program([instruction], base_addr=0x0100) # Load program at address 0x0100, so it doesn't interfere with the "crosses_lower_boundary" test
    cpu.pc = 0x0100

    cpu.run(1)
    assert cpu.reg[3] == value & 0xFF
    assert cpu.reg[3] <= 0xFF # Should fit into a byte
    assert cpu.flags["Z"] == int(zero_flag)
    assert cpu.flags["N"] == int(negative_flag)

@pytest.mark.parametrize("instruction, addr, offset, value", [
    (0b1101_011_001_00000_0, 0x4321,  0, 0x1200), # STOREB r3, [r1]
    (0b1101_011_001_00010_0, 0x4321,  2, 0x3419), # STOREB r3, [r1 + 2]
    (0b1101_011_001_11111_0, 0x4321, -1, 0x567B), # STOREB r3, [r1 - 1]
    (0b1101_011_001_00001_0, 0xFFFF,  1, 0x782A), # STOREB r3, [0xFFFF + 1] (wraps to 0x0000)
    (0b1101_011_001_11111_0, 0x0000, -1, 0x9A63), # STOREB r3, [0x0000 - 1] (wraps to 0xFFFF)
], ids=["no_offset", "positive_offset", "negative_offset", "crosses_lower_boundary", "crosses_upper_boundary"])
def test_store_indirect_byte(cpu, instruction, addr, offset, value):
    cpu.reg[1] = addr # Holds base address
    cpu.reg[3] = value
    cpu.mem.load_program([instruction], base_addr=0x0100) # Load program at address 0x0100, so it doesn't interfere with the "crosses_lower_boundary" test
    cpu.pc = 0x0100

    cpu.run(1)
    assert cpu.mem.data[(addr + offset) & 0xFFFF] == value & 0xFF # Only lower byte should be stored
    assert cpu.mem.data[(addr + offset) & 0xFFFF] <= 0xFF # Should fit into a byte

@pytest.mark.parametrize("instruction, addr, offset, value, zero_flag, negative_flag", [
    (0b1110_011_010_00000_0, 0xA070,  0, 0x0000, True,  False), # LOAD r3, [r2]
    (0b1110_011_010_00010_0, 0xA070,  2, 0x1234, False, False), # LOAD r3, [r2 + 2]
    (0b1110_011_010_11011_0, 0xA070, -5, 0xABCD, False, True),  # LOAD r3, [r2 - 5]
    (0b1110_011_010_00001_0, 0xFFFF,  1, 0x42,   False, False), # LOAD r3, [0xFFFF + 1] (wraps to 0x0000)
    (0b1110_011_010_11111_0, 0x0000, -1, 0x99,   False, False), # LOAD r3, [0x0000 - 1] (wraps to 0xFFFF)
], ids=["no_offset", "positive_offset", "negative_offset", "crosses_lower_boundary", "crosses_upper_boundary"])
def test_load_indirect_word(cpu, instruction, addr, offset, value, zero_flag, negative_flag):
    cpu.reg[2] = addr # Holds base address
    cpu.reg[3] = 0xABCD # Initial value should be overwritten
    cpu.flags["Z"] = int(not zero_flag)
    cpu.flags["N"] = int(not negative_flag)
    cpu.mem.data[(addr + offset) & 0xFFFF] = (value >> 8) & 0xFF
    cpu.mem.data[(addr + offset + 1) & 0xFFFF] = value & 0xFF
    cpu.mem.load_program([instruction], base_addr=0x0100) # Load program at address 0x0100, so it doesn't interfere with the "crosses_lower_boundary" test
    cpu.pc = 0x0100

    cpu.run(1)
    assert cpu.reg[3] == value
    assert cpu.flags["Z"] == int(zero_flag)
    assert cpu.flags["N"] == int(negative_flag)

@pytest.mark.parametrize("instruction, addr, offset, value", [
    (0b1111_011_001_00000_0, 0x4321,  0, 0x0000), # STORE r3, [r1]
    (0b1111_011_001_00010_0, 0x4321,  2, 0x1234), # STORE r3, [r1 + 2]
    (0b1111_011_001_11111_0, 0x4321, -1, 0x7B9A), # STORE r3, [r1 - 1]
    (0b1111_011_001_00001_0, 0xFFFF,  1, 0x2A3B), # STORE r3, [0xFFFF + 1] (wraps to 0x0000)
    (0b1111_011_001_11111_0, 0x0000, -1, 0x6364), # STORE r3, [0x0000 - 1] (wraps to 0xFFFF)
], ids=["no_offset", "positive_offset", "negative_offset", "crosses_lower_boundary", "crosses_upper_boundary"])
def test_store_indirect_word(cpu, instruction, addr, offset, value):
    cpu.reg[1] = addr # Holds base address
    cpu.reg[3] = value
    cpu.mem.load_program([instruction], base_addr=0x0100) # Load program at address 0x0100, so it doesn't interfere with the "crosses_lower_boundary" test
    cpu.pc = 0x0100

    cpu.run(1)
    assert cpu.mem.data[(addr + offset) & 0xFFFF] == (value >> 8) & 0xFF
    assert cpu.mem.data[(addr + offset + 1) & 0xFFFF] == value & 0xFF

def test_pop_byte(cpu):
    cpu.sp = 0xFFFE
    cpu.flags["Z"] = 1
    cpu.flags["N"] = 1
    cpu.mem.data[0xFFFF] = 69
    program = [
        0b1100_011_00000000_1, # POPB r3
    ]
    cpu.mem.load_program(program)

    cpu.run(1)
    assert cpu.reg[3] == 69
    assert cpu.reg[3] < 0xFF # Should fit into a byte
    assert cpu.sp == 0xFFFE + 1 # Was the SP incremented?
    assert cpu.flags["Z"] == 0
    assert cpu.flags["N"] == 0

def test_push_byte(cpu):
    cpu.sp = 0xFFFF
    cpu.reg[3] = 0x4A69
    program = [
        0b1101_011_00000000_1, # PUSHB r3
    ]
    cpu.mem.load_program(program)

    cpu.run(1)
    assert cpu.mem.data[0xFFFF] == 0x69
    assert cpu.mem.data[0xFFFF] < 0xFF # Should fit into a byte
    assert cpu.sp == 0xFFFF - 1 # Was the SP decremented?

def test_push_pop_byte(cpu):
    cpu.reg[3] = 0xABCD
    cpu.flags["Z"] = 1
    cpu.flags["N"] = 1
    cpu.mem.data[0xFFFE] = 0
    program = [
        0b1101_011_00000000_1,  # PUSH r3
        0b1100_010_00000000_1,  # POP r2
    ]
    cpu.mem.load_program(program)

    cpu.run(2)
    assert cpu.mem.data[0xFFFE] == 0 # Upper bit should not get stored
    assert cpu.reg[2] == 0xCD # Only lower byte should get loaded
    assert cpu.sp == 0xFFFF # Stack pointer returns to original position
    assert cpu.flags["Z"] == 0
    assert cpu.flags["N"] == 0

def test_pop_word(cpu):
    cpu.sp = 0xFFFD
    cpu.flags["Z"] = 1
    cpu.flags["N"] = 1
    cpu.mem.data[0xFFFE] = 0x4A
    cpu.mem.data[0xFFFF] = 0x69
    program = [
        0b1110_011_00000000_1, # POP r3
    ]
    cpu.mem.load_program(program)

    cpu.run(1)
    assert cpu.reg[3] == 0x4A69
    assert cpu.sp == 0xFFFD + 2 # Was the SP incremented?
    assert cpu.flags["Z"] == 0
    assert cpu.flags["N"] == 0

def test_push_word(cpu):
    cpu.sp = 0xFFFF
    cpu.reg[3] = 0x4A69
    program = [
        0b1111_011_00000000_1, # PUSH r3
    ]
    cpu.mem.load_program(program)

    cpu.run(1)
    assert cpu.mem.data[0xFFFE] == 0x4A
    assert cpu.mem.data[0xFFFF] == 0x69
    assert cpu.sp == 0xFFFF - 2 # Was the SP decremented?

def test_push_pop_word(cpu):
    cpu.reg[3] = 0xABCD
    cpu.flags["Z"] = 1
    cpu.flags["N"] = 0
    program = [
        0b1111_011_00000000_1,  # PUSH r3
        0b1110_010_00000000_1,  # POP r2
    ]
    cpu.mem.load_program(program)

    cpu.run(2)
    assert cpu.reg[2] == 0xABCD
    assert cpu.sp == 0xFFFF # Stack pointer returns to original position
    assert cpu.flags["Z"] == 0
    assert cpu.flags["N"] == 1