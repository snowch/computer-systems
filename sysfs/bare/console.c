/* A console, a way to stop, and the C entry point. Shared by every program in Part II.
 *
 * The UART is a 16550 at a fixed address. Writing a byte to its transmit register sends it;
 * reading the line-status register says whether it is ready for another. That is the whole
 * driver, and it is worth seeing at this size once, because the interrupts-and-drivers chapter's version in the kernel is the
 * same two registers underneath a great deal of machinery about interrupts and sleeping.
 */
#include "bare.h"

#include <stdarg.h>

#define UART_THR 0 /* transmit holding register: write a byte, it goes out */
#define UART_LSR 5 /* line status register */
#define UART_LSR_THRE (1 << 5) /* transmit holding register empty */

static volatile uint8 *uart = (volatile uint8 *)BARE_UART_BASE;

void bare_putc(char c) {
    while ((uart[UART_LSR] & UART_LSR_THRE) == 0) {
        /* The device has a byte in hand. Spin: there is nothing else to do and nobody to
         * yield to. A kernel would sleep here, which is the interrupts-and-drivers chapter's subject. */
    }
    uart[UART_THR] = (uint8)c;
}

void bare_print(const char *s) {
    for (; *s; s++) {
        bare_putc(*s);
    }
}

static void print_unsigned(uint64 value, int base) {
    char digits[] = "0123456789abcdef";
    char buffer[32];
    int i = 0;

    do {
        buffer[i++] = digits[value % (uint64)base];
        value /= (uint64)base;
    } while (value != 0);

    while (i-- > 0) {
        bare_putc(buffer[i]);
    }
}

/* Enough of printf to write a readable line, and no more: %d, %u, %x, %p, %s, %c, %%.
 *
 * Deliberately not variadic-argument-promotion-correct beyond what these programs use. It is
 * thirty lines because it is scaffolding, not a subject — the subject is what the programs
 * print, not how they printed it. */
void bare_printf(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);

    for (; *fmt; fmt++) {
        if (*fmt != '%') {
            bare_putc(*fmt);
            continue;
        }
        switch (*++fmt) {
        case 'd': {
            int64 value = va_arg(ap, int64);
            if (value < 0) {
                bare_putc('-');
                value = -value;
            }
            print_unsigned((uint64)value, 10);
            break;
        }
        case 'u':
            print_unsigned(va_arg(ap, uint64), 10);
            break;
        case 'x':
            print_unsigned(va_arg(ap, uint64), 16);
            break;
        case 'p':
            bare_print("0x");
            print_unsigned(va_arg(ap, uint64), 16);
            break;
        case 's': {
            const char *s = va_arg(ap, const char *);
            bare_print(s ? s : "(null)");
            break;
        }
        case 'c':
            bare_putc((char)va_arg(ap, int));
            break;
        case '%':
            bare_putc('%');
            break;
        default:
            bare_putc('%');
            bare_putc(*fmt);
            break;
        }
    }
    va_end(ap);
}

void bare_exit(void) {
    /* SiFive test finisher: the low half is a status code, 0x5555 means "pass, shut down". A
     * program with no operating system has no exit(2) to call, and spinning for ever would make
     * every run of the harness time out rather than finish. */
    volatile uint32 *finisher = (volatile uint32 *)BARE_FINISHER_BASE;
    *finisher = 0x5555;
    for (;;) {
    }
}

/* Every hart above zero parks, unless a program says otherwise. The bare-metal paging chapter is the one that does. */
__attribute__((weak)) void bare_secondary(uint64 hartid) {
    (void)hartid;
    bare_park();
}

volatile uint64 bare_resume_at;
volatile uint64 bare_resume_sp;
volatile uint64 bare_resume_ra;

__attribute__((aligned(16))) char bare_stacks[BARE_STACK_BYTES * 8];

void bare_start(uint64 hartid) {
    if (hartid == 0) {
        main();
        bare_exit();
    }
    bare_secondary(hartid);
    bare_park();
}
