from emulator import CPU
cpu = CPU()
program = [
    0b0110_000_000000001,   # 0:  MOV r0, 1
    0b0110_001_000000101,   # 2:  MOV r1, 5
    0b0110_010_000000000,   # 4:  MOV r2, 0
    # .loop:
    0b0000_010_010_000_000, # 6:  ADD r2 = r2 + r0
    0b0001_000_000001_000,  # 8:  INC r0
    0b0000_000_000_001_111, # 10: CMP r0, r1
    0b0010_011_111111101,   # 12: JLT -3 instructions back (relative -6 bytes)
    0b0111_000000000000,    # 14: HALT
]
cpu.mem.load_program(program)
cpu.run(max_cycles=30, dump_state=True)
