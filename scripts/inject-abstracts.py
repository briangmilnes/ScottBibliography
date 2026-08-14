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
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OVERVIEW = os.path.join(ROOT, "docs", "overview.html")

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
        for j in range(i, len(src)):
            if src[j] == "[":
                depth += 1
            elif src[j] == "]":
                depth -= 1
                if depth == 0:
                    end = j
                    break
        depth, start = 0, None
        for j in range(i + 1, end):
            if src[j] == "{":
                if depth == 0:
                    start = j
                depth += 1
            elif src[j] == "}":
                depth -= 1
                if depth == 0:
                    yield start, j + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=os.path.join(ROOT, "analyses"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    recs = json.load(open(os.path.join(a.json, "abstracts-extracted.json"),
                          encoding="utf-8"))
    by_pdf = {r["pdf"]: r for r in recs}

    src = open(OVERVIEW, encoding="utf-8").read()
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
        print("\ndry run: docs/overview.html not written")
        return
    open(OVERVIEW, "w", encoding="utf-8").write(result)
    print("\nwrote %s (%d -> %d bytes)" % (OVERVIEW, len(src), len(result)))


if __name__ == "__main__":
    main()
