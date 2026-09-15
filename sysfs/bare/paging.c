/* ch06 (first half): one page table, installed by hand, and an address that means something else.
 *
 * Three entries is the whole table. Each one covers a gigabyte, which is large enough that no
 * second or third level is needed and small enough to write out and read back. Two of them map
 * memory to itself, so that the running program does not disappear the instant translation is
 * switched on. The third is the interesting one: it points a different virtual address at the
 * same physical memory, and afterwards two addresses that are a gigabyte apart name one byte.
 */
#include "bare.h"

#define PTE_V (1UL << 0)
#define PTE_R (1UL << 1)
#define PTE_W (1UL << 2)
#define PTE_X (1UL << 3)
#define PTE_A (1UL << 6) /* accessed  */
#define PTE_D (1UL << 7) /* dirty: set by hand, because nothing else will */
#define PTE_LEAF (PTE_V | PTE_R | PTE_W | PTE_X | PTE_A | PTE_D)

#define SATP_SV39 (8UL << 60)
#define GIGABYTE (1UL << 30)

#define DEVICES_BASE 0x00000000UL /* the UART and the CLINT live in this gigabyte */
#define RAM_BASE 0x80000000UL     /* and this one is where the program is */
#define ALIAS_BASE 0x40000000UL   /* unused by anything, which is why it is free to point at RAM */

#define MSTATUS_MPP (3UL << 11)
#define MSTATUS_MPP_S (1UL << 11)
#define MSTATUS_MPP_M (3UL << 11)
#define CAUSE_ECALL_FROM_S 9

/* One page, 512 entries of eight bytes, aligned as the hardware requires. */
static uint64 root[512] __attribute__((aligned(BARE_PAGE_BYTES)));

static volatile uint64 marker_direct;
static volatile uint64 marker_through_alias;
static volatile uint64 entries_used;
static volatile int reached_supervisor;
static volatile uint64 unexpected_cause;

static uint64 marker = 0xC0FFEE;

__attribute__((interrupt("machine"), aligned(4))) static void handler(void) {
    uint64 cause = bare_csr_read(mcause);
    if (cause == CAUSE_ECALL_FROM_S) {
        bare_csr_clear(mstatus, MSTATUS_MPP);
        bare_csr_set(mstatus, MSTATUS_MPP_M);
        bare_csr_write(mepc, bare_resume_at);
        return;
    }
    unexpected_cause = cause;
    bare_csr_write(mepc, bare_csr_read(mepc) + 4);
}

/* A leaf entry for a whole gigabyte. The physical page number is the address shifted right by
 * twelve; the entry holds it shifted left by ten, which is the ten bits of flags underneath. */
static uint64 gigapage(uint64 physical) {
    return ((physical >> 12) << 10) | PTE_LEAF;
}

static void build_the_table(void) {
    root[DEVICES_BASE / GIGABYTE] = gigapage(DEVICES_BASE);
    root[RAM_BASE / GIGABYTE] = gigapage(RAM_BASE);
    root[ALIAS_BASE / GIGABYTE] = gigapage(RAM_BASE); /* the alias: a second name for RAM */
    entries_used = 3;
}

/* Runs with translation on. Everything it touches is either identity-mapped or the alias. */
__attribute__((noinline)) static void in_supervisor_mode(void) {
    uint64 offset = (uint64)&marker - RAM_BASE;
    volatile uint64 *through_alias = (volatile uint64 *)(ALIAS_BASE + offset);

    reached_supervisor = 1;
    marker_direct = marker;
    marker_through_alias = *through_alias;

    asm volatile("ecall"); /* ask machine mode to take us back */
}

int main(void) {
    build_the_table();

    bare_csr_write(mtvec, (uint64)handler);
    bare_open_memory();

    /* satp names the root table by physical page number and the scheme by mode. Until this is
     * written, and in machine mode afterwards, an address is a physical address and nothing
     * translates it. */
    bare_csr_write(satp, SATP_SV39 | ((uint64)root >> 12));
    asm volatile("sfence.vma zero, zero"); /* the processor may have cached the old answer */

    bare_csr_write(mepc, (uint64)in_supervisor_mode);
    bare_csr_clear(mstatus, MSTATUS_MPP);
    bare_csr_set(mstatus, MSTATUS_MPP_S);
    bare_enter_supervisor();

    bare_printf("paging entries_used %d\n", entries_used);
    bare_printf("paging reached_supervisor %d\n", reached_supervisor);
    bare_printf("paging marker_direct %x\n", marker_direct);
    bare_printf("paging alias_reads_the_same %d\n", marker_through_alias == marker_direct);
    bare_printf("paging alias_distance_gigabytes %d\n", (RAM_BASE - ALIAS_BASE) / GIGABYTE);
    bare_printf("paging machine_mode_ignores_satp %d\n", marker == 0xC0FFEE);
    bare_printf("paging unexpected_cause %d\n", unexpected_cause);
    bare_print("end paging\n");
    return 0;
}
