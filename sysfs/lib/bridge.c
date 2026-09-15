/* The bodies, instantiated once so that ch20 has something to disassemble.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * Deliberately nothing else: the definitions live in the header as a macro, because the xv6 half
 * of this chapter is one translation unit and has nowhere to link a second object to.
 */

#include "sysfs/bridge.h"

SYSFS_BRIDGE_DEFINE
