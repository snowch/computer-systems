/* Problems 9.1 and 9.2 — the two things a driver's caller has to know.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * Neither is in the repository. This chapter's patch counts interrupts and decides nothing, and
 * nothing in `sysfs/` knows what a device is.
 *
 *   python3 -m pytest tests/ch16
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* xv6's console input buffer, to the character. A driver's buffer is always this shape: a
 * producer that cannot be told to wait, a consumer that runs when it runs, and a fixed amount of
 * room between them. */
#define CONSOLE_BUF 128

/* -- Problem 9.1 -------------------------------------------------------------------------- */
/* How many characters does this console lose?
 *
 * `events` is a string read left to right. A '+' is one character arriving from the device, which
 * the handler must deal with immediately because the device will not hold it. A digit '1'..'9' is
 * the reading process draining that many characters, or as many as are there.
 *
 * The buffer holds CONSOLE_BUF characters. A character arriving at a full buffer is dropped, and
 * nothing anywhere is told: the handler cannot block, cannot allocate, and has nobody to return
 * an error to. Return how many were dropped.
 *
 * This is the whole reason a console loses characters when you paste into it, and it is not a
 * bug in anything.
 */
uint64_t console_lost(const char *events) {
  (void)events;
  return 0; /* Problem 9.1 */
}

/* -- Problem 9.2 -------------------------------------------------------------------------- */
/* How many interrupts will this cost?
 *
 * `completions` is how many separate operations the device is asked to complete. `per_interrupt`
 * is how many completions it reports at once — one for a device that interrupts on every one, and
 * more for a device that batches.
 *
 * Return the number of interrupts, or CONSOLE_UNDECIDABLE if the question does not have an answer
 * that follows from the workload. It does not always, and recognising when is the point: a device
 * that interrupts to say "ready for more" rather than "this is finished" is not reporting
 * completions at all, and no amount of knowing the workload will tell you how many times it does
 * it. `per_interrupt` of zero means exactly that device.
 */
#define CONSOLE_UNDECIDABLE ((uint64_t)-1)

uint64_t console_interrupts_for(uint64_t completions, uint64_t per_interrupt) {
  (void)completions;
  (void)per_interrupt;
  return 0; /* Problem 9.2 */
}

/* -- the harness, which you do not need to change ----------------------------------------- */

int main(int argc, char **argv) {
  for (int i = 1; i < argc; i++) {
    char *comma = strchr(argv[i], ',');
    switch (argv[i][0]) {
    case 'l': /* l<events> */
      printf("lost %d %llu\n", i, (unsigned long long)console_lost(argv[i] + 1));
      break;
    case 'i': /* i<completions>,<per_interrupt> */
      if (comma == NULL) {
        fprintf(stderr, "console: expected completions,per_interrupt\n");
        return 2;
      }
      printf("interrupts %llu %llu %llu\n", (unsigned long long)strtoull(argv[i] + 1, NULL, 0),
             (unsigned long long)strtoull(comma + 1, NULL, 0),
             (unsigned long long)console_interrupts_for(strtoull(argv[i] + 1, NULL, 0),
                                                        strtoull(comma + 1, NULL, 0)));
      break;
    default:
      fprintf(stderr, "console: unknown command %s\n", argv[i]);
      return 2;
    }
  }
  printf("end console\n");
  return 0;
}
