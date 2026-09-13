"""Problem 0.2 — predict what the compiler does to a struct.

Here is the declaration, from tests/ch00/abi_puzzle.c. Do not run it yet.

    struct puzzle {
      char  flag;
      long  count;
      int   id;
      short code;
      char  tag;
    };

Fill in every None below with the number you expect on RV64 with the LP64D data model, then run

    python3 -m pytest tests/ch00/test_problem_2_abi.py

which compiles that struct for RISC-V, runs it, and compares. Chapter 0's tables give you the
sizes and alignments of the scalar types; the rest is the rule that follows from them.
"""

from __future__ import annotations

#: sizeof(struct puzzle), in bytes.
EXPECTED_SIZE: int | None = None

#: _Alignof(struct puzzle), in bytes.
EXPECTED_ALIGN: int | None = None

#: Byte offset of each member from the start of the struct.
EXPECTED_OFFSETS: dict[str, int | None] = {
    "flag": None,
    "count": None,
    "id": None,
    "code": None,
    "tag": None,
}
