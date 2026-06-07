; Prints null-terminated string to a given position on the screen
; Inputs: r0 = Pointer to the null-terminated string to print
;         r1 = Pointer to the console buffer
;         r2 = Position on the screen where to start printing, given through an offset relative to the console buffer start
@let str_ptr = r0
@let console_buffer_ptr = r1
@let print_position = r2
@let char = r2
print:
    add console_buffer_ptr, print_position  ; Move console buffer pointer to the specified position
.loop:
    loadb char, [str_ptr]                   ; Load value pointed to by str_ptr into char
    jz .done                                ; If it was a null byte, it's the end of the string
    storeb char, [console_buffer_ptr]
    add str_ptr, 1
    add console_buffer_ptr, 1
    jmp .loop
.done:
    ret

; Converts a 16-bit binary number to a 5-digit BCD ASCII string using the double dabble algorithm
; Inputs:  r0 = Pointer to a 6-byte output buffer
;          r1 = Number to convert (0–65535)
; Outputs: buffer filled with "DDDDD\0"
@let bcd_result_ptr = r0
@let num            = r1
@let bcd_upper      = r2                    ; BCD scratch bits [19:16] — ten-thousands
@let bcd_lower      = r3                    ; BCD scratch bits [15:0]  — thousands/hundreds/tens/ones
@let tmp            = r4
@let shift_ctr      = r5
convert_bcd:
    mov bcd_upper, 0                        ; Initialize registers
    mov bcd_lower, 0
    mov shift_ctr, 16
.loop:                                      ; Go through each digit and add 3 if it is >= 5
    mov tmp, bcd_lower                      ; Ones digit (bits [3:0])
    and tmp, 0xF
    cmp tmp, 5
    jlt .skip_ones
    add bcd_lower, 3
.skip_ones:
    mov tmp, bcd_lower                      ; Tens digit (bits [7:4])
    and tmp, 0xF0
    cmp tmp, 0x50
    jlt .skip_tens
    add bcd_lower, 0x30
.skip_tens:
    mov tmp, bcd_lower                      ; Hundreds digit (bits [11:8])
    and tmp, 0xF00
    cmp tmp, 0x500
    jlt .skip_hundreds
    add bcd_lower, 0x300
.skip_hundreds:
    mov tmp, bcd_lower                      ; Thousands digit (bits [15:12])
    and tmp, 0xF000
    cmp tmp, 0x5000
    jlt .skip_thousands
    add bcd_lower, 0x3000
.skip_thousands:
    cmp bcd_upper, 5                        ; Ten-thousands digit (bits [3:0] of upper)
    jlt .skip_ten_thousands
    add bcd_upper, 3
.skip_ten_thousands:
    mov tmp, bcd_lower                      ; Shift top bit of `bcd_lower` into bottom bit of `bcd_upper`
    shr tmp, 15
    shl bcd_upper, 1
    or  bcd_upper, tmp
    mov tmp, num                            ; Shift top bit of `num` into bottom bit of `bcd_lower`
    shr tmp, 15
    shl bcd_lower, 1
    or  bcd_lower, tmp
    shl num, 1                              ; Shift num
    sub shift_ctr, 1
    jnz .loop
.store_result:                              ; Convert digits to ASCII & store in buffer
    add bcd_upper, '0'                      ; Ten-thousands digit
    storeb bcd_upper, [bcd_result_ptr]
    add bcd_result_ptr, 1
    mov tmp, bcd_lower                      ; Thousands digit
    shr tmp, 12
    add tmp, '0'
    storeb tmp, [bcd_result_ptr]
    add bcd_result_ptr, 1
    mov tmp, bcd_lower                      ; Hundreds digit
    shr tmp, 8
    add tmp, '0'
    storeb tmp, [bcd_result_ptr]
    add bcd_result_ptr, 1
    mov tmp, bcd_lower                      ; Tens digit
    shr tmp, 4
    add tmp, '0'
    storeb tmp, [bcd_result_ptr]
    add bcd_result_ptr, 1
    mov tmp, bcd_lower                      ; Ones digit
    and tmp, 0xF
    add tmp, '0'
    storeb tmp, [bcd_result_ptr]
    add bcd_result_ptr, 1
    mov tmp, 0                              ; Null terminator
    storeb tmp, [bcd_result_ptr]
    ret