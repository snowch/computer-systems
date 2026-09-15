---
title: "The File System"
short_title: "20 · The File System"
---

(the-file-system)=
# 20 · The File System

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` — the teaching kernel under QEMU |
| **Prerequisites** | [ch19](#scheduling-and-context-switches) |
| **What it measures** | What one byte costs the disk, as a difference between two runs: `bench/results/blocks-xv6.json` |
:::

## The question

What has to be true on the disk for a crash mid-write to be survivable?

Every mechanism in [Part IV](#part4) so far has assumed the machine keeps running. A lock is held until it
is released; a page is mapped until it is unmapped; a process runs until it is switched away.
A file system cannot assume any of that. The power can fail between any two instructions, and what
is on the platter afterwards is whatever had reached it — so the only tool available is *the order
things are written in*, and the whole design follows from that one constraint.

## The material

### One byte

Start at the end, with what it costs.

```{include} _generated/the-file-system-amplification.md
```

The two runs are the same program making the same calls, differing in a single `write`. The last
column is therefore the byte's and nothing else: the file is created in both, removed in both, and
the shell forks and execs the program in both.

Written as the question was asked:

```{include} _generated/the-file-system-cost.md
```

That is the amplification factor, and it is not a rounding error. Nor is it waste — every one of
those writes is doing something, and the rest of this chapter is what.

Notice the second row of the last table as well. A file with nothing whatever in it, created and
immediately removed, costs more disk traffic than the byte does. Most of what a file system does
is bookkeeping, and the data is the small part.

### Why every block is written twice

Take the last column apart. The byte caused four blocks to be modified and ten writes to reach
the disk, and those two numbers are related by the design rather than by accident.

A committed transaction writes each of its blocks **twice**. Once into the log — a reserved run of
blocks that is not where the data belongs — and then again to the place it actually belongs.
Around those it writes the log's header twice: once to say what the transaction contains, and once
afterwards to say that it no longer contains anything.

So the writes a transaction costs are twice its blocks plus two, and the check in
`bench/run_blocks.py` refuses to stamp a result where that no longer holds. Problem 20.1 is that
formula, and it is worth deriving before reading on.

Doubling the traffic looks like a strange thing to do on purpose. It is the only thing that works.

### The commit is one write

Here is the constraint stated precisely. A crash can happen between any two block writes. For the
file system to be recoverable, **every prefix of what it writes must leave a state that recovery
can turn into a correct one.**

Consider updating a file in place, with no log. Write the data block, then the inode that records
the new size. A crash between them leaves a file whose size says one thing and whose contents say
another, and nothing on the disk records which was intended. There is no recovery procedure,
because there is no information to recover from.

The log removes the ambiguity by making one single write the moment everything becomes true:

1. The modified blocks are copied into the log. The header does not mention them, so as far as
   anything is concerned they are scratch.
2. **The header is written, naming them.** The transaction is now real.
3. The blocks are copied from the log to their homes.
4. The header is cleared. The transaction is over.

A crash before step 2 leaves blocks in the log that nothing points at, and recovery ignores them.
A crash after step 2 and before step 4 leaves a header naming blocks, and recovery copies them to
their homes — which is safe whether or not step 3 had already done it, because copying the same
block to the same place twice is the same as copying it once.

**There is no moment at which half a transaction is visible.** That is the entire purpose of the
exercise, and it is bought with exactly one thing: writing the header after the log and before the
homes. Problem 20.3 asks you to check the other five orderings, and the ones that fail are the
ones that look reasonable.

### Idempotence is doing the real work

Step 3's harmlessness is worth stopping on, because it is doing more than it appears to.

Recovery does not know how far the original run got. It cannot know: the only evidence is the
header, and the header says what the transaction *contains*, not what has been done about it. So
recovery replays everything the header names, every time, and this is correct only because
replaying an already-installed block changes nothing.

That is why the log holds **blocks and not changes**. "Set byte 40 of block 6 to `x`" is not safe
to apply twice if it is expressed as an increment; "block 6 now looks like this" is safe to apply
any number of times. Choosing the idempotent representation is what makes a recovery procedure
that does not need to know anything about history.

It also explains the amplification. A log of changes would be far smaller than a log of blocks,
and would not survive being replayed twice.

### The seven layers, and where the traffic comes from

Under `write` there are seven things, and each one is why one of the numbers above is what it is:
the file descriptor that names an open file, the inode that describes a file, the directory that
maps names to inodes, the block allocator that finds free space, the log that makes a group of
updates atomic, the buffer cache that keeps blocks in memory and decides when they reach the disk,
and the disk driver from [ch17](#interrupts-and-drivers).

Four blocks were modified for one byte: the data block itself, the inode recording that the file
is now one byte long and where that byte is, the bitmap recording that the data block is no longer
free, and the block the buffer cache had to fetch to make the change. The traffic is not the file
system being careless. It is a byte requiring four separate facts to be true at once, and a design
in which they become true together or not at all.

### The cache is why the reads are so few

One number is nearly zero and is worth a sentence. Creating and deleting a whole file read
**nothing** from the disk, and writing a byte read three blocks.

That is [ch17](#interrupts-and-drivers)'s buffer cache. A block already in memory is not fetched, and a short
workload touches the same handful of blocks — the superblock, the log header, the inode block,
the bitmap — over and over. Reads are the operation a cache can eliminate entirely; writes are the
operation it can only delay, and a log is a design that deliberately declines to delay them very
much.

## What we measured

Blocks reaching the disk for two runs of one program that differ by a single `write` call, and the
difference between them. Nothing was timed: what a block write *costs* is a property of a disk,
and the disk here is a file on a laptop.

The measurement is a difference for a reason worth repeating. A single run would have charged the
byte for the shell forking, for the kernel reading the program, and for the directory lookup that
found it — all of which happen whether a byte is written or not, and all of which are larger than
the thing being measured.

## What this cannot tell you

**What any of it costs in time.** A real disk charges enormously more for a write that has to
move a head than for one that does not, and orders of magnitude less for both if it is solid
state. The amplification factor is the same on every disk; what it means is not, and a design that
is obviously wasteful on one is obviously correct on another.

**Whether the double write is worth it.** The chapter has shown what the log buys and what it
costs, and has not compared it with the alternatives — soft updates, copy-on-write trees,
journalling only metadata — each of which makes a different trade and none of which is visible
here.

**Anything about the disk lying.** The whole argument rests on writes reaching the platter in the
order they were issued, and real drives have caches that reorder and acknowledge early. A file
system that assumes otherwise is correct on paper and loses data in practice, and the machinery
for saying "this one, really, now" is a write barrier — which is an instruction to a device rather
than to a processor, and shares nothing with [ch18](#locks-and-memory-ordering)'s fences but a name.

**What happens when the log is too small.** xv6 panics on a transaction larger than the log, which
is a reasonable thing for a teaching kernel to do and not a reasonable thing for a file system to
do. Making a large operation into several transactions that are each individually safe is most of
what makes a real journalling file system hard.

## Problems

Three, in `tests/the_file_system/filesystem.c`.

**20.1 — How many block writes does a transaction cost?**
Derive the formula. It is graded partly against this chapter's own measurement: whatever you
arrive at has to turn the blocks the book logged into the writes the book counted, or one of the
two is wrong.

```bash
python3 -m pytest tests/the_file_system/test_problem_1_writes.py
```

**20.2 — What must recovery do after a crash at each stage?**
Five stages; the answer changes exactly once on the way up and once on the way down. Finding where
is the design.

```bash
python3 -m pytest tests/the_file_system/test_problem_2_crash.py
```

**20.3 — Which orderings are safe?**
Six orderings of the same three writes. Exactly one is safe at every point a crash could happen,
and the question is not which produces the right end state — all six do, if nothing goes wrong.

```bash
python3 -m pytest tests/the_file_system/test_problem_3_ordering.py
```

## Where to go next

xv6's `kernel/log.c` @xv6-riscv-source is a hundred and fifty lines and is the whole of this
chapter. Read `commit` first — it is five lines and they are in the order this chapter argued for —
then `recover_from_log`, which is what makes those five lines mean anything.

`kernel/fs.c` and `kernel/bio.c` are the layers underneath, and `bio.c` is now the third thing in
this book to turn out to be a cache with a lock around it.

[ch21](#the-same-program-on-both-targets) is the hinge. Everything [Part IV](#part4) has established is about what a program *does*, on a
target chosen because you can stop it and look. The next chapter puts the same program on a machine
where you cannot, and asks what the first instrument failed to tell you — which is the question the
whole of [Part V](#part5) exists to answer.
