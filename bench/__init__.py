"""The book's Python tooling: measurement, figures, and the outline.

Nothing in here measures anything by itself. It exists so that every number the book prints
arrives with the conditions that produced it attached, and so that a number whose conditions
have changed fails the build instead of quietly becoming wrong.

    outline.py    the book's shape — chapters, parts, targets, checkpoint tags
    stamp.py      what a result must carry, and where it is allowed to have been measured
    measure.py    building and running the book's C, and reducing repeated runs to one number
    xv6.py        booting the teaching kernel under QEMU and driving its shell
    figures.py    every table and diagram the book contains, declared once
    tables.py     results to markdown
    diagrams.py   figures, drawn by code, as deterministic SVG
    run_*.py      the runners that produce bench/results/*.json
"""
