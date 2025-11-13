@let CONSOLE_BASE_REG = 0xF000      ; Memory-mapped register that holds the address, where the console starts
@let CONSOLE_START    = 0xC000      ; Actual region in memory of the console
@let KEYBRD_DATA      = 0xF002
@let KEYBRD_STATUS    = 0xF003

@let char   = r0
@let cursor = r1
@let tmp    = r4

@let ESCPAE = 0x1B
@let BCKSPC = 0x08
@let SPACE  = 0x20
@let TAB    = 0x09
@let ENTER  = 0x0D
@let ARWKEY = 0xE0
@let ARWUP  = 0x48
@let ARWRGT = 0x4D
@let ARWDWN = 0x50
@let ARWLFT = 0x4B

@let TBWDTH = 4
@let TABMSK = 0b1111_1111_1111_1100 ; Tab mask for a tab width of 4 (0xFFFF << log_2(TBWDTH))

main:
    mov cursor CONSOLE_START        ; Initialize console by writing the cursor pointer to CONSOLE_BASE_REG
    store cursor, CONSOLE_BASE_REG
wait_key:
    loadb tmp, KEYBRD_STATUS        ; Wait for input from keyboard
    jz wait_key
    loadb char, KEYBRD_DATA         ; Read keyboard input
    cmp char, ESCPAE                ; Escape?
    jeq escape
    cmp char, BCKSPC                ; Backspace?
    jeq backspace
    cmp char, TAB                   ; Tab?
    jeq tab
    cmp char, ENTER                 ; Enter?
    jeq newline
    cmp char, ARWKEY                ; Arrow key?
    jeq arrow_key
    call shift_text_up              ; shift all text in front up by one, if there is any
    storeb char [cursor]            ; Print char & move cursor to next position
    add cursor, 1
    jmp wait_key

; Handle special keys
escape:
    halt                            ; Stop the program
backspace:
    call check_start                ; Don't do anything if cursor is at beginning of console
    sub cursor, 1                   ; Move cursor back and print a space character
    mov char, SPACE
    storeb char [cursor]
    jmp wait_key
tab:
    and cursor, TABMSK              ; Remove two lower bits, round down the cursor pointer to the next multiple of 4
    add cursor, TBWDTH              ; Add 4, to move the cursor to the next tab position
    jmp wait_key
newline:
    jmp wait_key

; Handle arrow keys
arrow_key:
    loadb char, KEYBRD_DATA         ; Arrow key presses send two bytes. First is 0xE0 and the next one tells which arrow key it was
    cmp char, ARWLFT                ; Left arrow key?
    jeq arrow_left
    jmp wait_key
arrow_left:
    call check_start                ; Don't do anything if cursor is at beginning of console
    sub cursor, 1                   ; Move cursor back
    jmp wait_key

check_start:
    cmp cursor, CONSOLE_START       ; Check if the cursor is at the beginning of the console screen
    jeq wait_key                    ; If so, don't do anything and wait for next input
    ret

shift_text_down:
    ret
shift_text_up:
    ret