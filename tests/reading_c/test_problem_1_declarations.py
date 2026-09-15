"""Problem 1.1 — read a declaration from the name outwards.

The pairs that differ only by a parenthesis are the whole exercise, and the scaffolding asserts
that the set actually contains them: a table where every entry is distinguishable by its
punctuation alone would be a spelling test rather than a reading one.
"""

from __future__ import annotations

import pytest

from tests.reading_c.harness import (
    D_ARRAY,
    D_ARRAY_PTR,
    D_FUNC,
    D_FUNC_PTR,
    D_POINTER,
    D_PTR_ARRAY,
    D_VALUE,
    KIND_NAMES,
    ask,
)

CASES = {
    "int x": D_VALUE,
    "int *x": D_POINTER,
    "int **x": D_POINTER,
    "int x[4]": D_ARRAY,
    "int x[]": D_ARRAY,
    "int *x[4]": D_ARRAY_PTR,
    "int (*x)[4]": D_PTR_ARRAY,
    "int *x(void)": D_FUNC,
    "int (*x)(void)": D_FUNC_PTR,
    "int *(*x)(void)": D_FUNC_PTR,
    "int (*x[4])(void)": D_ARRAY_PTR,
}


def test_the_hard_pairs_are_actually_in_the_table():
    """Scaffolding: two pairs differing by one parenthesis, and they must disagree."""
    assert CASES["int *x[4]"] != CASES["int (*x)[4]"]
    assert CASES["int *x(void)"] != CASES["int (*x)(void)"]


def test_an_array_of_function_pointers_is_an_array_of_pointers():
    """Scaffolding: the one ch16 actually uses, and the one most likely to be got wrong.

    `int (*x[4])(void)` binds the subscript first, so the name is an array; what it is an array of
    is pointers. A reader who takes the `*` first calls it a pointer and is wrong.
    """
    assert CASES["int (*x[4])(void)"] == D_ARRAY_PTR


@pytest.mark.problem
def test_each_declaration_names_what_it_names(declarations):
    names = sorted(CASES)
    answered = ask(declarations, [f"d{name}" for name in names])
    wrong = {
        name: {
            "expected": KIND_NAMES[CASES[name]],
            "got": KIND_NAMES.get(answered["declare"][i], answered["declare"][i]),
        }
        for i, name in enumerate(names)
        if answered["declare"][i] != CASES[name]
    }
    assert not wrong, f"start at the name and read outwards, tightest binding first: {wrong}"
