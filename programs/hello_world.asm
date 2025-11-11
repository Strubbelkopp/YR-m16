@import "programs/lib.asm"

main:
    push str                    ; push string pointer as a function argument to the stack (set up call stack)
    call print
    add sp, 1                   ; bring the sp back
    halt

str:
    @data "Hello World!", '\0'