import msvcrt
while True:
    if msvcrt.kbhit():
        char = msvcrt.getch()
        if char:
            print(hex(ord(char)))