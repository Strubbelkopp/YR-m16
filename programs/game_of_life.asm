@let WIDTH = 80
@let HEIGHT = 24
@let DISPLAY_BUFFER_A = 0xC000
@let DISPLAY_BUFFER_B = 0xC780 ; + DISPLAY_BUFFER_SIZE
@let DISPLAY_BUFFER_SIZE = 1920 ; WIDTH * HEIGHT
@let STATE_BUFFER_A = 0xCF00 ; + DISPLAY_BUFFER_SIZE
@let STATE_BUFFER_B = 0xD754 ; + STATE_BUFFER_SIZE
@let STATE_BUFFER_SIZE = 2132 ; (WIDTH + 2) * (HEIGHT + 2)
@let DEAD = ' '
@let ALIVE = '@'
@let CONSOLE_BASE_REG = 0xF000

@let front_buffer = 0x1000
@let back_buffer = 0x1002
@let current_state_buffer = 0x1004
@let new_state_buffer = 0x1006

main:
    call init
    call copy_state_to_display
    call swap_buffers
.loop:
    call calculate_new_generation
    call copy_state_to_display
    call swap_buffers
    jmp .loop
.end:
    jmp .end

@let current_cell = r0
@let new_cell = r1
@let state = r5
@let generation = r6
init:
    mov current_cell, DISPLAY_BUFFER_A          ; Initialize display buffer addresses
    store current_cell, [front_buffer]
    mov new_cell, DISPLAY_BUFFER_B
    store new_cell, [back_buffer]
    store current_cell, CONSOLE_BASE_REG        ; Set console to display front_buffer
    mov current_cell, STATE_BUFFER_A            ; Initialize state buffer addresses
    store current_cell, [current_state_buffer]
    mov new_cell, STATE_BUFFER_B
    store new_cell, [new_state_buffer]
.loop:
    mov state, "  "                             ; Initialize both state buffers with dead cells, two cells at a time
    store state, [current_cell]
    store state, [new_cell]
    add current_cell, 2                         ; Advance to next cell pair
    add new_cell, 2
    cmp current_cell, STATE_BUFFER_B            ; Reached end of buffer / beginning of next buffer?
    jne .loop
.end:
    call load_pattern
    ret

@let current_cell = r0
@let new_cell = r1
@let x_counter = r2
@let y_counter = r3
@let neighbours = r4
@let state = r5
@let neighbour_cell = r6
calculate_new_generation:
    load current_cell, [current_state_buffer]   ; Load in cell pointers of (1,1) in state buffer
    add current_cell, 83 ; WIDTH+3
    load new_cell, [new_state_buffer]
    add new_cell, 83 ; WIDTH+3
    mov y_counter, HEIGHT
.y_loop:
    mov x_counter, WIDTH
.x_loop:
.calculate_neighbours:
    mov neighbours, 0
    mov neighbour_cell, current_cell
.top_left:
    sub neighbour_cell, 83 ; WIDTH+3
    loadb state, [neighbour_cell]
    cmp state, ALIVE
    jne .top_center
    add neighbours, 1
.top_center:
    add neighbour_cell, 1
    loadb state, [neighbour_cell]
    cmp state, ALIVE
    jne .top_right
    add neighbours, 1
.top_right:
    add neighbour_cell, 1
    loadb state, [neighbour_cell]
    cmp state, ALIVE
    jne .center_left
    add neighbours, 1
.center_left:
    add neighbour_cell, 80 ; WIDTH
    loadb state, [neighbour_cell]
    cmp state, ALIVE
    jne .center_right
    add neighbours, 1
.center_right:
    add neighbour_cell, 2
    loadb state, [neighbour_cell]
    cmp state, ALIVE
    jne .bottom_left
    add neighbours, 1
.bottom_left:
    add neighbour_cell, 80 ; WIDTH
    loadb state, [neighbour_cell]
    cmp state, ALIVE
    jne .bottom_center
    add neighbours, 1
.bottom_center:
    add neighbour_cell, 1
    loadb state, [neighbour_cell]
    cmp state, ALIVE
    jne .bottom_right
    add neighbours, 1
.bottom_right:
    add neighbour_cell, 1
    loadb state, [neighbour_cell]
    cmp state, ALIVE
    jne .apply_rules
    add neighbours, 1
.apply_rules:
    loadb state, [current_cell]
    cmp state, ALIVE
    jne .dead
.alive:
    cmp neighbours, 2                           ; Living cell with < 2 neighbours dies (underpopulation)
    jlt .set_dead
    cmp neighbours, 3                           ; Living cell with > 3 neighbours dies (overpopulation)
    jgt .set_dead
    jmp .set_new_state
.dead:
    cmp neighbours, 3                           ; Dead cell with 3 neighbours lives (reproduction)
    jne .set_new_state
.set_living:
    mov state, ALIVE
    jmp .set_new_state
.set_dead:
    mov state, DEAD
.set_new_state:
    storeb state, [new_cell]
    ; call print_neighbours
    add current_cell, 1                         ; Advance to next cell
    add new_cell, 1
    sub x_counter, 1
    jnz .x_loop
    add current_cell, 2
    add new_cell, 2
    sub y_counter, 1
    jnz .y_loop
.end:
    ret

@let state_buffer_addr = r0
@let display_buffer_addr = r1
@let x_counter = r2
@let y_counter = r3
@let state = r5
copy_state_to_display:
    load state_buffer_addr, [new_state_buffer]  ; Index of (1,1) in state buffer
    add state_buffer_addr, 83 ; WIDTH+3
    load display_buffer_addr, [back_buffer]     ; Index of (0,0) in display buffer
    mov y_counter, HEIGHT
.y_loop:
    mov x_counter, WIDTH
.x_loop:
    load state, [state_buffer_addr]             ; Write state into back buffer, two cells at a time
    store state, [display_buffer_addr]
    add state_buffer_addr, 2                    ; Advance to next cell pair
    add display_buffer_addr, 2
    sub x_counter, 2
    jnz .x_loop
    add state_buffer_addr, 2                    ; Advance to next row
    sub y_counter, 1
    jnz .y_loop
.end:
    ret

@let buffer_a = r0
@let buffer_b = r1
swap_buffers:
    load buffer_a, [current_state_buffer]       ; Swap state buffers
    load buffer_b, [new_state_buffer]
    store buffer_a, [new_state_buffer]
    store buffer_b, [current_state_buffer]
    load buffer_a, [front_buffer]               ; Swap display buffers
    load buffer_b, [back_buffer]
    store buffer_a, [back_buffer]
    store buffer_b, [front_buffer]
    store buffer_b, CONSOLE_BASE_REG            ; Point console to new front buffer
    ret

@let new_cell = r1
@let neighbours = r4
print_neighbours:                               ; Debug function to print the amount of living neighbours around each cell. Call after "calculate_neighbours"
    add neighbours, '0'                         ; Convert number to ASCII
    storeb neighbours, [new_cell]
    ret

@let cell_addr = r0
@let pattern = r1
@let state = r5
load_pattern:
    mov state, ALIVE
    mov pattern, glider_gun                     ; Load pattern pointer
    ; mov pattern, glider
.loop:
    load cell_addr, [pattern]                   ; Load current cell
    jz .done                                    ; Look for 0x0000 at end of pattern
    add cell_addr, STATE_BUFFER_B               ; Add offset to get the actual address
    storeb state, [cell_addr]
    add pattern, 2                              ; Advance to next cell in pattern
    jmp .loop
.done:
    ret

glider:
    @data 0x00, 0x54, 0x00, 0xA7, 0x00, 0xF7, 0x00, 0xF8, 0x00, 0xF9
    @data 0x00, 0x00
glider_gun:
    @data 0x00, 0x6B, 0x00, 0xBB, 0x00, 0xBD, 0x01, 0x03, 0x01, 0x04, 0x01, 0x0B, 0x01, 0x0C, 0x01, 0x19
    @data 0x01, 0x1A, 0x01, 0x54, 0x01, 0x58, 0x01, 0x5D, 0x01, 0x5E, 0x01, 0x6B, 0x01, 0x6C, 0x01, 0x9B
    @data 0x01, 0x9C, 0x01, 0xA5, 0x01, 0xAB, 0x01, 0xAF, 0x01, 0xB0, 0x01, 0xED, 0x01, 0xEE, 0x01, 0xF7
    @data 0x01, 0xFB, 0x01, 0xFD, 0x01, 0xFE, 0x02, 0x03, 0x02, 0x05, 0x02, 0x49, 0x02, 0x4F, 0x02, 0x57
    @data 0x02, 0x9C, 0x02, 0xA0, 0x02, 0xEF, 0x02, 0xF0
    @data 0x00, 0x00