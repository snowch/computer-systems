/* The four functions ch05 disassembles. One line each, on purpose.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 */

#include "sysfs/signedness.h"

int sysfs_signed_grows(int x) { return x + 1 > x; }

int sysfs_unsigned_grows(unsigned x) { return x + 1 > x; }

int sysfs_signed_quarter(int x) { return x / 4; }

unsigned sysfs_unsigned_quarter(unsigned x) { return x / 4; }
