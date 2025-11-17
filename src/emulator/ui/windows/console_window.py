from unicurses import mvwaddstr
from ui.windows.window import Window

SCREEN_HEIGHT = 24
SCREEN_WIDTH = 80

class ConsoleWindow(Window):
    def __init__(self, height, width, y, x, program_name, cpu):
        super().__init__(height, width, y, x, title=f"{program_name} (F1)")
        self.border = [
            '┌','─','┐',
            '│',    '│',
            '│',' ','│',
        ]
        self.memory = cpu.bus.memory
        self.console = cpu.bus.console

    def draw_contents(self):
        index = self.console.base_addr - self.memory.min_address
        screen_data = self.memory.data[index : index + SCREEN_WIDTH * SCREEN_HEIGHT]
        line_num = 0
        for i in range(0, len(screen_data), SCREEN_WIDTH):
            line = ''.join(chr(c) if c >= 32 else ' ' for c in screen_data[i:i+SCREEN_WIDTH])
            mvwaddstr(self.win, 1 + line_num, 2, line)
            line_num += 1