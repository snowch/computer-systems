/* Problem 5.1 — finish the reader.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * `sysfs/tools/elfdump.c` is complete and you may read it, but it does not contain either of the
 * two functions below, so it will not hand you the answer.
 *
 * Both are about the same idea: an ELF file describes itself, and everything in it is found by
 * following an offset. The specification @elf-abi has the field layouts; chapter 5 has the shape.
 *
 *   python3 -m pytest tests/linking_and_loading/test_problem_1_reader.py
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Little-endian field readers, given to you because the exercise is not byte fiddling. */
static uint16_t u16(const unsigned char *p) { return (uint16_t)(p[0] | (p[1] << 8)); }
static uint32_t u32(const unsigned char *p) {
  return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static uint64_t u64(const unsigned char *p) {
  return (uint64_t)u32(p) | ((uint64_t)u32(p + 4) << 32);
}

/* Problem 5.1a — how many bytes does this program occupy in memory once loaded?
 *
 * Not how big the file is. Walk the program headers, take the PT_LOAD ones, and account for the
 * fact that a segment's memory size and its file size are allowed to differ.
 *
 * Return 0 if the file has no loadable segments. */
uint64_t reader_memory_footprint(const unsigned char *elf) {
  (void)elf;
  (void)u16;
  (void)u64;
  return 0; /* Problem 5.1a */
}

/* Problem 5.1b — what is the name of the section containing this address?
 *
 * Return a pointer into the file's own section-name string table, or NULL if no section covers
 * the address. A section covers an address if it has one — some do not — and the address falls
 * within its size.
 *
 * The indirection to get a name is the part worth working out, and chapter 5 describes it. */
const char *reader_section_covering(const unsigned char *elf, uint64_t address) {
  (void)elf;
  (void)address;
  (void)u32;
  return NULL; /* Problem 5.1b */
}

/* The harness: prints the footprint, then the name of the section covering each address given
 * on the command line. */
int main(int argc, char **argv) {
  if (argc < 2) {
    fprintf(stderr, "usage: reader <elf> [address...]\n");
    return 2;
  }
  FILE *file = fopen(argv[1], "rb");
  if (!file) {
    return 1;
  }
  fseek(file, 0, SEEK_END);
  long length = ftell(file);
  fseek(file, 0, SEEK_SET);
  unsigned char *elf = malloc((size_t)length);
  if (!elf || fread(elf, 1, (size_t)length, file) != (size_t)length) {
    return 1;
  }
  fclose(file);

  printf("footprint %llu\n", (unsigned long long)reader_memory_footprint(elf));
  for (int index = 2; index < argc; index++) {
    const char *name = reader_section_covering(elf, strtoull(argv[index], NULL, 0));
    printf("covering %s %s\n", argv[index], name ? name : "(none)");
  }
  free(elf);
  return 0;
}
