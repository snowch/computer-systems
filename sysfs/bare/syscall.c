/* ch07: what has to exist before `ecall` is a system call rather than a trap.
 *
 * ch04's handler knew its caller: the same function, a few instructions earlier, compiled at the
 * same time. The compiler could therefore work out which registers mattered and save exactly
 * those. Here the caller is a stranger — it runs in a different privilege mode and the handler
 * has no idea which registers it was using — so the handler saves all of them, by hand, because
 * there is nobody left to work it out for you.
 *
 * On top of that: a number saying which call, somewhere to put arguments, somewhere to put a
 * result, and a dispatch. Those four things are the difference between a trap and an API.
 */
#include "bare.h"

#define FRAME_REGISTERS 31 /* x1..x31. x0 is hard-wired zero and has nothing to save. */
#define FRAME_BYTES 256

#define SYS_ADD 1
#define SYS_WITNESS 2
#define SYS_LEAVE 3
#define SYS_UNKNOWN_RESULT ((uint64)-1)

#define MSTATUS_MPP (3UL << 11)
#define MSTATUS_MPP_S (1UL << 11)
#define MSTATUS_MPP_M (3UL << 11)
#define CAUSE_ECALL_FROM_S 9

static volatile uint64 calls_dispatched;
static volatile uint64 unknown_calls_refused;
static volatile int saw_unknown_number;
static volatile uint64 last_arguments;

void syscall_dispatch(uint64 *frame);

/* The trap entry. Naked because every instruction in it matters and a prologue the compiler
 * chose would run before the caller's registers had been saved.
 *
 * This is the file's whole point, so it is spelled out rather than generated: thirty-one stores
 * on the way in and thirty-one loads on the way out, and the only reason it is not thirty-two is
 * that x0 cannot hold anything to lose. */
__attribute__((naked, aligned(4))) static void syscall_entry(void) {
    asm volatile(
        ".macro SAVE reg, slot\n"
        "  sd \\reg, \\slot*8(sp)\n"
        ".endm\n"
        ".macro LOAD reg, slot\n"
        "  ld \\reg, \\slot*8(sp)\n"
        ".endm\n"

        "addi sp, sp, -" _TOSTRING(FRAME_BYTES) "\n"

        "SAVE x1,1\n  SAVE x3,3\n  SAVE x4,4\n  SAVE x5,5\n  SAVE x6,6\n  SAVE x7,7\n"
        "SAVE x8,8\n  SAVE x9,9\n  SAVE x10,10\n SAVE x11,11\n SAVE x12,12\n SAVE x13,13\n"
        "SAVE x14,14\n SAVE x15,15\n SAVE x16,16\n SAVE x17,17\n SAVE x18,18\n SAVE x19,19\n"
        "SAVE x20,20\n SAVE x21,21\n SAVE x22,22\n SAVE x23,23\n SAVE x24,24\n SAVE x25,25\n"
        "SAVE x26,26\n SAVE x27,27\n SAVE x28,28\n SAVE x29,29\n SAVE x30,30\n SAVE x31,31\n"
        /* x2 is sp, and its caller's value is this frame's address plus the frame size. Storing
         * it too makes the count thirty-one rather than thirty, and makes the frame a complete
         * description of the caller rather than nearly one. */
        "addi t0, sp, " _TOSTRING(FRAME_BYTES) "\n"
        "sd   t0, 2*8(sp)\n"

        "mv   a0, sp\n"
        "call syscall_dispatch\n"

        "LOAD x1,1\n  LOAD x3,3\n  LOAD x4,4\n  LOAD x5,5\n  LOAD x6,6\n  LOAD x7,7\n"
        "LOAD x8,8\n  LOAD x9,9\n  LOAD x10,10\n LOAD x11,11\n LOAD x12,12\n LOAD x13,13\n"
        "LOAD x14,14\n LOAD x15,15\n LOAD x16,16\n LOAD x17,17\n LOAD x18,18\n LOAD x19,19\n"
        "LOAD x20,20\n LOAD x21,21\n LOAD x22,22\n LOAD x23,23\n LOAD x24,24\n LOAD x25,25\n"
        "LOAD x26,26\n LOAD x27,27\n LOAD x28,28\n LOAD x29,29\n LOAD x30,30\n LOAD x31,31\n"

        "addi sp, sp, " _TOSTRING(FRAME_BYTES) "\n"
        "mret\n");
}

void syscall_dispatch(uint64 *frame) {
    uint64 cause = bare_csr_read(mcause);
    uint64 number = frame[17]; /* a7, by convention — the convention is this line */
    uint64 first = frame[10];  /* a0 */
    uint64 second = frame[11]; /* a1 */

    if (cause != CAUSE_ECALL_FROM_S) {
        frame[10] = SYS_UNKNOWN_RESULT;
        bare_csr_write(mepc, bare_csr_read(mepc) + 4);
        return;
    }

    calls_dispatched++;
    last_arguments = first + second;

    switch (number) {
    case SYS_ADD:
        frame[10] = first + second;
        break;
    case SYS_WITNESS:
        frame[10] = frame[18]; /* s2, read out of the saved frame rather than out of the CPU */
        break;
    case SYS_LEAVE:
        bare_csr_clear(mstatus, MSTATUS_MPP);
        bare_csr_set(mstatus, MSTATUS_MPP_M);
        bare_csr_write(mepc, bare_resume_at);
        return; /* deliberately without advancing: mepc is the address we are going to */
    default:
        /* A number nobody implemented is a refusal, not a crash. Returning an error is what
         * makes this an interface rather than a trapdoor. */
        unknown_calls_refused++;
        saw_unknown_number = (number == 99);
        frame[10] = SYS_UNKNOWN_RESULT;
        break;
    }

    /* `ecall` traps with mepc pointing at the ecall itself, exactly as ch04's did. Four bytes on
     * is the instruction after it, which is where the caller expects to continue. */
    bare_csr_write(mepc, bare_csr_read(mepc) + 4);
}

static volatile uint64 add_result;
static volatile uint64 witness_result;
static volatile uint64 unknown_result;
static volatile uint64 witness_after;

static uint64 call(uint64 number, uint64 first, uint64 second) {
    register uint64 a0 asm("a0") = first;
    register uint64 a1 asm("a1") = second;
    register uint64 a7 asm("a7") = number;
    asm volatile("ecall" : "+r"(a0) : "r"(a1), "r"(a7) : "memory");
    return a0;
}

__attribute__((noinline)) static void user_of_the_interface(void) {
    asm volatile("li s2, 0x1234" : : : "s2");

    add_result = call(SYS_ADD, 3, 4);
    witness_result = call(SYS_WITNESS, 0, 0);
    unknown_result = call(99, 0, 0);

    asm volatile("mv %0, s2" : "=r"(witness_after) : : );
    call(SYS_LEAVE, 0, 0);
}

int main(void) {
    bare_csr_write(mtvec, (uint64)syscall_entry);
    bare_open_memory();

    bare_csr_write(mepc, (uint64)user_of_the_interface);
    bare_csr_clear(mstatus, MSTATUS_MPP);
    bare_csr_set(mstatus, MSTATUS_MPP_S);
    bare_enter_supervisor();

    bare_printf("syscall registers_in_frame %d\n", FRAME_REGISTERS);
    bare_printf("syscall calls_dispatched %d\n", calls_dispatched);
    bare_printf("syscall number_crossed %d\n", saw_unknown_number);
    bare_printf("syscall arguments_crossed %d\n", add_result == 7);
    bare_printf("syscall result_returned %d\n", add_result);
    bare_printf("syscall caller_register_in_frame %d\n", witness_result == 0x1234);
    bare_printf("syscall caller_register_intact %d\n", witness_after == 0x1234);
    bare_printf("syscall unknown_call_refused %d\n", unknown_calls_refused);
    bare_printf("syscall unknown_returned_error %d\n", unknown_result == SYS_UNKNOWN_RESULT);
    bare_print("end syscall\n");
    return 0;
}
