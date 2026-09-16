# The pinned toolchain for this book's *deterministic* results — the disassembly listings, and the
# structural xv6 and bare-metal results. These compile to a fixed target, and the instructions must
# not depend on which gcc happened to be installed: a listing that moves because the distro bumped
# its compiler is a spurious failure. Pinning the base to ubuntu:24.04 pins gcc 13.3.0 for both
# cross compilers, which is exactly what the committed listings were captured with
# (`Ubuntu 13.3.0-6ubuntu2~24.04.1`), so re-capturing here reproduces them byte for byte. A
# cross compiler's *target* output does not depend on the host architecture it runs on, so this
# gives the same instructions on a Mac, in CI, or on a contributor's laptop.
#
# Host timings are NOT built here. They are measured on real hardware (ch00), and bench/stamp.py
# refuses an emulated one — no container or QEMU can stand in for the board.
#
#   docker build -t sfs-toolchain .
#   docker run --rm -v "$PWD:/work" -w /work sfs-toolchain make regen-deterministic
#
# A gcc point-release inside 24.04 could in principle move a listing; if it does, that is a
# deliberate re-capture, committed on its own, not a silent drift.
#
# linux/amd64 is deliberate, and not only to match CI's x86 runner: on an arm64 host (an Apple
# Silicon Mac) `aarch64-linux-gnu` is the *native* target, so its gcc wants the native assembler
# and cannot cross-compile — pinning to amd64 makes both toolchains true cross compilers, exactly as
# CI has them. The compiler *output* is host-independent, so a listing captured here matches CI.
#
# CAVEAT for Apple Silicon: this image runs under emulation there, and the emulated gcc occasionally
# hits an internal-compiler-error segfault on the heavier files — it validates most listings and
# then falls over on one. That is a Rosetta/QEMU limitation, not a toolchain problem: on a real
# amd64 host (CI, an x86 laptop, a cloud runner) it runs clean start to finish. Regenerate there.
FROM --platform=linux/amd64 ubuntu:24.04

# gcc 13.3.0 for both targets (the matching binutils, hence objdump, come with them), and QEMU to
# boot xv6 and the bare-metal programs. qemu-user-static runs cross-built host-target binaries for
# the correctness checks. This is the same set quality.yml installs, pinned by the base image.
# --no-install-recommends keeps the image lean and avoids a python3-dev/gstreamer dependency mess
# that qemu's recommends drag in. The cross gcc packages ship the compiler but not, under that flag,
# their assembler or target libc headers — so binutils-*-linux-gnu (for `as`) and libc6-dev-*-cross
# (for <stdint.h> and friends, which the listings include) are named explicitly.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        gcc-riscv64-linux-gnu \
        gcc-aarch64-linux-gnu \
        binutils-riscv64-linux-gnu \
        binutils-aarch64-linux-gnu \
        libc6-dev-riscv64-cross \
        libc6-dev-arm64-cross \
        qemu-system-misc \
        qemu-user-static \
        python3 python3-pip \
        make git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# The tooling is stdlib plus PyYAML; the dev extras (pytest, ruff) let the same image run the whole
# check suite. --break-system-packages because a build container is not a system to protect.
COPY requirements.txt requirements-dev.txt /tmp/
RUN pip3 install --no-cache-dir --break-system-packages \
        -r /tmp/requirements.txt -r /tmp/requirements-dev.txt

WORKDIR /work
