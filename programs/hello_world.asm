@import "programs/lib.asm"

main:
    mov r0, str                    ; load pointer to "str" into r0 as an argument for "print"
    call print
end:
    jmp end

str:
    @data "Hello World!", '\0'