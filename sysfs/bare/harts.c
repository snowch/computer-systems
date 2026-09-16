/* The bare-metal paging chapter (second half): what a second core breaks.
 *
 * The usual demonstration starts two harts incrementing a counter as fast as they can and shows
 * that the total comes out short. That works, sometimes, and teaches the wrong lesson when it
 * does: it looks like updates go missing at random, and leaves the reader with a superstition
 * rather than a mechanism.
 *
 * So this loses an update on purpose, every run, by holding the two halves of one
 * read-modify-write apart and letting the other hart finish entirely in the gap. What is shown is
 * not that a race is likely. It is that `counter = counter + 1` is three instructions with two
 * gaps in it, and that anything at all happening in a gap is enough.
 */
#include "bare.h"

static volatile uint64 counter;
static volatile uint64 atomic_counter;

/* Plain ints, one per direction, so neither hart ever waits on a value it also writes. */
static volatile int hart1_running;
static volatile int hart1_may_go;
static volatile int hart1_finished;
static volatile int hart1_may_go_atomic;
static volatile int hart1_finished_atomic;

void bare_secondary(uint64 hartid) {
    if (hartid != 1) {
        bare_park(); /* this program wants exactly two */
    }

    hart1_running = 1;

    while (!hart1_may_go) {
    }
    counter = counter + 1; /* a whole increment, start to finish, inside hart 0's gap */
    __sync_synchronize();
    hart1_finished = 1;

    while (!hart1_may_go_atomic) {
    }
    __sync_fetch_and_add(&atomic_counter, 1); /* one instruction: no gap to get into */
    __sync_synchronize();
    hart1_finished_atomic = 1;

    bare_park();
}

int main(void) {
    uint64 stale;

    while (!hart1_running) {
    }

    /* The three instructions of `counter = counter + 1`, with the other hart invited into the
     * gap between the load and the store. */
    stale = counter;      /* 1. load:  reads 0 */
    hart1_may_go = 1;     /*    ... and here the other hart does its entire increment ... */
    while (!hart1_finished) {
    }
    counter = stale + 1;  /* 2. add, 3. store: writes 1 over the other hart's 1 */

    /* The same shape, with an instruction that has no gap in it. */
    __sync_fetch_and_add(&atomic_counter, 1);
    hart1_may_go_atomic = 1;
    while (!hart1_finished_atomic) {
    }

    bare_printf("harts second_hart_ran %d\n", hart1_running);
    bare_printf("harts increments_attempted %d\n", 2);
    bare_printf("harts counter_after %d\n", counter);
    bare_printf("harts updates_lost %d\n", 2 - counter);
    bare_printf("harts atomic_increments_attempted %d\n", 2);
    bare_printf("harts atomic_counter_after %d\n", atomic_counter);
    bare_printf("harts atomic_updates_lost %d\n", 2 - atomic_counter);
    bare_print("end harts\n");
    return 0;
}
