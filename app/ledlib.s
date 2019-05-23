.syntax unified

.text

.align 2
.global init_gpio
init_gpio:
@ Save state (Because we're calling functions with BL)
    PUSH {FP, LR}

@ Open /dev/gpiomem for read/write
    LDR R0, gpio_file       @ get GPIO Controller addr
    LDR R1, flags           @ set file-open flags
    BL  open                @ open /dev/gpiomem

@ Store file handle number in order to close it later
    MOV R4, R0

@ For mmap to work, file handle number needs to be at the top of the stack (SP):
@ R5 is just for padding, since we need 8 bytes.
    PUSH {R4, R5}

@ Build args for mmap
    MOV R0, #0              @ R0 let kernel pick device (file) mapping address
    MOV R1, #4096           @ R1 page size
    MOV R2, #3              @ R2 mode (3 = protected read/write)
    MOV R3, #1              @ R3 share virtual memory mapping? (1 = yes)

@ Map /dev/gpiomem to virtual memory
@ mmap stores the virtual memory address in R0
    BL  mmap
    POP {R4, R5}

@ Save virtual memory address for future reference
    MOV R5, R0

@ Set pin 3 mode to output
@ Read, modify, write first register (GPFSEL0)
    MOV R3, R5
    ADD R3, R3, #0x0        @ Offset to the correct register
    LDR R2, [R3]            @ Read contents of register
    ORR R2, R2, #0b001<<9   @ Shift by 9, so we're affecting bits 9-11 (pin 3)
    STR R2, [R3]            @ Write

@ Ensure write
    MOV R0, R5
    MOV R1, #4096
    MOV R2, #4              @ Wait for write to finish
    BL  msync

@ Restore state
    POP {FP, PC}

.global send_zero
send_zero:
    PUSH {FP, LR}

    BL    set_pin
    MOV   R0, #85
L1: SUBS  R0, R0, #1
    BNE   L1

    BL    clear_pin
    MOV   R0, #165
L2: SUBS  R0, R0, #1
    BNE   L2

    POP  {FP, PC}

.global send_one
send_one:
    PUSH {FP, LR}

    BL    set_pin
    MOV   R0, #200
L3: SUBS  R0, R0, #1
    BNE   L3

    BL    clear_pin
    MOV   R0, #165
L4: SUBS  R0, R0, #1
    BNE   L4

    POP  {FP, PC}

.global  set_pin
set_pin:
@ Save state
    PUSH {FP, LR}

@ Set pin 3
    MOV R3, R5
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
    MOV R3, R5
    ADD R3, R3, #0x28       @ Offset to GPCLR0
    LDR R2, [R3]            @ Read contents of GPCLR0
    ORR R2, R2, #1<<3       @ Shift by 3, so we're affecting bit 3 (pin 3)
    STR R2, [R3]            @ Write to GPCLR0

@ Restore state
    POP {FP, PC}

.global release_gpio
release_gpio:
@ Save state (because we're calling functions with BL)
    PUSH {FP, LR}

@ Unmap the virtual memory
    MOV     R0, R5          @ memory to unmap
    MOV     R1, #4096       @ amount we mapped
    BL      munmap          @ unmap it

@ Close the file
    MOV     R0, R4
    BL      close

@ Restore state
    POP {FP, PC}
@    BX LR

gpio_file:  .word   gpio_path               @ GPIO memory access file
gpio_start: .word   0x20200000              @ Physical memory address of first GPIO register
flags:      .word   0x00101002              @ Flags for opening the gpio_file

.data
gpio_path:  .ascii  "/dev/gpiomem"          @ GPIO memory access filename