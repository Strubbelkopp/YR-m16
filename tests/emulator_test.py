from src.emulator import CPU

import pytest

def test_halt():
    cpu = CPU()
    program = [
        0b0111_000000000000,  # HALT
        0b0110_001_000010001  # MOV r1, 17
    ]
    cpu.load_program(program)

    cpu.run()
    assert cpu.cycles == 1
    assert cpu.reg[1] == 0

def test_mov_immediate():
    cpu = CPU()
    program = [
        0b0110_001_000010001,  # MOV r1, 17
        0b0111_000000000000    # HALT
    ]
    cpu.load_program(program)

    cpu.run()
    assert cpu.reg[1] == 17
    assert cpu.flags["Z"] == 0
    assert cpu.flags["N"] == 0

def test_add():
    cpu = CPU()
    program = [
        0b0110_000_000000101,   # MOV r0, 5
        0b0110_001_000001010,   # MOV r1, 10
        0b0000_010_000_001_000, # ADD r2, r0, r1
        0b0111_000000000000     # HALT
    ]
    cpu.load_program(program)

    cpu.run()
    assert cpu.reg[2] == 15

def test_add_immediate():
    cpu = CPU()
    program = [
        0b0110_001_000000101,    # MOV r1, 5
        0b0001_001_001010_000,   # ADD r1, 10 (reg/imm)
        0b0111_000000000000      # HALT
    ]
    cpu.load_program(program)

    cpu.run()
    assert cpu.reg[1] == 15

def test_sub():
    cpu = CPU()
    program = [
        0b0110_000_000000101,   # MOV r0, 5
        0b0110_001_000001000,   # MOV r1, 8
        0b0000_010_000_001_001, # SUB r2, r0, r1
        0b0111_000000000000     # HALT
    ]
    cpu.load_program(program)

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
    cpu.load_program(program)

    cpu.run()
    assert cpu.reg[2] == 0b10001000
    assert cpu.reg[3] == 0b11101110
    assert cpu.reg[4] == 0b01100110

def test_shl_carry_flag():
    cpu = CPU()
    program = [
        0b0110_000_011111111,  # MOV r0, 0xFF
        0b0001_000_000001_101, # SHL r0, 1
        0b0001_000_001000_101, # SHL r0, 8
        0b0111_000000000000    # HALT
    ]
    cpu.load_program(program)

    cpu.step(2)
    assert cpu.reg[0] == 0x1fe
    assert cpu.flags["C"] == 0
    cpu.step()
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
    cpu.load_program(program)

    cpu.step(2)
    assert cpu.pc == 6  # JZ skipped one instruction ahead
    cpu.run()
    assert cpu.reg[0] == 0

def test_relative_jump_backward():
    cpu = CPU()
    # This program increments r0 3 times using a backward jump loop
    # Instruction offsets count in instructions (not bytes)
    program = [
        0b0110_000_000000000,   # 0: MOV r0, 0
        0b0110_001_000000001,   # 2: MOV r1, 1
        # loop start
        0b0000_000_000_001_000, # 4: ADD r0, r0, r1
        0b0000_000_000000011,   # 6: CMP r0, 3
        0b0010_010_111111110,   # 8: JNZ -2 instruction (offset -2) if we want to loop 3x
        0b0111_000000000000     # 10: HALT
    ]
    cpu.load_program(program)

    cpu.step(2) # Initialize registers
    cpu.step()  # ADD r0 += r1
    assert cpu.reg[0] == 1
    cpu.step(2)  # CMP & JNZ -2
    # PC should go back to ADD instruction
    assert cpu.pc == 4
    cpu.step()  # ADD r0 += r1 again
    assert cpu.reg[0] == 2
    cpu.step(2)  # CMP & JNZ -2
    assert cpu.pc == 4
    cpu.step()  # ADD r0 += r1 third time
    assert cpu.reg[0] == 3
    cpu.step(2)  # CMP & JNZ -2
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
    cpu.load_program(program)
    cpu.run()

    # CMP sets flags but does not store result
    assert cpu.flags["Z"] == 0
    assert cpu.flags["N"] == 1  # 2 - 3 = -1 => N flag set