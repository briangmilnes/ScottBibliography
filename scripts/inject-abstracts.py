#!/usr/bin/env python3
"""Write extracted abstracts into docs/overview.html.

Fills only entries whose `abstract` is currently null. The 24 abstracts already
recorded were transcribed by hand from the papers or their arXiv versions and
are left exactly as they are: this script adds what was missing, it does not
restate what was already checked.

Each abstract it adds carries an `abssrc` provenance string saying how the text
was obtained -- printed abstract or opening paragraph, text layer or OCR -- so a
reader can tell a transcription from a first-paragraph substitute.

Input is analyses/abstracts-extracted.json from extract-abstracts.py.
Pass --dry-run to report what would change without writing.

Usage: python3 scripts/inject-abstracts.py --json DIR [--dry-run]
"""

import argparse
import importlib.util
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OVERVIEW = os.path.join(ROOT, "docs", "overview.html")

# The string-aware scanner is shared with extract-abstracts.py rather than
# copied: both files must agree on where an entry object ends, and the naive
# brace count they used first stopped early once injected abstracts began to
# contain braces of their own ("E[x = {{u, v> :wevex})").
_spec = importlib.util.spec_from_file_location(
    "ea", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "extract-abstracts.py"))
_ea = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ea)
structural = _ea.structural

PROVENANCE = {
    ("marked", "text-layer"): "Verbatim from the paper (PDF).",
    ("marked", "ocr"): "Verbatim from the paper (PDF, OCR of the scan).",
    ("opening", "text-layer"):
        "Opening paragraph of the paper; no abstract is printed.",
    ("opening", "ocr"):
        "Opening paragraph of the paper (OCR of the scan); "
        "no abstract is printed.",
}


def js_string(s):
    """Encode as a double-quoted JavaScript string literal."""
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    s = s.replace("\n", " ").replace("\r", " ")
    # A literal </script> inside a script element would close it early.
    return '"' + s.replace("</", "<\\/") + '"'


def objects(src):
    """Yield (start, end) spans of every entry object in the three arrays."""
    for name in ("BOOKS", "PAPERS", "EXTRA"):
        i = src.index("const " + name)
        i = src.index("[", i)
        depth, end = 0, None
        for j, c in structural(src, i):
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    end = j
                    break
        if end is None:
            sys.exit("unterminated array: " + name)
        depth, start = 0, None
        for j, c in structural(src, i + 1):
            if j >= end:
                break
            if c == "{":
                if depth == 0:
                    start = j
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    yield start, j + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=os.path.join(ROOT, "analyses"))
    ap.add_argument("--page", default=OVERVIEW,
                    help="overview page to write into; defaults to "
                         "docs/overview.html")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    recs = json.load(open(os.path.join(a.json, "abstracts-extracted.json"),
                          encoding="utf-8"))
    by_pdf = {r["pdf"]: r for r in recs}

    src = open(a.page, encoding="utf-8").read()
    spans = list(objects(src))

    filled = skipped_recorded = skipped_none = 0
    out, last = [], 0
    for start, end in spans:
        obj = src[start:end]
        m = re.search(r'\bpdf:\s*"((?:[^"\\]|\\.)*)"', obj)
        if not m:
            continue
        rec = by_pdf.get(m.group(1))
        if rec is None:
            continue
        if re.search(r'\babstract:\s*"', obj):
            skipped_recorded += 1
            continue
        if not rec["abstract"]:
            skipped_none += 1
            continue
        prov = PROVENANCE.get((rec["mode"], rec["source"]))
        if prov is None:
            sys.exit("no provenance string for %s/%s" % (rec["mode"], rec["source"]))
        field = "abstract:%s, abssrc:%s" % (js_string(rec["abstract"]),
                                            js_string(prov))
        if re.search(r"\babstract:\s*null", obj):
            new = re.sub(r"\babstract:\s*null", field, obj, count=1)
        else:
            # EXTRA entries omit the key entirely rather than setting it null,
            # so the field is appended before the closing brace.
            new = obj[:-1].rstrip().rstrip(",") + ", " + field + "}"
        if new == obj:
            continue
        out.append(src[last:start])
        out.append(new)
        last = end
        filled += 1
    out.append(src[last:])
    result = "".join(out)

    print("entries filled          : %d" % filled)
    print("left as already recorded: %d" % skipped_recorded)
    print("left null (no abstract) : %d" % skipped_none)

    if a.dry_run:
        print("\ndry run: %s not written" % a.page)
        return
    open(a.page, "w", encoding="utf-8").write(result)
    print("\nwrote %s (%d -> %d bytes)" % (a.page, len(src), len(result)))


if __name__ == "__main__":
    main()
