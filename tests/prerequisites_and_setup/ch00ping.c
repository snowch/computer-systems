/* Problem 0.3 — your first xv6 program.
 *
 * Make this print, on one line:
 *
 *     pong <n+1>
 *
 * where <n> is the number given on the command line. `ch00ping 41` prints `pong 42`.
 *
 * The arithmetic is not the exercise. The exercise is the path: this file is staged into the
 * kernel tree, compiled by the RISC-V cross compiler, linked against xv6's user library,
 * written into the file system image, booted under QEMU and run at the shell — and if any link
 * in that chain is missing, you find out now rather than in the traps chapter.
 *
 * xv6 has no libc. What you have is declared in user/user.h: printf, atoi, exit, and not much
 * else. `exit` takes an argument and does not return.
 *
 *     python3 -m pytest tests/prerequisites_and_setup/test_problem_3_xv6.py
 */

#include "kernel/types.h"
#include "user/user.h"

int main(int argc, char *argv[]) {
  /* TODO: Problem 0.3. Read the number out of argv, add one, and print `pong <n+1>`.
   * Silence is what this program does now, and silence is what the test is objecting to. */
  (void)argc;
  (void)argv;
  exit(0);
}
