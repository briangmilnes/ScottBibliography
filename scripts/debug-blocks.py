#!/usr/bin/env python3
"""Show why extract-abstracts.py accepted or rejected each block of a PDF.

Diagnostic companion to extract-abstracts.py. Prints the front-matter blocks in
order with the verdict of each filter, so a wrong abstract can be traced to the
rule that caused it rather than guessed at.

Usage: python3 scripts/debug-blocks.py <pdf-path> [--plain]
"""

import argparse
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "ea", os.path.join(HERE, "extract-abstracts.py"))
ea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ea)

ap = argparse.ArgumentParser()
ap.add_argument("pdf")
ap.add_argument("--plain", action="store_true",
                help="use the unsplit reading instead of the column-split one")
a = ap.parse_args()

split, plain, per_page = ea.front_matter(a.pdf)
print("per-page chars:", per_page)
bs = ea.blocks(plain if a.plain else split)
for i, b in enumerate(bs[:24]):
    head = ea.RUNNING_HEAD.sub("", b)
    why = []
    if ea.rejected(head):
        for p in ea.NOT_ABSTRACT:
            if p.search(head):
                why.append("NOT_ABSTRACT<%s>" % p.pattern[:38])
    if ea.STOP.match(head):
        why.append("STOP")
    if ea.MARKER.match(head):
        why.append("MARKER")
    if not ea.is_prose(head):
        alpha = [c for c in head if c.isalpha()]
        lower = (sum(1 for c in alpha if c.islower()) / len(alpha)) if alpha else 0
        why.append("not-prose(len=%d alpha=%d lower=%.2f digit=%.2f front=%s)" % (
            len(head), len(alpha), lower,
            (sum(1 for c in head if c.isdigit()) / len(head)) if head else 0,
            bool(ea.FRONT.search(head))))
    print("\n[%02d] %s" % (i, ", ".join(why) if why else "ACCEPTED"))
    print("     " + head[:220].replace("\n", " "))
