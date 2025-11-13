; Memory-mapped registers
@let CONSOLE_BASE   = 0xF000
@let KEYBRD_DATA    = 0xF002
@let KEYBRD_STATUS  = 0xF003

; Constants
@let CONSOLE_START  = 0xC000                ; Initial beginning of the console buffer
@let DATA_RDY_FLAG  = 0b0000_0001
@let TAB_WIDTH      = 4
@let TAB_MASK       = 0b1111_1111_1111_1100 ; Tab mask for a tab width of 4 (0xFFFF << log_2(TAB_WIDTH))
@let BLINK_RATE     = 10000                 ; Cursor blink rate (in wait_key loops)
@let BLINK_RATE_HLF = 5000
@let CURSOR_CHAR    = '_'

; Register assignments
@let key        = r0
@let active_chr = r1
@let cursor     = r2
@let tmp        = r4
@let counter    = r5

; Keycodes
@let ESCAPE     = 0x1B
@let BACKSPACE  = 0x08
@let SPACE      = 0x20
@let TAB        = 0x09
@let ENTER      = 0x0D
@let EXT_KEY    = 0xE0
@let ARW_UP     = 0x48
@let ARW_RIGHT  = 0x4D
@let ARW_DOWN   = 0x50
@let ARW_LEFT   = 0x4B
@let DELETE     = 0x53

main:
    mov cursor CONSOLE_START        ; Initialize console by writing the cursor pointer to CONSOLE_BASE
    store cursor, CONSOLE_BASE
    mov counter, 0                  ; Initialize counter for cursor blinking
wait_key:
    cmp counter, BLINK_RATE_HLF     ; TODO: Change to BLINK_RATE/2 once my assembler supports this
    jeq .set_cursor
    cmp counter, BLINK_RATE
    jne .check_status
    storeb active_chr, [cursor]     ; Restore character at cursor
    mov counter, 0                  ; Reset counter
    jmp .check_status
.set_cursor:
    mov tmp, CURSOR_CHAR            ; Print cursor
    storeb tmp, [cursor]
.check_status:
    add counter, 1
    loadb tmp, KEYBRD_STATUS        ; Wait for input from keyboard
    and tmp, DATA_RDY_FLAG
    jz wait_key
    loadb key, KEYBRD_DATA          ; Read keyboard input
    cmp key, ESCAPE                 ; Escape?
    jeq escape
    cmp key, BACKSPACE              ; Backspace?
    jeq backspace
    cmp key, TAB                    ; Tab?
    jeq tab
    cmp key, ENTER                  ; Enter?
    jeq newline
    cmp key, EXT_KEY                ; Extended key code?
    jeq extended_key
    call shift_text_up              ; shift all text in front up by one, if there is any
    storeb key, [cursor]            ; Print char & move cursor to next position
    add cursor, 1
    loadb active_chr [cursor]       ; Store char at cursor (for cursor blinking)
    jmp wait_key

; Handle special keys
escape:
    halt                            ; Stop the program
backspace:
    call check_start                ; Don't do anything if cursor is at beginning of console
    storeb active_chr [cursor]      ; Store active char, in case the cursor is there at the moment
    sub cursor, 1                   ; Move cursor back
    call shift_text_down            ; Shift text in front down
    jmp wait_key
tab:
    and cursor, TAB_MASK            ; Remove two lower bits, round down the cursor pointer to the next multiple of 4
    add cursor, TAB_WIDTH           ; Add 4, to move the cursor to the next tab position
    jmp wait_key
newline:
    jmp wait_key

; Handle extended key codes
extended_key:
    loadb key, KEYBRD_DATA          ; Extended key presses send two bytes. First is 0xE0 and the next one tells which extended key it was
    cmp key, ARW_LEFT               ; Left arrow key?
    jeq arrow_left
    cmp key, DELETE                 ; Delete?
    jeq delete
    jmp wait_key
arrow_left:
    call check_start                ; Don't do anything if cursor is at beginning of console
    storeb active_chr [cursor]      ; Store active char, in case the cursor is there at the moment
    sub cursor, 1                   ; Move cursor back
    loadb active_chr [cursor]       ; Store char at cursor (for cursor blinking)
    jmp wait_key
delete:
    call check_end
    call shift_text_down
    jmp wait_key

check_start:
    cmp cursor, CONSOLE_START       ; Check if the cursor is at the beginning of the console screen
    jeq wait_key                    ; If so, don't do anything and wait for next input
    ret
check_end:
    ret

shift_text_down:
    mov tmp, ' '                    ; TODO: For now just print a space character
    storeb tmp, [cursor]
    loadb active_chr, [cursor]      ; Store char at cursor (for cursor blinking)
    ret
shift_text_up:
    ret