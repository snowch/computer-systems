/* Problems 1.1, 1.2 and 1.3 — read a declaration, walk a buffer, round an address.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * None of these is in the repository.
 *
 *   python3 -m pytest tests/memory_is_one_array
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* -- Problem 1.1 --------------------------------------------------------------------------- */
/* What does each declaration name?
 *
 * You are given a declaration as a string, in one of the shapes the chapter's table covers, and
 * must say what the name in it *is*. Return one of:
 *
 *   D_VALUE     a plain object            int x
 *   D_POINTER   a pointer to an object    int *x
 *   D_ARRAY     an array of objects       int x[4]
 *   D_ARRAY_PTR an array of pointers      int *x[4]
 *   D_PTR_ARRAY a pointer to an array     int (*x)[4]
 *   D_FUNC_PTR  a pointer to a function   int (*x)(void)
 *   D_FUNC      a function                int *x(void)
 *
 * You are not being asked to write a C parser. Every declaration you are given has exactly one
 * name in it, the type is always `int`, and the only punctuation is `*`, `[]`, `()` and spaces.
 *
 * Read from the name outwards, taking whatever binds tightest first: `[]` and `()` bind tighter
 * than `*`, and parentheses override that. The two that differ only by a pair of brackets are the
 * reason this problem exists — one of them is how every driver in the drivers chapter is reached.
 */
#define D_VALUE 0
#define D_POINTER 1
#define D_ARRAY 2
#define D_ARRAY_PTR 3
#define D_PTR_ARRAY 4
#define D_FUNC_PTR 5
#define D_FUNC 6

int d_classify(const char *declaration) {
  (void)declaration;
  return D_VALUE; /* Problem 1.1 */
}

/* -- Problem 1.2 --------------------------------------------------------------------------- */
/* Walk a buffer with pointers rather than subscripts.
 *
 * Three of the routines the kernel supplies for itself, because nothing supplies them to it.
 * Write each with pointers that move — no `[]` anywhere — so that kernel/string.c reads as
 * something you have already written.
 *
 * `d_length` returns the number of bytes before the terminating zero.
 * `d_copy` copies exactly `n` bytes from `src` to `dst` and returns `dst`.
 * `d_compare` returns 0 if the first `n` bytes match, and otherwise the difference between the
 *   first pair that does not, as `unsigned char` values, first minus second.
 *
 * `d_copy`'s regions never overlap here, which is a promise the real `memmove` does not get and
 * the C-as-machine-code chapter comes back to.
 */
uint64_t d_length(const char *s) {
  (void)s;
  return 0; /* Problem 1.2 */
}

void *d_copy(void *dst, const void *src, uint64_t n) {
  (void)src;
  (void)n;
  return dst; /* Problem 1.2 */
}

int d_compare(const void *a, const void *b, uint64_t n) {
  (void)a;
  (void)b;
  (void)n;
  return 0; /* Problem 1.2 */
}

/* -- Problem 1.3 --------------------------------------------------------------------------- */
/* Round an address to a boundary, both ways.
 *
 * `align` is a power of two. `d_round_down` returns the largest multiple of `align` that is not
 * greater than `address`; `d_round_up` returns the smallest that is not less than it. An address
 * already on a boundary is its own answer in both directions.
 *
 * This is address arithmetic, not pointer arithmetic: the quantity is a number of bytes and
 * nothing here scales by an element. The kernel does this on every page it touches, and the
 * freestanding-C chapter's allocator opens by rounding one way and closing by rounding the other — which is the pair of
 * decisions this problem is really about.
 *
 * Both can be written without a division, a modulo or a branch. Finding that form is the exercise;
 * a correct answer that divides still passes.
 */
uint64_t d_round_down(uint64_t address, uint64_t align) {
  (void)align;
  return address; /* Problem 1.3 */
}

uint64_t d_round_up(uint64_t address, uint64_t align) {
  (void)align;
  return address; /* Problem 1.3 */
}

/* -- the harness, which you do not need to change ----------------------------------------- */

/* Answers are keyed by the command's position, so two cases with identical arguments still land
 * somewhere the caller can find them. */

int main(int argc, char **argv) {
  for (int i = 1; i < argc; i++) {
    char *arg = argv[i] + 1;
    switch (argv[i][0]) {
    case 'd': /* d<declaration> */
      printf("declare %d %d\n", i - 1, d_classify(arg));
      break;
    case 'l': /* l<string> */
      printf("length %d %llu\n", i - 1, (unsigned long long)d_length(arg));
      break;
    case 'c': { /* c<n>:<bytes> — copy n bytes and let the harness, not the reader, check them */
      char *colon = strchr(arg, ':');
      if (!colon) {
        fprintf(stderr, "declarations: malformed copy %s\n", argv[i]);
        return 2;
      }
      *colon = '\0';
      uint64_t n = strtoull(arg, NULL, 10);
      char *source = colon + 1;
      char buffer[256];
      memset(buffer, '.', sizeof buffer);
      if (n > sizeof buffer || n > strlen(source)) {
        fprintf(stderr, "declarations: copy out of range %s\n", argv[i]);
        return 2;
      }
      d_copy(buffer, source, n);
      /* Summed here rather than through d_compare: checking one of the reader's functions with
       * another lets two wrong answers agree, and a stub that does nothing would pass. */
      uint64_t sum = 0;
      for (uint64_t k = 0; k < n; k++)
        sum = sum * 31 + (unsigned char)buffer[k];
      printf("copy %d %llu %d\n", i - 1, (unsigned long long)sum,
             (int)(unsigned char)buffer[n]);
      break;
    }
    case 'm': { /* m<a>,<b>,<n> — compare two strings' first n bytes */
      char *first = strchr(arg, ',');
      if (!first) {
        fprintf(stderr, "declarations: malformed compare %s\n", argv[i]);
        return 2;
      }
      *first = '\0';
      char *second = first + 1;
      char *last = strchr(second, ',');
      if (!last) {
        fprintf(stderr, "declarations: malformed compare %s\n", argv[i]);
        return 2;
      }
      *last = '\0';
      uint64_t n = strtoull(last + 1, NULL, 10);
      printf("compare %d %d\n", i - 1, d_compare(arg, second, n));
      break;
    }
    case 'r': { /* r<address>,<align> */
      char *p = arg;
      uint64_t address = strtoull(p, &p, 0);
      uint64_t align = strtoull(*p == ',' ? p + 1 : p, NULL, 0);
      printf("round %d %llu %llu\n", i - 1, (unsigned long long)d_round_down(address, align),
             (unsigned long long)d_round_up(address, align));
      break;
    }
    default:
      fprintf(stderr, "declarations: unknown command %s\n", argv[i]);
      return 2;
    }
  }
  printf("end declarations\n");
  return 0;
}
