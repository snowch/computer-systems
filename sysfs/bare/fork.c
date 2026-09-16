/* The fork chapter: fork, built rather than read.
 *
 * The least a machine needs before two programs run on it: somewhere to keep what a program is,
 * a way to give the second one its own memory, and a way to put a saved program back on the
 * processor. `fork` is then a short function, and the famous part — that it returns twice with
 * different answers — stops being a riddle. It returns once per saved frame, and the frames
 * differ because one of them was edited.
 */
#include "bare.h"

#define SYS_FORK 1
#define SYS_PEEK 2
#define SYS_POKE 3

#define PTE_V (1UL << 0)
#define PTE_R (1UL << 1)
#define PTE_W (1UL << 2)
#define PTE_X (1UL << 3)
#define PTE_U (1UL << 4)
#define PTE_A (1UL << 6)
#define PTE_D (1UL << 7)
#define PTE_LEAF (PTE_V | PTE_R | PTE_W | PTE_X | PTE_A | PTE_D)
#define PTE_DATA (PTE_V | PTE_R | PTE_W | PTE_A | PTE_D)

#define SATP_SV39 (8UL << 60)
#define GIGABYTE (1UL << 30)
#define DEVICES_BASE 0x00000000UL
#define RAM_BASE 0x80000000UL

/* The one page of memory a process has of its own, at the same virtual address in each. Two
 * processes reading this address read different bytes, which is the entire point. */
#define USER_VA 0x40000000UL

#define PROCESSES 2
#define PAGE_POOL 16

static uint64 pool[PAGE_POOL][BARE_PAGE_BYTES / sizeof(uint64)]
    __attribute__((aligned(BARE_PAGE_BYTES)));
static int pages_taken;
static uint64 pages_copied;

struct proc {
    uint64 frame[32]; /* the registers it had when it last left the processor */
    uint64 epc;       /* and where it was */
    uint64 *root;     /* its address space */
    uint64 *page;     /* the physical page behind USER_VA, so machine mode can look */
    int used;
};

static struct proc procs[PROCESSES];
static int current;
static int children_made;

static volatile uint64 parent_saw_before_fork;
static volatile uint64 child_saw_at_birth;
static volatile uint64 parent_saw_after;
static volatile uint64 parent_fork_result;
static volatile uint64 child_fork_result;
static volatile int parent_reported;
static volatile int child_reported;

void bare_enter_process(uint64 *frame, uint64 epc);

static uint64 *take_page(void) {
    uint64 *page = pool[pages_taken++];
    for (uint64 i = 0; i < BARE_PAGE_BYTES / sizeof(uint64); i++) {
        page[i] = 0;
    }
    return page;
}

/* Walk to the leaf entry for one virtual address, making the levels that are missing. Three
 * levels, nine bits each, because Sv39 is thirty-nine bits of address and the bottom twelve are
 * the offset within a page. The bare-metal paging chapter used gigabyte leaves and needed none of this. */
static uint64 *leaf_entry(uint64 *root, uint64 va) {
    uint64 *table = root;
    for (int level = 2; level > 0; level--) {
        uint64 *entry = &table[(va >> (12 + 9 * level)) & 0x1FF];
        if (*entry & PTE_V) {
            table = (uint64 *)(((*entry) >> 10) << 12);
        } else {
            uint64 *next = take_page();
            *entry = (((uint64)next >> 12) << 10) | PTE_V; /* no R/W/X: a pointer, not a leaf */
            table = next;
        }
    }
    return &table[(va >> 12) & 0x1FF];
}

static uint64 *build_address_space(uint64 *user_page) {
    uint64 *root = take_page();
    /* The kernel's own mappings, identity, so that the code keeps running with paging on. */
    root[DEVICES_BASE / GIGABYTE] = ((DEVICES_BASE >> 12) << 10) | PTE_LEAF;
    root[RAM_BASE / GIGABYTE] = ((RAM_BASE >> 12) << 10) | PTE_LEAF;
    *leaf_entry(root, USER_VA) = (((uint64)user_page >> 12) << 10) | PTE_DATA | PTE_U;
    return root;
}

static int fork_current(uint64 *frame) {
    struct proc *parent = &procs[current];
    struct proc *child = &procs[current + 1];

    for (int i = 0; i < 32; i++) {
        child->frame[i] = frame[i];
    }
    /* The one edit that makes the answer differ. Everything else about the two is identical. */
    child->frame[10] = 0;
    child->epc = bare_csr_read(mepc) + 4;

    child->page = take_page();
    for (uint64 i = 0; i < BARE_PAGE_BYTES / sizeof(uint64); i++) {
        child->page[i] = parent->page[i];
    }
    pages_copied++;

    child->root = build_address_space(child->page);
    child->used = 1;
    children_made++;
    return current + 1;
}

uint64 bare_syscall(uint64 number, uint64 *frame) {
    switch (number) {
    case SYS_FORK:
        return (uint64)fork_current(frame);

    /* The handler runs in machine mode, and machine mode ignores `satp`. So it cannot simply
     * dereference the address its caller gave it: `USER_VA` here would be a *physical* address,
     * and on this board there is a PCI window at that number which answers every read with ones.
     *
     * What the kernel has to do instead is translate for itself — here trivially, because it
     * remembers which physical page it gave each process. A real kernel walks the caller's page
     * table to do the same thing, and `copyin` is what that function is called. */
    case SYS_PEEK:
        return procs[current].page[0];
    case SYS_POKE:
        procs[current].page[0] = frame[10];
        return 0;
    default:
        return (uint64)-1;
    }
}

/* Both processes are this function. They differ in what `fork` told them, and in the page they
 * are looking at when they read the same address. */
__attribute__((noinline)) static void process(void) {
    uint64 mine = bare_call(SYS_FORK, 0, 0, 0);

    if (mine == 0) {
        child_fork_result = mine;
        child_saw_at_birth = bare_call(SYS_PEEK, 0, 0, 0); /* what the parent had written */
        bare_call(SYS_POKE, 0xC4111D, 0, 0);
        child_reported = 1;
    } else {
        parent_fork_result = mine;
        parent_reported = 1;
    }
    bare_call(BARE_SYS_LEAVE, 0, 0, 0);
}

/* Machine mode's whole scheduler: when a process leaves, put the next one on. */
void bare_process_left(void) {
    if (current + 1 < PROCESSES && procs[current + 1].used) {
        current++;
        bare_csr_write(satp, SATP_SV39 | ((uint64)procs[current].root >> 12));
        asm volatile("sfence.vma zero, zero");
        bare_enter_process(procs[current].frame, procs[current].epc);
    }
}

int main(void) {
    procs[0].page = take_page();
    procs[0].page[0] = 0xBEEF; /* the parent's byte, written before there was a second process */
    procs[0].root = build_address_space(procs[0].page);
    procs[0].used = 1;
    parent_saw_before_fork = procs[0].page[0];

    bare_csr_write(satp, SATP_SV39 | ((uint64)procs[0].root >> 12));
    asm volatile("sfence.vma zero, zero");
    bare_run_in_supervisor(process);

    /* Machine mode ignores satp, so both pages can be read here by their physical addresses —
     * which is how we can say what each process has without asking either of them. */
    parent_saw_after = procs[0].page[0];

    bare_printf("fork processes %d\n", children_made + 1);
    bare_printf("fork pages_copied %d\n", pages_copied);
    bare_printf("fork parent_result %d\n", parent_fork_result);
    bare_printf("fork child_result %d\n", child_fork_result);
    bare_printf("fork results_differ %d\n", parent_fork_result != child_fork_result);
    bare_printf("fork both_ran %d\n", parent_reported && child_reported);
    bare_printf("fork child_inherited %x\n", child_saw_at_birth);
    bare_printf("fork child_saw_the_parents_byte %d\n", child_saw_at_birth == 0xBEEF);
    bare_printf("fork parent_after %x\n", parent_saw_after);
    bare_printf("fork childs_write_stayed_in_its_own_page %d\n", parent_saw_after == 0xBEEF);
    bare_printf("fork address_spaces %d\n", children_made + 1);
    bare_printf("fork unexpected_trap %d\n", bare_trap_was_unexpected);
    bare_print("end fork\n");
    return 0;
}
