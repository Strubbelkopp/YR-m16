; Memory-mapped registers
@let CONSOLE_BASE   = 0xF000
@let KEYBRD_DATA    = 0xF002
@let KEYBRD_STATUS  = 0xF003

; Constants
@let CONSOLE_START  = 0xC000                ; Initial beginning of the console text buffer
@let DATA_RDY_FLAG  = 0b0000_0001
@let TAB_WIDTH      = 4
@let TAB_MASK       = 0b1111_1111_1111_1100 ; Tab mask for a tab width of 4 (0xFFFF << log_2(TAB_WIDTH))
@let BLINK_RATE     = 10000                 ; Cursor blink rate (in wait_key loops)
@let BLINK_RATE_HLF = 5000
@let CURSOR_CHAR    = '_'

; Variable assignments
@let key        = r0
@let active_chr = r1
@let cursor     = r2
@let i          = r3
@let tmp        = r4
@let counter    = r5
@let end_ptr    = 0x1000
@let start_ptr  = 0x1002

; Keycodes
@let ESCAPE     = 0x1B
@let SPACE      = 0x20
@let TAB        = 0x09
@let ENTER      = 0x0A
@let EXT_KEY    = 0xE0
@let BACKSPACE  = 0x08
@let ARW_UP     = 0x48
@let ARW_RIGHT  = 0x4D
@let ARW_DOWN   = 0x50
@let ARW_LEFT   = 0x4B
@let DELETE     = 0x53

main:
    mov cursor CONSOLE_START        ; Initialize console
    store cursor, start_ptr
    store cursor, end_ptr
    store cursor, CONSOLE_BASE
    mov active_chr, 0
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
    cmp key, EXT_KEY                ; Extended key code?
    jeq extended_key
    cmp key, ESCAPE                 ; Escape?
    jeq escape
    cmp key, TAB                    ; Tab?
    jeq tab
    cmp key, ENTER                  ; Enter?
    jeq newline
print_char:
    call shift_text_up              ; shift all text in front up by one, if there is any ; TODO: should this function handle updating end_ptr?
    storeb key, [cursor]            ; Print char & move cursor to next position
    add cursor, 1
    cmp cursor, [end_ptr]           ; Check if cursor moved past end_ptr
    jgt .update_end_ptr
    jmp wait_key
.update_end_ptr:
    store cursor, end_ptr
    jmp wait_key

; Handle special keys
escape:
    halt                            ; Stop the program
backspace:
    call check_start                ; Don't do anything if cursor is at beginning of console
    sub cursor, 1                   ; Move cursor back
    call shift_text_down            ; TODO: should this function handle updating end_ptr?
    load tmp, end_ptr               ; Decrement end_ptr. This should always happen (if we're not at the start of course)
    sub tmp, 1                      ; TODO: make sure to properly handle circular buffer wrap around
    store tmp, end_ptr
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
    cmp key, BACKSPACE              ; Backspace?
    jeq backspace
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
    cmp cursor, [start_ptr]         ; Check if the cursor is at the beginning of the console text buffer
    jeq .at_start                   ; If so, don't do anything and wait for next input
    ret
.at_start:
    pop tmp                         ; Pop return address off of stack
    jmp wait_key
check_end:
    cmp cursor, [end_ptr]           ; Check if the cursor is at the end of the console text buffer
    jeq .at_end                     ; If so, don't do anything and wait for next input
    ret
.at_end:
    pop tmp                         ; Pop return address off of stack
    jmp wait_key

shift_text_down:                    ; TODO: in the future just do it until end of line, unless you cross the line boundary
    push cursor                     ; Save current cursor postition
    storeb active_chr, [cursor]     ; Begin by moving the active char down (don't load if from the text buffer, since that might be the cursor at the moment)
.loop:
    add cursor, 1                   ; Move to next position and check if we're done
    cmp cursor, [end_ptr]
    jeq .done
    loadb tmp, [cursor + 1]         ; Move char one position down
    storeb tmp, [cursor]
    jmp .loop
.done:
    mov tmp, 0                      ; Move the value 0 at the end, making sure to erase any characters that were there
    storeb tmp, cursor
    pop cursor                      ; Restore cursor
    ret
shift_text_up:
    push cursor                     ; Save current cursor position
    cmp cursor, end_ptr             ; No shifting needed, if we're already at the end
    jeq .done
    load cursor, end_ptr            ; Move cursor to the end
.loop:
    sub cursor, 1
    loadb tmp, [cursor]             ; Move char one position up
    storeb tmp [cursor + 1]
    cmp cursor, [sp + 1]            ; Check if we're back at the original cursor position
    jeq .done
    jmp .loop
.done:
    pop cursor                      ; Restore cursor
    ret