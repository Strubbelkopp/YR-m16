from unicurses import *
from time import sleep
from random import randint

CONSOLE_W = 80
CONSOLE_H = 24
CONSOLE_Y = 1
CONSOLE_X = 2

STATUS_W = 24
STATUS_H = 14
STATUS_Y = 26
STATUS_X = 2

MEMORY_W = 53
MEMORY_H = 12
MEMORY_Y = 26
MEMORY_X = 29

ACTION_W = 53
ACTION_H = 1
ACTION_Y = 39
ACTION_X = 29

SCREEN_W = CONSOLE_W + 4
SCREEN_H = CONSOLE_H + STATUS_H + 3
SCREEN_Y = 0
SCREEN_X = 0

def draw_borders(win): # Redraw on focus change
    mvwhline(win, SCREEN_Y, SCREEN_X, '─', SCREEN_W)
    mvwhline(win, CONSOLE_Y + CONSOLE_H, CONSOLE_X - 1, '─', CONSOLE_W + 2)
    mvwhline(win, MEMORY_Y + MEMORY_H, MEMORY_X - 1, '─', MEMORY_W + 2)
    mvwhline(win, SCREEN_Y + SCREEN_H - 1, SCREEN_X, '─', SCREEN_W)

    mvwvline(win, SCREEN_Y, SCREEN_X, '│', SCREEN_H)
    mvwvline(win, STATUS_Y, STATUS_X + STATUS_W + 1, '│', STATUS_H)
    mvwvline(win, SCREEN_Y, SCREEN_X + SCREEN_W - 1, '│', SCREEN_H)

    mvwaddch(win, SCREEN_Y, SCREEN_X, '┌')
    mvwaddch(win, SCREEN_Y, SCREEN_X + SCREEN_W - 1, '┐')
    mvwaddch(win, STATUS_Y - 1, STATUS_X - 2, '├')
    mvwaddch(win, ACTION_Y - 1, ACTION_X - 2, '├')
    mvwaddch(win, MEMORY_Y - 1, MEMORY_X + MEMORY_W + 1, '┤')
    mvwaddch(win, ACTION_Y - 1, ACTION_X + ACTION_W + 1, '┤')
    mvwaddch(win, MEMORY_Y - 1, MEMORY_X - 2, '┬')
    mvwaddch(win, ACTION_Y + 1, ACTION_X - 2, '┴')
    mvwaddch(win, SCREEN_Y + SCREEN_H - 1, SCREEN_X, '└')
    mvwaddch(win, SCREEN_Y + SCREEN_H - 1, SCREEN_X + SCREEN_W - 1, '┘')

def draw_titles(win, program_name):
    console_title = f"┤ {program_name} (F1) ├"
    mvwaddstr(win, CONSOLE_Y - 1, CONSOLE_X + ((CONSOLE_W - len(console_title))//2), console_title)

    status_title = "┤ Status ├"
    mvwaddstr(win, STATUS_Y - 1, STATUS_X + ((STATUS_W - len(status_title))//2), status_title)

    memory_title = "┤ Memory View (F2) ├"
    mvwaddstr(win, MEMORY_Y - 1, MEMORY_X + ((MEMORY_W - len(memory_title))//2), memory_title)


def draw_console_win(win, data):
    wclear(win)
    start = 0
    end = 80 * 24
    string = ''.join([chr(i) for i in data["memory"][start:end]])
    mvwaddstr(win, 0, 0, string)
    wrefresh(win)
def draw_status_win(win, data):
    wmove(win, 0, 0)
    regs = data["regs"]
    flags = data["flags"]
    string = "Registers:\n" + "\n".join(
        f"r{i}: {regs[i]:04X}, r{i+1}: {regs[i+1]:04X}" for i in range(0, 6, 2)
    ) + f"\nr6: {regs[6]:04X}\nSP: {regs[7]:04X}, PC: {regs[8]:04X}" + "\n\n" + "Flags:\n" + ", ".join(
        f"{flag}: {'1' if flags[flag] else '0'}" for flag in flags
    ) + "\n\n" + f"Clock Cycle: {frame}"
    mvwaddstr(win, 0, 0, string)

    wrefresh(win)
def draw_memory_win(win, data, start_addr):
    hexdump = ""
    for addr in range(start_addr, start_addr + 11*16, 16):
        chunk = data["memory"][addr:addr+16]
        hex_bytes = ' '.join(f'{b:02X}' for b in chunk)
        hexdump += f"{addr:04X}: {hex_bytes}"

    string = f"Address: {start_addr:04X}\n" + hexdump
    mvwaddstr(win, 0, 0, string)
    wrefresh(win)
def draw_action_win(win):
    string = "Quit (F3) | Pause (F4) | Continue (F5) | Step (F6)"
    mvwaddstr(win, 0, (ACTION_W - len(string))//2, string)
    wrefresh(win)

def main(stdscr):
    program_name = "program1.bin"

    global frame
    frame = 0
    curs_set(0) # Hide cursor
    noecho() # Don't echo keyboard inputs
    cbreak() #Don't wait for 'Enter' key
    nodelay(stdscr, True) # Non-blocking input
    use_default_colors()

    console_win = newwin(CONSOLE_H, CONSOLE_W, CONSOLE_Y, CONSOLE_X)
    status_win = newwin(STATUS_H, STATUS_W, STATUS_Y, STATUS_X)
    memory_win = newwin(MEMORY_H, MEMORY_W, MEMORY_Y, MEMORY_X)
    action_win = newwin(ACTION_H, ACTION_W, ACTION_Y, ACTION_X)

    draw_borders(stdscr)
    draw_titles(stdscr, program_name)
    wrefresh(stdscr)

    data = {
        "regs": [0] * 9,
        "flags": {
            "Z": True,
            "N": False,
            "C": True,
            "V": False,
            "IE": False
        },
        "memory": [randint(0, 0xFF) for i in range(0, 0xFFFF)]
    }

    start_addr = 0
    while True:
        if frame % 10000 == 0:
            start_addr = randint(0, 4080) * 16
        elif frame % 700 == 0:
            data["regs"][randint(0, 8)] = randint(0, 0xFFFF)
            # data["flags"][(data["flags"].keys())[randint(0, 3)]] = False if randint(0, 1) == 0 else 1
        data["memory"][randint(0, 0xFFFF-1)] = randint(32, 0xFF)
        if frame % 60 == 0:
            draw_console_win(console_win, data)
        draw_status_win(status_win, data)
        draw_memory_win(memory_win, data, start_addr)
        draw_action_win(action_win)
        # sleep(1.0 / 15)
        frame += 1

if __name__ == "__main__":
    wrapper(main)