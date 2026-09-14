---
description: Re-run the measurements and refresh every figure
---

Re-run what can be measured here and bring the book's figures back into agreement with the code.

1. `make bench-xv6` — every `xv6`-target result. Runs anywhere QEMU does.
2. `make bench-board` — every `host`-target result. **Only on the VisionFive 2 Lite**; it
   refuses to run anywhere else, and that refusal is correct.
3. `python3 scripts/render-figures.py` to rewrite the fragments and diagrams.
4. `python3 scripts/verify-numbers.py` — every stamp, hash and provenance rule.
5. If a measurement has landed for a figure still marked `pending=` in `bench/figures.py`,
   remove the marker in the same commit, and check that the prose around it now reads correctly
   with real numbers in place.

Report which results moved and by how much. A figure that changed materially since the last
commit needs the surrounding prose re-read, not just re-rendered.
