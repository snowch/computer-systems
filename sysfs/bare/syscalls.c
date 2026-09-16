/* The bare-metal system-call chapter's mechanism, tidied and shared.
 *
 * The descriptors chapter and the fork chapter need system calls and are not about system calls, so the entry stub the bare-metal system-call chapter spells
 * out instruction by instruction lives here once. It is the same code: a full frame saved by
 * hand, a dispatch on a7, a result in a0, and mepc advanced past the `ecall`.
 *
 * What a program supplies is `bare_syscall`, and that is the whole interface — which is itself
 * the bare-metal system-call chapter's lesson stated in a build system: once the boundary exists, what crosses it is a
 * number and some registers, and both sides can be written without knowing the other.
 */
#include "bare.h"

#define FRAME_BYTES 256
#define CAUSE_ECALL_FROM_S 9

#define MSTATUS_MPP (3UL << 11)
#define MSTATUS_MPP_S (1UL << 11)
#define MSTATUS_MPP_M (3UL << 11)

void bare_syscall_dispatch(uint64 *frame);

/* A program with more than one process supplies this; the rest do not. */
__attribute__((weak)) void bare_process_left(void) {}

__attribute__((naked, aligned(4))) void bare_trap_entry(void) {
    asm volatile(".macro SAVE reg, slot\n  sd \\reg, \\slot*8(sp)\n.endm\n"
                 ".macro LOAD reg, slot\n  ld \\reg, \\slot*8(sp)\n.endm\n"

                 "addi sp, sp, -" _TOSTRING(FRAME_BYTES) "\n"
                 "SAVE x1,1\n  SAVE x3,3\n  SAVE x4,4\n  SAVE x5,5\n  SAVE x6,6\n  SAVE x7,7\n"
                 "SAVE x8,8\n  SAVE x9,9\n  SAVE x10,10\n SAVE x11,11\n SAVE x12,12\n"
                 "SAVE x13,13\n SAVE x14,14\n SAVE x15,15\n SAVE x16,16\n SAVE x17,17\n"
                 "SAVE x18,18\n SAVE x19,19\n SAVE x20,20\n SAVE x21,21\n SAVE x22,22\n"
                 "SAVE x23,23\n SAVE x24,24\n SAVE x25,25\n SAVE x26,26\n SAVE x27,27\n"
                 "SAVE x28,28\n SAVE x29,29\n SAVE x30,30\n SAVE x31,31\n"
                 "addi t0, sp, " _TOSTRING(FRAME_BYTES) "\n"
                 "sd   t0, 2*8(sp)\n"

                 "mv   a0, sp\n"
                 "call bare_syscall_dispatch\n"

                 "LOAD x1,1\n  LOAD x3,3\n  LOAD x4,4\n  LOAD x5,5\n  LOAD x6,6\n  LOAD x7,7\n"
                 "LOAD x8,8\n  LOAD x9,9\n  LOAD x10,10\n LOAD x11,11\n LOAD x12,12\n"
                 "LOAD x13,13\n LOAD x14,14\n LOAD x15,15\n LOAD x16,16\n LOAD x17,17\n"
                 "LOAD x18,18\n LOAD x19,19\n LOAD x20,20\n LOAD x21,21\n LOAD x22,22\n"
                 "LOAD x23,23\n LOAD x24,24\n LOAD x25,25\n LOAD x26,26\n LOAD x27,27\n"
                 "LOAD x28,28\n LOAD x29,29\n LOAD x30,30\n LOAD x31,31\n"
                 "addi sp, sp, " _TOSTRING(FRAME_BYTES) "\n"
                 "mret\n");
}

void bare_syscall_dispatch(uint64 *frame) {
    if (bare_csr_read(mcause) != CAUSE_ECALL_FROM_S) {
        /* Anything that is not a system call is, for these programs, a bug in the program.
         * Returning to it would loop; going back to machine mode reports it instead. */
        bare_csr_clear(mstatus, MSTATUS_MPP);
        bare_csr_set(mstatus, MSTATUS_MPP_M);
        bare_csr_write(mepc, bare_resume_at);
        bare_trap_was_unexpected = bare_csr_read(mcause);
        return;
    }

    if (frame[17] == BARE_SYS_LEAVE) {
        bare_process_left(); /* if another process is waiting, this does not return */
        bare_csr_clear(mstatus, MSTATUS_MPP);
        bare_csr_set(mstatus, MSTATUS_MPP_M);
        bare_csr_write(mepc, bare_resume_at);
        return;
    }

    frame[10] = bare_syscall(frame[17], frame);
    bare_csr_write(mepc, bare_csr_read(mepc) + 4);
}

uint64 bare_trap_was_unexpected;

void bare_run_in_supervisor(void (*entry)(void)) {
    bare_csr_write(mtvec, (uint64)bare_trap_entry);
    bare_open_memory();
    bare_csr_write(mepc, (uint64)entry);
    bare_csr_clear(mstatus, MSTATUS_MPP);
    bare_csr_set(mstatus, MSTATUS_MPP_S);
    bare_enter_supervisor();
}

uint64 bare_call(uint64 number, uint64 a, uint64 b, uint64 c) {
    register uint64 a0 asm("a0") = a;
    register uint64 a1 asm("a1") = b;
    register uint64 a2 asm("a2") = c;
    register uint64 a7 asm("a7") = number;
    asm volatile("ecall" : "+r"(a0) : "r"(a1), "r"(a2), "r"(a7) : "memory");
    return a0;
}

/* Put a saved process back on the processor: its registers, and where it was.
 *
 * `sp` is loaded last because every other load is relative to it, and a frame is not somewhere
 * you can still address once you have replaced the pointer to it. */
__attribute__((naked)) void bare_enter_process(uint64 *frame, uint64 epc) {
    asm volatile("csrw mepc, a1\n"
                 "mv   sp, a0\n"
                 "ld x1,1*8(sp)\n  ld x3,3*8(sp)\n  ld x4,4*8(sp)\n  ld x5,5*8(sp)\n"
                 "ld x6,6*8(sp)\n  ld x7,7*8(sp)\n  ld x8,8*8(sp)\n  ld x9,9*8(sp)\n"
                 "ld x10,10*8(sp)\n ld x11,11*8(sp)\n ld x12,12*8(sp)\n ld x13,13*8(sp)\n"
                 "ld x14,14*8(sp)\n ld x15,15*8(sp)\n ld x16,16*8(sp)\n ld x17,17*8(sp)\n"
                 "ld x18,18*8(sp)\n ld x19,19*8(sp)\n ld x20,20*8(sp)\n ld x21,21*8(sp)\n"
                 "ld x22,22*8(sp)\n ld x23,23*8(sp)\n ld x24,24*8(sp)\n ld x25,25*8(sp)\n"
                 "ld x26,26*8(sp)\n ld x27,27*8(sp)\n ld x28,28*8(sp)\n ld x29,29*8(sp)\n"
                 "ld x30,30*8(sp)\n ld x31,31*8(sp)\n"
                 "ld x2,2*8(sp)\n"
                 "mret\n");
}
