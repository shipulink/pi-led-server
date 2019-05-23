.syntax unified

.text

.align 2
.global main
main:
    PUSH  {FP, LR}

    BL    init_gpio@PLT

L1: BL    send_one@PLT
    B     L1

    BL    release_gpio@PLT
    POP   {FP, LR}
    MOV   R0, #0
    BX    LR