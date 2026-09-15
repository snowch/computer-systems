/* Where the machine starts, and nothing else.
 *
 * QEMU's `virt` board enters at 0x80000000 with no firmware in front of it when started with
 * `-bios none`, so that address is not a choice this script makes so much as one it records.
 * Everything else here exists because there is no loader: no program headers are interpreted,
 * no relocations are applied, and no BSS is zeroed for us. What the linker lays out is exactly
 * what the processor will find in memory.
 */
OUTPUT_ARCH("riscv")
ENTRY(_entry)

SECTIONS
{
  . = 0x80000000;

  .text : {
    *(.text.entry)          /* first, because execution begins at the lowest address */
    *(.text .text.*)
  }

  .rodata : { *(.rodata .rodata.*) }
  .data   : { *(.data .data.*) }

  /* start.S zeroes this range by hand. Nothing else will. */
  .bss : {
    PROVIDE(bare_bss_start = .);
    *(.bss .bss.*)
    *(COMMON)
    PROVIDE(bare_bss_end = .);
  }

  . = ALIGN(4096);
  PROVIDE(bare_free_memory = .);
}
