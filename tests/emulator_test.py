from src.emulator import CPU

import pytest

def test_halt():
    cpu = CPU()
    program = [
        0b0111_000000000000,  # HALT
        0b0110_001_000010001  # MOV r1, 17
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.cycles == 1
    assert cpu.reg[1] == 0

def test_mov_immediate():
    cpu = CPU()
    program = [
        0b0110_001_000100011,  # MOV r1, 17
        0b0111_000000000000    # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.reg[1] == 17
    assert cpu.flags["Z"] == 0
    assert cpu.flags["N"] == 0

def test_add():
    cpu = CPU()
    program = [
        0b0110_000_000001011,   # MOV r0, 5
        0b0110_001_000010101,   # MOV r1, 10
        0b0000_010_000_001_000, # ADD r2, r0, r1
        0b0111_000000000000     # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.reg[2] == 15

def test_add_immediate():
    cpu = CPU()
    program = [
        0b0110_001_000001011,    # MOV r1, 5
        0b0001_001_001010_000,   # ADD r1, 10 (reg/imm)
        0b0111_000000000000      # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.reg[1] == 15

def test_sub():
    cpu = CPU()
    program = [
        0b0110_000_000001011,   # MOV r0, 5
        0b0110_001_000010001,   # MOV r1, 8
        0b0000_010_000_001_001, # SUB r2, r0, r1
        0b0111_000000000000     # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.reg[2] == (5 - 8) & 0xFFFF
    assert cpu.flags["N"] == 1
    assert cpu.flags["Z"] == 0

def test_and_or_xor():
    cpu = CPU()
    cpu.reg[0] = 0b10101010
    cpu.reg[1] = 0b11001100
    program = [
        0b0000_010_000_001_010,  # AND r2, r0, r1
        0b0000_011_000_001_011,  # OR  r3, r0, r1
        0b0000_100_000_001_100,  # XOR r4, r0, r1
        0b0111_000000000000      # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.reg[2] == 0b10001000
    assert cpu.reg[3] == 0b11101110
    assert cpu.reg[4] == 0b01100110

def test_shl_carry_flag():
    cpu = CPU()
    program = [
        0b0110_000_111111111,  # MOV r0, 0xFF
        0b0001_000_000001_101, # SHL r0, 1
        0b0001_000_001000_101, # SHL r0, 8
        0b0111_000000000000    # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run(2)
    assert cpu.reg[0] == 0x1fe
    assert cpu.flags["C"] == 0
    cpu.run()
    assert cpu.reg[0] == 0xfe00
    assert cpu.flags["C"] == 1

def test_relative_jump_forward():
    cpu = CPU()
    program = [
        0b0110_000_000000000,  # MOV r0, 0
        0b0010_001_000000010,  # JZ +2
        0b0110_000_000000101,  # MOV r0, 5 (should be skipped)
        0b0111_000000000000    # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run(2)
    assert cpu.pc == 6  # JZ skipped one instruction ahead
    cpu.run()
    assert cpu.reg[0] == 0

def test_relative_jump_backward():
    cpu = CPU()
    # This program increments r0 3 times using a backward jump loop
    # Instruction offsets count in instructions (not bytes)
    program = [
        0b0110_000_000000001,   # 0: MOV r0, 0
        0b0110_001_000000011,   # 2: MOV r1, 1
        # loop start
        0b0000_000_000_001_000, # 4: ADD r0, r0, r1
        0b0000_000_000000011,   # 6: CMP r0, 3
        0b0010_010_111111110,   # 8: JNZ -2 instruction (offset -2) if we want to loop 3x
        0b0111_000000000000     # 10: HALT
    ]
    cpu.mem.load_program(program)

    cpu.run(2) # Initialize registers
    cpu.run(1)  # ADD r0 += r1
    assert cpu.reg[0] == 1
    cpu.run(2)  # CMP & JNZ -2
    # PC should go back to ADD instruction
    assert cpu.pc == 4
    cpu.run(1)  # ADD r0 += r1 again
    assert cpu.reg[0] == 2
    cpu.run(2)  # CMP & JNZ -2
    assert cpu.pc == 4
    cpu.run(1)  # ADD r0 += r1 third time
    assert cpu.reg[0] == 3
    cpu.run(2)  # CMP & JNZ -2
    assert cpu.pc == 4
    cpu.run()
    assert cpu.pc == 12

def test_cmp_flags():
    cpu = CPU()
    program = [
        0b0110_000_000000010,  # MOV r0, 2
        0b0110_001_000000011,  # MOV r1, 3
        0b0000_000_000_001_111, # CMP r0, r1
        0b0111_000000000000     # HALT
    ]
    cpu.mem.load_program(program)
    cpu.run()

    # CMP sets flags but does not store result
    assert cpu.flags["Z"] == 0
    assert cpu.flags["N"] == 1  # 2 - 3 = -1 => N flag set

def test_load_immediate_byte():
    cpu = CPU()
    cpu.mem.data[0x72] = 69
    program = [
        0b1000_011_001110010, # LOADB r3, 0x72
        0b0111_000000000000   # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.reg[3] == 69
    assert cpu.reg[3] < 0xFF # Should fit into a byte

def test_store_immediate_byte():
    cpu = CPU()
    cpu.reg[3] = 0x4A69
    program = [
        0b1001_011_001110010, # STOREB r3, 0x72
        0b0111_000000000000   # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.mem.data[0x72] == 0x69 # Only lower byte should be stored
    assert cpu.mem.data[0x72] < 0xFF # Should fit into a byte

def test_load_immediate_word():
    cpu = CPU()
    cpu.mem.data[0x52] = 0xFE
    cpu.mem.data[0x53] = 0x73
    program = [
        0b1010_011_001010010, # LOAD r3, 0x52
        0b0111_000000000000   # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.reg[3] == 0xFE73

def test_store_immediate_word():
    cpu = CPU()
    cpu.reg[3] = 0xFE73
    program = [
        0b1011_011_001010010, # STORE r3, 0x72
        0b0111_000000000000   # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.mem.data[0x52] == 0xFE
    assert cpu.mem.data[0x53] == 0x73

def test_load_indirect_byte(): # Load byte from memory address [register + offset]
    cpu = CPU()
    cpu.reg[2] = 0xA070
    cpu.mem.data[0xA070] = 69
    cpu.mem.data[0xA072] = 25
    program = [
        0b1100_011_010_00000_0, # LOADB r3, [r2]
        0b1100_100_010_00010_0, # LOADB r4, [r2 + 2]
        0b0111_000000000000   # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.reg[3] == 69
    assert cpu.reg[4] == 25
    assert cpu.reg[3] < 0xFF # Should fit into a byte
    assert cpu.reg[4] < 0xFF

def test_store_indirect_byte(): # Store byte to memory address [register + offset]
    cpu = CPU()
    cpu.reg[1] = 0x4321
    cpu.reg[3] = 0x4A69
    cpu.reg[4] = 0xABCD
    program = [
        0b1101_011_001_00000_0, # STOREB r3, [r1]
        0b1101_100_001_00010_0, # STOREB r4, [r1 + 2]
        0b0111_000000000000   # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.mem.data[0x4321] == 0x69 # Only lower byte should be stored
    assert cpu.mem.data[0x4323] == 0xCD
    assert cpu.mem.data[0x4321] < 0xFF # Should fit into a byte
    assert cpu.mem.data[0x4323] < 0xFF

def test_load_indirect_word(): # Load word from memory address [register + offset]
    cpu = CPU()
    cpu.reg[2] = 0xA070
    cpu.mem.data[0xA070] = 0x69
    cpu.mem.data[0xA071] = 0x42
    cpu.mem.data[0xA074] = 0x12
    cpu.mem.data[0xA075] = 0x34
    program = [
        0b1110_011_010_00000_0, # LOAD r3, [r2]
        0b1110_100_010_00100_0, # LOAD r4, [r2 + 4]
        0b0111_000000000000   # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.reg[3] == 0x6942
    assert cpu.reg[4] == 0x1234

def test_store_indirect_word(): # Store word to memory address [register + offset]
    cpu = CPU()
    cpu.reg[1] = 0x4321
    cpu.reg[3] = 0x4A69
    cpu.reg[4] = 0xABCD
    program = [
        0b1111_011_001_00000_0, # STORE r3, [r1]
        0b1111_100_001_00010_0, # STORE r4, [r1 + 2]
        0b0111_000000000000   # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.mem.data[0x4321] == 0x4A
    assert cpu.mem.data[0x4322] == 0x69
    assert cpu.mem.data[0x4323] == 0xAB
    assert cpu.mem.data[0x4324] == 0xCD

def test_pop_byte():
    cpu = CPU()
    cpu.sp = 0xFFFE
    cpu.mem.data[0xFFFF] = 69
    program = [
        0b1100_011_00000000_1, # POPB r3
        0b0111_000000000000   # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.reg[3] == 69
    assert cpu.reg[3] < 0xFF # Should fit into a byte
    assert cpu.sp == 0xFFFE + 1 # Was the SP incremented?

def test_push_byte():
    cpu = CPU()
    cpu.sp = 0xFFFF
    cpu.reg[3] = 0x4A69
    program = [
        0b1101_011_00000000_1, # PUSHB r3
        0b0111_000000000000   # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.mem.data[0xFFFF] == 0x69
    assert cpu.mem.data[0xFFFF] < 0xFF # Should fit into a byte
    assert cpu.sp == 0xFFFF - 1 # Was the SP decremented?

def test_push_pop_byte():
    cpu = CPU()
    cpu.mem.data[0xFFFE] = 0
    cpu.reg[3] = 0xABCD
    program = [
        0b1101_011_00000000_1,  # PUSH r3
        0b1100_010_00000000_1,  # POP r2
        0b0111_000000000000    # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.mem.data[0xFFFE] == 0 # Upper bit should not get stored
    assert cpu.reg[2] == 0xCD # Only lower byte should get loaded
    assert cpu.sp == 0xFFFF # Stack pointer returns to original position

def test_pop_word():
    cpu = CPU()
    cpu.sp = 0xFFFD
    cpu.mem.data[0xFFFE] = 0x4A
    cpu.mem.data[0xFFFF] = 0x69
    program = [
        0b1110_011_00000000_1, # POP r3
        0b0111_000000000000   # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.reg[3] == 0x4A69
    assert cpu.sp == 0xFFFD + 2 # Was the SP incremented?

def test_push_word():
    cpu = CPU()
    cpu.sp = 0xFFFF
    cpu.reg[3] = 0x4A69
    program = [
        0b1111_011_00000000_1, # PUSH r3
        0b0111_000000000000   # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.mem.data[0xFFFE] == 0x4A
    assert cpu.mem.data[0xFFFF] == 0x69
    assert cpu.sp == 0xFFFF - 2 # Was the SP decremented?

def test_push_pop_word():
    cpu = CPU()
    cpu.reg[3] = 0xABCD
    program = [
        0b1111_011_00000000_1,  # PUSH r3
        0b1110_010_00000000_1,  # POP r2
        0b0111_000000000000    # HALT
    ]
    cpu.mem.load_program(program)

    cpu.run()
    assert cpu.reg[2] == 0xABCD
    assert cpu.sp == 0xFFFF # Stack pointer returns to original position