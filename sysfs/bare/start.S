# The first instructions on the machine, and the only assembly this part needs you to write.
#
# Three things have to be true before C can run, and at reset none of them is: there is a stack
# pointer, the zero-initialised data is actually zero, and the harts that are not doing that
# setup are kept out of the way while it happens. Everything after this file is C.

        .section .text.entry
        .globl _entry
_entry:
        csrr    t0, mhartid             # QEMU releases every hart here, at the same instant

        # sp = bare_stacks + (hartid + 1) * BARE_STACK_BYTES. Each hart gets its own and they
        # grow down into it. Two harts sharing one stack looks exactly like memory corruption.
        la      sp, bare_stacks
        li      t1, 4096
        addi    t2, t0, 1
        mul     t1, t1, t2
        add     sp, sp, t1

        bnez    t0, wait_for_hart0

        # Zero the bss. No loader has done it, and C is entitled to assume it.
        la      t3, bare_bss_start
        la      t4, bare_bss_end
zero:
        bgeu    t3, t4, zeroed
        sd      zero, 0(t3)
        addi    t3, t3, 8
        j       zero
zeroed:
        fence   w, w                    # the zeroes land before the flag that announces them
        la      t3, bare_ready
        li      t4, 1
        sw      t4, 0(t3)
        j       enter

        # A secondary hart that ran ahead would read uninitialised globals and blame C for it.
        # This flag lives in .data precisely so that it is not itself waiting to be zeroed.
wait_for_hart0:
        la      t3, bare_ready
1:      lw      t4, 0(t3)
        beqz    t4, 1b
        fence   r, r

enter:
        mv      a0, t0
        call    bare_start              # does not return

        .globl bare_park
bare_park:
        wfi
        j       bare_park

        .section .data
        .globl bare_ready
        .align 2
bare_ready:
        .word 0
