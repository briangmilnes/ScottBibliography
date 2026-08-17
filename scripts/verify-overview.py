#!/usr/bin/env python3
"""Check docs/overview.html parses as the page's own JavaScript would read it.

Why a dedicated checker: the entry arrays are scanned by matching braces, and
abstracts contain braces of their own -- "(x,y) = {{x}, {x, y}}" -- so a naive
matcher silently mis-parses the file and reports nonsense counts. This scanner
tracks string state, counting structure only outside string literals.

It reports per-array counts of entries, abstracts, nulls and provenance
strings, and fails loudly on an unterminated string or unbalanced structure.

Usage: python3 scripts/verify-overview.py
"""

import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OVERVIEW = os.path.join(ROOT, "docs", "overview.html")


def scan_array(src, name):
    """Return the list of entry-object sources for one array, string-aware."""
    i = src.index("const " + name)
    i = src.index("[", i)
    depth = 0
    in_str = False
    quote = ""
    esc = False
    objs, start, odepth = [], None, 0
    for j in range(i, len(src)):
        c = src[j]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == quote:
                in_str = False
            continue
        if c in "\"'":
            in_str, quote = True, c
            continue
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                if odepth != 0:
                    sys.exit("unbalanced braces in %s" % name)
                return objs
        elif c == "{":
            if odepth == 0:
                start = j
            odepth += 1
        elif c == "}":
            odepth -= 1
            if odepth == 0:
                objs.append(src[start:j + 1])
    sys.exit("unterminated array: " + name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", default=OVERVIEW,
                    help="overview page to verify; defaults to docs/overview.html")
    a = ap.parse_args()
    src = open(a.page, encoding="utf-8").read()
    if src.count("<script") != src.count("</script"):
        sys.exit("script tags unbalanced")

    total_entries = total_abs = total_null = total_src = 0
    print("%-7s %8s %9s %6s %7s" % ("array", "entries", "abstract", "null", "abssrc"))
    for name in ("BOOKS", "PAPERS", "EXTRA"):
        objs = scan_array(src, name)
        has = sum(1 for o in objs if re.search(r'\babstract:\s*"', o))
        nul = sum(1 for o in objs if re.search(r"\babstract:\s*null", o))
        prov = sum(1 for o in objs if re.search(r'\babssrc:\s*"', o))
        print("%-7s %8d %9d %6d %7d" % (name, len(objs), has, nul, prov))
        total_entries += len(objs)
        total_abs += has
        total_null += nul
        total_src += prov

    print("\ntotal entries        : %d" % total_entries)
    print("with abstract text   : %d" % total_abs)
    print("abstract:null        : %d" % total_null)
    print("carrying abssrc      : %d" % total_src)

    pdfs = re.findall(r'\bpdf2?:\s*"([^"]+)"', src)
    missing = [p for p in pdfs
               if not os.path.exists(os.path.normpath(
                   os.path.join(ROOT, "docs", p)))]
    print("pdf paths            : %d, unresolved %d" % (len(pdfs), len(missing)))
    for m in missing:
        print("   MISSING " + m)

    if total_entries != 109:
        print("\nNOTE: expected 109 entry objects (4 books + 99 papers + 6 extra)")
    if missing:
        sys.exit(1)


if __name__ == "__main__":
    main()
