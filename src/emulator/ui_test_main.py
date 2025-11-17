from unicurses import *
from ui import UI

def main(stdscr):
    ui = UI(stdscr, program_name="hello_world.bin")
    while True:
        ui.draw()

if __name__ == "__main__":
    wrapper(main)