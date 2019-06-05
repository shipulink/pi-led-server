.syntax unified

.text

.global read_buffer
.align 2
read_buffer:
    PUSH {FP, LR}

    MOV  R3, R0
    ADD  R3, R3, #0

    MOV  R2, #0
A1: LDR  R0, =string
    LDRB R1, [R3, R2]
    PUSH {R1, R2, R3, LR}
    BL   printf
    POP  {R1, R2, R3, LR}
    ADD  R2, R2, #1
    CMP  R1, #0
    BNE  A1

    POP  {FP, PC}

.global init_gpio
init_gpio:
@ Save state (Because we're calling functions with BL)
    PUSH {FP, LR}

@ Set pin 3 mode to output
@ Read, modify, write first register (GPFSEL0)
    MOV R3, R0
    ADD R3, R3, #0x0        @ Offset to the correct register
    LDR R2, [R3]            @ Read contents of register
    ORR R2, R2, #0b001<<9   @ Shift by 9, so we're affecting bits 9-11 (pin 3)
    STR R2, [R3]            @ Write

    BL clear_pin

@ Restore state
    POP {FP, PC}

.global send_byte_array
@ R0: GPIO address
@ R1: Color byte array address
@ R2: size
send_byte_array:
    PUSH {FP, LR}

    MOV  R3, #0
BA1:PUSH {R0, R1, R2, R3}
    LDRB R1, [R1, R3]
    BL   send_byte
    POP  {R0, R1, R2, R3}
    ADD  R3, R3, #1
    CMP  R3, R2
    BNE  BA1

    BL   latch

    POP  {FP, PC}

.global send_byte
@ Sends the byte in R0 to pin 3
send_byte:
    PUSH {FP, LR}

    MOV  R2, #1
    MOV  R3, R1
B1: AND  R4, R3, R2

    CMP  R4, R2
    PUSH {R2, R3, R4, R5}
    BLEQ send_one
    POP  {R2, R3, R4, R5}
    CMP  R4, R2
    PUSH {R2, R3, R4, R5}
    BLNE send_zero
    POP  {R2, R3, R4, R5}
    MOV  R2, R2, LSL #1
    CMP  R2, #256
    BNE  B1

    POP  {FP, PC}

.global send_zero
send_zero:
    PUSH {FP, LR}

    BL    set_pin
    MOV   R1, #85
L1: SUBS  R1, R1, #1
    BNE   L1

    BL    clear_pin
    MOV   R1, #165
L2: SUBS  R1, R1, #1
    BNE   L2

    POP  {FP, PC}

.global send_one
send_one:
    PUSH {FP, LR}

    BL    set_pin
    MOV   R1, #200
L3: SUBS  R1, R1, #1
    BNE   L3

    BL    clear_pin
    MOV   R1, #165
L4: SUBS  R1, R1, #1
    BNE   L4

    POP  {FP, PC}

.global  latch
@ Wait a little over 6 us
latch:
    PUSH {FP, LR}
    MOV  R1, #0x800
L5: SUBS R1, R1, #1
    BNE  L5
    POP  {FP, PC}

.global  set_pin
set_pin:
@ Save state
    PUSH {FP, LR}

@ Set pin 3
    MOV R3, R0
    ADD R3, R3, #0x1C       @ Offset to GPSET0
    LDR R2, [R3]            @ Read contents of GPSET0
    ORR R2, R2, #1<<3       @ Shift by 3, so we're affecting bit 3 (pin 3)
    STR R2, [R3]            @ Write to GPSET0

@ Restore state
    POP {FP, PC}

.global  clear_pin
clear_pin:
@ Save state
    PUSH {FP, LR}

@ Clear pin 3
    MOV R3, R0
    ADD R3, R3, #0x28       @ Offset to GPCLR0
    LDR R2, [R3]            @ Read contents of GPCLR0
    ORR R2, R2, #1<<3       @ Shift by 3, so we're affecting bit 3 (pin 3)
    STR R2, [R3]            @ Write to GPCLR0

@ Restore state
    POP {FP, PC}

gpio_file:  .word   gpio_path               @ GPIO memory access file
gpio_start: .word   0x20200000              @ Physical memory address of first GPIO register
flags:      .word   0x00101002              @ Flags for opening the gpio_file

.data
string:     .asciz  "%u\n"
gpio_path:  .ascii  "/dev/gpiomem"          @ GPIO memory access filename