#!/usr/bin/env python3
"""Census the text layer of every PDF referenced by docs/overview.html.

Why this exists: docs/overview.html carries a hand-authored `abstract:` field
per entry, and 79 of them say `null`. That null is an assertion, not a
measurement -- it records "nobody transcribed one", which conflates three very
different states:

  has-text-layer  the PDF yields characters, so an abstract can be extracted
  image-only      the PDF yields ~nothing, so it needs OCR before any claim
  unreadable      pdftotext failed outright

This script measures which state each PDF is in and prints the per-file
character yield of its first two pages. It makes no claim about abstracts; it
only establishes which files can be read at all. Extraction is a later step.

Usage: python3 scripts/text-layer-census.py
"""

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OVERVIEW = os.path.join(ROOT, "docs", "overview.html")

# A PDF page of real prose yields hundreds of characters. Scanned pages with no
# text layer yield 0; pages carrying only a stamped header or page number yield
# a few dozen. 200 separates those two populations with a wide margin.
TEXT_LAYER_MIN_CHARS = 200


def js_arrays(src):
    """Yield (array_name, [object_source, ...]) for the three data arrays.

    Brace-matched rather than line-matched: entries wrap across lines, and a
    line-based scan silently undercounts them.
    """
    for name in ("BOOKS", "PAPERS", "EXTRA"):
        i = src.index("const " + name)
        i = src.index("[", i)
        depth = 0
        end = None
        for j in range(i, len(src)):
            if src[j] == "[":
                depth += 1
            elif src[j] == "]":
                depth -= 1
                if depth == 0:
                    end = j
                    break
        if end is None:
            sys.exit("unterminated array: " + name)
        body = src[i + 1:end]
        objs = []
        depth = 0
        start = None
        for j, c in enumerate(body):
            if c == "{":
                if depth == 0:
                    start = j
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    objs.append(body[start:j + 1])
        yield name, objs


def field(obj, key):
    m = re.search(r'\b' + key + r':\s*"((?:[^"\\]|\\.)*)"', obj)
    return m.group(1) if m else None


def page_text(path, first=1, last=2):
    """Return extracted text, or None if pdftotext failed."""
    try:
        r = subprocess.run(
            ["pdftotext", "-f", str(first), "-l", str(last), path, "-"],
            capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def main():
    src = open(OVERVIEW, encoding="utf-8").read()
    rows = []
    for name, objs in js_arrays(src):
        for obj in objs:
            pdf = field(obj, "pdf")
            if not pdf:
                continue
            ident = field(obj, "id")
            n = re.search(r"\bn:\s*(\d+)", obj)
            label = ("#" + n.group(1)) if n else ("book " + ident) if ident else "extra"
            title = field(obj, "title") or ""
            has_abs = re.search(r'\babstract:\s*"', obj) is not None
            path = os.path.normpath(os.path.join(ROOT, "docs", pdf))
            txt = page_text(path)
            if txt is None:
                state = "unreadable"
                chars = 0
            else:
                chars = len(txt.strip())
                state = "has-text" if chars >= TEXT_LAYER_MIN_CHARS else "image-only"
            rows.append((name, label, state, chars, has_abs, title, pdf))

    rows.sort(key=lambda r: (r[2] != "image-only", r[2] != "unreadable", r[0], r[1]))

    print("%-7s %-6s %-11s %8s %4s  %s" %
          ("array", "entry", "state", "chars", "abs?", "title"))
    for name, label, state, chars, has_abs, title, _ in rows:
        print("%-7s %-6s %-11s %8d %4s  %s" %
              (name, label, state, chars, "yes" if has_abs else "-", title[:58]))

    total = len(rows)
    by = {}
    for r in rows:
        by[r[2]] = by.get(r[2], 0) + 1
    print("\n--- census ---")
    print("pdf files examined      : %d" % total)
    for k in ("has-text", "image-only", "unreadable"):
        print("%-24s: %d" % (k, by.get(k, 0)))
    need = [r for r in rows if r[2] == "has-text" and not r[4]]
    print("has-text, abstract:null : %d   <- extractable, currently unrecorded" % len(need))
    ocr = [r for r in rows if r[2] != "has-text"]
    print("needs OCR before reading: %d" % len(ocr))
    for r in ocr:
        print("    %-6s %s" % (r[1], r[6]))


if __name__ == "__main__":
    main()
