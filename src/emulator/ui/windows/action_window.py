from .window import Window

class ActionWindow(Window):
    def __init__(self, term, height, width, y, x):
        super().__init__(term, height, width, y, x)
        self.border = [
            '├','─','┤',
            '│',    '│',
            '┴','─','┘',
        ]

    def draw_contents(self):
        string = "Quit (F3) | Pause (F4) | Continue (F5) | Step (F6)"
        self.print_str(1, (self.width - len(string))//2, string)