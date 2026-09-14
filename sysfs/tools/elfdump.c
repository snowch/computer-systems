/* elfdump — read an ELF64 file with no library at all, and say what is in it.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * ch05 takes a binary apart. It could do that with `readelf`, and a reader who has only ever used
 * `readelf` believes an ELF file is a thing a tool understands. Writing the reader is how it
 * stops being that: the format is a header naming two arrays, and everything else is offsets.
 *
 * Deliberately no <elf.h>. The structures below are declared from the specification @elf-abi
 * rather than included, because half the point is that they are a documented layout of bytes and
 * not a secret. They are read field by field rather than by casting the file onto a struct, which
 * would work on these two machines and is a habit that stops working the moment the file came
 * from a different one.
 *
 * Prints one fact per line, `kind name value...`, like every other tool in this book.
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define EI_NIDENT 16
#define ET_EXEC 2
#define ET_DYN 3
#define PT_LOAD 1
#define SHT_SYMTAB 2
#define SHT_STRTAB 3
#define STT_FUNC 2
#define STT_OBJECT 1
#define SHN_UNDEF 0

/* Little-endian readers. The file says which byte order it uses and this book's machines are
 * both little; a reader that handles both is a good exercise and is Problem 5.1's second half. */
static uint16_t u16(const unsigned char *p) { return (uint16_t)(p[0] | (p[1] << 8)); }

static uint32_t u32(const unsigned char *p) {
  return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static uint64_t u64(const unsigned char *p) {
  return (uint64_t)u32(p) | ((uint64_t)u32(p + 4) << 32);
}

/* Field offsets, straight out of the specification. Named rather than written inline so that a
 * reader with the document open can check each one. */
#define EH_TYPE 16
#define EH_MACHINE 18
#define EH_ENTRY 24
#define EH_PHOFF 32
#define EH_SHOFF 40
#define EH_PHENTSIZE 54
#define EH_PHNUM 56
#define EH_SHENTSIZE 58
#define EH_SHNUM 60
#define EH_SHSTRNDX 62

#define PH_TYPE 0
#define PH_FLAGS 4
#define PH_OFFSET 8
#define PH_VADDR 16
#define PH_FILESZ 32
#define PH_MEMSZ 40
#define PH_ALIGN 48

#define SH_NAME 0
#define SH_TYPE 4
#define SH_FLAGS 8
#define SH_ADDR 16
#define SH_OFFSET 24
#define SH_SIZE 32
#define SH_LINK 40
#define SH_ENTSIZE 56

#define SYM_NAME 0
#define SYM_INFO 4
#define SYM_SHNDX 6
#define SYM_VALUE 8
#define SYM_SIZE 16
#define SYM_ENTSIZE 24

static unsigned char *slurp(const char *path, long *length) {
  FILE *file = fopen(path, "rb");
  if (!file) {
    return NULL;
  }
  fseek(file, 0, SEEK_END);
  *length = ftell(file);
  fseek(file, 0, SEEK_SET);
  unsigned char *bytes = malloc((size_t)*length);
  if (bytes && fread(bytes, 1, (size_t)*length, file) != (size_t)*length) {
    free(bytes);
    bytes = NULL;
  }
  fclose(file);
  return bytes;
}

/* A section's name is not in the section header. The header holds an offset into a string table,
 * and which string table is named by the file header — an indirection that is the first thing to
 * trip over and the reason `readelf` output looks like it required effort. */
static const char *section_name(const unsigned char *elf, uint64_t shoff, uint16_t entsize,
                                uint16_t shstrndx, uint32_t name_offset) {
  const unsigned char *strtab_header = elf + shoff + (uint64_t)shstrndx * entsize;
  uint64_t strtab = u64(strtab_header + SH_OFFSET);
  return (const char *)(elf + strtab + name_offset);
}

int main(int argc, char **argv) {
  if (argc != 2) {
    fprintf(stderr, "usage: elfdump <file>\n");
    return 2;
  }
  long length = 0;
  unsigned char *elf = slurp(argv[1], &length);
  if (!elf || length < 64) {
    fprintf(stderr, "elfdump: cannot read %s\n", argv[1]);
    return 1;
  }
  if (memcmp(elf, "\177ELF", 4) != 0) {
    fprintf(stderr, "elfdump: %s is not an ELF file\n", argv[1]);
    return 1;
  }

  printf("elfdump 1\n");
  printf("class %d\n", elf[4] == 2 ? 64 : 32);
  printf("endian %s\n", elf[5] == 1 ? "little" : "big");
  printf("type %s\n", u16(elf + EH_TYPE) == ET_EXEC     ? "executable"
                      : u16(elf + EH_TYPE) == ET_DYN ? "shared"
                                                     : "object");
  printf("machine %d\n", u16(elf + EH_MACHINE));
  printf("entry %llu\n", (unsigned long long)u64(elf + EH_ENTRY));

  /* The two arrays. Sections are for the linker; segments are for whatever loads the program.
   * The same bytes usually appear in both, described twice for two different audiences. */
  uint64_t shoff = u64(elf + EH_SHOFF);
  uint16_t shentsize = u16(elf + EH_SHENTSIZE);
  uint16_t shnum = u16(elf + EH_SHNUM);
  uint16_t shstrndx = u16(elf + EH_SHSTRNDX);

  for (uint16_t index = 0; index < shnum; index++) {
    const unsigned char *header = elf + shoff + (uint64_t)index * shentsize;
    const char *name = section_name(elf, shoff, shentsize, shstrndx, u32(header + SH_NAME));
    printf("section %s %llu %llu %llu\n", name[0] ? name : "(unnamed)",
           (unsigned long long)u64(header + SH_ADDR), (unsigned long long)u64(header + SH_SIZE),
           (unsigned long long)u64(header + SH_FLAGS));
  }

  uint64_t phoff = u64(elf + EH_PHOFF);
  uint16_t phentsize = u16(elf + EH_PHENTSIZE);
  uint16_t phnum = u16(elf + EH_PHNUM);
  for (uint16_t index = 0; index < phnum; index++) {
    const unsigned char *header = elf + phoff + (uint64_t)index * phentsize;
    if (u32(header + PH_TYPE) != PT_LOAD) {
      continue;
    }
    /* memsz can exceed filesz, and the difference is .bss: space the loader must provide and
     * zero, which is not in the file because a megabyte of zeroes is not worth storing. */
    printf("segment %llu %llu %llu %u %llu\n", (unsigned long long)u64(header + PH_VADDR),
           (unsigned long long)u64(header + PH_FILESZ),
           (unsigned long long)u64(header + PH_MEMSZ), u32(header + PH_FLAGS),
           (unsigned long long)u64(header + PH_ALIGN));
  }

  /* Symbols, and in particular the undefined ones: a name the file uses and cannot supply. */
  for (uint16_t index = 0; index < shnum; index++) {
    const unsigned char *header = elf + shoff + (uint64_t)index * shentsize;
    if (u32(header + SH_TYPE) != SHT_SYMTAB) {
      continue;
    }
    uint64_t table = u64(header + SH_OFFSET);
    uint64_t size = u64(header + SH_SIZE);
    uint64_t entsize = u64(header + SH_ENTSIZE);
    const unsigned char *strings_header = elf + shoff + (uint64_t)u32(header + SH_LINK) * shentsize;
    const char *strings = (const char *)(elf + u64(strings_header + SH_OFFSET));

    uint64_t defined = 0, undefined = 0;
    for (uint64_t offset = 0; offset + entsize <= size; offset += entsize) {
      const unsigned char *symbol = elf + table + offset;
      const char *name = strings + u32(symbol + SYM_NAME);
      if (!name[0]) {
        continue;
      }
      if (u16(symbol + SYM_SHNDX) == SHN_UNDEF) {
        undefined++;
        printf("undefined %s\n", name);
      } else {
        defined++;
      }
    }
    printf("symbols %llu %llu\n", (unsigned long long)defined, (unsigned long long)undefined);
  }

  printf("end elfdump\n");
  free(elf);
  return 0;
}
