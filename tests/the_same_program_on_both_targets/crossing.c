/* Problems 13.1, 13.2 and 13.3 — the move the whole of Part V depends on.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * Three things differ between this book's two targets at once: an emulator against hardware, one
 * kernel against another, and one instruction set against another. Attributing a difference to the
 * wrong one of those is the commonest way to be confidently wrong about performance, and these
 * three problems are about not doing it.
 *
 *   python3 -m pytest tests/the_same_program_on_both_targets
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Six configurations a reader could plausibly get hold of. Each is three facts. */
struct crossing_config {
  char name;
  int emulated; /* 1 if under an emulator */
  char kernel;  /* 'x' for xv6, 'l' for Linux */
  char isa;     /* 'r' for RISC-V, 'a' for AArch64 */
};

static const struct crossing_config CONFIGS[] = {
    {'A', 1, 'x', 'r'}, /* the book's first target */
    {'B', 1, 'l', 'r'}, {'C', 0, 'l', 'r'}, {'D', 0, 'l', 'a'}, /* the book's second target */
    {'E', 0, 'x', 'r'}, {'F', 1, 'l', 'a'},
};
#define CROSSING_CONFIGS 6

const struct crossing_config *crossing_config(char name) {
  for (int i = 0; i < CROSSING_CONFIGS; i++)
    if (CONFIGS[i].name == name)
      return &CONFIGS[i];
  return NULL;
}

/* -- Problem 13.1 -------------------------------------------------------------------------- */
/* What does comparing these two configurations isolate?
 *
 * Return:
 *   'e'  only whether it is emulated differs, so the comparison isolates that
 *   'k'  only the kernel differs
 *   'i'  only the instruction set differs
 *   'n'  nothing differs, so the comparison isolates nothing
 *   'x'  more than one differs, so the comparison confounds them
 *
 * The last answer is the one worth being able to give quickly. A measurement that moves when two
 * things changed tells you a number and nothing about why, and no amount of care taken over the
 * number afterwards recovers what the design gave away.
 */
char crossing_isolates(char first, char second) {
  (void)first;
  (void)second;
  return 'x'; /* Problem 13.1 */
}

/* -- Problem 13.2 -------------------------------------------------------------------------- */
/* Which pair would test this claim?
 *
 * `claim` is 'e', 'k' or 'i' — somebody says the difference they measured is caused by emulation,
 * by the kernel, or by the instruction set. Starting from configuration `from`, write into
 * `other` the name of the configuration that, compared with it, isolates exactly that variable.
 *
 * Return 1 if such a configuration exists among the six and 0 if it does not. When more than one
 * would do, give the earliest by name.
 *
 * Sometimes the answer is that you cannot test the claim with what you have, and saying so is a
 * better answer than a measurement that cannot mean what it is being asked to mean.
 */
int crossing_pair_for(char claim, char from, char *other) {
  (void)claim;
  (void)from;
  (void)other;
  return 0; /* Problem 13.2 */
}

/* -- Problem 13.3 -------------------------------------------------------------------------- */
/* Does this observation transfer from one target to the other?
 *
 * `what` names something you could observe about a program:
 *
 *   'a'  the answer it computes
 *   'l'  the layout of its structures in memory
 *   'i'  how many instructions it executes
 *   'c'  how many cache misses it takes
 *   'p'  how many page faults it takes
 *   't'  how long it takes
 *
 * Return 1 if observing it on one of this book's targets tells you the value on the other, and 0
 * if it does not. Assume the same source compiled for both, as the crossing chapter's program is.
 *
 * Two of these are less obvious than they look, and are worth thinking about rather than sorting
 * into "structure" and "cost".
 */
int crossing_transfers(char what) {
  (void)what;
  return 1; /* Problem 13.3 */
}

/* -- the harness, which you do not need to change ----------------------------------------- */

int main(int argc, char **argv) {
  for (int i = 1; i < argc; i++) {
    switch (argv[i][0]) {
    case 'i': /* i<first><second> */
      printf("isolates %c%c %c\n", argv[i][1], argv[i][2],
             crossing_isolates(argv[i][1], argv[i][2]));
      break;
    case 'p': { /* p<claim><from> */
      char other = '?';
      int found = crossing_pair_for(argv[i][1], argv[i][2], &other);
      printf("pair %c%c %d %c\n", argv[i][1], argv[i][2], found, found ? other : '-');
      break;
    }
    case 't': /* t<what> */
      printf("transfers %c %d\n", argv[i][1], crossing_transfers(argv[i][1]));
      break;
    default:
      fprintf(stderr, "crossing: unknown command %s\n", argv[i]);
      return 2;
    }
  }
  printf("end crossing\n");
  return 0;
}
