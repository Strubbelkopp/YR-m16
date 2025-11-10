import argparse
from cpu import CPU

with open("hello_world.bin", "rb") as program:
    cpu = CPU()
    cpu.bus.memory.load_program(program.read())
    cpu.run()

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(prog="YR-µ16 Emulator")
#     parser.add_argument("filename", help="program binary to execute")
#     args = parser.parse_args()

#     with open(args.filename, "rb") as program:
#         cpu = CPU()
#         cpu.bus.memory.load_program(program.read())
#         cpu.run()