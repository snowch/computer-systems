"""Compile the reader's fault-policy code and ask it questions.

Three pure functions in one program, so there is one thing to build and one place to look. None
of them touches a kernel: the decisions a fault handler makes are arithmetic and comparisons, and
separating them from the machinery is how you find out whether you understand them.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from bench.measure import PORTABLE_FLAGS, HostTarget, compile_program
from bench.stamp import ROOT

POLICY = ROOT / "tests" / "ch08" / "policy.c"
NATIVE = HostTarget(name="native-other", cc="cc", flags=PORTABLE_FLAGS)

PAGE = 4096

#: The kernel's own names, so the reader is answering in the kernel's terms.
EAGER, LAZY = 1, 2
LOAD, STORE, FETCH = 13, 15, 12
ALLOCATE, KILL, PANIC = 0, 1, 2
AT_REQUEST, AT_TOUCH, NEVER = 0, 1, 2


def build(build_dir: Path) -> Path:
    return compile_program([POLICY], build_dir / "ch08policy", NATIVE).path


def ask(program: Path, commands: list[str]) -> dict:
    printed = subprocess.run(
        [str(program), *commands], capture_output=True, text=True, check=True
    ).stdout
    out: dict = {"faults": [], "action": {}, "observed": {}}
    for line in printed.splitlines():
        parts = line.split()
        match parts:
            case ["faults", count]:
                out["faults"].append(int(count))
            case ["action", cause, va, mapped, verdict]:
                out["action"][(int(cause), int(va), int(mapped))] = int(verdict)
            case ["observed", policy, requested, touched, available, verdict]:
                key = (int(policy), int(requested), int(touched), int(available))
                out["observed"][key] = int(verdict)
    return out


def count_faults(program: Path, runs: list[tuple[int, int]]) -> int:
    commands = [f"t{start:#x},{length:#x}" for start, length in runs] + ["n"]
    return ask(program, commands)["faults"][0]
