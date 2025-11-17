from argparse import ArgumentParser
from cpu import CPU
from ui.ui import UI
from time import perf_counter
from unicurses import wrapper

def execute_program(stdscr, filename, max_cycles):
    with open(filename, "rb") as program:
        cpu = CPU(stdscr)
        cpu.bus.memory.load_program(program.read())
        ui = UI(stdscr, filename, cpu)

        start = perf_counter()
        cpu.run(max_cycles=max_cycles, ui=ui)
        print(f"Executed '{filename}' in {(perf_counter() - start):.05f}s")

if __name__ == "__main__":
    parser = ArgumentParser(prog="YR-µ16 Emulator")
    parser.add_argument("filename", help="program binary to execute")
    parser.add_argument("--max-cycles", type=int, default=-1, help="maximum CPU cycles to execute before exiting")
    args = parser.parse_args()
    wrapper(execute_program, args.filename, args.max_cycles)