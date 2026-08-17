#!/usr/bin/env python3
"""Insert paper rows into index.html's Papers table in year order, renumbering.

Why a script: the table's leading "#" column is a running 1..N index, not the
bibliography number, so inserting a row mid-table shifts every number after it.
Doing that by hand across ~80 rows invites an off-by-one that no build would
catch, because the file is static HTML nobody compiles.

Rows to add are listed in NEW_ROWS below as (year, authors, href, title). The
script inserts each after the last existing row of the same year, so ordering
within a year stays as it was, then rewrites the whole column sequentially.

Idempotent: a row whose href is already present is skipped, so a second run
changes nothing.

Usage: python3 scripts/add-index-rows.py [--check]
"""

import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")

NEW_ROWS = [
    (1958, "Gal, Rosser &amp; Scott",
     "papers/Gal-Rosser-Scott-1958-Generalization-of-a-Lemma-of-G-F-Rose.pdf",
     "Generalization of a lemma of G. F. Rose"),
    (1964, "Scott",
     "papers/Scott-1964-Measurement-Structures-and-Linear-Inequalities.pdf",
     "Measurement structures and linear inequalities"),
    (1972, "Scott",
     "papers/Scott-1972-Semantical-Archaeology-A-Parable-REPRINT-SemanticsOfNaturalLanguage.pdf",
     "Semantical archaeology: a parable (1972 Reidel reprint)"),
    (1975, "Scott",
     "papers/Scott-1975-Some-Philosophical-Issues-Concerning-Theories-of-Combinators.pdf",
     "Some philosophical issues concerning theories of combinators"),
    (1993, "Scherlis &amp; Scott",
     "papers/Scherlis-Scott-1993-First-Steps-Towards-Inferential-Programming-REPRINT-ProgramVerification.pdf",
     "First steps towards inferential programming (1993 Kluwer reprint)"),
]

ROW = re.compile(
    r'<tr><td class="n">(\d+)</td><td class="y">(\d{4})</td>'
    r'<td>(.*?)</td><td><a href="([^"]+)">(.*?)</a></td></tr>')


def render(n, year, authors, href, title):
    return ('<tr><td class="n">%d</td><td class="y">%d</td><td>%s</td>'
            '<td><a href="%s">%s</a></td></tr>' % (n, year, authors, href, title))


# README.md carries the same list as a markdown table with its own running
# number, so it needs the same insert-and-renumber treatment. Authors there are
# written with a literal "&", not the HTML entity.
MD_ROW = re.compile(
    r'\|\s*(\d+)\s*\|\s*(\d{4})\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|'
    r'\s*\[PDF\]\(([^)]+)\)\s*\|')


def md_render(n, year, authors, href, title):
    return "| %d | %d | %s | %s | [PDF](%s) |" % (
        n, year, authors.replace("&amp;", "&"), title, href)


TARGETS = [
    ("index.html", ROW, render, "<h2>Papers</h2>",
     lambda m: (int(m.group(2)), m.group(3), m.group(4), m.group(5))),
    ("README.md", MD_ROW, md_render, "## Papers",
     lambda m: (int(m.group(2)), m.group(3), m.group(5), m.group(4))),
]


def patch(path, row_re, render_fn, heading, fields, check):
    lines = open(path, encoding="utf-8").read().split("\n")

    # Locate the Papers table by finding the contiguous run of rows that
    # follows its heading. Both files also carry a shorter book-length table,
    # which must not be touched.
    try:
        h = next(i for i, l in enumerate(lines) if l.strip() == heading)
    except StopIteration:
        sys.exit("could not find %r in %s" % (heading, path))
    first = next((i for i in range(h, len(lines)) if row_re.match(lines[i].strip())),
                 None)
    if first is None:
        sys.exit("no table rows found after %r in %s" % (heading, path))
    last = first
    while last + 1 < len(lines) and row_re.match(lines[last + 1].strip()):
        last += 1

    rows = []
    for i in range(first, last + 1):
        year, authors, href, title = fields(row_re.match(lines[i].strip()))
        rows.append([year, authors, href, title])

    have = {r[2] for r in rows}
    added = []
    for year, authors, href, title in NEW_ROWS:
        if href in have:
            continue
        # Insert after the last existing row of the same year; if the year is
        # new, before the first later year.
        pos = None
        for i, r in enumerate(rows):
            if r[0] <= year:
                pos = i + 1
        rows.insert(pos if pos is not None else 0, [year, authors, href, title])
        added.append(href)

    missing = [r[2] for r in rows
               if not os.path.exists(os.path.join(ROOT, r[2]))]
    if missing:
        sys.exit("ABORT: these hrefs do not resolve on disk:\n  " +
                 "\n  ".join(missing))

    body = [render_fn(i + 1, *r) for i, r in enumerate(rows)]
    out = lines[:first] + body + lines[last + 1:]

    print("%-12s rows %d -> %d, added %d, all hrefs resolve" % (
        os.path.basename(path), last - first + 1, len(rows), len(added)))
    for h_ in added:
        print("    + %s" % h_)
    if check:
        return
    open(path, "w", encoding="utf-8").write("\n".join(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report what would change without writing")
    a = ap.parse_args()
    for name, row_re, render_fn, heading, fields in TARGETS:
        patch(os.path.join(ROOT, name), row_re, render_fn, heading, fields,
              a.check)
    print("--check: nothing written" if a.check else "written")


if __name__ == "__main__":
    main()
