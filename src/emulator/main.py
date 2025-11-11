import argparse
from cpu import CPU
import time

def execute_program(filename):
    with open(filename, "rb") as program:
        cpu = CPU()
        cpu.bus.memory.load_program(program.read())

        start = time.perf_counter()
        cpu.run()
        print(f"Executed '{filename}' in {(time.perf_counter() - start):.05f}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="YR-µ16 Emulator")
    parser.add_argument("filename", help="program binary to execute")
    args = parser.parse_args()
    execute_program(args.filename)