from argparse import ArgumentParser
from .cpu import CPU
from .ui.ui import UI
from time import perf_counter
from blessed import Terminal

def execute_program(filename, max_cycles, term=None):
    with open(filename, "rb") as program:
        cpu = CPU(term)
        cpu.bus.memory.load_program(program.read())
        ui = UI(filename, cpu) if term else None
        start = perf_counter()
        cpu.run(max_cycles=max_cycles, ui=ui)
        print(f"Executed '{filename}' in {(perf_counter() - start):.05f}s")

def main():
    parser = ArgumentParser(prog="YR-µ16 Emulator")
    parser.add_argument("filename", help="program binary to execute")
    parser.add_argument("--max-cycles", type=int, default=-1, help="maximum CPU cycles to execute before exiting")
    args = parser.parse_args()
    term = Terminal()
    with term.fullscreen(), term.hidden_cursor(), term.cbreak():
        execute_program(args.filename, args.max_cycles, term)