"""Problem 3 of the trap chapter — take the compiler's help away.

The trap chapter's handler is declared `interrupt("machine")`, and the compiler therefore saves the registers
it uses and ends the function with `mret` instead of `ret`. Write one that does neither: an
ordinary function, with the saving and the return done by you.

Put your program in `answer.c` beside this file. It is linked against the same runtime as every
program in the chapter, so `bare.h` is available and `main` is where it starts. It must print

    trap register_survived 1
    end trap

and it must not contain the string `interrupt(`.
"""
