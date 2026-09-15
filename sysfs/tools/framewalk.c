/* framewalk — climb the stack by hand, one saved frame pointer at a time.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * A debugger does this for you and makes it look like magic. It is not: with frame pointers
 * enabled, each frame stores the caller's frame pointer at a known offset from its own, so the
 * frames are a linked list and walking them is a loop. ch11 reads this alongside the same walk
 * done in gdb, and the point of having both is that the second stops being magic.
 *
 * Built with -fno-omit-frame-pointer, without which there is no list to walk — which is itself
 * worth knowing, because it is why a release build's stack trace is often a disappointment.
 */

#include <stdio.h>

/* Where a frame keeps the two things needed to leave it. Fixed by the psABI, not by this
 * program: on RV64 the frame pointer points one word past the top of its own frame, with the
 * return address immediately below it and the caller's frame pointer below that. */
#define RETURN_ADDRESS_SLOT (-1)
#define SAVED_FRAME_SLOT (-2)

#ifndef SYSFS_MAX_FRAMES
#define SYSFS_MAX_FRAMES 8
#endif

/* Read the frame pointer out of the machine rather than inferring it. __builtin_frame_address(0)
 * is the compiler telling us what it decided, which beats guessing at the register. */
static void walk(const char *from) {
  void **frame = (void **)__builtin_frame_address(0);
  printf("walk from %s\n", from);

  for (int depth = 0; depth < SYSFS_MAX_FRAMES; depth++) {
    void *return_address = frame[RETURN_ADDRESS_SLOT];
    void **caller = (void **)frame[SAVED_FRAME_SLOT];

    /* Stop before dereferencing nonsense. The outermost frame's saved pointer is not another
     * frame, and a walker that trusts it reads whatever happens to be there — which is how a
     * stack trace comes to contain a function that was never called. */
    if (caller == NULL || caller <= frame) {
      printf("frame %d end\n", depth);
      break;
    }
    printf("frame %d bytes %ld returns_to %p\n", depth, (long)((char *)caller - (char *)frame),
           return_address);
    frame = caller;
  }
  printf("end walk\n");
}

/* `noinline` on all three, and the reason is the lesson rather than a workaround. Without it the
 * optimiser inlines this chain into main and the walk below finds one frame where the source has
 * four — because there genuinely is one. A frame is not a call in the source, it is a call the
 * machine still makes, and inlining is the commonest reason a stack trace is shorter than the
 * code that produced it. */
static __attribute__((noinline)) void inner(void) { walk("inner"); }
static __attribute__((noinline)) void middle(void) { inner(); }
static __attribute__((noinline)) void outer(void) { middle(); }

int main(void) {
  outer();
  return 0;
}
