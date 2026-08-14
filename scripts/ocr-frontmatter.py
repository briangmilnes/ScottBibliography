#!/usr/bin/env python3
"""OCR the front matter of image-only PDFs to sidecar text. Originals untouched.

Why this exists: 10 of the 86 held PDFs are scans with no text layer, or with a
text layer covering only a scanned cover sheet. pdftotext returns nothing
usable for them, so their abstracts cannot be read by extract-abstracts.py.

Why it does not write back into the PDFs: these are mathematics papers, and
ocrmypdf's normal in-place mode re-encodes the file through Ghostscript, which
can degrade or drop embedded math fonts. Every run here writes its rebuilt PDF
to a throwaway path under --work and keeps only the --sidecar text. The files
in papers/ are never opened for writing and stay byte-identical.

Reads the mode from analyses/abstracts-extracted.json (produced by
extract-abstracts.py) and processes every entry whose mode is no-text or none.

Usage: python3 scripts/ocr-frontmatter.py --json DIR --work DIR
"""

import argparse
import importlib.util
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# CHAPTER_START is shared with extract-abstracts.py rather than duplicated: if
# the two disagreed about where a contribution begins, OCR would be run on one
# page range and read back from another.
_spec = importlib.util.spec_from_file_location(
    "ea", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "extract-abstracts.py"))
_ea = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ea)
CHAPTER_START = _ea.CHAPTER_START

# OCR only the front matter. The Compendium of Continuous Lattices is a whole
# book; rasterising all of it to read one abstract would cost minutes per file.
OCR_PAGE_SPAN = 8

# The corpus is English. Adding languages to tesseract lowers accuracy on text
# that is in fact English, so extra languages are opt-in per run.
DEFAULT_LANG = "eng"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=os.path.join(ROOT, "analyses"),
                    help="directory holding abstracts-extracted.json")
    ap.add_argument("--work", required=True,
                    help="scratch directory for sidecar text and discarded PDFs")
    ap.add_argument("--lang", default=DEFAULT_LANG)
    a = ap.parse_args()

    recs = json.load(open(os.path.join(a.json, "abstracts-extracted.json"),
                          encoding="utf-8"))
    todo = [r for r in recs
            if r["mode"] in ("no-text", "none") or r.get("needs_ocr")]
    if not todo:
        print("nothing to OCR")
        return

    os.makedirs(a.work, exist_ok=True)
    sidecar_dir = os.path.join(a.work, "sidecar")
    os.makedirs(sidecar_dir, exist_ok=True)

    ok = fail = 0
    for r in todo:
        src = os.path.normpath(os.path.join(ROOT, "docs", r["pdf"]))
        stem = os.path.splitext(os.path.basename(src))[0]
        txt = os.path.join(sidecar_dir, stem + ".txt")
        out = os.path.join(a.work, stem + ".ocr.pdf")
        before = os.path.getsize(src)
        start = CHAPTER_START.get(stem, 1)
        pages = "%d-%d" % (start, start + OCR_PAGE_SPAN - 1)
        cmd = ["ocrmypdf", "--force-ocr", "--pages", pages,
               "-l", a.lang, "--sidecar", txt, src, out]
        p = subprocess.run(cmd, capture_output=True, text=True)
        after = os.path.getsize(src)
        if after != before:
            sys.exit("ABORT: %s changed size %d -> %d" % (src, before, after))
        if p.returncode == 0 and os.path.exists(txt):
            n = len(open(txt, encoding="utf-8", errors="replace").read().strip())
            print("%-8s ok    %6d chars  %s" % (r["entry"], n, stem[:52]))
            ok += 1
        else:
            print("%-8s FAIL  rc=%d  %s" % (r["entry"], p.returncode, stem[:52]))
            print("         " + (p.stderr or "").strip().split("\n")[-1][:110])
            fail += 1

    print("\nocr ok: %d   failed: %d" % (ok, fail))
    print("sidecar text: %s" % sidecar_dir)
    print("originals in papers/ verified unchanged by size after every run")


if __name__ == "__main__":
    main()
