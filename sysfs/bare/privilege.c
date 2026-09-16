/* The bare-metal privilege chapter: what arrives without being asked for, and what a privilege level actually refuses.
 *
 * Two things happen here that the bare-metal trap chapter's trap did not. The first arrives on its own — nothing in the
 * program asked for it and no instruction caused it. The second is a refusal: the same
 * instruction that worked a moment ago stops working, because the processor is in a different
 * mode and the mode is the whole of the difference.
 */
#include "bare.h"

/* The core-local interruptor, at the address QEMU's `virt` board puts it. `mtime` counts up on
 * its own; when it reaches `mtimecmp` the processor takes a timer interrupt. That is the entire
 * mechanism, and it is the one every scheduler in the world is built on. */
#define CLINT_BASE 0x02000000UL
#define CLINT_MTIMECMP (CLINT_BASE + 0x4000)
#define CLINT_MTIME (CLINT_BASE + 0xBFF8)

#define MSTATUS_MIE (1UL << 3)   /* machine interrupts enabled at all */
#define MSTATUS_MPP (3UL << 11)  /* the mode mret will return to */
#define MSTATUS_MPP_S (1UL << 11)
#define MSTATUS_MPP_M (3UL << 11)
#define MIE_MTIE (1UL << 7) /* this particular interrupt */

#define CAUSE_INTERRUPT (1UL << 63) /* the top bit says asynchronous */
#define CAUSE_ILLEGAL_INSTRUCTION 2

enum phase { PHASE_TIMER, PHASE_SUPERVISOR, PHASE_BACK };

static volatile enum phase phase = PHASE_TIMER;
static volatile uint64 interrupt_cause;
static volatile uint64 interrupt_epc;
static volatile uint64 spins_before_interrupt;
static volatile uint64 refusal_cause;
static volatile int refused;
static volatile uint64 unexpected;

/* Supervisor mode tries to read a machine-mode register. Naked because it is not a function the
 * C world calls or returns from — it is entered by `mret` and left by trapping. */
__attribute__((naked, aligned(4))) static void supervisor_probe(void) {
    asm volatile("csrr t0, mhartid\n" /* 0xF14: machine mode only. This is the refusal. */
                 "j    .\n");         /* never reached, and says so if it ever is */
}

__attribute__((interrupt("machine"), aligned(4))) static void handler(void) {
    uint64 cause = bare_csr_read(mcause);

    if (cause & CAUSE_INTERRUPT) {
        /* An interrupt's mepc is wherever the program happened to be. There is no instruction
         * that "caused" it, so unlike the bare-metal trap chapter's trap there is nothing to advance past. */
        interrupt_cause = cause;
        interrupt_epc = bare_csr_read(mepc);
        bare_csr_clear(mie, MIE_MTIE); /* once is the demonstration; twice is a loop */
        return;
    }

    if (phase == PHASE_SUPERVISOR) {
        refusal_cause = cause;
        refused = 1;
        /* Go back to machine mode, at the instruction after the `mret` that left it. Changing
         * MPP is how a handler decides which mode it is returning *to* — the same field that
         * dropped us into supervisor mode brings us back out. */
        bare_csr_clear(mstatus, MSTATUS_MPP);
        bare_csr_set(mstatus, MSTATUS_MPP_M);
        bare_csr_write(mepc, bare_resume_at);
        phase = PHASE_BACK;
        return;
    }

    /* An exception nobody planned for. Record it; main stops rather than return into it. */
    unexpected = bare_csr_read(mcause);
    bare_csr_write(mepc, bare_csr_read(mepc) + 4);
}

static void wait_for_the_timer(void) {
    volatile uint64 *mtime = (volatile uint64 *)CLINT_MTIME;
    volatile uint64 *mtimecmp = (volatile uint64 *)CLINT_MTIMECMP;

    bare_csr_write(mtvec, (uint64)handler);
    *mtimecmp = *mtime + 100000;
    bare_csr_set(mie, MIE_MTIE);
    bare_csr_set(mstatus, MSTATUS_MIE);

    /* This loop asks for nothing. It reads no device, executes no `ecall`, and would run for
     * ever left alone. The interrupt is what stops it. */
    while (interrupt_cause == 0) {
        spins_before_interrupt++;
    }
    bare_csr_clear(mstatus, MSTATUS_MIE);
}

static void be_refused(void) {
    bare_open_memory();
    phase = PHASE_SUPERVISOR;
    bare_csr_write(mepc, (uint64)supervisor_probe);
    bare_csr_clear(mstatus, MSTATUS_MPP);
    bare_csr_set(mstatus, MSTATUS_MPP_S);

    /* `la` before `mret`, in one asm block, so the label is the instruction the handler sends us
     * back to. Split across two statements the compiler is entitled to put anything in between. */
    bare_enter_supervisor();
}

int main(void) {
    wait_for_the_timer();
    be_refused();

    bare_printf("privilege interrupt_arrived %d\n", interrupt_cause != 0);
    bare_printf("privilege cause_is_asynchronous %d\n",
                (interrupt_cause & CAUSE_INTERRUPT) != 0);
    bare_printf("privilege interrupt_code %d\n", interrupt_cause & 0xff);
    bare_printf("privilege nothing_asked_for_it %d\n", spins_before_interrupt > 0);
    bare_printf("privilege dropped_to_supervisor %d\n", refused);
    bare_printf("privilege machine_register_refused %d\n", refused);
    bare_printf("privilege refusal_code %d\n", refusal_cause);
    bare_printf("privilege refusal_is_illegal_instruction %d\n",
                refusal_cause == CAUSE_ILLEGAL_INSTRUCTION);
    bare_printf("privilege back_in_machine_mode %d\n", phase == PHASE_BACK);
    bare_print("end privilege\n");
    return 0;
}
