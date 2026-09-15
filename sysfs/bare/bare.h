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
 * `mret` does not restore a stack. The supervisor-mode code runs on the same stack and leaves it
 * deeper than it found it, and the handler's own entry and exit move it again, so a machine-mode
 * function that resumes without putting `sp` back is running its own epilogue against somebody
 * else's frame. It does not fault. It returns to whatever that frame happened to contain.
 */
extern volatile uint64 bare_resume_at;
extern volatile uint64 bare_resume_sp;

#define bare_enter_supervisor()                                \
    asm volatile("la   t0, 8f\n"                               \
                 "sd   t0, bare_resume_at, t1\n"               \
                 "sd   sp, bare_resume_sp, t1\n"               \
                 "mret\n"                                      \
                 "8:\n"                                        \
                 "ld   sp, bare_resume_sp\n"                   \
                 :                                             \
                 :                                             \
                 : "t0", "t1", "memory")

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
