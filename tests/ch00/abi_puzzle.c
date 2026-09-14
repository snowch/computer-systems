/* Problem 0.2's struct, and a program that reports what the compiler did with it.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * You are not meant to read this file before answering. Predict the numbers first, in
 * tests/ch00/problem_2_abi.py, and let the test tell you whether you were right.
 */

#include <stdio.h>
#include <stddef.h>

struct puzzle {
  char  flag;
  long  count;
  int   id;
  short code;
  char  tag;
};

int main(void) {
  printf("size %d\n", (int)sizeof(struct puzzle));
  printf("align %d\n", (int)_Alignof(struct puzzle));
  printf("offset flag %d\n", (int)offsetof(struct puzzle, flag));
  printf("offset count %d\n", (int)offsetof(struct puzzle, count));
  printf("offset id %d\n", (int)offsetof(struct puzzle, id));
  printf("offset code %d\n", (int)offsetof(struct puzzle, code));
  printf("offset tag %d\n", (int)offsetof(struct puzzle, tag));
  return 0;
}
