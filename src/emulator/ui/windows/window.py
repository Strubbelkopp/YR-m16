from unicurses import *

class Window():
    def __init__(self, height, width, y, x, title=None):
        self.win = newwin(height, width, y, x)
        self.height = height
        self.width = width
        self.y = y
        self.x = x
        self.title = title

    def draw_contents(self):
        pass

    def draw_border(self):
        # Corners
        if self.border[0] != ' ':
            mvwaddch(self.win, 0, 0, self.border[0])
        if self.border[2] != ' ':
            mvwaddch(self.win, 0, self.width - 1, self.border[2])
        if self.border[5] != ' ':
            mvwaddch(self.win, self.height - 1, 0, self.border[5])
        if self.border[7] != ' ':
            mvwaddch(self.win, self.height - 1, self.width - 1, self.border[7])

        # Top and bottom
        if self.border[1] != ' ':
            mvwhline(self.win, 0, 1, self.border[1], self.width - 2)
        if self.border[6] != ' ':
            mvwhline(self.win, self.height - 1, 1, self.border[6], self.width - 2)

        # Sides
        if self.border[3] != ' ':
            mvwvline(self.win, 1, 0, self.border[3], self.height - 2)
        if self.border[4] != ' ':
            mvwvline(self.win, 1, self.width - 1, self.border[4], self.height - 2)

        self.draw_title()

    def draw_title(self):
        if self.title:
            title = f"┤ {self.title} ├"
            mvwaddstr(self.win, 0, (self.width - len(title)) // 2, title)
