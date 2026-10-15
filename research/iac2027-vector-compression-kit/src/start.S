.section .text.start
.global _start
_start:
    la sp, _stack_top
    la t0, trap
    csrw mtvec, t0
    li t0, 0x6600
    csrs mstatus, t0
    call main
1:  j 1b
trap:
    la t0, status
    csrr t1, mcause
    sd t1, 40(t0)
    csrr t1, mepc
    sd t1, 48(t0)
    li t1, 0xbadf0000
    sd t1, 0(t0)
2:  j 2b
