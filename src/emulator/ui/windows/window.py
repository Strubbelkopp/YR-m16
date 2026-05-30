import sys

class Window():
    def __init__(self, term, height, width, y, x, title=None):
        self.term = term
        self.height = height
        self.width = width
        self.y = y
        self.x = x
        self.title = title
        self.buffer = []

    def draw_contents(self):
        pass

    def draw_border(self):
        # Corners
        if self.border[0] != ' ':
            self.print_str(0, 0, self.border[0])
        if self.border[2] != ' ':
            self.print_str(0, self.width - 1, self.border[2])
        if self.border[5] != ' ':
            self.print_str(self.height - 1, 0, self.border[5])
        if self.border[7] != ' ':
            self.print_str(self.height - 1, self.width - 1, self.border[7])

        # Top and bottom
        if self.border[1] != ' ':
            self.print_str(0, 1, self.border[1] * (self.width - 2))
        if self.border[6] != ' ':
            self.print_str(self.height - 1, 1, self.border[6] * (self.width - 2))

        # Sides
        if self.border[3] != ' ':
            for i in range(self.height - 2):
                self.print_str(i+1, 0, self.border[3])
        if self.border[4] != ' ':
            for i in range(self.height - 2):
                self.print_str(i+1, self.width - 1, self.border[4])

        self.draw_title()

    def draw_title(self):
        if self.title:
            title = f"┤ {self.title} ├"
            self.print_str(0, (self.width - len(title)) // 2, title)

    def print_str(self, y, x, string):
        self.buffer.append(self.term.move_xy(self.x + x, self.y + y) + str(string))

    def flush(self):
        if self.buffer:
            sys.stdout.write(''.join(self.buffer))
            self.buffer.clear()