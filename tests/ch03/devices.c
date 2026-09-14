/* Problem 3.3 — four operations, and a table to put them in.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * The test generates the dispatch table from your answer and links it against this file. Read
 * what each function does rather than what it is called: one of these names is a trap.
 */

#include <stdio.h>

/* Puts the device back to a known state and reports how many registers it cleared. */
int device_clear_all(int argument) {
  (void)argument;
  return 4;
}

/* Hands back the value the device is holding, which is whatever was written plus its port. */
int device_fetch(int argument) { return argument + 100; }

/* Accepts a value and reports how many bytes it consumed. */
int device_store(int argument) { return argument > 255 ? 2 : 1; }

/* Reports the device's flags. Despite the name, this does not reset anything. */
int device_reset_flags(int argument) { return argument & 0x3; }
