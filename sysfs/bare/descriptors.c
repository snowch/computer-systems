/* ch08: a small integer that means a device.
 *
 * `write(1, ...)` and `write(2, ...)` are the same instruction sequence with one register
 * different, and they end up in completely unrelated places. That is the whole of what a
 * descriptor is for, and it is invisible with only one thing to write to — so there are two: the
 * serial port, which is a device at a fixed physical address, and an array of bytes with a
 * cursor, which is not a file system and is not pretending to be one.
 *
 * What the table buys is that the caller does not know which it got.
 */
#include "bare.h"

#define SYS_WRITE 1
#define SYS_READ 2
#define SYS_DUP 3

#define SLOTS 4
#define SCRATCH_BYTES 64
#define BAD_DESCRIPTOR ((uint64)-1)

/* The two things a descriptor can find. A third would need nothing but another case here and
 * another `kind`, which is the point: the table is the interface. */
enum backend { BACKEND_NONE, BACKEND_CONSOLE, BACKEND_MEMORY };

struct open_file {
    enum backend kind;
    uint64 cursor; /* where in the scratch array the next byte goes, for BACKEND_MEMORY */
};

/* Two tables, and the distinction between them is the whole subject.
 *
 * `descriptors` is indexed by the small integer and holds nothing but a number: which open file
 * this one refers to. `open_files` holds what is actually open, including how far through it we
 * are. Two descriptors can name one open file, and then they share a cursor — which is why a
 * shell can point a program's output somewhere and have it append rather than overwrite.
 *
 * Putting the cursor in the descriptor instead would be simpler and would quietly make `dup` a
 * copy rather than a second name. It is the same distinction ch09's `fork` turns on: the table
 * is copied, the things it refers to are not. */
#define OPEN_FILES 4
#define NO_FILE (-1)

static int descriptors[SLOTS];
static struct open_file open_files[OPEN_FILES];
static char scratch[SCRATCH_BYTES];

static struct open_file *file_for(int fd) {
    if (fd < 0 || fd >= SLOTS || descriptors[fd] == NO_FILE) {
        return 0;
    }
    return &open_files[descriptors[fd]];
}

static volatile uint64 wrote_to_console;
static volatile uint64 wrote_to_memory;
static volatile uint64 read_back;
static volatile uint64 bad_result;
static volatile uint64 dup_result;
static volatile int dup_shares_backend;
static volatile int same_call_reached_both;

static uint64 write_to(int fd, const char *bytes, uint64 count) {
    struct open_file *file = file_for(fd);
    if (!file) {
        return BAD_DESCRIPTOR;
    }
    switch (file->kind) {
    case BACKEND_CONSOLE:
        for (uint64 i = 0; i < count; i++) {
            bare_putc(bytes[i]);
        }
        return count;
    case BACKEND_MEMORY: {
        uint64 written = 0;
        while (written < count && file->cursor < SCRATCH_BYTES) {
            scratch[file->cursor++] = bytes[written++];
        }
        return written;
    }
    default:
        return BAD_DESCRIPTOR;
    }
}

static uint64 read_from(int fd, char *into, uint64 count) {
    struct open_file *file = file_for(fd);
    if (!file || file->kind != BACKEND_MEMORY) {
        return BAD_DESCRIPTOR; /* the console here is write-only, and says so rather than lying */
    }
    uint64 taken = 0;
    while (taken < count && taken < file->cursor) {
        into[taken] = scratch[taken];
        taken++;
    }
    return taken;
}

static uint64 duplicate(int fd, int onto) {
    if (onto < 0 || onto >= SLOTS || !file_for(fd)) {
        return BAD_DESCRIPTOR;
    }
    /* One number is copied. The open file it refers to is not, so afterwards two descriptors are
     * two names for one thing — including one cursor between them. */
    descriptors[onto] = descriptors[fd];
    return (uint64)onto;
}

uint64 bare_syscall(uint64 number, uint64 *frame) {
    switch (number) {
    case SYS_WRITE:
        return write_to((int)frame[10], (const char *)frame[11], frame[12]);
    case SYS_READ:
        return read_from((int)frame[10], (char *)frame[11], frame[12]);
    case SYS_DUP:
        return duplicate((int)frame[10], (int)frame[11]);
    default:
        return BAD_DESCRIPTOR;
    }
}

static char taken[SCRATCH_BYTES];

__attribute__((noinline)) static void user_of_the_table(void) {
    static const char message[] = "hello\n";
    const uint64 length = sizeof(message) - 1;

    /* The same call, twice, differing in one register. */
    wrote_to_console = bare_call(SYS_WRITE, 1, (uint64)message, length);
    wrote_to_memory = bare_call(SYS_WRITE, 2, (uint64)message, length);
    same_call_reached_both = (wrote_to_console == length) && (wrote_to_memory == length);

    read_back = bare_call(SYS_READ, 2, (uint64)taken, length);
    bad_result = bare_call(SYS_WRITE, 3, (uint64)message, length);

    dup_result = bare_call(SYS_DUP, 2, 3, 0);
    bare_call(SYS_WRITE, 3, (uint64)"!", 1); /* through the duplicate, into the same array */

    bare_call(BARE_SYS_LEAVE, 0, 0, 0);
}

int main(void) {
    for (int fd = 0; fd < SLOTS; fd++) {
        descriptors[fd] = NO_FILE;
    }
    open_files[0].kind = BACKEND_CONSOLE;
    open_files[1].kind = BACKEND_MEMORY;
    descriptors[1] = 0; /* by convention, and the convention is these two lines */
    descriptors[2] = 1;

    bare_run_in_supervisor(user_of_the_table);

    /* The write through descriptor 3 moved descriptor 2's cursor, because there was only ever
     * one cursor. That is what "shares" means, and it is checkable rather than asserted. */
    dup_shares_backend = descriptors[3] == descriptors[2] && open_files[1].cursor == 7;

    bare_printf("descriptors descriptor_slots %d\n", SLOTS);
    bare_printf("descriptors open_file_slots %d\n", OPEN_FILES);
    bare_printf("descriptors backends %d\n", 2);
    bare_printf("descriptors wrote_to_console %d\n", wrote_to_console);
    bare_printf("descriptors wrote_to_memory %d\n", wrote_to_memory);
    bare_printf("descriptors same_call_reached_both %d\n", same_call_reached_both);
    bare_printf("descriptors memory_kept_the_bytes %d\n", taken[0] == 'h' && taken[4] == 'o');
    bare_printf("descriptors read_back %d\n", read_back);
    bare_printf("descriptors closed_slot_refused %d\n", bad_result == BAD_DESCRIPTOR);
    bare_printf("descriptors dup_returned %d\n", dup_result);
    bare_printf("descriptors dup_shares_the_open_file %d\n", dup_shares_backend);
    bare_printf("descriptors shared_cursor %d\n", open_files[1].cursor);
    bare_printf("descriptors unexpected_trap %d\n", bare_trap_was_unexpected);
    bare_print("end descriptors\n");
    return 0;
}
