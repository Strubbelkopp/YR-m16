@import "programs/lib.asm"

@let CONSOLE_BASE_REG = 0xF000                  ; Memory-mapped register that holds the address, where the console starts reading text to display
@let CONSOLE_BUFFER = 0xC000

@let str_ptr = r0
@let console_buffer_ptr = r1
@let print_position = r2
main:
    mov console_buffer_ptr, CONSOLE_BUFFER      ; Load pointer to "str", console buffer & print position as arguments for the print function
    store console_buffer_ptr, CONSOLE_BASE_REG  ; Initialize console base register to point to the beginning of the console buffer
    mov str_ptr, str
    mov print_position, 0
    call print
.end:
    jmp .end

str:
    @data "Hello World!", '\0'