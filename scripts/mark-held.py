#!/usr/bin/env python3
"""Mark numbered entries as held in the overview pages: set pdf, drop route.

Why this exists: docs/overview.html computes an entry's state as
`held = !!it.pdf`, so acquiring a paper means editing exactly two fields of its
record -- `pdf:null` becomes the path, and the `route:"..."` retrieval note
becomes unreachable and must go. Doing that by hand across two pages invites
one of them being missed, which is how the held count and the page disagreed
before (fixed in 4c9e41d).

Both docs/overview.html and docs/overviewplusabstracts.html are patched, and
the path is checked to resolve on disk relative to docs/ before anything is
written.

Idempotent: an entry that already carries a pdf path is left alone.

Usage: python3 scripts/mark-held.py [--check]
"""

import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["docs/overview.html", "docs/overviewplusabstracts.html"]

# entry number -> path relative to docs/
HELD = {
    8: "../papers/Gal-Rosser-Scott-1958-Generalization-of-a-Lemma-of-G-F-Rose.pdf",
    19: "../papers/Scott-1964-Measurement-Structures-and-Linear-Inequalities.pdf",
    34: "../papers/Scott-1972-Semantical-Archaeology-A-Parable-REPRINT-SemanticsOfNaturalLanguage.pdf",
    50: "../papers/Scott-1975-Some-Philosophical-Issues-Concerning-Theories-of-Combinators.pdf",
    65: "../papers/Scherlis-Scott-1993-First-Steps-Towards-Inferential-Programming-REPRINT-ProgramVerification.pdf",
}

# Venue corrections for entries whose held copy is a reprint, not the original.
# Recorded on the page so a reader who opens the PDF is not surprised by a
# different volume and pagination than the citation gives.
VENUE_NOTE = {
    34: " — held as the 1972 Reidel reprint in Semantics of Natural Language, pp. 666–674.",
    65: " — held as the 1993 Kluwer reprint in Program Verification, pp. 99–133.",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    for page in PAGES:
        path = os.path.join(ROOT, page)
        src = open(path, encoding="utf-8").read()
        changed = skipped = 0
        for n, pdf in sorted(HELD.items()):
            target = os.path.normpath(os.path.join(ROOT, "docs", pdf))
            if not os.path.exists(target):
                sys.exit("ABORT: %s does not resolve on disk" % pdf)
            m = re.search(r"\{n:%d,.*?\},\n" % n, src, re.S)
            if not m:
                sys.exit("ABORT: entry n:%d not found in %s" % (n, page))
            rec = m.group(0)
            if 'pdf:null' not in rec:
                skipped += 1
                continue
            new = rec.replace('pdf:null', 'pdf:"%s"' % pdf)
            # The retrieval route describes how to obtain a paper that is now
            # held; leaving it would contradict the badge next to it.
            new = re.sub(r',\s*route:"(?:[^"\\]|\\.)*"', "", new)
            if n in VENUE_NOTE:
                new = re.sub(r'(venue:"(?:[^"\\]|\\.)*?)"',
                             lambda mm: mm.group(1) + VENUE_NOTE[n] + '"',
                             new, count=1)
            src = src[:m.start()] + new + src[m.end():]
            changed += 1
        print("%-40s marked %d, already held %d" %
              (page, changed, skipped))
        if not a.check:
            open(path, "w", encoding="utf-8").write(src)
    print("--check: nothing written" if a.check else "written")


if __name__ == "__main__":
    main()
