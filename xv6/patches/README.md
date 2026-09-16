# Kernel patches

Empty until the traps-and-system-calls chapter, which is the first chapter that needs to change
the kernel rather than only read it.

Each patch is a `git diff` against the submodule commit pinned in `.gitmodules`, named
`NN-what-it-does.patch` so `git apply` order matches chapter order, and headed by a comment
saying which chapter added it and what it exists to measure. `xv6/README.md` has the recipe and
the reasoning.
