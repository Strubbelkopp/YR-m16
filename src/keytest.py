from unicurses import *
from queue import Queue

def read_keys(stdscr):
    cbreak()
    noecho()
    keypad(stdscr, True)
    nodelay(stdscr, True)
    input_buffer = Queue()
    while True:
        ch = getch()
        if ch != -1:
            clear()
            addstr(f"Key pressed: {[f"{c:02X}" for c in get_key_code(ch)]}\n")
            refresh()
        if ch == ord('q'):
            break

def get_key_code(key):
    if 0 <= key <= 255:
        return bytes([key])
    else:
        EXTENDED_KEY_MAP = {
            3:  0x48,  # Up Arrow
            2:  0x50,  # Down Arrow
            4:  0x4B,  # Left Arrow
            5:  0x4D,  # Right Arrow
            7:  0x08,  # Backspace
            74: 0x53,  # Delete
        }
        addstr( f"Extended key: {key & 0xFF}\n")
        return bytes([0xE0, EXTENDED_KEY_MAP.get(key & 0xFF, 0x00)])

if __name__ == "__main__":
    wrapper(read_keys)