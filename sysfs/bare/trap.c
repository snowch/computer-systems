/* The bare-metal trap chapter: a trap, with nothing else in the machine.
 *
 * One handler, one deliberate trap, and every question about it answered from the machine rather
 * than from a diagram: where the processor went, which instruction it was on when it went, what
 * it left untouched, and what has to happen before it can come back.
 */
#include "bare.h"

#define CAUSE_ECALL_FROM_M 11

static volatile uint64 taken;
static volatile uint64 seen_cause;
static volatile uint64 seen_epc;

/* `interrupt("machine")` makes the compiler do two things a normal function does not: save every
 * register it touches, including the caller-saved ones an ordinary function may clobber, and end
 * with `mret` rather than `ret`. That is the whole difference between a function and a handler,
 * and the bare-metal system-call chapter is where you write it out by hand, because a handler that
 * has to read the caller's registers and change one needs them somewhere it can reach. */
__attribute__((interrupt("machine"), aligned(4))) static void handler(void) {
    taken++;
    seen_cause = bare_csr_read(mcause);
    seen_epc = bare_csr_read(mepc);

    /* mepc holds the address *of* the instruction that trapped, not the one after it. Returning
     * without moving it re-executes the ecall, which traps again, for ever. The machine does not
     * consider this an error; it is doing exactly what it was told. */
    bare_csr_write(mepc, seen_epc + 4);
}

int main(void) {
    uint64 ecall_at = 0;
    uint64 witness_after = 0;

    bare_csr_write(mtvec, (uint64)handler);

    /* s2 is set before the trap and read after it. Nothing in the trap mechanism preserves it:
     * the handler's prologue does, because the compiler was told this function is a handler. */
    asm volatile("li   s2, 0x5eed\n"
                 "la   %0, 1f\n"
                 "1:\n"
                 "ecall\n"
                 "mv   %1, s2\n"
                 : "=&r"(ecall_at), "=r"(witness_after)
                 :
                 : "s2", "memory");

    bare_printf("trap mtvec_is_handler %d\n", bare_csr_read(mtvec) == (uint64)handler);
    bare_printf("trap cause %d\n", seen_cause);
    bare_printf("trap cause_is_ecall %d\n", seen_cause == CAUSE_ECALL_FROM_M);
    bare_printf("trap mepc_is_the_ecall %d\n", seen_epc == ecall_at);
    bare_printf("trap mepc_advance %d\n", 4);
    bare_printf("trap register_survived %d\n", witness_after == 0x5eed);
    bare_printf("trap resumed %d\n", 1);
    bare_printf("trap taken %d\n", taken);
    bare_print("end trap\n");
    return 0;
}
