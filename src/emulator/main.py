from argparse import ArgumentParser
from cpu import CPU
from time import perf_counter
from unicurses import initscr

def execute_program(filename, max_cycles):
    with open(filename, "rb") as program:
        cpu = CPU(stdscr=initscr())
        cpu.bus.memory.load_program(program.read())

        start = perf_counter()
        cpu.run(max_cycles=max_cycles)
        print(f"Executed '{filename}' in {(perf_counter() - start):.05f}s")

if __name__ == "__main__":
    parser = ArgumentParser(prog="YR-µ16 Emulator")
    parser.add_argument("filename", help="program binary to execute")
    parser.add_argument("--max-cycles", type=int, default=-1, help="maximum CPU cycles to execute before exiting")
    args = parser.parse_args()
    execute_program(args.filename, args.max_cycles)