#!/bin/sh
# Walk one C file through the toolchain, keeping what each stage produced (ch01).
#
# Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
#
#   sysfs/tools/stages.sh sysfs/tools/sameanswer.c /tmp/walk riscv64-linux-gnu-gcc
#
# Four commands, and the only difference between them is where the compiler driver is told to
# stop. That is the point: `gcc a.c -o a` is not one program, it is four, and each hands the next
# a file you are allowed to look at. This script does nothing but decline to delete them.
#
# Prints one fact per line, `kind name value`, for the same reason the probe does: a format a
# shell can read with `cut` is one a test can assert on without a parser. bench/run_stages.py
# parses it and stamps the result; nothing here computes anything the reader cannot repeat by
# typing the four commands themselves.
set -eu

source=${1:?usage: stages.sh <source.c> <outdir> [cc]}
outdir=${2:?usage: stages.sh <source.c> <outdir> [cc]}
cc=${3:-riscv64-linux-gnu-gcc}
stem=$(basename "$source" .c)
root=$(cd "$(dirname "$0")/../.." && pwd)

mkdir -p "$outdir"
flags="-O2 -Wall -Wextra -march=rv64gc -mabi=lp64d -I$root/sysfs/include"

echo "stagewalk 1"
echo "cc $($cc --version | head -1)"
echo "flags $flags"

# 1. Preprocess. Text in, text out: includes pasted in, macros expanded, comments deleted.
#    No C has been understood yet — cpp does not know what a function is.
$cc $flags -E "$source" -o "$outdir/$stem.i"

# 2. Compile. The only stage that makes decisions. C in, assembly out.
$cc $flags -S "$outdir/$stem.i" -o "$outdir/$stem.s"

# 3. Assemble. Assembly in, object out: instructions become bytes, and anything whose address is
#    not yet known becomes a relocation for the linker to fill in.
$cc $flags -c "$outdir/$stem.s" -o "$outdir/$stem.o"

# 4. Link. Objects and libraries in, one program out. -static so the result runs under user-mode
#    QEMU, which has no RISC-V loader to offer it.
$cc $flags -static "$outdir/$stem.o" -o "$outdir/$stem"

for stage in i s o ''; do
  case $stage in
    i) file=$outdir/$stem.i; label=preprocess ;;
    s) file=$outdir/$stem.s; label=compile ;;
    o) file=$outdir/$stem.o; label=assemble ;;
    *) file=$outdir/$stem;   label=link ;;
  esac
  echo "stage $label $(wc -c < "$file" | tr -d ' ') $(wc -l < "$file" | tr -d ' ')"
done

# What the object still owes the linker, and what the program no longer owes anybody. `U` is an
# undefined symbol: the assembler wrote a hole and a note saying what belongs in it.
nm="${cc%gcc}nm"
echo "undefined_in_object $($nm -u "$outdir/$stem.o" | wc -l | tr -d ' ')"
echo "undefined_in_program $($nm -u "$outdir/$stem" 2>/dev/null | wc -l | tr -d ' ')"
echo "end stagewalk"
