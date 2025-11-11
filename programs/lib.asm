@let CONSOLE_BASE_REG = 0xF000  ; Memory-mapped register that holds the address, where the console starts
@let CONSOLE = 0xC000           ; Actual region in memory of the console

@let str_ptr = r0
@let char = r1
@let tmp = r2
@let i = r2

print:
    mov tmp, CONSOLE            ; Initialize console base register to point to the beginning of the memory region, where it should read the text
    store tmp, CONSOLE_BASE_REG
    mov i, 0                    ; reset index register
    load str_ptr, [sp + 3]      ; retrieve string pointer argument (can't use pop, since calling the function pushed the PC onto the stack)
.loop:
    loadb char, [str_ptr]       ; load value pointed to by str_ptr into char
    jz .done                    ; if it was a null byte, it's the end of the string
    storeb char, [CONSOLE + i]  ; could also mov CONSOLE into a register and inc that
    add str_ptr, 1
    add i, 1
    jmp .loop
.done:
    ret