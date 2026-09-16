/* What every program in Part II has, and nothing more.
 *
 * There is no C library here. `printf` is somebody else's code calling `write`, which is a system
 * call, which needs a kernel — and the whole point of this part is that there is not one. So the
 * console below is thirty lines that put a byte in a device register, and the formatting is the
 * least that makes the programs readable.
 */
#ifndef BARE_H
#define BARE_H

typedef unsigned char uint8;
typedef unsigned int uint32;
typedef unsigned long uint64;
typedef long int64;

/* Pasting a compile-time constant into an assembly string, so a frame size is stated
 * once and the stores that use it cannot drift from it. */
#define _STRINGIFY(x) #x
#define _TOSTRING(x) _STRINGIFY(x)

#define BARE_STACK_BYTES 4096
#define BARE_PAGE_BYTES 4096

/* QEMU's `virt` board, from its own documentation. Neither address is negotiable: they are where
 * the board puts these devices, and a program with no firmware under it has nobody to ask. */
#define BARE_UART_BASE 0x10000000UL
#define BARE_FINISHER_BASE 0x100000UL

/* Console. */
void bare_putc(char c);
void bare_print(const char *s);
void bare_printf(const char *fmt, ...);

/* Stop the machine. QEMU's `virt` board exits when the test finisher is written, which is the
 * only way a program with no operating system can end other than by spinning for ever. */
void bare_exit(void);

/* Each program's body. hart 0 calls main(); any other hart calls bare_secondary(), which parks
 * unless the program defines its own. */
int main(void);
void bare_secondary(uint64 hartid);

/* A handler declared `interrupt("machine")` must not call another function.
 *
 * The compiler's prologue for such a function saves what *it* uses; a call makes the whole
 * caller-saved set live, and on this target the result is not a diagnostic but a machine that
 * stops taking interrupts at all. Handlers here therefore record what happened in a global and
 * let `main` do the printing, which is also the shape a real kernel's handlers have and for a
 * related reason: a handler is not a good place to be doing anything slow.
 */

/* Leaving machine mode, and getting back.
 *
 * Machine mode drops to supervisor mode with `mret`, and comes back only through a trap. So the
 * way back has to be arranged before leaving: the address to resume at, and — the part that is
 * easy to miss and hard to diagnose — the stack pointer to resume with.
 *
 * `mret` restores no registers at all. The handler that brings us back has just reloaded the
 * *supervisor* caller's whole register set from its frame, so at the resume label every register
 * holds somebody else's value — `sp` points into the supervisor code's stack, and `ra` is the
 * supervisor code's return address. A machine-mode function that resumes and then returns is
 * jumping wherever that other program was going to.
 *
 * So `sp` and `ra` are put back explicitly, and everything else is declared clobbered, which
 * makes the compiler spill anything it was keeping in a register to the stack — where the stack
 * is the one this macro just restored. That is a context switch with the interesting parts taken
 * out, and the scheduling chapter is the version with them left in.
 */
extern volatile uint64 bare_resume_at;
extern volatile uint64 bare_resume_sp;
extern volatile uint64 bare_resume_ra;

#define bare_enter_supervisor()                                             \
    asm volatile("la   t0, 8f\n"                                            \
                 "sd   t0, bare_resume_at, t1\n"                            \
                 "sd   sp, bare_resume_sp, t1\n"                            \
                 "sd   ra, bare_resume_ra, t1\n"                            \
                 "mret\n"                                                   \
                 "8:\n"                                                     \
                 "ld   sp, bare_resume_sp\n"                                \
                 "ld   ra, bare_resume_ra\n"                                \
                 :                                                          \
                 :                                                          \
                 : "t0", "t1", "t2", "t3", "t4", "t5", "t6", "memory",       \
                   "a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7",           \
                   "s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7",           \
                   "s8", "s9", "s10", "s11")

/* Open all of memory to supervisor and user mode.
 *
 * With no firmware in front of the program every PMP region starts closed, and closed means
 * closed to every mode but machine. Without this a supervisor-mode program faults on its first
 * instruction, for a reason that has nothing to do with what it was trying to do. */
#define bare_open_memory()                                     \
    do {                                                       \
        bare_csr_write(pmpaddr0, 0x3fffffffffffffUL);          \
        bare_csr_write(pmpcfg0, 0xf);                          \
    } while (0)

/* The shared system-call layer (sysfs/bare/syscalls.c), for the programs that need calls and
 * are not about calls. `bare_syscall` is what a program supplies; everything else is the bare-metal system-call chapter's. */
#define BARE_SYS_LEAVE 0 /* return to machine mode; every program's last call */

void bare_trap_entry(void);
void bare_run_in_supervisor(void (*entry)(void));
uint64 bare_call(uint64 number, uint64 a, uint64 b, uint64 c);
uint64 bare_syscall(uint64 number, uint64 *frame);
void bare_process_left(void);
extern uint64 bare_trap_was_unexpected;

/* Entered from start.S. */
void bare_start(uint64 hartid);
void bare_park(void);

/* Reading and writing a control and status register by name, without inline asm at every use.
 * `csr` is pasted into the instruction, so it must be a literal — which is why this is a macro
 * and not a function. */
#define bare_csr_read(csr)                                     \
    ({                                                         \
        uint64 __v;                                            \
        asm volatile("csrr %0, " #csr : "=r"(__v));            \
        __v;                                                   \
    })

#define bare_csr_write(csr, value)                             \
    do {                                                       \
        uint64 __v = (value);                                  \
        asm volatile("csrw " #csr ", %0" : : "r"(__v));        \
    } while (0)

#define bare_csr_set(csr, bits)                                \
    do {                                                       \
        uint64 __v = (bits);                                   \
        asm volatile("csrs " #csr ", %0" : : "r"(__v));        \
    } while (0)

#define bare_csr_clear(csr, bits)                              \
    do {                                                       \
        uint64 __v = (bits);                                   \
        asm volatile("csrc " #csr ", %0" : : "r"(__v));        \
    } while (0)

#endif /* BARE_H */
