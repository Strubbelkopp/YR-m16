; Constants
@let DISPLAY_BUFFER_A = 0xC000
@let DISPLAY_BUFFER_B = 0xC780 ; DISPLAY_BUFFER_A + BUFFER_SIZE
@let WIDTH = 80
@let HEIGHT = 24
@let BUFFER_SIZE = 1920 ; WIDTH * HEIGHT
@let DEAD = ' '
@let ALIVE = '@'
; Memory locations
@let console_base_reg = 0xF000
@let active_buffer = 0x1000
@let hidden_buffer = 0x1002
; Local variables
@let tmp = r6
@let active_cell = r0
@let new_cell = r1
@let neighbours = r2
@let state = r3
@let i = r4

main:
    mov active_cell, DISPLAY_BUFFER_A
    store active_cell, console_base_reg
    store active_cell, active_buffer
    mov new_cell, DISPLAY_BUFFER_B
    store new_cell, hidden_buffer
    call init_buffers
.loop:
    call calculate_next_generation
    jmp .loop
.end:
    jmp .end

init_buffers:
.loop:
    mov state, DEAD
    storeb state, [active_cell]
    storeb state, [new_cell]
    add active_cell, 1
    add new_cell, 1
    cmp active_cell, DISPLAY_BUFFER_B ; Whole buffer filled, once it reaches the start of the 'B' buffer
    jne .loop
.set_patterns:
    mov state, ALIVE
    storeb state, [0xC28A]
    storeb state, [0xC2DB]
    storeb state, [0xC329]
    storeb state, [0xC32A]
    storeb state, [0xC32B]
    ret

calculate_next_generation:
    load active_cell, [active_buffer]
    load new_cell, [hidden_buffer]
    mov i, 0                            ; Initialize counter
.loop:

.calculate_neighbours:
    mov neighbours, 0
    mov tmp, active_cell
.top_left:
    sub tmp, 81 ; WIDTH - 1
    loadb state, [tmp]
    cmp state, ALIVE
    jne .top_center
    add neighbours, 1
.top_center:
    add tmp, 1
    loadb state, [tmp]
    cmp state, ALIVE
    jne .top_right
    add neighbours, 1
.top_right:
    add tmp, 1
    loadb state, [tmp]
    cmp state, ALIVE
    jne .center_left
    add neighbours, 1
.center_left:
    add tmp, 78 ; WIDTH - 2
    loadb state, [tmp]
    cmp state, ALIVE
    jne .center_right
    add neighbours, 1
.center_right:
    add tmp, 2
    loadb state, [tmp]
    cmp state, ALIVE
    jne .bottom_left
    add neighbours, 1
.bottom_left:
    add tmp, 78; WIDTH - 2
    loadb state, [tmp]
    cmp state, ALIVE
    jne .bottom_center
    add neighbours, 1
.bottom_center:
    add tmp, 1
    loadb state, [tmp]
    cmp state, ALIVE
    jne .bottom_right
    add neighbours, 1
.bottom_right:
    add tmp, 1
    loadb state, [tmp]
    cmp state, ALIVE
    jne .apply_rules
    add neighbours, 1

.apply_rules:
    loadb state, [active_cell]
    cmp state, ALIVE
    jne .dead
.alive:
    cmp neighbours, 2 ; Living cell with < 2 neighbours dies (underpopulation)
    jlt .set_dead
    cmp neighbours, 3 ; Living cell with > 3 neighbours dies (overpopulation)
    jgt .set_dead
    jmp .set_new_state
.dead:
    cmp neighbours, 3 ; Dead cell with 3 neighbours lives (reproduction)
    jne .set_new_state
.set_living:
    mov state, ALIVE
    jmp .set_new_state
.set_dead:
    mov state, DEAD
.set_new_state:
    storeb state, [new_cell]

    add active_cell, 1                  ; Move to next cell
    add new_cell, 1
    add i, 1
    cmp i, BUFFER_SIZE
    jne .loop
.swap_buffers:
    load tmp, [active_buffer]
    push tmp
    load tmp, [hidden_buffer]
    store tmp, [active_buffer]
    store tmp, console_base_reg
    pop tmp
    store tmp, [hidden_buffer]
    ret

print_neighbours: ; Debug function to print the amount of living neighbours around each cell. Call after "calculate_neighbours"
    add neighbours, 48
    storeb neighbours, [new_cell]
    ret